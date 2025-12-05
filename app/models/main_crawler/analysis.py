from pydantic import BaseModel, HttpUrl

class CrawlerAnalysisRequest(BaseModel):
    """크롤러 분석 요청 모델"""
    url: HttpUrl

class CrawlerAnalysisResponse(BaseModel):
    """크롤러 분석 응답 모델 (요약 + 워드 클라우드)"""
    summary: str  # 크롤링 결과 요약 텍스트
    ncp_url: str  # 워드 클라우드 시각화 NCP URL

    class Config:
        # None 값인 필드는 JSON에서 제외
        exclude_none = True
