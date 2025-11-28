import asyncio
import time
import logging
import platform
import subprocess
import os
import re
from typing import Optional, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from app.models.crawler.web_crawler import CrawlRequest, CrawlResponse, CrawlerStatus

logger = logging.getLogger(__name__)

class WebCrawlerService:
    """간결한 웹 크롤러 (리눅스 환경 최적화)"""
    
    def __init__(self):
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "total_content_length": 0
        }
    
    def _create_stable_driver(self, user_agent: str = None) -> webdriver.Chrome:
        """안정적인 Chrome WebDriver 생성"""
        try:
            options = Options()
            
            # 기본 헤드리스 설정
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-images")
            options.add_argument("--window-size=1920,1080")
            
            # 리눅스 환경을 위한 추가 설정
            if platform.system().lower() == "linux":
                options.add_argument("--disable-background-timer-throttling")
                options.add_argument("--disable-backgrounding-occluded-windows")
                options.add_argument("--disable-renderer-backgrounding")
                options.add_argument("--disable-features=TranslateUI")
                options.add_argument("--disable-web-security")
                options.add_argument("--memory-pressure-off")
            
            # User Agent
            ua = user_agent or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            options.add_argument(f"--user-agent={ua}")
            
            # 페이지 로딩 전략
            options.page_load_strategy = 'eager'
            
            # ChromeDriver 서비스 설정
            service = Service(ChromeDriverManager().install())
            
            # WebDriver 생성
            driver = webdriver.Chrome(service=service, options=options)
            
            # 타임아웃 설정
            driver.implicitly_wait(3)
            driver.set_page_load_timeout(20)
            
            return driver
            
        except Exception as e:
            error_msg = f"Chrome WebDriver 생성 실패: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """깔끔한 텍스트만 추출 (불필요한 요소 제거)"""
        # 불필요한 태그 제거
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 
                        'form', 'input', 'button', 'select', 'textarea', 'iframe',
                        'noscript', 'meta', 'link', 'title', 'head']):
            tag.decompose()
        
        # 테이블 전체 제거 (네이버 서비스 링크 등 포함)
        for table in soup.find_all('table'):
            table.decompose()
        
        # 메인 콘텐츠 영역 찾기
        main_content = soup.find('body') or soup
        
        # 텍스트 추출
        text_content = main_content.get_text(separator='\n', strip=True)
        
        # 텍스트 정리
        unwanted_texts = [
            'nexearch', 'top_hty', 'utf8', '로그인', '회원가입',
            '검색', '추천검색어', '인기검색어', '관련검색어',
            '사이트맵', '홈', '뉴스', '지식백과', '블로그',
            '카페', '쇼핑', '영화', 'TV', '기사전체보기',
            '공유하기', '스크랩', '인쇄', '글씨크기',
            '전체메뉴', '바로가기', '최근검색', '인기검색',
            '자동완성', '로그아웃'
        ]
        
        lines = text_content.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            
            # 빈 줄 제거
            if not line:
                continue
                
            # 너무 짧은 줄 제거
            if len(line) < 3:
                continue
            
            # 불필요한 문자열 필터링
            if any(unwanted in line for unwanted in unwanted_texts):
                continue
            
            # 순수한 영어/숫자/특수문자만 있는 짧은 줄 제거
            if re.match(r'^[a-zA-Z0-9\s\W]+$', line) and not re.search(r'[가-힣一-鿿]', line):
                if len(line) < 10:
                    continue
            
            # 중복 라인 제거
            if clean_lines and line == clean_lines[-1]:
                continue
                
            clean_lines.append(line)
        
        # 최종 텍스트 정리
        final_text = '\n'.join(clean_lines)
        final_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', final_text)
        final_text = final_text.strip()
        
        if len(final_text) < 50:
            return "의미있는 콘텐츠를 찾을 수 없습니다."
        
        return final_text
    
    async def crawl_website(self, request: CrawlRequest) -> CrawlResponse:
        """웹사이트 크롤링"""
        start_time = time.time()
        self.stats["total_requests"] += 1
        driver = None
        
        try:
            # WebDriver 생성
            driver = self._create_stable_driver()
            
            # 페이지 로드
            driver.get(str(request.url))
            
            # 짧은 대기
            await asyncio.sleep(2)
            
            response_time = time.time() - start_time
            self.stats["total_response_time"] += response_time
            
            # 페이지 소스 가져오기
            html_content = driver.page_source
            if not html_content:
                html_content = "<html><body>Empty page</body></html>"
            
            content_length = len(html_content)
            self.stats["total_content_length"] += content_length
            
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 제목 추출
            title = None
            try:
                title = driver.title or soup.find('title')
                if title and hasattr(title, 'get_text'):
                    title = title.get_text(strip=True)
            except:
                pass
            
            # 깔끔한 텍스트 추출
            content = self._extract_clean_text(soup)
            
            self.stats["successful_requests"] += 1
            
            return CrawlResponse(
                url=str(request.url),
                status=CrawlerStatus.COMPLETED,
                title=title,
                content=content,
                response_time=response_time
            )
                
        except Exception as e:
            self.stats["failed_requests"] += 1
            response_time = time.time() - start_time
            
            error_message = f"크롤링 실패: {str(e)}"
            
            if "Status code was: 127" in str(e):
                error_message += "\n\n해결방법:"
                error_message += "\n1. sudo apt update && sudo apt install google-chrome-stable"
                error_message += "\n2. sudo apt install libnss3-dev libatk-bridge2.0-0 libdrm2"
                error_message += "\n3. sudo apt install xvfb"
            
            return CrawlResponse(
                url=str(request.url),
                status=CrawlerStatus.FAILED,
                error_message=error_message,
                response_time=response_time
            )
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def get_stats(self) -> Dict[str, Any]:
        """크롤링 통계 반환"""
        avg_response_time = (
            self.stats["total_response_time"] / self.stats["total_requests"]
            if self.stats["total_requests"] > 0 else 0.0
        )
        
        return {
            "total_requests": self.stats["total_requests"],
            "successful_requests": self.stats["successful_requests"],
            "failed_requests": self.stats["failed_requests"],
            "success_rate": (
                self.stats["successful_requests"] / self.stats["total_requests"] * 100
                if self.stats["total_requests"] > 0 else 0.0
            ),
            "average_response_time": round(avg_response_time, 3),
            "total_content_length": self.stats["total_content_length"]
        }

# 전역 크롤러 서비스 인스턴스
crawler_service = WebCrawlerService()
