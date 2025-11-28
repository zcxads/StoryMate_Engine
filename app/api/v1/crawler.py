from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict
import uuid
from datetime import datetime

from app.models.crawler.web_crawler import (
    CrawlRequest,
    CrawlResponse,
    CrawlJob,
    CrawlerStatus
)
from app.services.crawler.web_crawler import crawler_service
from app.utils.logger.setup import setup_logger

logger = setup_logger('crawler')

router = APIRouter(prefix="/crawler")

# 작업 저장소 (실제 환경에서는 Redis나 DB 사용 권장)
crawl_jobs: Dict[str, CrawlJob] = {}

async def perform_async_crawl(job_id: str, request: CrawlRequest):
    """
    백그라운드에서 크롤링을 수행하는 함수
    """
    try:
        # 작업 상태를 PROCESSING으로 변경
        if job_id in crawl_jobs:
            crawl_jobs[job_id].status = CrawlerStatus.PROCESSING
            
        logger.info(f"Starting background crawl for job {job_id}, URL: {request.url}")
        
        # 실제 크롤링 수행
        result = await crawler_service.crawl_website(request)
        
        # 작업 완료 처리
        if job_id in crawl_jobs:
            crawl_jobs[job_id].status = result.status
            crawl_jobs[job_id].completed_at = datetime.now().isoformat()
            crawl_jobs[job_id].result = result
            
            if result.status == CrawlerStatus.FAILED:
                crawl_jobs[job_id].error_message = result.error_message
                logger.error(f"Background crawl failed for job {job_id}: {result.error_message}")
            else:
                logger.info(f"Background crawl completed for job {job_id}")
                
    except Exception as e:
        logger.error(f"Background crawl error for job {job_id}: {str(e)}")
        if job_id in crawl_jobs:
            crawl_jobs[job_id].status = CrawlerStatus.FAILED
            crawl_jobs[job_id].completed_at = datetime.now().isoformat()
            crawl_jobs[job_id].error_message = f"Background crawl error: {str(e)}"

@router.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest):
    """
    웹사이트를 즉시 크롤링하고 결과를 반환합니다.
    """
    try:
        logger.info(f"Starting immediate crawl for URL: {request.url}")
        
        result = await crawler_service.crawl_website(request)
        
        if result.status == CrawlerStatus.FAILED:
            logger.error(f"Crawl failed for {request.url}: {result.error_message}")
            raise HTTPException(
                status_code=400,
                detail=f"Crawling failed: {result.error_message}"
            )
        
        logger.info(f"Successfully crawled {request.url}")
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error in crawl_website: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/crawl/async", response_model=CrawlJob)
async def crawl_website_async(request: CrawlRequest, background_tasks: BackgroundTasks):
    """
    웹사이트를 비동기로 크롤링하고 작업 ID를 반환합니다.
    """
    job_id = str(uuid.uuid4())
    
    # 작업 생성
    job = CrawlJob(
        job_id=job_id,
        url=str(request.url),
        status=CrawlerStatus.PENDING,
        created_at=datetime.now().isoformat()
    )
    
    crawl_jobs[job_id] = job
    
    # 백그라운드에서 크롤링 실행
    background_tasks.add_task(perform_async_crawl, job_id, request)
    
    logger.info(f"Created async crawl job {job_id} for URL: {request.url}")
    return job

@router.get("/jobs/{job_id}", response_model=CrawlJob)
async def get_crawl_job(job_id: str):
    """
    크롤링 작업 상태를 조회합니다.
    """
    if job_id not in crawl_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return crawl_jobs[job_id]

@router.delete("/jobs/{job_id}")
async def delete_crawl_job(job_id: str):
    """
    크롤링 작업을 삭제합니다.
    """
    if job_id not in crawl_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del crawl_jobs[job_id]
    return {"message": f"Job {job_id} deleted successfully"}

@router.get("/jobs")
async def list_crawl_jobs():
    """
    모든 크롤링 작업 목록을 조회합니다.
    """
    return {"jobs": crawl_jobs, "total": len(crawl_jobs)}

@router.get("/health")
async def crawler_health_check():
    """
    크롤러 서비스 상태를 확인합니다.
    """
    try:
        stats = crawler_service.get_stats()
        return {
            "status": "healthy",
            "service": "Web Crawler",
            "stats": stats,
            "active_jobs": len([job for job in crawl_jobs.values() if job.status == CrawlerStatus.PROCESSING]),
            "total_jobs": len(crawl_jobs)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "Web Crawler",
            "error": str(e)
        }
