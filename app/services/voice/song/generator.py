import os
import json
import boto3
import asyncio
import logging
import aiohttp
import tempfile
import time
from datetime import datetime
from fastapi import HTTPException

from app.utils.timing import timing_decorator
from app.utils.logger.setup import setup_logger
from app.utils.process_text import strip_rich_text_tags

from app.models.voice.song import SongRequest, SongResponse

# Load environment variables
if not os.getenv("ENVIRONMENT"):
    from dotenv import load_dotenv
    load_dotenv()

# 로거 설정
logger = setup_logger('voice_song')

s3_client = boto3.client(
    service_name=os.getenv("NAVER_SERVICE_NAME"),
    endpoint_url=os.getenv("NAVER_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("ACCESS"),
    aws_secret_access_key=os.getenv("SECRET")
)

BUCKET_NAME = os.getenv("NAVER_BUCKET_NAME")
FOLDER_NAME = os.getenv("NAVER_BUCKET_SONG")


def generate_unique_filename(base_name: str, extension: str) -> str:
    """SOUND API와 동일한 패턴으로 파일명 생성 (timestamp 기반)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 확장자에서 점(.) 제거 (이미 있을 경우 대비)
    ext = extension.lstrip('.')
    return f"song_{timestamp}.{ext}"


@timing_decorator
async def create_audio_task(request: SongRequest, max_retries: int = 5, retry_interval: int = 10) -> str:
    """
    Create an audio task and return the generated task ID.
    """
    start_time = time.time()
    try:
        logger.info("🔄 AceData Cloud 시도")
        result = await _create_audio_task_acedata(request, max_retries, retry_interval)
        if result:
            execution_time = time.time() - start_time
            logger.info(f"✅ AceData Cloud 성공 (처리 시간: {execution_time:.2f}초)")
            return result
    except Exception as e:
        execution_time = time.time() - start_time
        logger.warning(f"AceData Cloud 실패: {e} (처리 시간: {execution_time:.2f}초)")
    
    raise HTTPException(status_code=500, detail="Failed to create audio task with AceData Cloud.")

async def _create_audio_task_acedata(request: SongRequest, max_retries: int = 5, retry_interval: int = 10) -> str:
    """AceData Cloud를 통한 오디오 태스크 생성"""
    start_time = time.time()
    try:
        # Unity Rich Text 태그 필터링
        clean_lyrics = request.lyrics if isinstance(request.lyrics, str) else "\n".join(request.lyrics)
        clean_lyrics = strip_rich_text_tags(clean_lyrics)

        payload = {
            "action": "generate",
            "model": "chirp-v4",
            "custom": True,
            "instrumental": False,
            "lyric": clean_lyrics,
            "title": request.songTitle,
            "style": "a fairy tale song for children",
            "prompt": "Create a fairy tale song for children.",
            "continue_at": 120
        }

        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {os.getenv('SUNO')}",
            "content-type": "application/json",
        }

        timeout = aiohttp.ClientTimeout(total=600)
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 AceData Cloud 시도 {attempt + 1}/{max_retries}")
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post("https://api.acedata.cloud/suno/audios", json=payload, headers=headers) as response:
                        logger.info(f"📡 AceData Cloud HTTP 상태: {response.status}")
                        
                        if response.status == 200:
                            response_data = await response.json()
                            logger.info(f"AceData Cloud 응답: {response_data}")

                            task_id = response_data.get("task_id")
                            if not task_id:
                                raise ValueError("Task ID not found in response.")
                            
                            execution_time = time.time() - start_time
                            logger.info(f"✅ AceData Cloud 태스크 생성 완료 (처리 시간: {execution_time:.2f}초)")
                            return task_id
                        else:
                            error_text = await response.text()
                            logger.error(f"AceData Cloud HTTP {response.status}: {error_text}")
                            raise Exception(f"AceData Cloud HTTP {response.status}: {error_text}")
            except Exception as e:
                logger.error(f"AceData Cloud - Error on attempt {attempt + 1}: {e}")
            await asyncio.sleep(retry_interval)

        raise ValueError("Failed to create audio task with AceData Cloud.")
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"AceData Cloud - Unexpected error: {e} (처리 시간: {execution_time:.2f}초)")
        raise

@timing_decorator
async def retrieve_audio_file(task_id: str, max_retries: int = 20, retry_interval: int = 5):
    """
    Retrieve the audio file from the response when the task is complete.
    """
    start_time = time.time()
    try:
        payload = {"id": task_id, "action": "retrieve"}
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {os.getenv('SUNO')}",
            "content-type": "application/json",
        }

        for attempt in range(max_retries):
            logger.info(f"🔄 Task 검색 시도 {attempt + 1}/{max_retries}")
            
            try:
                logger.info("🔄 AceData Cloud task 검색")
                async with aiohttp.ClientSession() as session:
                    async with session.post("https://api.acedata.cloud/suno/tasks", json=payload, headers=headers) as response:
                        logger.info(f"📡 AceData Cloud task HTTP 상태: {response.status}")
                        
                        if response.status == 200:
                            response_data = await response.json()
                            logger.info(f"AceData Cloud task 응답: {response_data}")

                            task_response = response_data.get("response", {})
                            if task_response.get("success"):
                                task_data = [
                                    item for item in task_response.get("data", [])
                                    if item.get("state") == "succeeded"
                                ]
                                if task_data:
                                    execution_time = time.time() - start_time
                                    logger.info(f"✅ AceData Cloud task 성공 (처리 시간: {execution_time:.2f}초)")
                                    return (
                                        task_data[0].get("audio_url"),
                                        task_data[0].get("image_url"),
                                        task_data[0].get("video_url"),
                                    )
                            else:
                                logger.info(f"Task {task_id} not complete yet. Retrying...")
                        else:
                            error_text = await response.text()
                            logger.warning(f"AceData Cloud task HTTP {response.status}: {error_text}")
            except Exception as e:
                logger.warning(f"AceData Cloud task 검색 실패: {e}")
                
            await asyncio.sleep(retry_interval)

        raise ValueError(f"Task {task_id} did not complete within retries.")
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Error retrieving audio file: {e} (처리 시간: {execution_time:.2f}초)")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve audio file.")


@timing_decorator
async def download_and_upload_to_s3(file_url: str, file_name: str) -> str:
    """
    Download the file from the given URL and upload it to S3 with public access.
    """
    start_time = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                response.raise_for_status()

                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file_path = temp_file.name
                    while chunk := await response.content.read(8192):
                        temp_file.write(chunk)

                s3_key = f"{FOLDER_NAME}/{file_name}"
                s3_client.upload_file(
                    temp_file_path,
                    BUCKET_NAME,
                    s3_key,
                    ExtraArgs={'ACL': 'public-read'}
                )

                os.remove(temp_file_path)

                public_url = f"{BUCKET_NAME}/{s3_key}"
                execution_time = time.time() - start_time
                logger.info(f"✅ S3 업로드 완료: {public_url} (처리 시간: {execution_time:.2f}초)")
                return public_url
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"File upload error to S3: {e} (처리 시간: {execution_time:.2f}초)")
        raise HTTPException(
            status_code=500, detail="Failed to upload file to S3.")


@timing_decorator
async def process_song_request(request: SongRequest) -> SongResponse:
    """
    Process a song request: create task, retrieve files, and upload to S3.
    """
    start_time = time.time()
    if not request.lyrics or (isinstance(request.lyrics, list) and len(request.lyrics) == 0):
        return SongResponse(
            mp3_url="",
            image_url="",
            video_url="",
            state="Incomplete"
        )
    try:
        logger.info(f"🎵 노래 생성 시작: {request.songTitle}")
        
        task_id = await create_audio_task(request)

        audio_url, _, _ = await retrieve_audio_file(task_id)

        mp3_file_name = generate_unique_filename(
            request.songTitle, ".mp3")

        mp3_file_url = await download_and_upload_to_s3(audio_url, mp3_file_name)

        execution_time = time.time() - start_time
        logger.info(f"✅ 노래 생성 완료: {mp3_file_url} (총 처리 시간: {execution_time:.2f}초)")
        
        return SongResponse(
            mp3_url=mp3_file_url,
            image_url="",
            video_url="",  # 빈 video_url 반환
            state="Completed"
        )
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Error during song processing: {e} (처리 시간: {execution_time:.2f}초)")
        return SongResponse(
            mp3_url="",
            image_url="",
            video_url="",
            state="Incomplete"
        )