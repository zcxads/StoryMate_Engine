"""
책 내용 기반 추천 질문 생성 서비스
"""

import json
import logging
from typing import List, Dict, Any
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from app.utils.language.generator import language_generator
from app.prompts.language.question.generator import get_question_prompt
from app.models.language.question import RecommendedQuestion
from app.utils.logger.setup import setup_logger

# 로거 설정
logger = setup_logger('question_generator', 'logs/services')

async def generate_recommended_questions(pages: List[Dict[str, Any]], model: str = "gemini", question_count: int = 5) -> List[RecommendedQuestion]:
    """
    책 페이지들의 내용을 받아서 추천 질문들을 생성합니다.
    
    Args:
        pages: 페이지 데이터 리스트 (pageKey, text 포함)
        model: 사용할 언어 모델
        question_count: 생성할 질문 개수
    
    Returns:
        List[RecommendedQuestion]: 생성된 추천 질문 리스트
    """
    try:
        logger.info(f"추천 질문 생성 시작 - 모델: {model}, 페이지 수: {len(pages)}, 생성할 질문 수: {question_count}")
        
        # 모든 페이지의 텍스트를 하나로 합치기
        book_content = ""
        for page in pages:
            page_text = page.get('text', '')
            if page_text.strip():
                book_content += f"\n\n[페이지 {page.get('pageKey', 'Unknown')}]\n{page_text}"
        
        if not book_content.strip():
            raise ValueError("질문을 생성할 내용이 없습니다.")
        
        logger.debug(f"전체 책 내용 길이: {len(book_content)} 문자")

        # AI 기반 언어 감지
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

        # 프롬프트 템플릿 가져오기 (감지된 언어 사용)
        prompt_template = get_question_prompt(language=detected_language)
        
        # 체인 구성
        chain = (
            RunnablePassthrough.assign(
                book_content=lambda x: x["book_content"],
                question_count=lambda x: x["question_count"]
            )
            | prompt_template
            | language_generator
            | StrOutputParser()
        )
        
        # 입력 데이터 준비
        input_data = {
            "book_content": book_content.strip(),
            "question_count": question_count
        }
        
        # 모델 설정과 함께 체인 실행
        config = {"model": model}
        response = await chain.ainvoke(input_data, config=config)
        
        logger.debug(f"LLM 응답: {response}")
        
        # JSON 응답 파싱
        try:
            # JSON 부분만 추출 (```json이나 기타 마크다운 제거)
            response_clean = response.strip()
            if "```json" in response_clean:
                start_idx = response_clean.find("```json") + 7
                end_idx = response_clean.find("```", start_idx)
                if end_idx != -1:
                    response_clean = response_clean[start_idx:end_idx].strip()
            elif "```" in response_clean:
                start_idx = response_clean.find("```") + 3
                end_idx = response_clean.find("```", start_idx)
                if end_idx != -1:
                    response_clean = response_clean[start_idx:end_idx].strip()
            
            # JSON 파싱
            questions_data = json.loads(response_clean)
            
            # RecommendedQuestion 객체로 변환
            recommended_questions = []
            for q_data in questions_data:
                if isinstance(q_data, dict) and all(key in q_data for key in ["question", "reason", "category", "search_keywords"]):
                    recommended_questions.append(RecommendedQuestion(
                        question=q_data["question"],
                        reason=q_data["reason"],
                        category=q_data["category"],
                        search_keywords=q_data["search_keywords"]
                    ))
            
            if not recommended_questions:
                raise ValueError("유효한 질문이 생성되지 않았습니다.")
            
            logger.info(f"추천 질문 생성 완료 - 생성된 질문 수: {len(recommended_questions)}")
            return recommended_questions
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            logger.error(f"원본 응답: {response}")
            
            # JSON 파싱 실패 시 기본 질문 생성
            fallback_questions = _generate_fallback_questions(book_content)
            logger.warning(f"기본 질문으로 대체: {len(fallback_questions)}개")
            return fallback_questions
        
    except Exception as e:
        logger.error(f"추천 질문 생성 중 오류 발생: {str(e)}", exc_info=True)
        raise

def _generate_fallback_questions(book_content: str) -> List[RecommendedQuestion]:
    """
    JSON 파싱이 실패했을 때 사용할 기본 질문들을 생성합니다.
    """
    fallback_questions = [
        RecommendedQuestion(
            question="이 책의 주인공은 누구이고, 어떤 특징을 가지고 있나요?",
            reason="주인공의 성격, 외모, 행동 특성을 파악하여 캐릭터에 대해 더 깊이 이해해보세요. 주인공과 비슷한 다른 책의 캐릭터도 찾아보면 좋습니다.",
            category="등장인물",
            search_keywords=["주인공", "캐릭터", "특징"]
        ),
        RecommendedQuestion(
            question="이야기가 일어나는 배경은 어디인가요?",
            reason="책의 배경이 되는 장소의 특징과 환경을 조사해보고, 그 장소가 이야기에 어떤 영향을 미치는지 알아보세요.",
            category="배경지식",
            search_keywords=["배경", "장소", "환경"]
        ),
        RecommendedQuestion(
            question="이 책에서 배울 수 있는 교훈은 무엇인가요?",
            reason="책이 전달하고자 하는 메시지나 가르침을 생각해보고, 일상생활에서 어떻게 적용할 수 있는지 고민해보세요.",
            category="교훈",
            search_keywords=["교훈", "메시지", "가르침"]
        )
    ]
    
    return fallback_questions 