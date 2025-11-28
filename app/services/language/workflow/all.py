import os
import json
import asyncio
from dotenv import load_dotenv

from app.models.language.all import AllRequest
from app.models.state import (
    OrthographyState, SoundState, Page, PageText, parse_final_result
)
from app.services.language.workflow.orthography import process_orthography_workflow_wrapper
from app.services.language.workflow.sound import process_sound_workflow_wrapper
from app.services.language.workflow.quiz import process_quiz_workflow_wrapper
from app.utils.logger.setup import setup_logger

# 로거 설정
logger = setup_logger('all', 'logs/workflow')

# 환경 변수 로드
load_dotenv()

async def process_all_workflow_wrapper(request) -> dict:
    """
    API 요청을 입력받아 OCR 전처리와 Sound, Quiz 처리를 순차적으로 실행하고,
    최종 결과를 반환하는 wrapper 함수.
    """
    try:
        logger.info("통합 워크플로우 처리 시작")
        
        # 텍스트 교정 전처리 실행
        logger.info("텍스트 교정 전처리 시작")
        orthography_result = await process_orthography_workflow_wrapper(request)
        logger.info("텍스트 교정 전처리 완료")
        
        # 교정 결과를 Sound와 Quiz 입력 형식으로 변환
        llmText_data = {"llmText": orthography_result["llmText"]}
        
        # 퀴즈 개수 가져오기 (default: 5)
        quiz_count = getattr(request, "quizCount", 5) if hasattr(request, "quizCount") else request.get("quizCount", 5)
        llmText_data["quizCount"] = quiz_count
        
        # model 필드 전달
        model = getattr(request, "model", "gemini") if hasattr(request, "model") else request.get("model", "gemini")
        llmText_data["model"] = model
        
        logger.debug("사운드와 퀴즈 처리를 위한 입력 준비 완료")
        
        # Sound와 Quiz 병렬 처리
        logger.info("사운드와 퀴즈 병렬 처리 시작")
        sound_task = asyncio.create_task(process_sound_workflow_wrapper(llmText_data))
        quiz_task = asyncio.create_task(process_quiz_workflow_wrapper(llmText_data))
        
        sound_result, quiz_result = await asyncio.gather(sound_task, quiz_task)
        logger.info("병렬 처리 완료")
        
        # 최종 결과 통합
        logger.info("최종 결과 통합 중")
        final_result = parse_final_result(orthography_result, sound_result, quiz_result)
        
        logger.info("통합 워크플로우 처리 성공")
        return final_result
        
    except Exception as e:
        logger.error(f"통합 워크플로우 처리 중 오류 발생: {str(e)}", exc_info=True)
        raise

# Kafka 서비스용 프로세서 함수
async def process_all(request: AllRequest):
    """Kafka Service가 호출할 프로세서 함수"""
    try:
        # 요청을 사전으로 변환
        request_dict = request.dict() if hasattr(request, 'dict') else request
        
        # 처리 실행
        logger.info("Processing all request via Kafka Service")
        result = await process_all_workflow_wrapper(request_dict)
        
        return result
    except Exception as e:
        logger.error(f"Kafka 서비스 통합 처리 중 오류: {str(e)}", exc_info=True)
        # 오류 응답 구성
        error_response = {
            "state": "Incompleted",
            "error": str(e)
        }
        return error_response
