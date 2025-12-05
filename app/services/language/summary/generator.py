"""
책 내용 요약 생성 서비스
"""

from typing import List, Dict, Any
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from app.utils.language.generator import language_generator
from app.utils.logger.setup import setup_logger

# 로거 설정
logger = setup_logger('summary_generator', 'logs/services')

async def generate_book_summary(pages: List[Dict[str, Any]], model: str) -> str:
    """
    책 페이지들의 내용을 받아서 요약을 생성합니다.
    
    Args:
        pages: 페이지 데이터 리스트 (pageKey, text 포함)
        model: 사용할 언어 모델
    
    Returns:
        str: 생성된 책 요약
    """
    try:
        logger.info(f"책 요약 생성 시작 - 모델: {model}, 페이지 수: {len(pages)}")
        
        # 모든 페이지의 텍스트를 하나로 합치기
        book_content = ""
        for page in pages:
            page_text = page.get('text', '')
            if page_text.strip():
                # 페이지 마커 없이 두 줄 바꿈으로만 페이지를 구분
                book_content += f"\n\n{page_text}"
        
        if not book_content.strip():
            raise ValueError("요약할 내용이 없습니다.")

        # 언어 감지 로깅
        sample_text = book_content[:200]
        logger.info(f"입력 텍스트 샘플: {sample_text}")

        # AI 기반 언어 감지 (39개 언어 지원)
        detected_language = "ko"  # 기본값
        if book_content.strip():
            try:
                from app.services.language.language_detection.detector import detect_language_with_ai

                detection_result = await detect_language_with_ai(book_content.strip(), model)
                detected_language = detection_result.get("primary_language")
                confidence = detection_result.get("confidence", 0.0)

                logger.info(f"AI 언어 감지 결과: {detected_language} - 신뢰도: {confidence:.3f}")
            except Exception as e:
                logger.warning(f"AI 언어 감지 실패, 기본값(en) 사용: {e}")

        # 언어별 프롬프트 선택 (fallback 포함)
        from app.prompts.language.summary import get_summary_prompt

        prompt_template = get_summary_prompt(detected_language)
        logger.info(f"사용할 언어: {detected_language}")
        
        # 체인 구성
        chain = (
            RunnablePassthrough.assign(
                book_content=lambda x: x["book_content"],
                page_count=lambda x: x["page_count"]
            )
            | prompt_template
            | language_generator
            | StrOutputParser()
        )
        
        # 입력 데이터 준비
        input_data = {
            "book_content": book_content.strip(),
            "page_count": len(pages)
        }
        
        # 모델 설정과 함께 체인 실행
        config = {"model": model}
        summary = await chain.ainvoke(input_data, config=config)
        
        logger.info("책 요약 생성 완료")
        
        return summary.strip()
        
    except Exception as e:
        logger.error(f"책 요약 생성 중 오류 발생: {str(e)}", exc_info=True)
        raise 