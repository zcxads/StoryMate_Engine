import os, asyncio, json, time
from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.config import settings
from app.models.voice.tts import (
    TTSRequest, SingleTTSRequest, TTSResponse, SingleTTSResponse,
    JobStatusResponse, VoiceListResponse,
    PlayTTSRequest, SupportedTTSModelsResponse, SUPPORTED_TTS_MODELS
)
from app.services.voice.tts.generator import TTSService
from app.services.voice.tts.notification import notification_service

# 로깅 설정
from app.utils.logger.setup import setup_logger
logger = setup_logger('tts_api', 'logs/tts')

router = APIRouter(prefix="/tts")
@router.get("/models", response_model=SupportedTTSModelsResponse)
async def get_supported_models() -> SupportedTTSModelsResponse:
    """지원되는 TTS 모델 목록을 반환합니다."""
    # settings의 기본 제공자 모델을 기본값으로 노출
    default_model = settings.openai_tts_model if settings.default_tts_provider == "openai" else settings.tts_model
    return SupportedTTSModelsResponse(
        supported_models=SUPPORTED_TTS_MODELS,
        default_model=default_model,
        total_count=len(SUPPORTED_TTS_MODELS)
    )


# TTS 서비스 인스턴스
tts_service = TTSService()

@router.get("/voices", response_model=VoiceListResponse)
async def get_available_voices(provider: str | None = None):
    """사용 가능한 목소리 목록 조회 (config 기반 제공자 선택)"""
    return tts_service.get_voice_list(provider)

@router.get("/health")
async def health_check():
    """API 상태 및 TTS 연결 확인"""

    # TTS API 연결 테스트 (설정된 제공자)
    tts_connected = await tts_service.test_tts_connection()

    # 알림 서비스 연결 통계
    connection_stats = notification_service.get_connection_stats()

    return {
        "status": "healthy" if tts_connected else "unhealthy",
        "tts_connection": tts_connected,
        "tts_provider": settings.tts_provider,
        "app_name": settings.app_name,
        "version": settings.app_version,
        "notification_connections": connection_stats
    }

@router.post("/generate", response_model=SingleTTSResponse)
async def generate_single_tts(request: SingleTTSRequest):
    """단일 TTS 파일 생성"""
    
    try:
        result = await tts_service.generate_single_tts(request)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/generate/batch", response_model=TTSResponse)
async def generate_batch_tts(request: TTSRequest):
    """배치 TTS 파일 생성"""
    
    try:
        # 입력 데이터 검증
        if not request.texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="텍스트가 필요합니다."
            )
        
        result = await tts_service.generate_batch_tts(request)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"배치 TTS 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.websocket("/jobs/{job_id}/ws")
async def websocket_job_status(websocket: WebSocket, job_id: str):
    """WebSocket을 통한 실시간 작업 상태 알림 - 하트비트 개선"""
    
    await websocket.accept()
    await notification_service.add_websocket_connection(job_id, websocket)
    
    connection_start_time = time.time()
    last_ping_time = time.time()
    ping_interval = 15  # 15초마다 핑
    max_idle_time = 60  # 60초 이상 응답 없으면 연결 종료
    
    try:
        # 초기 상태 전송
        job_status = tts_service.get_job_status(job_id)
        if job_status:
            await websocket.send_json({
                "type": "initial_status",
                "data": {
                    "job_id": job_id,
                    "status": job_status.status.value,
                    "progress": job_status.progress,
                    "total_files": job_status.total_files,
                    "completed_files": job_status.completed_files,
                    "failed_files": job_status.failed_files
                },
                "connection_info": {
                    "connected_at": connection_start_time,
                    "ping_interval": ping_interval
                }
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Job {job_id} not found"
            })
            await websocket.close()
            return
        
        # 연결 유지 및 핑-퐁 (개선된 로직)
        while True:
            try:
                # 동적 타임아웃 계산 (연결 시간에 따라 조정)
                connection_duration = time.time() - connection_start_time
                if connection_duration > 300:  # 5분 이상 연결된 경우
                    current_timeout = 10  # 더 짧은 타임아웃
                else:
                    current_timeout = 20  # 기본 타임아웃
                
                # 클라이언트로부터 메시지 대기
                message = await asyncio.wait_for(
                    websocket.receive_text(), 
                    timeout=current_timeout
                )
                
                current_time = time.time()
                
                if message == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": current_time,
                        "server_time": current_time
                    })
                    last_ping_time = current_time
                    
                elif message == "status":
                    # 현재 상태 요청
                    current_status = tts_service.get_job_status(job_id)
                    if current_status:
                        # 연결 건강성 정보 추가
                        health_info = await notification_service.get_connection_health(job_id)
                        
                        await websocket.send_json({
                            "type": "current_status",
                            "data": {
                                "job_id": job_id,
                                "status": current_status.status.value,
                                "progress": current_status.progress,
                                "total_files": current_status.total_files,
                                "completed_files": current_status.completed_files,
                                "failed_files": current_status.failed_files
                            },
                            "connection_health": health_info,
                            "timestamp": current_time
                        })
                
                elif message == "health":
                    # 연결 건강성 정보 요청
                    health_info = await notification_service.get_connection_health(job_id)
                    await websocket.send_json({
                        "type": "health_status",
                        "health": health_info,
                        "connection_duration": current_time - connection_start_time,
                        "last_ping_ago": current_time - last_ping_time,
                        "timestamp": current_time
                    })
                
                elif message.startswith("heartbeat_interval:"):
                    # 클라이언트가 하트비트 간격 조정 요청
                    try:
                        new_interval = int(message.split(":")[1])
                        if 5 <= new_interval <= 60:  # 5초~60초 범위
                            ping_interval = new_interval
                            await websocket.send_json({
                                "type": "heartbeat_interval_updated",
                                "new_interval": ping_interval,
                                "timestamp": current_time
                            })
                    except (ValueError, IndexError):
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid heartbeat interval format"
                        })
                
                else:
                    # 알 수 없는 메시지
                    await websocket.send_json({
                        "type": "unknown_message",
                        "received": message,
                        "timestamp": current_time
                    })
                
            except asyncio.TimeoutError:
                current_time = time.time()
                time_since_last_ping = current_time - last_ping_time
                
                # 마지막 핑으로부터 너무 오래 지났으면 연결 종료
                if time_since_last_ping > max_idle_time:
                    logger.warning(f"⏰ WebSocket connection timeout for job {job_id} (idle: {time_since_last_ping:.1f}s)")
                    await websocket.send_json({
                        "type": "connection_timeout",
                        "idle_time": time_since_last_ping,
                        "max_idle_time": max_idle_time
                    })
                    break
                
                # 서버에서 핑 전송 (클라이언트 응답 확인)
                try:
                    await websocket.send_json({
                        "type": "server_ping",
                        "timestamp": current_time,
                        "connection_duration": current_time - connection_start_time,
                        "expected_pong": True
                    })
                    logger.debug(f"💓 Server ping sent to job {job_id}")
                except:
                    logger.warning(f"❌ Failed to send server ping to job {job_id}")
                    break
                    
            except WebSocketDisconnect:
                logger.info(f"📡 WebSocket disconnected for job {job_id}")
                break
            except Exception as e:
                logger.error(f"❌ WebSocket error for job {job_id}: {str(e)}")
                break
                
    except Exception as e:
        logger.error(f"❌ WebSocket setup error for job {job_id}: {str(e)}")
        
    finally:
        await notification_service.remove_websocket_connection(job_id, websocket)

@router.get("/jobs/{job_id}/stream")
async def stream_job_status(job_id: str):
    """Server-Sent Events를 통한 실시간 작업 상태 스트림 - 하트비트 개선"""
    
    async def event_stream():
        # SSE 연결을 위한 큐 생성
        event_queue = asyncio.Queue()
        connection_start_time = time.time()
        last_event_time = time.time()
        heartbeat_interval = 20  # 20초마다 하트비트
        max_queue_size = 100
        
        try:
            await notification_service.add_sse_connection(job_id, event_queue)
            logger.info(f"📡 SSE connection added for job {job_id}")
            
            # 초기 상태 전송
            job_status = tts_service.get_job_status(job_id)
            if job_status:
                # 연결 건강성 정보 포함
                health_info = await notification_service.get_connection_health(job_id)
                
                initial_data = {
                    "type": "initial_status",
                    "job_id": job_id,
                    "status": job_status.status.value,
                    "progress": job_status.progress,
                    "total_files": job_status.total_files,
                    "completed_files": job_status.completed_files,
                    "failed_files": job_status.failed_files,
                    "connection_info": {
                        "connected_at": connection_start_time,
                        "heartbeat_interval": heartbeat_interval,
                        "max_queue_size": max_queue_size
                    },
                    "connection_health": health_info,
                    "timestamp": connection_start_time
                }
                yield f"data: {json.dumps(initial_data)}\n\n"
                logger.debug(f"📡 SSE initial status sent for job {job_id}")
                last_event_time = time.time()
            else:
                error_data = {
                    "type": "error",
                    "message": f"Job {job_id} not found",
                    "timestamp": time.time()
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                logger.error(f"❌ SSE job not found: {job_id}")
                return
            
            # 이벤트 스트림 처리 (개선된 로직)
            while True:
                try:
                    # 동적 타임아웃 (연결 시간에 따라 조정)
                    connection_duration = time.time() - connection_start_time
                    if connection_duration > 600:  # 10분 이상 연결된 경우
                        timeout = 15  # 더 짧은 타임아웃
                    else:
                        timeout = heartbeat_interval
                    
                    # 큐에서 이벤트 대기
                    event_data = await asyncio.wait_for(event_queue.get(), timeout=timeout)
                    current_time = time.time()
                    
                    # 이벤트 데이터에 추가 정보 포함
                    event_data["sse_info"] = {
                        "queue_size": event_queue.qsize(),
                        "connection_duration": current_time - connection_start_time,
                        "last_event_ago": current_time - last_event_time
                    }
                    
                    # 디버깅 로그 추가
                    # print(f"📡 SSE event data: {json.dumps(event_data, indent=2)}")  # 이 줄 추가

                    logger.debug(f"📡 SSE event received for job {job_id}: {event_data.get('type', 'unknown')}")
                    
                    # SSE 형식으로 데이터 전송
                    yield f"data: {json.dumps(event_data)}\n\n"
                    last_event_time = current_time
                    
                    # 작업이 완료되거나 실패하면 스트림 종료
                    if event_data.get("type") == "completion":
                        logger.info(f"📡 SSE stream completed for job {job_id}")
                        # 완료 후 추가 정보 전송
                        final_data = {
                            "type": "stream_ended",
                            "reason": "job_completed",
                            "total_duration": current_time - connection_start_time,
                            "timestamp": current_time
                        }
                        yield f"data: {json.dumps(final_data)}\n\n"
                        break
                        
                except asyncio.TimeoutError:
                    current_time = time.time()
                    
                    # 큐 크기 확인 및 정리
                    if event_queue.qsize() > max_queue_size:
                        logger.debug(f"⚠️ SSE queue cleanup for job {job_id}: {event_queue.qsize()} items")
                        # 오래된 메시지 제거
                        while event_queue.qsize() > max_queue_size // 2:
                            try:
                                event_queue.get_nowait()
                            except asyncio.QueueEmpty:
                                break
                    
                    # 연결 유지를 위한 heartbeat (향상된 정보 포함)
                    health_info = await notification_service.get_connection_health(job_id)
                    
                    heartbeat_data = {
                        "type": "heartbeat",
                        "timestamp": current_time,
                        "connection_duration": current_time - connection_start_time,
                        "last_event_ago": current_time - last_event_time,
                        "queue_size": event_queue.qsize(),
                        "connection_health": health_info,
                        "heartbeat_interval": heartbeat_interval
                    }
                    yield f"data: {json.dumps(heartbeat_data)}\n\n"
                    logger.debug(f"💓 SSE heartbeat sent for job {job_id} (queue: {event_queue.qsize()})")
                    
                    # 장시간 비활성 상태 확인
                    if current_time - last_event_time > 300:  # 5분 이상 이벤트 없음
                        inactive_data = {
                            "type": "inactive_warning",
                            "inactive_duration": current_time - last_event_time,
                            "timestamp": current_time,
                            "message": "Long period of inactivity detected"
                        }
                        yield f"data: {json.dumps(inactive_data)}\n\n"
                    
                except Exception as e:
                    logger.error(f"❌ SSE stream error for job {job_id}: {str(e)}")
                    error_data = {
                        "type": "stream_error",
                        "error": str(e),
                        "timestamp": time.time(),
                        "connection_duration": time.time() - connection_start_time
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
                    
        except Exception as e:
            logger.error(f"❌ SSE connection error for job {job_id}: {str(e)}")
            error_data = {
                "type": "connection_error",
                "error": str(e),
                "timestamp": time.time()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            
        finally:
            await notification_service.remove_sse_connection(job_id, event_queue)
            logger.info(f"📡 SSE connection removed for job {job_id}")
            
            # 연결 종료 정보
            end_time = time.time()
            final_data = {
                "type": "connection_closed",
                "total_duration": end_time - connection_start_time,
                "timestamp": end_time
            }
            yield f"data: {json.dumps(final_data)}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "X-Accel-Buffering": "no",  # nginx 버퍼링 비활성화
            "X-Heartbeat-Interval": "20",  # 클라이언트에게 하트비트 간격 힌트
        }
    )

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """작업 상태 조회 - 연결 정보 포함"""
    
    result = tts_service.get_job_status(job_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 작업 ID를 찾을 수 없습니다."
        )
    
    return result

@router.get("/jobs")
async def get_all_jobs():
    """모든 작업 상태 조회 - 연결 정보 포함"""
    
    jobs = tts_service.get_all_jobs()
    connection_stats = notification_service.get_connection_stats()
    
    return {
        "jobs": jobs,
        "connection_stats": connection_stats
    }

@router.post("/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """작업 일시 중단"""
    success = tts_service.pause_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 작업 ID를 찾을 수 없습니다."
        )
    
    return {"message": f"작업 {job_id}이 일시 중단되었습니다."}

@router.post("/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """작업 재개"""
    success = tts_service.resume_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 작업 ID를 찾을 수 없습니다."
        )
    
    return {"message": f"작업 {job_id}이 재개되었습니다."}

@router.get("/notifications/stats")
async def get_notification_stats():
    """실시간 알림 연결 통계 - 상세 정보 포함"""
    
    stats = notification_service.get_connection_stats()
    
    # 추가 통계 정보
    total_jobs = len(set(list(notification_service.websocket_connections.keys()) + list(notification_service.sse_connections.keys())))
    
    stats["summary"] = {
        "total_unique_jobs": total_jobs,
        "avg_connections_per_job": (
            (stats["total_websocket_connections"] + stats["total_sse_connections"]) / 
            max(total_jobs, 1)
        ),
        "connection_types": {
            "websocket_only": len([
                job_id for job_id in notification_service.websocket_connections.keys()
                if job_id not in notification_service.sse_connections
            ]),
            "sse_only": len([
                job_id for job_id in notification_service.sse_connections.keys()
                if job_id not in notification_service.websocket_connections
            ]),
            "both": len([
                job_id for job_id in notification_service.websocket_connections.keys()
                if job_id in notification_service.sse_connections
            ])
        }
    }
    
    return stats

@router.delete("/files/{filename}")
async def delete_file(filename: str):
    """생성된 파일 삭제"""
    
    file_path = os.path.join(settings.output_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다."
        )
    
    try:
        os.remove(file_path)
        return {"message": f"파일 '{filename}'이 성공적으로 삭제되었습니다."}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 삭제 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/play/generate", response_model=TTSResponse)
async def generate_play(request: PlayTTSRequest) -> TTSResponse:
    """
    연극 제목과 대사로 MP3 파일을 생성하는 API 엔드포인트
    """
    """배치 TTS 파일 생성"""
    
    try:
        # 입력 데이터 검증
        if not request.script or len(request.script) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="대본(script)이 필요합니다."
            )
            
        if not request.playTitle:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="연극 제목(playTitle)이 필요합니다."
            )
        
        result = await tts_service.generate_play_tts(request)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"연극 음성 파일 생성 중 오류가 발생했습니다: {str(e)}"
        )