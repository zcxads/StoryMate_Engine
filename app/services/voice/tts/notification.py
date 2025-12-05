from typing import Dict, Set, Any, Optional
import asyncio
import time
from datetime import datetime
from fastapi import WebSocket
from app.models.voice.tts import JobStatusResponse

# 로깅 설정
from app.utils.logger.setup import setup_logger
logger = setup_logger('notification')

class NotificationService:
    """실시간 알림을 위한 서비스 (WebSocket, SSE) - 하트비트 개선"""
    
    def __init__(self):
        # WebSocket 연결 관리
        self.websocket_connections: Dict[str, Set[WebSocket]] = {}
        # SSE 연결 관리  
        self.sse_connections: Dict[str, Set[asyncio.Queue]] = {}
        # 연결 상태 추적
        self.connection_health: Dict[str, Dict[str, Any]] = {}
        # 하트비트 작업 관리
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        
    def _calculate_heartbeat_interval(self, job_id: str, total_files: int = 0) -> int:
        """배치 크기와 처리 시간에 따른 적응적 하트비트 간격 계산"""
        if total_files == 0:
            return 15  # 기본값
        
        # 파일 수에 따른 동적 간격 (최소 10초, 최대 30초)
        base_interval = min(30, max(10, total_files // 2))
        
        # 연결 수가 많으면 더 자주 체크
        total_connections = (
            len(self.websocket_connections.get(job_id, set())) + 
            len(self.sse_connections.get(job_id, set()))
        )
        
        if total_connections > 5:
            base_interval = max(5, base_interval // 2)
        
        return base_interval
    
    async def add_websocket_connection(self, job_id: str, websocket: WebSocket):
        """WebSocket 연결 추가 - 연결 상태 추적 포함"""
        if job_id not in self.websocket_connections:
            self.websocket_connections[job_id] = set()
        
        self.websocket_connections[job_id].add(websocket)
        
        # 연결 상태 초기화
        if job_id not in self.connection_health:
            self.connection_health[job_id] = {
                'websocket_count': 0,
                'sse_count': 0,
                'last_heartbeat': time.time(),
                'heartbeat_failures': 0,
                'created_at': time.time()
            }
        
        self.connection_health[job_id]['websocket_count'] = len(self.websocket_connections[job_id])
        
        logger.info(f"📡 WebSocket connected for job {job_id} (total: {len(self.websocket_connections[job_id])})")
        
        # 하트비트 작업 시작
        await self._start_heartbeat_task(job_id)
    
    async def remove_websocket_connection(self, job_id: str, websocket: WebSocket):
        """WebSocket 연결 제거"""
        if job_id in self.websocket_connections:
            self.websocket_connections[job_id].discard(websocket)
            
            # 연결 상태 업데이트
            if job_id in self.connection_health:
                self.connection_health[job_id]['websocket_count'] = len(self.websocket_connections[job_id])
            
            # 연결이 없으면 딕셔너리에서 제거
            if not self.websocket_connections[job_id]:
                del self.websocket_connections[job_id]
                # 하트비트 작업 정리
                await self._cleanup_heartbeat_task(job_id)
        
        logger.info(f"📡 WebSocket disconnected for job {job_id}")
    
    async def add_sse_connection(self, job_id: str, queue: asyncio.Queue):
        """SSE 연결 추가 - 연결 상태 추적 포함"""
        if job_id not in self.sse_connections:
            self.sse_connections[job_id] = set()
        
        self.sse_connections[job_id].add(queue)
        
        # 연결 상태 초기화
        if job_id not in self.connection_health:
            self.connection_health[job_id] = {
                'websocket_count': 0,
                'sse_count': 0,
                'last_heartbeat': time.time(),
                'heartbeat_failures': 0,
                'created_at': time.time()
            }
        
        self.connection_health[job_id]['sse_count'] = len(self.sse_connections[job_id])
        
        logger.info(f"📡 SSE connected for job {job_id} (total: {len(self.sse_connections[job_id])})")
        
        # 하트비트 작업 시작
        await self._start_heartbeat_task(job_id)
    
    async def remove_sse_connection(self, job_id: str, queue: asyncio.Queue):
        """SSE 연결 제거"""
        if job_id in self.sse_connections:
            self.sse_connections[job_id].discard(queue)
            
            # 연결 상태 업데이트
            if job_id in self.connection_health:
                self.connection_health[job_id]['sse_count'] = len(self.sse_connections[job_id])
            
            # 연결이 없으면 딕셔너리에서 제거
            if not self.sse_connections[job_id]:
                del self.sse_connections[job_id]
                # 하트비트 작업 정리
                await self._cleanup_heartbeat_task(job_id)
        
        logger.info(f"📡 SSE disconnected for job {job_id}")
    
    async def _start_heartbeat_task(self, job_id: str):
        """하트비트 작업 시작"""
        if job_id in self.heartbeat_tasks:
            return  # 이미 실행 중
        
        async def heartbeat_worker():
            while (job_id in self.websocket_connections and self.websocket_connections[job_id]) or \
                (job_id in self.sse_connections and self.sse_connections[job_id]):
                
                interval = self._calculate_heartbeat_interval(job_id)
                await asyncio.sleep(interval)
                
                # 연결 상태 확인 및 하트비트 전송
                await self._perform_heartbeat_check(job_id)
        
        self.heartbeat_tasks[job_id] = asyncio.create_task(heartbeat_worker())
        logger.info(f"💓 Heartbeat task started for job {job_id}")
    
    async def _cleanup_heartbeat_task(self, job_id: str):
        """하트비트 작업 정리"""
        if job_id in self.heartbeat_tasks:
            self.heartbeat_tasks[job_id].cancel()
            try:
                await self.heartbeat_tasks[job_id]
            except asyncio.CancelledError:
                pass
            del self.heartbeat_tasks[job_id]
            logger.info(f"💓 Heartbeat task cleaned up for job {job_id}")
        
        # 연결 상태 정보도 정리
        if job_id in self.connection_health:
            # 모든 연결이 없을 때만 정리
            if (job_id not in self.websocket_connections or not self.websocket_connections[job_id]) and \
                (job_id not in self.sse_connections or not self.sse_connections[job_id]):
                del self.connection_health[job_id]
    
    async def _perform_heartbeat_check(self, job_id: str):
        """연결 상태 확인 및 하트비트 전송"""
        if job_id not in self.connection_health:
            return
        
        current_time = time.time()
        health_info = self.connection_health[job_id]
        
        # WebSocket 연결 상태 확인
        if job_id in self.websocket_connections:
            await self._check_websocket_health(job_id)
        
        # SSE 하트비트 전송
        if job_id in self.sse_connections:
            await self._send_sse_heartbeat(job_id)
        
        # 하트비트 시간 업데이트
        health_info['last_heartbeat'] = current_time
        
        logger.debug(f"💓 Heartbeat performed for job {job_id} - WS: {health_info['websocket_count']}, SSE: {health_info['sse_count']}")
    
    async def _check_websocket_health(self, job_id: str):
        """WebSocket 연결 상태 확인"""
        if job_id not in self.websocket_connections:
            return
        
        disconnected = set()
        active_count = 0
        
        for websocket in self.websocket_connections[job_id].copy():
            try:
                # 핑 전송으로 연결 상태 확인
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": time.time(),
                    "job_id": job_id
                })
                active_count += 1
            except Exception as e:
                logger.warning(f"❌ WebSocket ping failed for job {job_id}: {str(e)}")
                disconnected.add(websocket)
        
        # 끊어진 연결 제거
        for websocket in disconnected:
            await self.remove_websocket_connection(job_id, websocket)
        
        # 연결 상태 업데이트
        if job_id in self.connection_health:
            self.connection_health[job_id]['websocket_count'] = active_count
    
    async def _send_sse_heartbeat(self, job_id: str):
        """SSE 하트비트 전송"""
        if job_id not in self.sse_connections:
            return
        
        heartbeat_data = {
            "type": "heartbeat",
            "timestamp": time.time(),
            "job_id": job_id,
            "connection_status": "active"
        }
        
        disconnected = set()
        active_count = 0
        
        for queue in self.sse_connections[job_id].copy():
            try:
                # 큐가 가득 찬 경우 대비
                if queue.qsize() > 100:  # 큐 크기 제한
                    logger.warning(f"⚠️ SSE queue full for job {job_id}, clearing old messages")
                    while not queue.empty():
                        try:
                            queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                
                await queue.put(heartbeat_data)
                active_count += 1
            except Exception as e:
                logger.warning(f"❌ SSE heartbeat failed for job {job_id}: {str(e)}")
                disconnected.add(queue)
        
        # 끊어진 연결 제거
        for queue in disconnected:
            await self.remove_sse_connection(job_id, queue)
        
        # 연결 상태 업데이트
        if job_id in self.connection_health:
            self.connection_health[job_id]['sse_count'] = active_count
    
    async def has_active_connections(self, job_id: str) -> bool:
        """활성 연결이 있는지 확인"""
        ws_count = len(self.websocket_connections.get(job_id, set()))
        sse_count = len(self.sse_connections.get(job_id, set()))
        return ws_count > 0 or sse_count > 0
    
    async def get_connection_health(self, job_id: str) -> Optional[Dict[str, Any]]:
        """연결 상태 정보 반환"""
        if job_id not in self.connection_health:
            return None
        
        health_info = self.connection_health[job_id].copy()
        health_info['last_heartbeat_ago'] = time.time() - health_info['last_heartbeat']
        health_info['uptime'] = time.time() - health_info['created_at']
        
        return health_info
    
    async def broadcast_job_update(self, job_id: str, job_status: JobStatusResponse):
        """작업 상태 업데이트를 모든 연결된 클라이언트에게 브로드캐스트 - 재시도 로직 포함"""
        
        message_data = {
            "type": "job_update",  # 이 줄이 누락되었을 수 있음
            "job_id": job_id,
            "status": job_status.status.value,
            "progress": job_status.progress,
            "total_files": job_status.total_files,
            "completed_files": job_status.completed_files,
            "failed_files": job_status.failed_files,
            "timestamp": datetime.now().isoformat(),
            "files": job_status.files
        }
        
        logger.info(f"📡 Broadcasting job update for {job_id}: {job_status.status.value} ({int(job_status.progress * 100)}%)")
        
        # 활성 연결이 없으면 경고
        if not await self.has_active_connections(job_id):
            logger.warning(f"⚠️ No active connections for job {job_id}")
            return False
        
        # WebSocket으로 브로드캐스트 (재시도 포함)
        ws_success = await self._broadcast_websocket_with_retry(job_id, message_data)
        
        # SSE로 브로드캐스트 (재시도 포함)
        sse_success = await self._broadcast_sse_with_retry(job_id, message_data)
        
        return ws_success or sse_success
    
    async def _broadcast_websocket_with_retry(self, job_id: str, message_data: Dict[str, Any], max_retries: int = 3) -> bool:
        """WebSocket 브로드캐스트 (재시도 로직 포함)"""
        if job_id not in self.websocket_connections:
            return False
        
        for attempt in range(max_retries):
            disconnected = set()
            sent_count = 0
            
            for websocket in self.websocket_connections[job_id].copy():
                try:
                    await websocket.send_json(message_data)
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"❌ WebSocket send failed (attempt {attempt + 1}): {str(e)}")
                    disconnected.add(websocket)
            
            # 끊어진 연결 제거
            for websocket in disconnected:
                await self.remove_websocket_connection(job_id, websocket)
            
            if sent_count > 0:
                logger.debug(f"📡 WebSocket broadcast sent to {sent_count} connections for job {job_id}")
                return True
            
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))  # 지수 백오프
        
        return False
    
    async def _broadcast_sse_with_retry(self, job_id: str, message_data: Dict[str, Any], max_retries: int = 3) -> bool:
        """SSE 브로드캐스트 (재시도 로직 포함)"""
        if job_id not in self.sse_connections:
            return False
        
        for attempt in range(max_retries):
            disconnected = set()
            sent_count = 0
            
            for queue in self.sse_connections[job_id].copy():
                try:
                    # 큐 크기 체크
                    if queue.qsize() > 50:
                        logger.warning(f"⚠️ SSE queue size warning for job {job_id}: {queue.qsize()}")
                    
                    await queue.put(message_data)
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"❌ SSE send failed (attempt {attempt + 1}): {str(e)}")
                    disconnected.add(queue)
            
            # 끊어진 연결 제거
            for queue in disconnected:
                await self.remove_sse_connection(job_id, queue)
            
            if sent_count > 0:
                logger.debug(f"📡 SSE broadcast sent to {sent_count} connections for job {job_id}")
                return True
            
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))  # 지수 백오프
        
        return False
    
    async def notify_job_progress(self, job_id: str, progress_data: Dict[str, Any]):
        """작업 진행상황 알림 (파일 단위) - 연결 상태 확인 포함"""
        
        # 활성 연결 확인
        if not await self.has_active_connections(job_id):
            logger.warning(f"⚠️ No active connections for progress notification: {job_id}")
            return False
        
        message = {
            "job_id": job_id,
            "type": "progress",
            "data": progress_data,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.debug(f"📡 Notifying progress for job {job_id}: {progress_data.get('filename', 'unknown')} - {progress_data.get('status', 'unknown')}")
        
        # WebSocket으로 진행상황 알림
        ws_success = await self._broadcast_websocket_with_retry(job_id, message)
        sse_success = await self._broadcast_sse_with_retry(job_id, message)
        
        return ws_success or sse_success
    
    async def notify_job_completion(self, job_id: str, final_status: JobStatusResponse):
        """작업 완료/실패 알림"""
        
        completion_message = {
            "job_id": job_id,
            "type": "completion",
            "status": final_status.status.value,
            "progress": final_status.progress,
            "total_files": final_status.total_files,
            "completed_files": final_status.completed_files,
            "failed_files": final_status.failed_files,
            "timestamp": datetime.now().isoformat(),
            "message": f"작업이 {final_status.status.value}되었습니다."
        }
        
        logger.info(f"🎉 Job {job_id} completed - notifying all clients")
        
        # 완료 알림 브로드캐스트
        ws_success = await self._broadcast_websocket_with_retry(job_id, completion_message)
        sse_success = await self._broadcast_sse_with_retry(job_id, completion_message)
        
        logger.info(f"🎉 Job {job_id} completion notifications sent")
        
        # 완료 후 하트비트 작업 정리 (약간의 지연 후)
        async def cleanup_after_completion():
            await asyncio.sleep(5)  # 클라이언트가 메시지를 받을 시간 제공
            await self._cleanup_heartbeat_task(job_id)
        
        asyncio.create_task(cleanup_after_completion())
        
        return ws_success or sse_success
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """연결 통계 반환 - 상태 정보 포함"""
        stats = {
            "websocket_connections": {
                job_id: len(connections) 
                for job_id, connections in self.websocket_connections.items()
            },
            "sse_connections": {
                job_id: len(connections) 
                for job_id, connections in self.sse_connections.items()
            },
            "total_websocket_jobs": len(self.websocket_connections),
            "total_sse_jobs": len(self.sse_connections),
            "total_websocket_connections": sum(len(conns) for conns in self.websocket_connections.values()),
            "total_sse_connections": sum(len(conns) for conns in self.sse_connections.values()),
            "connection_health": {
                job_id: {
                    "websocket_count": health["websocket_count"],
                    "sse_count": health["sse_count"],
                    "last_heartbeat_ago": time.time() - health["last_heartbeat"],
                    "uptime": time.time() - health["created_at"]
                }
                for job_id, health in self.connection_health.items()
            },
            "active_heartbeat_tasks": len(self.heartbeat_tasks)
        }
        
        return stats

# 전역 알림 서비스 인스턴스
notification_service = NotificationService()