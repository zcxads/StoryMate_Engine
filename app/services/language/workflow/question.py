"""
책 내용 기반 추천 질문 워크플로우 래퍼
"""

import time
from typing import Dict, Any, Union, List

from app.models.language.question import QuestionRequest, RecommendedQuestion
from app.services.language.question.generator import generate_recommended_questions
from app.utils.logger.setup import setup_logger

# 로거 설정
logger = setup_logger('question_workflow', 'logs/workflow')

async def process_question_workflow_wrapper(request: Union[QuestionRequest, Dict[str, Any]]) -> Dict[str, Any]:
    """
    API 요청을 입력받아 책 내용 기반 추천 질문을 생성하고 결과를 반환하는 wrapper 함수.
    
    Args:
        request: QuestionRequest 객체 또는 딕셔너리 형태의 요청 데이터
    
    Returns:
        Dict[str, Any]: 추천 질문 결과를 포함한 응답 데이터
    """
    start_time = time.time()
    
    try:
        logger.info("추천 질문 워크플로우 처리 시작")
        
        # 요청 데이터 추출
        if isinstance(request, dict):
            model = request.get("model", "gemini")
            pages = request.get("pages", [])
            question_count = request.get("problem", 5)
        else:
            model = getattr(request, "model", "gemini")
            pages = getattr(request, "pages", [])
            question_count = getattr(request, "problem", 5)
            # Pydantic 모델인 경우 dict로 변환
            if hasattr(request, 'dict'):
                request_dict = request.dict()
                pages = [page for page in request_dict.get("pages", [])]
                question_count = request_dict.get("problem", 5)
        
        if not pages:
            raise ValueError("질문을 생성할 페이지 데이터가 없습니다.")
        
        logger.info(f"추천 질문 생성 시작 - 모델: {model}, 페이지 수: {len(pages)}, 생성할 질문 수: {question_count}")
        
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
        
        # 추천 질문 생성
        recommended_questions = await generate_recommended_questions(pages_data, model, question_count)
        
        # 실행 시간 계산
        execution_time = f"{time.time() - start_time:.2f}s"
        
        # RecommendedQuestion 객체들을 딕셔너리로 변환
        questions_data = []
        for question in recommended_questions:
            if hasattr(question, 'dict'):
                questions_data.append(question.dict())
            else:
                questions_data.append({
                    "question": question.question,
                    "reason": question.reason,
                    "category": question.category,
                    "search_keywords": question.search_keywords
                })
        
        # 결과 구성
        result = {
            "recommended_questions": questions_data,
            "model_used": model,
            "page_count": len(pages_data),
            "execution_time": execution_time,
            "status": "success"
        }
        
        logger.info(f"추천 질문 워크플로우 처리 완료 - 실행시간: {execution_time}, 생성된 질문 수: {len(questions_data)}")
        return result
        
    except Exception as e:
        execution_time = f"{time.time() - start_time:.2f}s"
        error_msg = f"추천 질문 워크플로우 처리 중 오류 발생: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 오류 응답 구성
        return {
            "recommended_questions": [],
            "model_used": model if 'model' in locals() else "unknown",
            "page_count": len(pages) if 'pages' in locals() else 0,
            "execution_time": execution_time,
            "status": "error",
            "error": str(e)
        } 