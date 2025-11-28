"""
컨텐츠 카테고리 분석 서비스
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
from app.utils.language.generator import call_llm

from app.models.language.content_category import (
    ContentCategoryRequest,
    ContentCategoryResponse,
    Genre,
    ContentType,
    VisualizationType
)
from app.prompts.language.content_category import get_content_category_analysis_prompt
from app.utils.logger.setup import setup_logger

logger = setup_logger('content_category_analyzer', 'logs/services')

class ContentCategoryAnalyzer:
    """컨텐츠 카테고리 분석 클래스"""
    
    def __init__(self):
        pass
    
    async def analyze_content(self, request: ContentCategoryRequest) -> ContentCategoryResponse:
        """
        컨텐츠 카테고리 분석

        Args:
            request: 분석 요청

        Returns:
            ContentCategoryResponse: 분석 결과
        """
        start_time = time.time()

        try:
            logger.info(f"컨텐츠 카테고리 분석 시작 - 모델: {request.model}, 언어: {request.language}")

            # llmText에서 모든 텍스트 추출
            combined_text = self._extract_text_from_llm_text(request.llmText)

            if not combined_text or not combined_text.strip():
                raise ValueError("분석할 텍스트가 제공되지 않았습니다.")

            # 단일 문장(텍스트 아이템 1개)이고 30자 미만일 경우: 장르는 판별하되 모든 컨텐츠는 False로 반환
            try:
                text_item_count = 0
                single_text_value = None
                for page in request.llmText:
                    for item in page.texts:
                        if item.text and item.text.strip():
                            text_item_count += 1
                            if single_text_value is None:
                                single_text_value = item.text.strip()

                if text_item_count == 1 and single_text_value is not None and len(single_text_value) < 30:
                    logger.info(f"⚠️ 짧은 단일 문장 입력 감지 (길이: {len(single_text_value)}) → 장르만 판별, 나머지는 False 처리")
                    genre_only = await self._analyze_genre_only(single_text_value, request)
                    response = ContentCategoryResponse(
                        genre=genre_only,
                        song=False,
                        play=False,
                        quiz=False,
                        summary=False,
                        visualization=False,
                        visualization_option=None,
                    )
                    response.execution_time = f"{time.time() - start_time:.2f}s"
                    return response
            except Exception as _:
                # 사전 조건 검사 실패 시 무시하고 일반 흐름 진행
                pass

            # 입력 텍스트 정보 로깅
            original_length = len(combined_text)
            truncated_length = min(original_length, 8000)
            logger.info(f"📝 입력 텍스트 - 원본: {original_length} chars, 분석용: {truncated_length} chars")

            # 프롬프트 생성
            prompt_text = get_content_category_analysis_prompt(request.language)

            # 분석 텍스트와 프롬프트를 포함한 메시지 생성
            prompt_content = f"{prompt_text}\n\n# 분석할 텍스트:\n\n{combined_text}"
            
            logger.info(f"LLM 분석 호출 시작... (텍스트 길이: {len(prompt_content)} chars)")
            llm_start_time = time.time()

            # 통합 언어 모델 생성기를 사용한 LLM 호출
            logger.info(f"📡 {request.model} 모델 호출 중...")
            response = await call_llm(prompt_content, model=request.model)
            result_text = response.content if response and response.content else ""

            llm_time = time.time() - llm_start_time
            logger.info(f"🚀 LLM 분석 완료 - 소요시간: {llm_time:.2f}s")

            # LLM 응답이 비어있는 경우 확인
            if not result_text or result_text.strip() == "":
                logger.error(f"❌ LLM에서 빈 응답 수신! 모델: {request.model}, 소요시간: {llm_time:.2f}s")
                raise ValueError(f"LLM에서 빈 응답을 받았습니다 (모델: {request.model})")

            analysis_result = self._parse_analysis_response(result_text, request.language)
            
            execution_time = f"{time.time() - start_time:.2f}s"
            analysis_result.execution_time = execution_time

            # 전체 실행 시간 요약 로그
            logger.info(f"🏁 컨텐츠 카테고리 분석 완료 - 실행시간: {execution_time}")

            return analysis_result
            
        except Exception as e:
            logger.error(f"컨텐츠 카테고리 분석 중 오류 발생: {str(e)}", exc_info=True)
    
    async def _analyze_genre_only(self, text: str, request: ContentCategoryRequest) -> Genre:
        """짧은 입력의 경우 장르만 신뢰성 있게 판별. 분류 불가 시 practical 반환"""
        try:
            prompt = (
                "아래 문장의 주된 주제에 근거해 장르를 하나만 선택하세요.\n"
                "**반드시 다음 6가지 중 하나를 선택해야 합니다: science, history, philosophy, literature, art, practical**\n"
                "**분류가 어렵거나 애매한 경우 'practical'을 선택하세요.**\n"
                "JSON으로만 답하세요. 예: {\"genre\": \"practical\"}\n\n"
                f"문장: {text}"
            )
            logger.info("장르 전용 판별 LLM 호출")
            response = await call_llm(prompt, model=request.model)
            content = response.content if response and response.content else ""

            try:
                import re, json as _json
                json_match = re.search(r"\{[\s\S]*\}", content)
                if json_match:
                    parsed = _json.loads(json_match.group(0))
                    genre_str = parsed.get("genre", "practical")

                    # null이나 빈 문자열인 경우 practical로 폴백
                    if not genre_str or genre_str.lower() == "null":
                        logger.warning(f"장르가 null로 반환됨 → practical로 폴백")
                        return Genre.PRACTICAL

                    try:
                        return Genre(genre_str)
                    except ValueError:
                        logger.warning(f"알 수 없는 장르 '{genre_str}' → practical로 폴백")
                        return Genre.PRACTICAL
            except Exception as e:
                logger.error(f"장르 파싱 실패: {str(e)} → practical로 폴백")
                return Genre.PRACTICAL

        except Exception as e:
            logger.error(f"장르 판별 중 오류: {str(e)} → practical로 폴백")
            return Genre.PRACTICAL

    def _parse_analysis_response(self, response_text: str, language: str) -> ContentCategoryResponse:
        """분석 응답 파싱"""
        try:
            import re
            
            # 빈 응답 처리
            if not response_text or response_text.strip() == "":
                logger.error("빈 응답 수신")
                return self._create_fallback_response(language)
            
            # 더 견고한 JSON 추출 로직 (3단계 fallback)
            json_str = None

            # 1. JSON 코드 블록 추출 시도 (```json ... ``` 패턴)
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                potential_json = json_match.group(1).strip()
                # JSON 형태인지 확인
                if potential_json.startswith('{') and potential_json.rstrip().endswith('}'):
                    json_str = potential_json
                    logger.info("JSON 코드 블록에서 추출 성공")

            # 2. 순수 JSON 객체 추출 시도 ({ ... } 패턴)
            if not json_str:
                json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                    logger.info("순수 JSON 객체에서 추출 성공")

            # 3. 전체 응답을 JSON으로 시도
            if not json_str:
                stripped = response_text.strip()
                if stripped.startswith('{') and stripped.endswith('}'):
                    json_str = stripped
                    logger.info("전체 응답을 JSON으로 파싱 시도")

            if not json_str:
                logger.error(f"JSON 형식을 찾을 수 없음: {response_text[:500]}...")
                logger.debug(f"전체 응답: {response_text}")
                return self._create_fallback_response(language)
                        
            # JSON 파싱 및 검증
            try:
                parsed = json.loads(json_str)
                logger.info(f"JSON 파싱 성공: {parsed}")
                
                # 필수 필드 검증
                required_fields = ['genre', 'song', 'play', 'quiz', 'summary', 'visualization']
                missing_fields = [field for field in required_fields if field not in parsed]

                if missing_fields:
                    logger.error(f"필수 필드 누락: {missing_fields}")
                    return self._create_fallback_response(language)
                
                # 데이터 타입 검증
                for bool_field in ['song', 'play', 'quiz', 'summary', 'visualization']:
                    if not isinstance(parsed.get(bool_field), bool):
                        logger.error(f"{bool_field}가 boolean이 아님")
                        return self._create_fallback_response(language)
                    
            except json.JSONDecodeError as je:
                logger.error(f"JSON 파싱 실패: {je}, 원본: {json_str[:200]}...")
                return self._create_fallback_response(language)
            except Exception as e:
                logger.error(f"JSON 검증 중 오류: {str(e)}")
                return self._create_fallback_response(language)

            # Genre 매핑: 'null' 또는 매핑 불가 → practical로 폴백
            raw_genre = parsed.get('genre', 'practical')
            genre: Genre = Genre.PRACTICAL  # 기본값은 practical

            if isinstance(raw_genre, str):
                normalized = raw_genre.strip()
                if normalized == "" or normalized.lower() == "null":
                    logger.warning(f"장르가 null 또는 빈 문자열 → practical로 폴백")
                    genre = Genre.PRACTICAL
                else:
                    try:
                        genre = Genre(normalized)
                    except ValueError:
                        logger.warning(f"알 수 없는 장르 '{normalized}' → practical로 폴백")
                        genre = Genre.PRACTICAL
            elif raw_genre is None:
                logger.warning(f"장르가 None → practical로 폴백")
                genre = Genre.PRACTICAL

            # Boolean 필드 추출
            song = bool(parsed.get('song', False))
            play = bool(parsed.get('play', False))
            quiz = bool(parsed.get('quiz', False))
            summary = bool(parsed.get('summary', False))
            visualization = bool(parsed.get('visualization', False))

            # visualization_option 처리
            visualization_option = None
            if visualization:
                viz_option = parsed.get('visualization_option', None)
                if viz_option and viz_option in ['chart', 'table']:
                    visualization_option = viz_option
            
            return ContentCategoryResponse(
                genre=genre,
                song=song,
                play=play,
                quiz=quiz,
                summary=summary,
                visualization=visualization,
                visualization_option=visualization_option
            )
            
        except Exception as e:
            logger.error(f"분석 응답 파싱 실패: {str(e)}")
            return self._create_fallback_response(language)

    def _create_fallback_response(self, language: str) -> ContentCategoryResponse:
        """fallback 응답 생성 - 장르는 항상 practical로 설정"""
        logger.warning("Fallback 응답 생성 → 장르를 practical로 설정")
        return ContentCategoryResponse(
            genre=Genre.PRACTICAL,  # null 대신 practical
            song=False,
            play=False,
            quiz=False,
            summary=False,
            visualization=False,
            visualization_option=None
        )

    def _extract_text_from_llm_text(self, llm_text) -> str:
        """llmText 배열에서 모든 텍스트를 추출하여 하나의 문자열로 결합"""
        combined_texts = []

        for page_text in llm_text:
            page_key = page_text.pageKey
            page_texts = []

            for text_item in page_text.texts:
                if text_item.text and text_item.text.strip():
                    page_texts.append(text_item.text.strip())

            if page_texts:
                # 페이지별로 텍스트를 줄바꿈으로 구분
                page_content = "\n".join(page_texts)
                combined_texts.append(f"[페이지 {page_key + 1}]\n{page_content}")

        # 모든 페이지의 텍스트를 합침
        result = "\n\n".join(combined_texts)
        logger.info(f"📄 텍스트 추출 완료 - 페이지 수: {len(llm_text)}, 총 텍스트 길이: {len(result)} chars")

        return result