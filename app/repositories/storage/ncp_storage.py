import os
import boto3
from typing import Optional
from io import BytesIO
from datetime import datetime
from app.config import settings
from app.utils.logger.setup import setup_logger

logger = setup_logger('ncp_storage', 'logs/storage')


class NCPStorageRepository:
    """NCP Object Storage 업로드를 담당하는 Repository"""

    def __init__(self):
        """NCP S3 클라이언트 초기화"""
        self.s3_client = None
        if settings.ncp_access_key and settings.ncp_secret_key:
            try:
                self.s3_client = boto3.client(
                    service_name=settings.naver_service_name,
                    endpoint_url=settings.naver_endpoint_url,
                    aws_access_key_id=settings.ncp_access_key,
                    aws_secret_access_key=settings.ncp_secret_key
                )
                logger.info("✅ NCP S3 client initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Warning: Failed to initialize NCP S3 client: {str(e)}")
                self.s3_client = None
        else:
            logger.warning("⚠️ Warning: NCP credentials not configured")

    def _generate_ncp_path(self, filename: str, folder: str) -> str:
        """파일명에서 NCP 경로 생성"""
        date_folder = datetime.now().strftime("%Y%m%d")
        return f"{folder}/{date_folder}/{filename}"

    async def upload_to_ncp(self, file_path: str, folder: str = None) -> Optional[str]:
        """파일을 NCP에 업로드하고 URL 반환

        Args:
            file_path: 업로드할 로컬 파일 경로
            folder: NCP 버킷 내 폴더 경로 (기본값: TTS 폴더)

        Returns:
            업로드된 파일의 공개 URL (실패시 None)
        """
        if not self.s3_client or not settings.naver_bucket_name:
            logger.warning("⚠️ NCP S3 client or bucket name not configured")
            return None

        # 폴더 기본값 설정
        if folder is None:
            folder = settings.naver_bucket_tts_folder

        try:
            filename = os.path.basename(file_path)
            ncp_path = self._generate_ncp_path(filename, folder)

            # 파일을 바이트로 읽기
            with open(file_path, 'rb') as f:
                file_content = f.read()

            file_obj = BytesIO(file_content)

            # NCP에 파일 업로드
            self.s3_client.upload_fileobj(
                file_obj,
                settings.naver_bucket_name,
                ncp_path
            )

            # 파일을 공개로 설정
            self.s3_client.put_object_acl(
                Bucket=settings.naver_bucket_name,
                Key=ncp_path,
                ACL='public-read'
            )

            # URL 생성 및 반환
            file_url = f"{settings.naver_bucket_name}/{ncp_path}"
            logger.info(f"✅ Successfully uploaded to NCP: {file_url}")
            return file_url

        except Exception as e:
            logger.error(f"⚠️ NCP upload failed for {file_path}: {str(e)}")
            return None
