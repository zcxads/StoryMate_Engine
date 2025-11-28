import logging
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from app.utils.language.generator import call_llm

logger = logging.getLogger(__name__)

class NaverWebCrawler:
    """네이버 블로그/카페 특화 크롤러"""

    def __init__(self, selenium_driver, model=None):
        self._selenium_driver = selenium_driver
        self.model = model
    
    async def extract_naver_content(self) -> str:
        """네이버 사이트 본문 추출 (블로그/카페만 특화 처리)"""
        try:
            current_url = self._selenium_driver.current_url
            logger.info("🔍 네이버 사이트 본문 추출 시도")
            
            # 네이버 블로그/카페만 특화 로직 사용
            if 'blog.naver.com' in current_url or 'cafe.naver.com' in current_url:
                logger.info("📝 네이버 블로그/카페 감지, 특화 iframe 추출 로직 사용")
                return await self._extract_naver_iframe_content()
            
            # 그 외 네이버 사이트(뉴스, 지식인 등)는 일반 사이트로 처리
            logger.info("🌐 네이버 뉴스/기타 사이트 감지, 일반 사이트로 처리")
            return ""
            
        except Exception as e:
            logger.error(f"❌ 네이버 본문 추출 실패: {str(e)}")
            return ""
    
    async def _extract_naver_iframe_content(self) -> str:
        """네이버 iframe 내부 본문 추출 (최적화된 버전)"""
        try:
            logger.info("🔍 네이버 iframe 내부 본문 추출 시도")
            
            # 페이지 로딩 대기 (단축: 3초)
            try:
                WebDriverWait(self._selenium_driver, 3).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning("⚠️ 페이지 로딩 시간 초과, 계속 진행")
            
            # 1단계: 모든 iframe 순회 (빠른 검색)
            iframes = self._selenium_driver.find_elements(By.TAG_NAME, "iframe")
            logger.info(f"📊 발견된 iframe 수: {len(iframes)}")
            
            for i, iframe in enumerate(iframes):
                try:
                    # iframe으로 전환
                    self._selenium_driver.switch_to.default_content()
                    self._selenium_driver.switch_to.frame(iframe)
                    
                    # iframe 내부 로딩 대기 (단축: 1초)
                    try:
                        WebDriverWait(self._selenium_driver, 1).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                    except TimeoutException:
                        self._selenium_driver.switch_to.default_content()
                        continue
                    
                    # iframe 내부에서 본문 요소 검색 (즉시 검색, 대기 없음)
                    content_selectors = [
                        '.se-main-container',
                        '.se-component-content',
                        '.article_container',
                        '.article_content',
                        '.content_area',
                        '.cafe_content',
                        '.article_body',
                        '.post_content',
                        '.entry-content',
                        '.se-text-paragraph',
                        '.se-component',
                        '.article_viewer',
                        '.article_content'
                    ]
                    
                    for selector in content_selectors:
                        try:
                            # 즉시 검색 (대기 시간 제거)
                            elements = self._selenium_driver.find_elements(By.CSS_SELECTOR, selector)
                            if len(elements) > 0:
                                content = elements[0].text.strip()
                                self._selenium_driver.switch_to.default_content()
                                return self._clean_content(content)
                        except Exception as e:
                            continue
                    
                    # 메인 프레임으로 복귀
                    self._selenium_driver.switch_to.default_content()
                    
                except Exception as e:
                    logger.error(f"❌ iframe {i+1} 처리 실패: {str(e)}")
                    continue
            
            # 2단계: 빠른 iframe HTML 처리 (대기 시간 없음)
            logger.warning("⚠️ iframe에서 본문 요소를 찾지 못함, iframe HTML을 LLM으로 처리")
            
            for i, iframe in enumerate(iframes):
                try:
                    self._selenium_driver.switch_to.default_content()
                    self._selenium_driver.switch_to.frame(iframe)
                    
                    # iframe 내부 HTML 가져오기 (즉시)
                    iframe_html = self._selenium_driver.page_source
                    iframe_text = self._selenium_driver.find_element(By.TAG_NAME, "body").text.strip()
                    
                    self._selenium_driver.switch_to.default_content()

                    # LLM으로 iframe 내부 본문 추출
                    if self.model:
                        extracted_content = self._extract_content_with_llm(iframe_html)
                        if extracted_content:
                            return self._clean_content(extracted_content)
                    else:
                        # LLM이 없는 경우 텍스트 그대로 반환
                        return self._clean_content(iframe_text)
                    
                except Exception as e:
                    logger.error(f"❌ iframe {i+1} HTML 처리 실패: {str(e)}")
                    continue
            
            # 3단계: 전체 페이지 HTML을 LLM으로 처리 (최후의 수단)
            logger.warning("⚠️ iframe에서도 본문을 찾지 못함, 전체 페이지 HTML을 LLM으로 처리")
            try:
                full_html = self._selenium_driver.page_source
                full_text = self._selenium_driver.find_element(By.TAG_NAME, "body").text.strip()
                
                if len(full_text) > 500:  # 충분한 텍스트가 있는 경우
                    logger.info(f"✅ 전체 페이지에서 충분한 텍스트 발견 ({len(full_text)}자)")
                    if self.model:
                        extracted_content = await self._extract_content_with_llm(full_html)
                        if extracted_content:
                            return self._clean_content(extracted_content)
                    else:
                        return self._clean_content(full_text)
            except Exception as e:
                logger.error(f"❌ 전체 페이지 HTML 처리 실패: {str(e)}")
            
            logger.warning("⚠️ 모든 방법으로 본문을 찾지 못함")
            return ""
            
        except Exception as e:
            logger.error(f"❌ 네이버 iframe 본문 추출 실패: {str(e)}")
            return ""
    
    async def _extract_content_with_llm(self, html_content: str) -> str:
        """LLM을 사용하여 본문 추출"""
        try:
            logger.info("🔄 LLM으로 본문 추출")

            # BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(html_content, 'html.parser')

            # 원본 HTML을 텍스트로 변환
            original_text = soup.get_text(separator='\n', strip=True)

            logger.info(f"✅ 원본 HTML 텍스트 변환 완료 ({len(original_text)}자)")

            # AI 기반 언어 감지
            from app.services.language.language_detection.detector import detect_language_with_ai
            detection_result = await detect_language_with_ai(original_text)
            lang_code = detection_result.get("primary_language")
            confidence = detection_result.get("confidence", 0.0)
            logger.info(f"🌐 AI 언어 감지: {lang_code}, 신뢰도: {confidence:.2f}")

            # 언어별 프롬프트 가져오기
            from app.prompts.main_crawler.generator import get_content_extraction_prompt
            prompt_template = get_content_extraction_prompt(lang_code)
            formatted_prompt = prompt_template.format(raw_content=original_text)
            messages = [{"role": "user", "content": formatted_prompt}]

            # async call_llm 호출
            response = await call_llm(prompt=messages, model=self.model)
            extracted_text = response.content.strip()

            logger.info(f"✅ LLM 본문 추출 완료 ({len(extracted_text)}자)")

            return extracted_text

        except Exception as e:
            logger.error(f"❌ LLM 본문 추출 중 오류: {str(e)}")
            return ""
    
    def _clean_content(self, text: str) -> str:
        """추출된 텍스트 정리"""
        if not text:
            return ""
        
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 빈 줄 제거
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text
