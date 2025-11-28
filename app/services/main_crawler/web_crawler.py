from typing import Dict, Any, Optional
from urllib.parse import urlparse

from app.utils.logger.setup import setup_logger
from app.utils.language.generator import call_llm
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnablePassthrough

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests

# 설정 및 프롬프트 템플릿 import
from app.core.config import settings
from app.prompts.main_crawler.generator import get_content_extraction_prompt
from app.services.main_crawler.naver_web_crawler import NaverWebCrawler
from app.services.language.language_detection.detector import detect_language_with_ai

import re
import time

logger = setup_logger('main_crawler')

class MainCrawlerAgent:
    """URL 본문 추출 에이전트 - LangChain/LangGraph 기반"""

    # 싱글톤 인스턴스
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, llm_api_key: str = None):
        # 이미 초기화된 경우 중복 초기화 방지
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        # API 키 설정 (매개변수 우선, 없으면 설정에서 가져오기)
        self.openai_api_key = llm_api_key or settings.openai_api_key

        # Selenium WebDriver 설정
        self._selenium_driver = None
        self._setup_selenium_driver()

        # 크롤링 통계
        self.crawl_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "total_content_length": 0
        }

        # 모델명 저장 (call_llm 사용)
        self.model = settings.web_crawler_model
        self.setup_workflow()
    
    @classmethod
    def get_instance(cls):
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def cleanup(cls):
        """정적 cleanup 메서드 - 전역 WebDriver 정리"""
        if cls._instance and cls._instance._selenium_driver:
            try:
                cls._instance._close_selenium_driver()
                logger.info("🧹 전역 Selenium WebDriver 정리 완료")
            except Exception as e:
                logger.error(f"⚠️ 전역 Selenium WebDriver 정리 중 오류: {str(e)}")
        else:
            logger.info("ℹ️ 정리할 WebDriver 인스턴스가 없습니다")
    
    def _setup_selenium_driver(self):
        """Selenium WebDriver 설정"""
        try:
            chrome_options = Options()

            # 설정에서 가져온 옵션 적용
            if settings.web_crawler_headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument(f'--window-size={settings.web_crawler_window_size}')
            chrome_options.add_argument(f'--user-agent={settings.web_crawler_user_agent}')
            
            # 자동화 감지 방지
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self._selenium_driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 자동화 감지 방지 스크립트 실행
            self._selenium_driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            logger.error(f"Selenium WebDriver 초기화 실패: {str(e)}")
            self._selenium_driver = None
    
    def _close_selenium_driver(self):
        """Selenium WebDriver 종료"""
        if self._selenium_driver:
            try:
                self._selenium_driver.quit()
                self._selenium_driver = None
            except Exception as e:
                logger.error(f"Selenium WebDriver 종료 실패: {str(e)}")
    
    def _handle_302_redirect(self, url: str) -> str:
        """302 에러 처리 및 리다이렉트 URL 반환"""
        try:
            logger.info(f"🔄 302 리다이렉트 체크: {url}")
            
            # requests를 사용하여 302 리다이렉트 체크
            headers = {
                'User-Agent': settings.web_crawler_user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # 리다이렉트 허용하여 요청
            response = requests.get(
                url, 
                headers=headers, 
                allow_redirects=True, 
                timeout=10,
                verify=False
            )
            
            final_url = response.url
            status_code = response.status_code
            
            # 302 에러인 경우에만 처리
            if status_code == 302:
                logger.info(f"🔄 302 리다이렉트 감지: {url} → {final_url}")
                return final_url
            else:
                logger.info(f"📊 HTTP 상태 코드: {status_code} (302 아님)")
                return url
                
        except requests.exceptions.TooManyRedirects:
            logger.error(f"❌ 너무 많은 리다이렉트: {url}")
            return url
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ 302 체크 타임아웃: {url}")
            return url
            
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ 연결 오류: {url}")
            return url
            
        except Exception as e:
            logger.error(f"❌ 302 처리 중 오류: {str(e)}")
            return url
    
    async def _crawl_website(self, url: str) -> tuple[str, str]:
        """웹사이트 크롤링 - 개선된 timeout 처리"""
        self.crawl_stats["total_requests"] += 1
        
        max_retries = 2  # 최대 재시도 횟수
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                if not self._selenium_driver:
                    self._setup_selenium_driver()
                
                # 1단계: 302 에러 체크 및 처리
                final_url = self._handle_302_redirect(url)
                logger.info(f"🌐 최종 URL: {final_url}")
                
                # 2단계: 페이지 로드 (재시도 시 더 짧은 timeout)
                current_timeout = settings.web_crawler_timeout - (retry_count * 10)  # 재시도 시 timeout 단축
                current_timeout = max(current_timeout, 15)  # 최소 15초 보장
                
                logger.info(f"🌐 페이지 로드 시작: {final_url} (timeout: {current_timeout}초, 시도: {retry_count + 1}/{max_retries + 1})")
                self._selenium_driver.set_page_load_timeout(current_timeout)
                self._selenium_driver.get(final_url)
                
                # 3단계: 페이지 로딩 대기 (재시도 시 더 짧은 대기시간)
                wait_timeout = 15 - (retry_count * 3)  # 재시도 시 대기시간 단축
                wait_timeout = max(wait_timeout, 5)  # 최소 5초 보장
                
                try:
                    WebDriverWait(self._selenium_driver, wait_timeout).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    logger.info(f"✅ 페이지 로딩 완료 (대기시간: {wait_timeout}초)")
                except TimeoutException:
                    if retry_count < max_retries:
                        logger.warning(f"⚠️ 페이지 로딩 타임아웃 (대기시간: {wait_timeout}초), 재시도 예정")
                        retry_count += 1
                        continue
                    else:
                        logger.warning("⚠️ 페이지 로딩 타임아웃, 계속 진행")

                # 4단계: 제목 추출
                title = self._selenium_driver.title
                
                # 5단계: 본문 추출
                content = await self._extract_content()
                
                if content and len(content) > 0:
                    self.crawl_stats["successful_requests"] += 1
                    logger.info(f"✅ 크롤링 성공: {len(content)}자")
                    return content, title
                else:
                    if retry_count < max_retries:
                        logger.warning(f"⚠️ 콘텐츠 추출 실패, 재시도 예정 (시도: {retry_count + 1}/{max_retries + 1})")
                        retry_count += 1
                        continue
                    else:
                        self.crawl_stats["failed_requests"] += 1
                        logger.error("❌ 크롤링 실패")
                        return "", title
            
            except WebDriverException as e:
                error_msg = str(e)
                
                # WebDriver 관련 오류 처리
                if "ERR_NAME_NOT_RESOLVED" in error_msg:
                    logger.error(f"❌ DNS 해석 실패: {url}")
                    return "", ""
                elif "ERR_CONNECTION_REFUSED" in error_msg:
                    logger.error(f"❌ 연결 거부됨: {url}")
                    return "", ""
                elif "ERR_CONNECTION_TIMED_OUT" in error_msg:
                    if retry_count < max_retries:
                        logger.warning(f"⚠️ 연결 타임아웃, 재시도 예정: {url}")
                        retry_count += 1
                        continue
                    else:
                        logger.error(f"❌ 연결 타임아웃 (최대 재시도 초과): {url}")
                        self.crawl_stats["failed_requests"] += 1
                        return "", ""
                elif "ERR_SSL_PROTOCOL_ERROR" in error_msg:
                    logger.error(f"❌ SSL 프로토콜 오류: {url}")
                    return "", ""
                elif "ERR_CERT_AUTHORITY_INVALID" in error_msg:
                    logger.error(f"❌ SSL 인증서 오류: {url}")
                    return "", ""
                else:
                    if retry_count < max_retries:
                        logger.warning(f"⚠️ WebDriver 오류, 재시도 예정: {error_msg}")
                        retry_count += 1
                        continue
                    else:
                        logger.error(f"❌ WebDriver 오류 (최대 재시도 초과): {error_msg}")
                        self.crawl_stats["failed_requests"] += 1
                        return "", ""
                    
            except TimeoutException as e:
                if retry_count < max_retries:
                    logger.warning(f"⚠️ 페이지 로딩 타임아웃, 재시도 예정: {url}")
                    retry_count += 1
                    continue
                else:
                    logger.error(f"❌ 페이지 로딩 타임아웃 (최대 재시도 초과): {url}")
                    self.crawl_stats["failed_requests"] += 1
                    return "", ""
                    
            except Exception as e:
                if retry_count < max_retries:
                    logger.warning(f"⚠️ 크롤링 오류, 재시도 예정: {str(e)}")
                    retry_count += 1
                    continue
                else:
                    logger.error(f"❌ 크롤링 실패 (최대 재시도 초과): {str(e)}")
                    self.crawl_stats["failed_requests"] += 1
                    return "", ""
        
        # 모든 재시도 실패 시
        logger.error(f"❌ 최대 재시도 횟수 초과: {url}")
        self.crawl_stats["failed_requests"] += 1
        return "", ""
    
    async def _extract_content(self) -> str:
        """본문 추출"""
        extract_start = time.time()
        try:
            current_url = self._selenium_driver.current_url
            
            # 네이버 블로그/카페만 특화 크롤러 사용
            if 'blog.naver.com' in current_url or 'cafe.naver.com' in current_url:
                logger.info("🔍 네이버 블로그/카페 감지, NaverWebCrawler 사용")
                naver_crawler = NaverWebCrawler(self._selenium_driver, self.model)
                naver_content = await naver_crawler.extract_naver_content()
                if naver_content:
                    extract_time = time.time() - extract_start
                    logger.info(f"⏱️ 네이버 크롤러 본문 추출 완료: {extract_time:.2f}초")
                    return naver_content
            
            # 그 외 모든 사이트(네이버 뉴스 포함)는 일반 사이트로 처리
            logger.info("🌐 일반 사이트로 처리")
            result = await self._extract_general_content()
            extract_time = time.time() - extract_start
            logger.info(f"⏱️ LLM 기반 본문 추출 완료: {extract_time:.2f}초")
            return result
            
        except Exception as e:
            extract_time = time.time() - extract_start
            logger.error(f"❌ 본문 추출 실패 ({extract_time:.2f}초): {str(e)}")
            return ""
    
    async def _extract_general_content(self) -> str:
        """일반 사이트 본문 추출 - LLM 활용"""
        try:
            # 1단계: HTML 페이지 소스 가져오기
            html_content = self._selenium_driver.page_source
            
            if not html_content or len(html_content) < 100:
                logger.warning(f"⚠️ 페이지 소스가 비어있거나 너무 짧음: {len(html_content) if html_content else 0}자")
                return ""
            
            logger.info(f"🔍 [EXTRACT] HTML 소스 길이: {len(html_content)}자")
            
            # 2단계: LLM에게 HTML을 전달해서 본문만 추출
            try:
                extracted_content = await self._extract_content_with_llm(html_content)
                
                if extracted_content and len(extracted_content.strip()) > 30:
                    logger.info(f"✅ [EXTRACT] LLM 추출 성공: {len(extracted_content)}자")
                    return self._clean_content(extracted_content)
                else:
                    logger.warning(f"⚠️ [EXTRACT] LLM 추출 결과가 부족: {len(extracted_content) if extracted_content else 0}자")
                    
            except Exception as llm_e:
                logger.error(f"❌ [EXTRACT] LLM 추출 실패: {str(llm_e)}")
                
        except Exception as e:
            logger.error(f"❌ [EXTRACT] 전체 본문 추출 실패: {str(e)}")
            return ""
    
    async def _extract_content_with_llm(self, html_content: str) -> str:
        """전체 HTML에서 본문 추출 + 메타데이터 제거 (통합, 언어별 프롬프트)"""
        try:
            logger.info("🔄 HTML 정리 및 언어 감지 중...")

            # 1단계: BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(html_content, 'html.parser')

            # 2단계: 안전한 태그 제거 (본문 보존)
            self._remove_unnecessary_tags(soup)

            # 3단계: 정리된 HTML을 텍스트로 변환
            cleaned_text = soup.get_text(separator='\n', strip=True)

            logger.info(f"✅ HTML 정리 완료 (원본: {len(html_content)}자 → 정리: {len(cleaned_text)}자)")

            # 4단계: 텍스트가 너무 적으면 원본 사용 (안전장치)
            if len(cleaned_text) < 100:
                logger.warning("⚠️ 정리된 텍스트가 너무 적음, 원본 HTML 사용")
                cleaned_text = soup.get_text(separator='\n', strip=True)

            # 5단계: AI 기반 언어 감지
            detection_result = await detect_language_with_ai(cleaned_text)
            lang_code = detection_result.get("primary_language")
            confidence = detection_result.get("confidence", 0.0)
            logger.info(f"🌐 AI 언어 감지: {lang_code}, 신뢰도: {confidence:.2f}")

            # 6단계: 언어별 프롬프트 가져오기
            prompt_template = get_content_extraction_prompt(lang_code)
            formatted_prompt = prompt_template.format(raw_content=cleaned_text)

            messages = [{"role": "user", "content": formatted_prompt}]

            # 7단계: LLM으로 본문 추출 + 메타데이터 제거 (1번만 호출)
            response = await call_llm(prompt=messages, model=self.model)
            extracted_text = response.content.strip()

            logger.info(f"✅ LLM 본문 추출 완료 ({len(extracted_text)}자, 언어: {lang_code})")

            return extracted_text

        except Exception as e:
            logger.error(f"❌ LLM 본문 추출 중 오류: {str(e)}")
            return ""
    
    def _remove_unnecessary_tags(self, soup: BeautifulSoup):
        """불필요한 HTML 태그들 제거"""
        try:
            # 1. 스크립트, 스타일, 메타 태그만 제거 (안전한 태그들)
            for tag in soup.find_all(['script', 'style', 'meta', 'link', 'noscript']):
                tag.decompose()
            
            # 2. 폼 관련 태그 제거 (검색창, 로그인 폼 등)
            for tag in soup.find_all(['form', 'input', 'button', 'select', 'textarea']):
                tag.decompose()
            
            # 3. 광고 관련 태그 제거
            for tag in soup.find_all(['iframe', 'embed', 'object']):
                tag.decompose()
            
            # 4. 명확히 불필요한 클래스명만 제거
            unwanted_classes = [
                'advertisement', 'banner', 'promotion', 'sponsor',
                'cookie-banner', 'popup', 'modal', 'overlay',
                'loading', 'spinner', 'progress'
            ]
            
            for class_name in unwanted_classes:
                unwanted_tags = soup.find_all(attrs={'class': re.compile(class_name, re.I)})
                for tag in unwanted_tags:
                    # 텍스트가 적은 경우만 제거 (본문 보존)
                    if len(tag.get_text(strip=True)) < 200:
                        tag.decompose()
            
            # 5. 완전히 빈 태그만 제거
            for tag in soup.find_all(['div', 'span', 'p']):
                text_content = tag.get_text(strip=True)
                has_images = tag.find_all(['img', 'video'])
                has_children = tag.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'a'])
                
                # 텍스트가 전혀 없고, 이미지도 없고, 자식 요소도 없는 경우만 제거
                if not text_content and not has_images and len(has_children) == 0:
                    tag.decompose()
            
            # 6. 과도한 공백만 정리
            for tag in soup.find_all(text=True):
                if tag.parent.name not in ['script', 'style']:
                    # 연속된 공백만 정리 (줄바꿈은 보존)
                    cleaned_text = re.sub(r'[ \t]+', ' ', tag.string)
                    # 줄바꿈은 보존하되 과도한 줄바꿈만 정리
                    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
                    if cleaned_text.strip():
                        tag.replace_with(cleaned_text)
                    else:
                        tag.extract()
                        
        except Exception as e:
            logger.error(f"❌ HTML 태그 제거 중 오류: {str(e)}")
    
    def _clean_content(self, text: str) -> str:
        """콘텐츠 기본 정리 (공백 정리만 수행, LLM에서 이미 메타데이터 제거 완료)"""
        try:
            # 기본적인 텍스트 정리만 수행
            lines = text.split('\n')
            clean_lines = []

            for line in lines:
                line = line.strip()
                if not line or len(line) < 3:
                    continue
                clean_lines.append(line)

            final_text = '\n'.join(clean_lines)
            final_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', final_text)
            final_text = final_text.strip()

            return final_text

        except Exception as e:
            logger.error(f"콘텐츠 정리 실패: {str(e)}")
            return text
    
    def setup_workflow(self):
        """LangGraph 워크플로우 설정"""
        
        # 상태 정의 - TypedDict 사용
        from typing import TypedDict
        
        class AgentState(TypedDict):
            url: str
            title: Optional[str]
            raw_content: Optional[str]
            extracted_content: Optional[str]
            error: Optional[str]
        
        # 노드 정의
        async def crawl_node(state: AgentState) -> AgentState:
            """웹 크롤링 노드"""
            url = state["url"]

            try:
                logger.info(f"🌐 [CRAWL] 크롤링 시작: {url}")

                # 크롤링 메서드 사용 (간단하게 await 사용)
                content, title = await self._crawl_website(url)

                # 응답 상태 로깅
                content_length = len(content) if content else 0
                logger.info(f"📋 [CRAWL] 크롤링 결과:")
                logger.info(f"   - 제목: {title if title else 'N/A'}")
                logger.info(f"   - 콘텐츠 길이: {content_length}자")

                if content and len(content) > 0:
                    preview = content[:100].replace('\n', ' ').strip()
                    logger.info(f"   - 콘텐츠 미리보기: {preview}...")

                # 성공 조건: 콘텐츠가 있고 의미있는 길이
                if content and len(content) > 30:
                    # _extract_content에서 이미 LLM으로 본문 추출 완료
                    state["extracted_content"] = content
                    state["title"] = title
                    logger.info(f"✅ [CRAWL] 크롤링 및 본문 추출 성공 - {content_length}자")
                    return state

                # 실패 케이스
                error_msg = f"크롤링된 콘텐츠가 없습니다 (콘텐츠 길이: {content_length}자)"

                # 실패 원인 분석
                if self._selenium_driver:
                    try:
                        current_url = self._selenium_driver.current_url
                        page_source_length = len(self._selenium_driver.page_source)

                        if current_url != url:
                            error_msg += f" - URL 리다이렉트: {url} → {current_url}"

                        if page_source_length == 0:
                            error_msg += " - 페이지 소스가 비어있음"

                    except Exception as e:
                        error_msg += f" - WebDriver 상태 확인 중 오류: {str(e)}"
                else:
                    error_msg += " - WebDriver가 초기화되지 않음"

                logger.error(f"❌ [CRAWL] 크롤링 실패: {error_msg}")
                state["error"] = error_msg
                return state

            except Exception as e:
                error_detail = str(e)
                logger.error(f"❌ [CRAWL] 예외 발생: {error_detail}")

                # 특정 오류 패턴 분석
                if "timeout" in error_detail.lower():
                    logger.error(f"   - 타임아웃 오류 감지")
                elif "connection" in error_detail.lower():
                    logger.error(f"   - 연결 오류 감지")
                elif "certificate" in error_detail.lower() or "ssl" in error_detail.lower():
                    logger.error(f"   - SSL/인증서 오류 감지")

                state["error"] = f"크롤링 중 오류 발생: {error_detail}"
                return state

        # 워크플로우 그래프 생성
        workflow = StateGraph(AgentState)

        # 노드 추가 (crawl_node에서 본문 추출까지 완료)
        workflow.add_node("crawl", crawl_node)

        # 엣지 연결 (단순화: crawl → END)
        workflow.set_entry_point("crawl")
        workflow.add_edge("crawl", END)

        # 컴파일
        self.app = workflow.compile()
    
    async def extract_content_from_url(self, url: str) -> Dict[str, Any]:
        """URL에서 본문 추출"""        
        try:
            # URL 검증
            if not self._is_valid_url(url):
                logger.error(f"❌ [AGENT] 유효하지 않은 URL: {url}")
                return {
                    "error": "유효하지 않은 URL입니다.",
                    "url": url
                }
            
            # 초기 상태 설정
            initial_state = {
                "url": url,
                "title": None,
                "raw_content": None,
                "extracted_content": None,
                "error": None
            }
            
            # 워크플로우 실행
            result = await self.app.ainvoke(initial_state)
            
            if result.get("error"):
                logger.error(f"❌ [AGENT] 워크플로우 실패 - 오류: {result['error']}")
                return {
                    "error": result["error"],
                    "url": url
                }
            
            # 결과 검증
            extracted_content = result.get("extracted_content", "")
            title = result.get("title", "")
            
            if not extracted_content:
                logger.warning(f"⚠️ [AGENT] 추출된 콘텐츠가 비어있음")
                return {
                    "error": "추출된 콘텐츠가 비어있습니다.",
                    "url": url
                }
            
            return {
                "url": url,
                "title": title,
                "content": extracted_content,
            }
            
        except Exception as e:
            logger.error(f"❌ [AGENT] 예외 발생: {str(e)}")
            return {
                "error": f"처리 중 오류 발생: {str(e)}",
                "url": url
            }
    
    def _is_valid_url(self, url: str) -> bool:
        """URL 유효성 검사"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
