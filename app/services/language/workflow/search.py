"""
검색 워크플로우 처리 서비스
"""

import time
from typing import Dict, Any

from app.models.language.search import SearchRequest, SearchResponse, StructuredAnswer
from app.services.language.search.web_searcher import WebSearchService
from app.utils.logger.setup import setup_logger

# 로거 설정
logger = setup_logger('search_workflow', 'logs/services')

class SearchWorkflowService:
    """검색 워크플로우를 처리하는 서비스 클래스"""
    
    def __init__(self):
        """SearchWorkflowService 초기화"""
        self.web_search_service = WebSearchService()

async def process_search_workflow_wrapper(request: SearchRequest) -> Dict[str, Any]:
    """
    검색 워크플로우 처리 래퍼 함수
    
    Args:
        request: 검색 요청 데이터
        
    Returns:
        Dict[str, Any]: 검색 결과 응답
    """
    start_time = time.time()
    
    try:
        logger.info("검색 워크플로우 처리 시작")
        logger.info(f"요청 - 모델: {request.model}, 질문: {request.question[:50]}...")
        logger.info(f"검색 키워드: {request.search_keywords}")
        
        # 워크플로우 서비스 초기화
        workflow_service = SearchWorkflowService()
        
        # 웹 검색 수행
        search_results = await workflow_service.web_search_service.perform_web_search(
            keywords=request.search_keywords,
            max_results=request.max_results
        )
        
        if not search_results:
            logger.warning("검색 결과가 없습니다.")
            no_results_answer = StructuredAnswer(
                direct_answer="해당 질문에 대한 검색 결과를 찾을 수 없습니다.",
                background_info="검색 키워드와 일치하는 정보가 부족합니다.",
                interesting_facts="다른 키워드나 더 구체적인 질문으로 다시 시도해보세요.",
                easy_explanation="지금은 답을 찾지 못했어요. 다른 방법으로 물어보면 도움을 드릴 수 있을 거예요!",
                key_concepts=["검색 결과 없음", "키워드 변경 필요"],
                related_topics=["다른 검색어", "구체적인 질문"]
            )
            return SearchResponse(
                question=request.question,
                search_keywords=request.search_keywords,
                search_results=[],
                summary="검색 결과를 찾을 수 없습니다.",
                answer=no_results_answer,
                model_used=request.model,
                execution_time=f"{time.time() - start_time:.2f}s"
            ).dict()
        
        # 검색 결과 분석
        summary, structured_answer = await workflow_service.web_search_service.analyze_search_results(
            question=request.question,
            keywords=request.search_keywords,
            search_results=search_results,
            model=request.model
        )

        # 장르 자동 감지
        genre_enum = None
        try:
            from app.services.language.content_category.analyzer import ContentCategoryAnalyzer
            from app.models.language.content_category import ContentCategoryRequest

            # 검색 결과와 요약을 결합하여 장르 분석
            combined_text = f"{request.question} {summary} {structured_answer.direct_answer}"

            analyzer = ContentCategoryAnalyzer()
            category_request = ContentCategoryRequest(
                llmText=[{"pageKey": 0, "texts": [{"text": combined_text}]}],
                model=request.model,
                language="ko"
            )

            category_result = await analyzer.analyze_content(category_request)
            genre_enum = category_result.genre
            logger.info(f"Auto-detected genre: {genre_enum.value}")
        except Exception as e:
            logger.warning(f"Failed to auto-detect genre: {str(e)}")

        # 실행 시간 계산
        execution_time = f"{time.time() - start_time:.2f}s"

        # 응답 생성
        response = SearchResponse(
            question=request.question,
            search_keywords=request.search_keywords,
            search_results=search_results,
            summary=summary,
            answer=structured_answer,
            genre=genre_enum,
            model_used=request.model,
            execution_time=execution_time
        )

        logger.info(f"검색 워크플로우 처리 완료 - 실행시간: {execution_time}")
        logger.info(f"검색 결과 수: {len(search_results)}")

        return response.dict()
        
    except Exception as e:
        execution_time = f"{time.time() - start_time:.2f}s"
        logger.error(f"검색 워크플로우 처리 중 오류 발생: {str(e)} - 실행시간: {execution_time}")
        
        # 오류 응답 생성
        error_answer = StructuredAnswer(
            direct_answer="검색 처리 중 오류가 발생했습니다.",
            background_info="시스템에 일시적인 문제가 있습니다.",
            interesting_facts="잠시 후 다시 시도해주세요.",
            easy_explanation="컴퓨터가 잠깐 쉬고 있어요. 조금 기다렸다가 다시 물어보세요!",
            key_concepts=["시스템 오류", "재시도 필요"],
            related_topics=["기술적 문제", "서비스 복구"]
        )
        
        error_response = SearchResponse(
            question=request.question,
            search_keywords=request.search_keywords,
            search_results=[],
            summary="검색 처리 중 오류가 발생했습니다.",
            answer=error_answer,
            model_used=request.model,
            execution_time=execution_time
        )
        
        return error_response.dict() 