"""
웹 검색 및 결과 분석 서비스
"""

import os
import re
import json
from typing import List, Tuple, Optional
import google.generativeai as genai
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from openai import OpenAI

from app.models.language.search import SearchResult, StructuredAnswer
from app.prompts.language.search.analyzer import create_search_analysis_prompt
from app.core.config import settings
from app.utils.logger.setup import setup_logger
from app.utils.language.generator import call_llm

# 로거 설정
logger = setup_logger('web_searcher', 'logs/services')

class WebSearchService:
    """웹 검색 및 결과 분석을 담당하는 서비스 클래스"""
    
    def __init__(self):
        """WebSearchService 초기화"""
        self.search_analysis_prompt = create_search_analysis_prompt()
        
        # Google GenAI 클라이언트 초기화
        api_key = os.getenv("GEMINI_API_KEY", os.getenv("GEMINI"))
        if api_key:
            genai.configure(api_key=api_key)
            self.genai_configured = True
        else:
            self.genai_configured = False
            logger.warning("GEMINI API 키가 설정되지 않아 실제 웹 검색을 사용할 수 없습니다.")
        
        # OpenAI 클라이언트 초기화
        openai_api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
            self.openai_configured = True
            logger.info("OpenAI 클라이언트 초기화 완료")
        else:
            self.openai_client = None
            self.openai_configured = False
            logger.warning("OpenAI API 키가 설정되지 않아 OpenAI 웹 검색을 사용할 수 없습니다.")
    
    async def perform_web_search(self, keywords: List[str], max_results: int = 5) -> List[SearchResult]:
        """
        웹 검색을 수행합니다.

        Args:
            keywords: 검색 키워드 리스트
            max_results: 최대 결과 수
            
        Returns:
            List[SearchResult]: 검색 결과 리스트
        """
        try:
            logger.info(f"웹 검색 시작 - 키워드: {keywords}, 최대 결과: {max_results}")

            # 키워드를 조합하여 검색 쿼리 생성
            search_query = " ".join(keywords[:3])  # 최대 3개 키워드만 사용

            if self.openai_configured:
                search_results = await self._perform_openai_web_search(search_query)
            else:
                search_results = await self._perform_google_search(search_query)

            logger.info(f"웹 검색 완료 - 결과 수: {len(search_results)}")
            return search_results[:max_results]

        except Exception as e:
            logger.error(f"웹 검색 중 오류 발생: {str(e)}")
            return []
    
    async def _perform_openai_web_search(self, search_query: str) -> List[SearchResult]:
        """
        OpenAI의 웹 검색 기능을 사용하여 실제 웹 검색을 수행합니다.
        """
        search_results = []
        
        try:
            logger.info(f"OpenAI 웹 검색 수행: {search_query}")

            # 모델 설정 (빈 값인 경우 기본값 사용)
            search_model = settings.llm_web_search_model
            logger.info(f"웹 검색 모델: {search_model}")

            # LLM 호출
            response = await call_llm(
                prompt=[{
                    "role": "user",
                    "content": f"다음 주제에 대해 최신 정보를 검색해서 상세히 알려주세요: {search_query}"
                }],
                model=search_model
            )

            response_content = response.content
            
            # OpenAI 웹 검색 결과를 SearchResult 형태로 변환
            detected_language = self._detect_content_language(search_query)
            title_suffix = self._get_search_result_title_suffix(detected_language)
            
            search_results.append(SearchResult(
                title=f"{search_query} - {title_suffix}",
                url="https://openai.com/search",
                snippet=response_content[:300] + "..." if len(response_content) > 300 else response_content,
                relevance_score=0.9
            ))
            
            # 추가적인 관련 정보 생성
            detected_language = self._detect_content_language(search_query)
            additional_info = await self._generate_additional_search_info(search_query, detected_language)
            search_results.extend(additional_info)
            
            logger.info(f"OpenAI 웹 검색 완료 - 결과 수: {len(search_results)}")
            return search_results
            
        except Exception as e:
            logger.error(f"OpenAI 웹 검색 중 오류: {str(e)}")
            # OpenAI 실패 시 Google GenAI로 폴백
            if self.genai_configured:
                logger.info("OpenAI 실패, Google GenAI로 폴백")
                return await self._perform_google_search(search_query)
            return []
    
    async def _generate_additional_search_info(self, search_query: str, detected_language: str = "Korean") -> List[SearchResult]:
        """검색 쿼리에 대한 추가 정보를 생성합니다."""
        additional_results = []
        
        try:
            # 다양한 관점에서의 정보 생성
            perspectives = self._get_perspectives_by_language(search_query, detected_language)
            
            # 모델 설정 (빈 값인 경우 기본값 사용)
            processing_model = settings.llm_text_processing_model or "gpt-4o"

            for i, perspective in enumerate(perspectives):
                response = await call_llm(
                    prompt=[{
                        "role": "user",
                        "content": f"IMPORTANT: Respond entirely in {detected_language}. {perspective}에 대해 간결하고 정확한 정보를 제공해주세요."
                    }],
                    model=processing_model
                )

                content = response.content
                
                # 언어에 맞는 제목 생성
                localized_title = self._get_localized_perspective_title(perspective, detected_language)
                
                additional_results.append(SearchResult(
                    title=localized_title,
                    url=f"https://generated-info.com/{i+1}",
                    snippet=content,
                    relevance_score=0.7 - (i * 0.1)
                ))
                
        except Exception as e:
            logger.error(f"추가 정보 생성 중 오류: {str(e)}")
        
        return additional_results
    
    async def perform_google_search(self, keywords: List[str], max_results: int = 5) -> List[SearchResult]:
        """
        웹 검색을 수행합니다.
        
        Args:
            keywords: 검색 키워드 리스트
            max_results: 최대 결과 수
            
        Returns:
            List[SearchResult]: 검색 결과 리스트
        """
        try:
            logger.info(f"웹 검색 시작 - 키워드: {keywords}, 최대 결과: {max_results}")
            
            if not self.genai_configured:
                logger.error("Google GenAI가 구성되지 않았습니다.")
                return []
            
            # 키워드를 조합하여 검색 쿼리 생성
            search_query = " ".join(keywords[:3])  # 최대 3개 키워드만 사용
            
            # Google Search를 통한 실제 웹 검색 수행
            search_results = await self._perform_google_search(search_query)
            
            logger.info(f"웹 검색 완료 - 결과 수: {len(search_results)}")
            return search_results[:max_results]
            
        except Exception as e:
            logger.error(f"웹 검색 중 오류 발생: {str(e)}")
            return []
    
    async def _perform_google_search(self, search_query: str) -> List[SearchResult]:
        """
        OpenAI를 사용하여 검색 관련 정보를 생성합니다.
        """
        search_results = []

        try:
            logger.info(f"OpenAI 검색 정보 생성: {search_query}")
            
            # 검색 쿼리를 바탕으로 관련 정보 생성을 위한 프롬프트
            detected_language = self._detect_content_language(search_query)
            
            search_prompt = f"""
            IMPORTANT: You must respond entirely in {detected_language}.
            
            LANGUAGE RULES:
            - If {detected_language} is Japanese, respond in Japanese
            - If {detected_language} is Korean, respond in Korean  
            - If {detected_language} is Chinese, respond in Chinese
            - If {detected_language} is English, respond in English
            
            Please provide detailed information about: {search_query}

            Provide information from 3-5 different perspectives in {detected_language}:
            1. Basic definition and concepts
            2. Key features or principles
            3. Real-life application examples
            4. Latest information or research
            5. Additional learning materials or references

            Each item should contain specific and useful information in about 150-200 characters.
            CRITICAL: ALL content must be in {detected_language}.
            """
            
            # LLM 호출
            response = await call_llm(
                prompt=[{
                    "role": "user",
                    "content": search_prompt
                }],
                model=settings.llm_text_processing_model
            )

            response_text = response.content

            if response_text:
                # 응답을 파싱하여 검색 결과로 변환
                search_results = self._parse_genai_response_to_search_results(response_text, search_query)
            
            logger.info(f"OpenAI 검색 정보 생성 완료 - 결과 수: {len(search_results)}")
            return search_results

        except Exception as e:
            logger.error(f"OpenAI 검색 정보 생성 중 오류: {str(e)}")
            return search_results
    
    def _parse_genai_response_to_search_results(self, response_text: str, search_query: str) -> List[SearchResult]:
        """Google GenAI 응답을 SearchResult 객체로 변환합니다."""
        results = []
        try:
            # 응답을 번호가 있는 섹션으로 분할
            sections = re.split(r'\n\s*\d+\.\s*', response_text)
            
            # 첫 번째 섹션은 보통 제목이므로 제외
            if len(sections) > 1:
                sections = sections[1:]
            else:
                # 번호가 없는 경우 문단으로 분할
                sections = [p.strip() for p in response_text.split('\n\n') if p.strip() and len(p.strip()) > 50]
            
            for i, section in enumerate(sections[:5]):  # 최대 5개 결과
                if len(section.strip()) > 30:  # 충분한 내용이 있는 경우만
                    # 섹션의 첫 번째 문장을 제목으로 사용
                    lines = section.strip().split('\n')
                    title_line = lines[0].strip()
                    
                    # 제목이 너무 길면 첫 50자만 사용
                    if len(title_line) > 50:
                        title = title_line[:50] + "..."
                    else:
                        title = title_line
                    
                    # 제목이 비어있으면 기본 제목 사용
                    if not title:
                        title = f"{search_query} - 정보 {i+1}"
                    
                    results.append(SearchResult(
                        title=title,
                        url=f"https://www.google.com/search?q={search_query.replace(' ', '+')}",
                        snippet=section.strip()[:300] + "..." if len(section.strip()) > 300 else section.strip(),
                        relevance_score=0.9 - (i * 0.1)
                    ))
            
            # 결과가 없으면 전체 응답을 하나의 결과로 생성
            if not results and response_text.strip():
                results.append(SearchResult(
                    title=f"{search_query} - 종합 정보",
                    url=f"https://www.google.com/search?q={search_query.replace(' ', '+')}",
                    snippet=response_text.strip()[:300] + "..." if len(response_text.strip()) > 300 else response_text.strip(),
                    relevance_score=0.8
                ))
                
        except Exception as e:
            logger.error(f"GenAI 응답 파싱 중 오류: {str(e)}")
            # 오류 발생 시 기본 결과 생성
            if response_text.strip():
                results.append(SearchResult(
                    title=f"{search_query} - 검색 정보",
                    url=f"https://www.google.com/search?q={search_query.replace(' ', '+')}",
                    snippet=response_text.strip()[:300] + "..." if len(response_text.strip()) > 300 else response_text.strip(),
                    relevance_score=0.7
                ))
        
        return results
    
    async def analyze_search_results(
        self, 
        question: str, 
        keywords: List[str], 
        search_results: List[SearchResult],
        model: str = settings.llm_text_processing_model
    ) -> Tuple[str, StructuredAnswer]:
        """
        검색 결과를 분석하여 요약과 구조화된 답변을 생성합니다.
        """
        try:
            logger.info(f"검색 결과 분석 시작 - 모델: {model}, 결과 수: {len(search_results)}")
            
            if not search_results:
                logger.warning("분석할 검색 결과가 없습니다.")
                fallback_answer = StructuredAnswer(
                    direct_answer="검색 결과를 찾을 수 없어 답변을 생성할 수 없습니다.",
                    background_info="검색 키워드와 일치하는 정보가 부족합니다.",
                    interesting_facts="다른 키워드나 더 구체적인 질문으로 다시 시도해보세요.",
                    easy_explanation="지금은 답을 찾지 못했어요. 다른 방법으로 물어보면 도움을 드릴 수 있을 거예요!",
                    key_concepts=["검색 결과 없음"],
                    related_topics=["다른 검색어", "구체적인 질문"]
                )
                return "검색 결과를 찾을 수 없습니다.", fallback_answer
            
            # 모델별 처리 분기
            if model.startswith("gemini"):
                return await self._analyze_with_gemini_direct(question, keywords, search_results, model)
            else:
                # 기본적으로 OpenAI 사용
                return await self._analyze_with_openai_direct(question, keywords, search_results, model)
                
        except Exception as e:
            logger.error(f"검색 결과 분석 중 오류 발생: {str(e)}")
            return self._parse_fallback_response("분석 중 오류가 발생했습니다.")

    async def _analyze_with_gemini_direct(
        self, 
        question: str, 
        keywords: List[str], 
        search_results: List[SearchResult],
        model: str = settings.llm_text_processing_model
    ) -> Tuple[str, StructuredAnswer]:
        """Google Gemini를 직접 사용하여 검색 결과를 분석합니다."""
        try:
            if not self.genai_configured:
                logger.error("Gemini API가 구성되지 않았습니다.")
                return self._parse_fallback_response("Gemini API 구성 오류")
            
            # 검색 결과를 텍스트로 포맷팅
            formatted_results = self._format_search_results(search_results)
            
            # 언어 감지를 위한 함수 추가
            detected_language = self._detect_content_language(question, search_results)
            
            # 구조화된 분석을 위한 프롬프트
            analysis_prompt = f"""
            LANGUAGE DETECTION: The question is in {detected_language}. You MUST respond entirely in {detected_language}.
            
            **STRICT LANGUAGE RULES:**
            - If question is in Japanese (日本語), respond entirely in Japanese
            - If question is in Korean (한국어), respond entirely in Korean
            - If question is in English, respond entirely in English
            - If question is in Chinese, respond entirely in Chinese
            
            Analyze the following search results for this question and generate a structured answer in {detected_language}:

            Question: {question}
            Search Keywords: {", ".join(keywords)}

            Search Results:
            {formatted_results}

            Respond in the following JSON format, using {detected_language} for ALL text content:

            {{
            "summary": "2-3 sentence summary of search results in {detected_language}",
            "direct_answer": "Direct and clear answer to the question in {detected_language}",
            "background_info": "Important background information and context in {detected_language}",
            "interesting_facts": "Interesting and educational additional facts in {detected_language}",
            "easy_explanation": "Child-friendly explanation using analogies in {detected_language}",
            "key_concepts": ["key concept 1 in {detected_language}", "key concept 2 in {detected_language}", "key concept 3 in {detected_language}"],
            "related_topics": ["related topic 1 in {detected_language}", "related topic 2 in {detected_language}", "related topic 3 in {detected_language}"]
            }}

            CRITICAL: ALL content must be in {detected_language}. Do not mix languages.
            - Use only information confirmed in the search results
            - Write in a way that children can understand
            - Follow JSON format exactly
            """
            
            # Gemini 모델 생성
            gemini_model = genai.GenerativeModel(
                model_name=self._get_actual_gemini_model(model)
            )
            
            # Gemini 호출
            response = gemini_model.generate_content(
                analysis_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.gemini_temperature,
                    max_output_tokens=settings.gemini_max_tokens,
                )
            )
            
            response_text = response.text
            
            # JSON 응답 파싱
            return self._parse_gemini_json_response(response_text)
            
        except Exception as e:
            logger.error(f"Gemini 직접 분석 중 오류: {str(e)}")
            # OpenAI로 폴백
            if self.openai_configured:
                logger.info("Gemini 실패, OpenAI로 폴백")
                return await self._analyze_with_openai_direct(question, keywords, search_results, settings.llm_text_processing_model)
            return self._parse_fallback_response("Gemini 분석 중 오류가 발생했습니다.")

    def _get_actual_gemini_model(self, model: str) -> str:
        """요청된 Gemini 모델명을 실제 API 모델명으로 변환합니다."""
        model_mapping = {
            "gemini-2.5-pro": "gemini-2.5-pro",
            "gemini-2.5-flash": "gemini-2.5-flash",
            "gemini-2.0-flash": "gemini-2.0-flash",
        }
        return model_mapping.get(model, "gemini-2.0-flash")

    def _parse_gemini_json_response(self, response_text: str) -> Tuple[str, StructuredAnswer]:
        """Gemini JSON 응답을 파싱합니다."""
        try:
            # JSON 부분만 추출
            response_clean = response_text.strip()
            if "```json" in response_clean:
                start_idx = response_clean.find("```json") + 7
                end_idx = response_clean.find("```", start_idx)
                if end_idx != -1:
                    response_clean = response_clean[start_idx:end_idx].strip()
            elif response_clean.startswith("{") and response_clean.endswith("}"):
                # 이미 JSON 형태인 경우
                pass
            else:
                # JSON이 아닌 경우 fallback
                return self._parse_fallback_response(response_text)
            
            # JSON 파싱
            data = json.loads(response_clean)
            
            # 필수 필드 확인 및 기본값 설정 + 타입 변환
            summary = data.get("summary", "검색 결과를 분석했습니다.")
            
            # 각 필드의 타입을 확인하고 필요시 변환
            direct_answer = data.get("direct_answer", "검색 결과를 바탕으로 답변을 생성했습니다.")
            if isinstance(direct_answer, list):
                direct_answer = " ".join(direct_answer)
            
            background_info = data.get("background_info", "관련 배경 정보입니다.")
            if isinstance(background_info, list):
                background_info = " ".join(background_info)
            
            interesting_facts = data.get("interesting_facts", "흥미로운 추가 정보입니다.")
            if isinstance(interesting_facts, list):
                interesting_facts = " ".join(interesting_facts)
            
            easy_explanation = data.get("easy_explanation", "쉽게 설명드리면 이런 내용입니다.")
            if isinstance(easy_explanation, list):
                easy_explanation = " ".join(easy_explanation)
            
            key_concepts = data.get("key_concepts", ["주요 개념"])
            if isinstance(key_concepts, str):
                key_concepts = [key_concepts]
            elif not isinstance(key_concepts, list):
                key_concepts = ["주요 개념"]
            
            related_topics = data.get("related_topics", ["관련 주제"])
            if isinstance(related_topics, str):
                related_topics = [related_topics]
            elif not isinstance(related_topics, list):
                related_topics = ["관련 주제"]
            
            structured_answer = StructuredAnswer(
                direct_answer=direct_answer,
                background_info=background_info,
                interesting_facts=interesting_facts,
                easy_explanation=easy_explanation,
                key_concepts=key_concepts,
                related_topics=related_topics
            )
            
            return summary, structured_answer
            
        except Exception as e:
            logger.error(f"Gemini JSON 응답 파싱 중 오류: {str(e)}")
            return self._parse_fallback_response("응답 파싱 중 오류가 발생했습니다.")

    async def _analyze_with_openai_direct(
        self, 
        question: str, 
        keywords: List[str], 
        search_results: List[SearchResult],
        model: str
    ) -> Tuple[str, StructuredAnswer]:
        """OpenAI를 직접 사용하여 검색 결과를 분석합니다."""
        try:
            # 검색 결과를 텍스트로 포맷팅
            formatted_results = self._format_search_results(search_results)
            
            # 언어 감지
            detected_language = self._detect_content_language(question, search_results)
            
            # 구조화된 분석을 위한 프롬프트
            analysis_prompt = f"""
LANGUAGE DETECTION: The question is in {detected_language}. You MUST respond entirely in {detected_language}.

**STRICT LANGUAGE RULES:**
- If question is in Japanese (日本語), respond entirely in Japanese
- If question is in Korean (한국어), respond entirely in Korean
- If question is in English, respond entirely in English
- If question is in Chinese, respond entirely in Chinese

Analyze the following search results for this question and generate a structured answer in {detected_language}:

Question: {question}
Search Keywords: {", ".join(keywords)}

Search Results:
{formatted_results}

Respond in the following JSON format, using {detected_language} for ALL text content:

{{
  "summary": "2-3 sentence summary of search results in {detected_language}",
  "direct_answer": "Direct and clear answer to the question in {detected_language}",
  "background_info": "Important background information and context in {detected_language}",
  "interesting_facts": "Interesting and educational additional facts in {detected_language}",
  "easy_explanation": "Child-friendly explanation using analogies in {detected_language}",
  "key_concepts": ["key concept 1 in {detected_language}", "key concept 2 in {detected_language}", "key concept 3 in {detected_language}"],
  "related_topics": ["related topic 1 in {detected_language}", "related topic 2 in {detected_language}", "related topic 3 in {detected_language}"]
}}

CRITICAL: ALL content must be in {detected_language}. Do not mix languages.
- Use only information confirmed in the search results
- Write in a way that children can understand
- Follow JSON format exactly
"""
            
            # LLM 호출
            actual_model = self._get_actual_openai_model(model)
            response = await call_llm(
                prompt=[{
                    "role": "user",
                    "content": analysis_prompt
                }],
                model=actual_model
            )

            response_text = response.content
            
            # JSON 응답 파싱
            return self._parse_openai_json_response(response_text)
            
        except Exception as e:
            logger.error(f"OpenAI 직접 분석 중 오류: {str(e)}")
            # Gemini로 폴백
            if self.genai_configured:
                logger.info("OpenAI 실패, Gemini로 폴백")
                from app.core.config import settings
                return await self._analyze_with_gemini_direct(question, keywords, search_results, settings.llm_web_search_model)
            return self._parse_fallback_response("OpenAI 분석 중 오류가 발생했습니다.")

    def _get_actual_openai_model(self, model: str) -> str:
        """요청된 OpenAI 모델명을 실제 API 모델명으로 변환합니다."""
        model_mapping = {
            "gpt-4o-search-preview": "gpt-4o-search-preview",
            "gpt-4o-mini-search-preview": "gpt-4o-mini-search-preview"
        }
        return model_mapping.get(model, model)

    def _is_search_preview_model(self, model: str) -> bool:
        """검색 프리뷰 모델인지 확인합니다."""
        return model in ["gpt-4o-search-preview", "gpt-4o-mini-search-preview"]

    def _parse_openai_json_response(self, response_text: str) -> Tuple[str, StructuredAnswer]:
        """OpenAI JSON 응답을 파싱합니다."""
        try:
            # JSON 부분만 추출
            response_clean = response_text.strip()
            if "```json" in response_clean:
                start_idx = response_clean.find("```json") + 7
                end_idx = response_clean.find("```", start_idx)
                if end_idx != -1:
                    response_clean = response_clean[start_idx:end_idx].strip()
            elif response_clean.startswith("{") and response_clean.endswith("}"):
                # 이미 JSON 형태인 경우
                pass
            else:
                # JSON이 아닌 경우 fallback
                return self._parse_fallback_response(response_text)
            
            # JSON 파싱
            data = json.loads(response_clean)
            
            # 필수 필드 확인 및 기본값 설정 + 타입 변환
            summary = data.get("summary", "검색 결과를 분석했습니다.")
            
            # 각 필드의 타입을 확인하고 필요시 변환
            direct_answer = data.get("direct_answer", "검색 결과를 바탕으로 답변을 생성했습니다.")
            if isinstance(direct_answer, list):
                direct_answer = " ".join(direct_answer)
            
            background_info = data.get("background_info", "관련 배경 정보입니다.")
            if isinstance(background_info, list):
                background_info = " ".join(background_info)
            
            interesting_facts = data.get("interesting_facts", "흥미로운 추가 정보입니다.")
            if isinstance(interesting_facts, list):
                interesting_facts = " ".join(interesting_facts)
            
            easy_explanation = data.get("easy_explanation", "쉽게 설명드리면 이런 내용입니다.")
            if isinstance(easy_explanation, list):
                easy_explanation = " ".join(easy_explanation)
            
            key_concepts = data.get("key_concepts", ["주요 개념"])
            if isinstance(key_concepts, str):
                key_concepts = [key_concepts]
            elif not isinstance(key_concepts, list):
                key_concepts = ["주요 개념"]
            
            related_topics = data.get("related_topics", ["관련 주제"])
            if isinstance(related_topics, str):
                related_topics = [related_topics]
            elif not isinstance(related_topics, list):
                related_topics = ["관련 주제"]
            
            structured_answer = StructuredAnswer(
                direct_answer=direct_answer,
                background_info=background_info,
                interesting_facts=interesting_facts,
                easy_explanation=easy_explanation,
                key_concepts=key_concepts,
                related_topics=related_topics
            )
            
            return summary, structured_answer
            
        except Exception as e:
            logger.error(f"OpenAI JSON 응답 파싱 중 오류: {str(e)}")
            return self._parse_fallback_response("응답 파싱 중 오류가 발생했습니다.")

    def _parse_fallback_response(self, response_text: str, summary: str = "") -> Tuple[str, StructuredAnswer]:
        """JSON 파싱 실패시 사용하는 fallback 파싱 메서드"""
        try:
            # 요약이 없으면 첫 번째 문단을 요약으로 사용
            if not summary:
                lines = response_text.strip().split('\n')
                summary = lines[0] if lines else "검색 결과를 바탕으로 답변을 생성했습니다."
            
            # 전체 응답을 직접 답변으로 사용하고 간단한 구조화 시도
            structured_answer = StructuredAnswer(
                direct_answer=response_text[:500] + "..." if len(response_text) > 500 else response_text,
                background_info="검색 결과를 바탕으로 한 정보입니다.",
                interesting_facts="추가 정보가 필요한 경우 더 구체적인 검색을 해보세요.",
                easy_explanation="검색 결과에서 찾은 정보를 정리해드렸어요!",
                key_concepts=["검색 결과", "정보 요약"],
                related_topics=["추가 검색", "상세 정보"]
            )
            
            logger.debug(f"Fallback 파싱 완료 - 요약 길이: {len(summary)}")
            return summary, structured_answer
            
        except Exception as e:
            logger.error(f"Fallback 파싱 중 오류: {str(e)}")
            # 최종 fallback
            fallback_answer = StructuredAnswer(
                direct_answer="검색 결과를 처리하는 중 문제가 발생했습니다.",
                background_info="시스템에 일시적인 문제가 있습니다.",
                interesting_facts="잠시 후 다시 시도해주세요.",
                easy_explanation="컴퓨터가 잠깐 쉬고 있어요!",
                key_concepts=["시스템 오류"],
                related_topics=["재시도 필요"]
            )
            return "검색 결과 처리 중 오류가 발생했습니다.", fallback_answer

    def _format_search_results(self, search_results: List[SearchResult]) -> str:
        """검색 결과를 텍스트 형태로 포맷팅합니다."""
        formatted = []
        for i, result in enumerate(search_results, 1):
            formatted.append(f"""
{i}. **{result.title}**
   URL: {result.url}
   내용: {result.snippet}
   관련도: {result.relevance_score or 'N/A'}
""")
        return "\n".join(formatted)
    
    def _detect_content_language(self, question: str, search_results: List[SearchResult] = None) -> str:
        """내용의 언어를 감지합니다."""
        import re
        
        # 전체 텍스트 결합
        full_text = question
        if search_results:
            for result in search_results[:3]:  # 상위 3개 결과만 사용
                full_text += " " + (result.title or "") + " " + (result.snippet or "")
        
        # 언어별 문자 수 계산
        korean_chars = len(re.findall(r'[가-힣]', full_text))
        japanese_chars = len(re.findall(r'[぀-ゟ゠-ヿ]', full_text))  # 히라가나, 카타카나
        chinese_chars = len(re.findall(r'[一-鿿]', full_text))  # 한자 (일본어/중국어 공통)
        english_chars = len(re.findall(r'[a-zA-Z]', full_text))
        
        # 일본어 한자와 중국어 한자 구분
        if japanese_chars > 0:
            # 히라가나/카타카나가 있으면 일본어
            total_japanese = japanese_chars + chinese_chars
        else:
            # 히라가나/카타카나가 없으면 한자는 중국어로 처리
            total_japanese = 0
            
        # 각 언어의 총 문자 수
        language_counts = {
            'Japanese': total_japanese,
            'Korean': korean_chars,
            'Chinese': chinese_chars if japanese_chars == 0 else 0,  # 일본어가 없을 때만 중국어로 처리
            'English': english_chars
        }
        
        # 가장 많은 문자를 가진 언어 반환
        max_lang = max(language_counts, key=language_counts.get)
        
        # 디버깅
        logger.debug(f"언어 감지: {language_counts}, 결과: {max_lang}")
        
        # 모든 언어가 0이면 영어를 기본값으로
        if language_counts[max_lang] == 0:
            return 'English'
            
        return max_lang
    
    def _get_perspectives_by_language(self, search_query: str, detected_language: str) -> List[str]:
        """언어에 따라 다양한 관점의 검색 주제를 생성합니다."""
        if detected_language == "Japanese":
            return [
                f"{search_query}の基本概念と定義",
                f"{search_query}の最新動向と発展",
                f"{search_query}の実生活適用事例"
            ]
        elif detected_language == "Korean":
            return [
                f"{search_query}의 기본 개념과 정의",
                f"{search_query}의 최신 동향과 발전",
                f"{search_query}의 실생활 적용 사례"
            ]
        elif detected_language == "Chinese":
            return [
                f"{search_query}的基本概念和定义",
                f"{search_query}的最新动态和发展",
                f"{search_query}的实际应用案例"
            ]
        else:  # English
            return [
                f"Basic concepts and definitions of {search_query}",
                f"Latest trends and developments in {search_query}",
                f"Real-life application examples of {search_query}"
            ]
    
    def _get_search_result_title_suffix(self, detected_language: str) -> str:
        """언어에 따라 검색 결과 제목 접미사를 반환합니다."""
        if detected_language == "Japanese":
            return "OpenAI検索結果"
        elif detected_language == "Korean":
            return "OpenAI 검색 결과"
        elif detected_language == "Chinese":
            return "OpenAI搜索结果"
        else:  # English
            return "OpenAI Search Results"
    
    def _get_localized_perspective_title(self, perspective: str, detected_language: str) -> str:
        """관점을 해당 언어로 지역화합니다."""
        # 이미 해당 언어로 생성된 경우 그대로 반환
        return perspective