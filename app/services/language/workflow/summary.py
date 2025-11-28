"""
책 내용 요약 워크플로우 래퍼
"""

import time
from typing import Dict, Any, Union

from app.models.language.summary import SummaryRequest
from app.services.language.summary.generator import generate_book_summary
from app.utils.logger.setup import setup_logger

# 로거 설정
logger = setup_logger('summary_workflow', 'logs/workflow')

async def process_summary_workflow_wrapper(request: Union[SummaryRequest, Dict[str, Any]]) -> Dict[str, Any]:
    """
    API 요청을 입력받아 책 내용 요약을 생성하고 결과를 반환하는 wrapper 함수.
    
    Args:
        request: SummaryRequest 객체 또는 딕셔너리 형태의 요청 데이터
    
    Returns:
        Dict[str, Any]: 요약 결과를 포함한 응답 데이터
    """
    start_time = time.time()
    
    try:
        logger.info("책 요약 워크플로우 처리 시작")
        
        # 요청 데이터 추출
        if isinstance(request, dict):
            model = request.get("model", "gemini")
            pages = request.get("pages", [])
        else:
            model = getattr(request, "model", "gemini")
            pages = getattr(request, "pages", [])
            # Pydantic 모델인 경우 dict로 변환
            if hasattr(request, 'dict'):
                request_dict = request.dict()
                pages = request_dict.get("pages", [])
                pages = [page for page in request_dict.get("pages", [])]
        
        if not pages:
            raise ValueError("요약할 페이지 데이터가 없습니다.")
        
        logger.info(f"요약 생성 시작 - 모델: {model}, 페이지 수: {len(pages)}")
        
        # 페이지 데이터를 딕셔너리 형태로 변환
        pages_data = []
        for page in pages:
            if isinstance(page, dict):
                pages_data.append(page)
            else:
                # Pydantic 모델인 경우
                pages_data.append({
                    "pageKey": getattr(page, "pageKey", 0),
                    "text": getattr(page, "text", "")
                })
        
        # 요약 생성
        summary = await generate_book_summary(pages_data, model)
        
        # 실행 시간 계산
        execution_time = f"{time.time() - start_time:.2f}s"
        
        # 결과 구성
        result = {
            "summary": summary,
            "model_used": model,
            "page_count": len(pages_data),
            "execution_time": execution_time,
            "status": "success"
        }
        
        logger.info(f"책 요약 워크플로우 처리 완료 - 실행시간: {execution_time}")
        return result
        
    except Exception as e:
        execution_time = f"{time.time() - start_time:.2f}s"
        error_msg = f"책 요약 워크플로우 처리 중 오류 발생: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 오류 응답 구성
        return {
            "summary": "",
            "model_used": model if 'model' in locals() else "unknown",
            "page_count": len(pages) if 'pages' in locals() else 0,
            "execution_time": execution_time,
            "status": "error",
            "error": str(e)
        } 