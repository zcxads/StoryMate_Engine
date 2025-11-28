"""
문제 해결 작업 관리 서비스
"""

import asyncio
import uuid
import time
import json
from typing import Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor

from app.models.language.explanation import (
    ExplanationJobInfo, 
    ExplanationJobStatus,
    ExplanationRequest,
    ExplanationJobStatusResponse
)
from app.services.language.workflow.explanation import process_explanation_workflow_wrapper
from app.utils.logger.setup import setup_logger

# 로거 설정
logger = setup_logger('explanation_job_manager', 'logs/services')

class ExplanationJobManager:
    """문제 해결 작업 관리 클래스"""
    
    def __init__(self):
        self.jobs: Dict[str, ExplanationJobInfo] = {}
        # 🚀 더 많은 worker와 긴 timeout 설정
        self.executor = ThreadPoolExecutor(max_workers=5)  # 동시에 5개 작업 처리
        self.notification_queues: Dict[str, asyncio.Queue] = {}
        
    def create_job(self, request: ExplanationRequest) -> str:
        """새로운 작업 생성"""
        job_id = str(uuid.uuid4())
        
        job_info = ExplanationJobInfo(
            job_id=job_id,
            status=ExplanationJobStatus.PENDING,
            request_data=request
        )
        
        self.jobs[job_id] = job_info
        self.notification_queues[job_id] = asyncio.Queue()
        
        logger.info(f"새로운 문제 해결 작업 생성: {job_id}")
        return job_id
    
    async def start_job(self, job_id: str) -> bool:
        """작업 시작"""
        if job_id not in self.jobs:
            return False
            
        job = self.jobs[job_id]
        if job.status != ExplanationJobStatus.PENDING:
            return False
            
        # 상태 업데이트
        job.status = ExplanationJobStatus.PROCESSING
        job.started_at = time.time()
        
        # 🚀 긴 timeout을 가진 비동기 작업 시작
        asyncio.create_task(self._process_job_with_extended_timeout(job_id))
        
        # 상태 변경 알림
        await self._notify_status_change(job_id, {
            "type": "status_update",
            "job_id": job_id,
            "status": job.status.value,
            "started_at": job.started_at,
            "timestamp": time.time()
        })
        
        logger.info(f"문제 해결 작업 시작: {job_id}")
        return True
    
    async def _process_job_with_extended_timeout(self, job_id: str):
        """확장된 timeout을 가진 작업 처리"""
        job = self.jobs[job_id]
        
        try:
            logger.info(f"문제 해결 처리 시작: {job_id}")
            
            # 진행상황 알림
            await self._notify_status_change(job_id, {
                "type": "progress_update",
                "job_id": job_id,
                "message": "이미지 분석 중... (최대 10분 소요 가능)",
                "timestamp": time.time()
            })
            
            # 🚀 asyncio.wait_for로 긴 timeout 설정 (10분)
            try:
                result = await asyncio.wait_for(
                    process_explanation_workflow_wrapper(job.request_data),
                    timeout=600.0  # 10분 timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"작업 {job_id} 시간 초과 (10분)")
                raise Exception("작업 처리 시간이 10분을 초과했습니다.")
            
            # 성공 완료
            job.status = ExplanationJobStatus.COMPLETED
            job.completed_at = time.time()
            job.execution_time = f"{job.completed_at - job.started_at:.2f}s"
            job.result = result
            
            # 완료 알림
            await self._notify_status_change(job_id, {
                "type": "completion",
                "job_id": job_id,
                "status": job.status.value,
                "result": result,
                "execution_time": job.execution_time,
                "timestamp": job.completed_at
            })
            
            logger.info(f"문제 해결 작업 완료: {job_id} (실행시간: {job.execution_time})")
            
        except Exception as e:
            # 실패 처리
            job.status = ExplanationJobStatus.FAILED
            job.completed_at = time.time()
            job.execution_time = f"{job.completed_at - job.started_at:.2f}s"
            job.error_message = str(e)
            
            # 실패 알림
            await self._notify_status_change(job_id, {
                "type": "error",
                "job_id": job_id,
                "status": job.status.value,
                "error_message": job.error_message,
                "execution_time": job.execution_time,
                "timestamp": job.completed_at
            })
            
            logger.error(f"문제 해결 작업 실패: {job_id} - {str(e)}")
    
    async def _process_job(self, job_id: str):
        """작업 처리 (백그라운드) - 기존 버전"""
        job = self.jobs[job_id]
        
        try:
            logger.info(f"문제 해결 처리 시작: {job_id}")
            
            # 진행상황 알림
            await self._notify_status_change(job_id, {
                "type": "progress_update",
                "job_id": job_id,
                "message": "이미지 분석 중...",
                "timestamp": time.time()
            })
            
            # 실제 문제 해결 처리
            result = await process_explanation_workflow_wrapper(job.request_data)
            
            # 성공 완료
            job.status = ExplanationJobStatus.COMPLETED
            job.completed_at = time.time()
            job.execution_time = f"{job.completed_at - job.started_at:.2f}s"
            job.result = result
            
            # 완료 알림
            await self._notify_status_change(job_id, {
                "type": "completion",
                "job_id": job_id,
                "status": job.status.value,
                "result": result,
                "execution_time": job.execution_time,
                "timestamp": job.completed_at
            })
            
            logger.info(f"문제 해결 작업 완료: {job_id} (실행시간: {job.execution_time})")
            
        except Exception as e:
            # 실패 처리
            job.status = ExplanationJobStatus.FAILED
            job.completed_at = time.time()
            job.execution_time = f"{job.completed_at - job.started_at:.2f}s"
            job.error_message = str(e)
            
            # 실패 알림
            await self._notify_status_change(job_id, {
                "type": "error",
                "job_id": job_id,
                "status": job.status.value,
                "error_message": job.error_message,
                "execution_time": job.execution_time,
                "timestamp": job.completed_at
            })
            
            logger.error(f"문제 해결 작업 실패: {job_id} - {str(e)}")
    
    async def _notify_status_change(self, job_id: str, data: Dict[str, Any]):
        """상태 변경 알림 전송"""
        if job_id in self.notification_queues:
            try:
                await self.notification_queues[job_id].put(data)
            except Exception as e:
                logger.error(f"알림 전송 실패 {job_id}: {str(e)}")
    
    def get_job_status(self, job_id: str) -> Optional[ExplanationJobStatusResponse]:
        """작업 상태 조회"""
        if job_id not in self.jobs:
            return None
            
        job = self.jobs[job_id]
        
        return ExplanationJobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            execution_time=job.execution_time,
            result=job.result,
            error_message=job.error_message,
            model_used=job.result.get("model_used") if job.result else None
        )
    
    def get_all_jobs(self) -> Dict[str, ExplanationJobStatusResponse]:
        """모든 작업 상태 조회"""
        return {
            job_id: self.get_job_status(job_id) 
            for job_id in self.jobs.keys()
        }
    
    async def get_notification_queue(self, job_id: str) -> Optional[asyncio.Queue]:
        """알림 큐 조회"""
        return self.notification_queues.get(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """작업 취소"""
        if job_id not in self.jobs:
            return False
            
        job = self.jobs[job_id]
        if job.status in [ExplanationJobStatus.COMPLETED, ExplanationJobStatus.FAILED]:
            return False
            
        job.status = ExplanationJobStatus.CANCELLED
        job.completed_at = time.time()
        
        logger.info(f"문제 해결 작업 취소: {job_id}")
        return True
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """오래된 작업 정리"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            job_age = current_time - job.created_at
            if job_age > max_age_seconds:
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            if job_id in self.notification_queues:
                del self.notification_queues[job_id]
        
        if jobs_to_remove:
            logger.info(f"오래된 작업 {len(jobs_to_remove)}개 정리됨")

# 전역 인스턴스
explanation_job_manager = ExplanationJobManager()
