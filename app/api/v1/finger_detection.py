from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import Union, Optional
import time
import base64
from app.models.language.finger_detection import (
    FingerDetectionRequest,
    FingerDetectionSimpleResponse,
    FingerDetectionSuccessResponse,
    DocumentReadingResponse,
    ImageToBase64Response,
    SupportedFingerDetectionModelsResponse,
    SUPPORTED_FINGER_DETECTION_MODELS
)
from app.services.language.finger_detection.detector import FingerDetectionService
from app.core.config import settings

# 로깅 설정
from app.utils.logger.setup import setup_logger

logger = setup_logger('finger_detection')

router = APIRouter(prefix="/finger-detection")

NO_FINGER_MESSAGE = "손가락을 인식할 수 없습니다. 명확하게 손가락으로 가리키는 이미지를 다시 업로드해주세요."


def clean_escape_characters(text: str) -> str:
    """응답 텍스트에서 모든 백슬래시 escape 패턴을 제거합니다."""
    if not text:
        return text

    # \" 패턴이 등장하면 \" 전체를 제거 (쌍따옴표까지 모두 제거)
    text = text.replace('\"', '')

    return text.strip()

def get_appropriate_error_message(result: dict) -> str:
    """결과에 따라 적절한 에러 메시지를 반환합니다."""
    # 모든 손가락 인식 실패 케이스에 대해 통일된 에러 메시지 반환
    return "손가락을 인식할 수 없습니다. 명확하게 손가락으로 가리키는 이미지를 다시 업로드해주세요."

@router.get("/models", response_model=SupportedFingerDetectionModelsResponse)
async def get_supported_models() -> SupportedFingerDetectionModelsResponse:
    """
    손가락 인식에서 지원되는 AI 모델 목록을 반환합니다.
    
    Returns:
        SupportedFingerDetectionModelsResponse: 지원되는 모델 목록과 기본 모델 정보
    """
    from app.core.config import settings
    return SupportedFingerDetectionModelsResponse(
        supported_models=SUPPORTED_FINGER_DETECTION_MODELS,
        default_model=settings.default_llm_model,
        total_count=len(SUPPORTED_FINGER_DETECTION_MODELS)
    )

@router.post("/analyze")
async def analyze_finger_pointing(request: FingerDetectionRequest) -> Union[FingerDetectionSimpleResponse, DocumentReadingResponse]:
    """
    손가락 인식 분석 또는 문서 읽기 분석을 수행합니다.
    
    모드별 동작:
    1. finger_detection (기본값):
       - 손가락으로 가리킨 이미지를 분석하여 가리키고 있는 내용을 식별
    
    2. document_reading:
       - 문서 이미지를 자동으로 분석하여 적절한 읽기 순서로 텍스트 추출
       - 대제목, 소제목, 본문을 구분하여 마크다운으로 구조화
       - 한국어/영어: 왼쪽→오른쪽, 일본만화: 오른쪽→왼쪽
    
    Args:
        request: 분석 요청 데이터
            - image_data: Base64로 인코딩된 이미지 데이터 (필수)
            - model: 사용할 LLM 모델 (기본값: gemini-2.5-flash)
            - mode: 분석 모드 (finger_detection | document_reading, 기본값: finger_detection)
            
    """
    start_time = time.time()
    
    try:
        mode = getattr(request, 'mode', 'finger_detection')
        
        # 서비스 초기화
        detector_service = FingerDetectionService()
        
        # 분석 수행
        result = await detector_service.analyze_finger_pointing(request)
        
        # 오류 발생 시 처리
        if result.get("status") == "error":
            error_message = result.get("error", f"{mode} 분석 중 알 수 없는 오류가 발생했습니다.")
            
            if mode == "document_reading":
                return DocumentReadingResponse(
                    markdown_content=clean_escape_characters(f"# 오류 발생\n\n분석 실패: {error_message}"),
                    detected_language="unknown",
                    document_type="unknown",
                    execution_time=result.get("execution_time", f"{time.time() - start_time:.2f}s")
                )
            else:
                return FingerDetectionSuccessResponse(
                    detected_word="분석 실패",
                    meaning="오류 발생",
                    explanation=clean_escape_characters(f"분석 실패: {error_message}"),
                    genre=result.get("genre"),
                    execution_time=result.get("execution_time", f"{time.time() - start_time:.2f}s"),
                    ncp_url=None
                )
        
        # 성공 시 모드별 응답 반환 (escape 문자 후처리 적용)
        if mode == "document_reading":
            return DocumentReadingResponse(
                markdown_content=clean_escape_characters(result.get("markdown_content", "")),
                detected_language=result.get("detected_language"),
                document_type=result.get("document_type"),
                execution_time=result.get("execution_time", f"{time.time() - start_time:.2f}s")
            )
        else:
            # 손가락 인식 실패 시 500 에러 반환
            if "message" in result and len(result) == 1:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=NO_FINGER_MESSAGE
                )

            # 손가락 인식 성공 시 응답 반환
            return FingerDetectionSuccessResponse(
                    detected_word=result.get("detected_word", "인식 실패"),
                    meaning=result.get("meaning", "의미를 파악할 수 없습니다"),
                    explanation=clean_escape_characters(result.get("explanation", get_appropriate_error_message(result))),
                    ncp_url=result.get("ncp_url"),
                    genre=result.get("genre"),
                    execution_time=result.get("execution_time", f"{time.time() - start_time:.2f}s"),
                )
        
    except HTTPException:
        # HTTPException은 그대로 재발생
        raise
    except Exception as e:
        mode = getattr(request, 'mode', 'finger_detection')
        mode_name = "문서 읽기" if mode == "document_reading" else "손가락 인식"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{mode_name} 분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/convert-to-base64", response_model=ImageToBase64Response)
async def convert_image_to_base64(
    image: UploadFile = File(..., description="Base64로 변환할 이미지 파일")
):
    """
    이미지 파일을 Base64 인코딩 값으로 변환합니다.
    
    Args:
        image: 변환할 이미지 파일 (JPEG, PNG, WebP, GIF 지원)
        
    Returns:
        ImageToBase64Response: Base64 인코딩된 이미지 데이터와 메타정보
    """
    try:
        # 업로드된 파일 읽기
        image_data = await image.read()

        # 이미지 형식 확인
        image_format = "Unknown"
        if image_data.startswith(b'\xff\xd8\xff'):
            image_format = "JPEG"
        elif image_data.startswith(b'\x89PNG\r\n\x1a\n'):
            image_format = "PNG"
        elif image_data[8:12] == b'WEBP':
            image_format = "WebP"
        elif image_data.startswith((b'GIF87a', b'GIF89a')):
            image_format = "GIF"
        
        # Base64 인코딩
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 파일 크기 정보 포맷팅
        def format_file_size(size_bytes):
            if size_bytes < 1024:
                return f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
        
        return ImageToBase64Response(
            image_data=image_base64,
            file_size=format_file_size(len(image_data)),
            image_format=image_format,
            base64_size=format_file_size(len(image_base64))
        )
        
    except HTTPException:
        # HTTPException은 그대로 재발생
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 변환 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/analyze-upload")
async def analyze_finger_pointing_upload(
    image: UploadFile = File(..., description="분석할 이미지 파일 (JPEG, PNG, WebP, GIF)"),
    mode: str = Form("finger_detection", description="분석 모드 (finger_detection | document_reading)"),
    model: str = Form(settings.default_llm_model, description="사용할 LLM 모델")
) -> Union[FingerDetectionSimpleResponse, DocumentReadingResponse]:
    """
    이미지 파일을 업로드하고 분석 모드를 선택하면 서버가 내부적으로 Base64로 인코딩 후
    모드에 따라 손가락 인식 또는 문서 읽기 분석을 수행합니다.
    """
    start_time = time.time()
    try:
        # 업로드된 파일 읽기
        image_data = await image.read()

        # Base64 인코딩
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # 서비스 호출용 요청 모델 구성
        request_model = FingerDetectionRequest(
            image_data=image_base64,
            model=model,
            mode=mode
        )

        detector_service = FingerDetectionService()
        result = await detector_service.analyze_finger_pointing(request_model)

        # 오류 처리
        if result.get("status") == "error":
            error_message = result.get("error", f"{mode} 분석 중 알 수 없는 오류가 발생했습니다.")
            if mode == "document_reading":
                return DocumentReadingResponse(
                    markdown_content=clean_escape_characters(f"# 오류 발생\n\n분석 실패: {error_message}"),
                    detected_language="unknown",
                    document_type="unknown",
                    execution_time=result.get("execution_time", f"{time.time() - start_time:.2f}s")
                )
            else:
                return FingerDetectionSuccessResponse(
                    detected_word="분석 실패",
                    meaning="오류 발생",
                    explanation=clean_escape_characters(f"분석 실패: {error_message}"),
                    genre=result.get("genre"),
                    execution_time=result.get("execution_time", f"{time.time() - start_time:.2f}s"),
                    ncp_url=None
                )

        # 성공 시 모드별 응답 반환
        if mode == "document_reading":
            return DocumentReadingResponse(
                markdown_content=clean_escape_characters(result.get("markdown_content", "")),
                detected_language=result.get("detected_language"),
                document_type=result.get("document_type"),
                execution_time=result.get("execution_time", f"{time.time() - start_time:.2f}s")
            )
        else:
            # 손가락 인식 실패 시 500 에러 반환
            if "message" in result and len(result) == 1:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=NO_FINGER_MESSAGE
                )

            # 손가락 인식 성공 시 응답 반환
            return FingerDetectionSuccessResponse(
                    detected_word=result.get("detected_word", "인식 실패"),
                    meaning=result.get("meaning", "의미를 파악할 수 없습니다"),
                    explanation=clean_escape_characters(result.get("explanation", get_appropriate_error_message(result))),
                    ncp_url=result.get("ncp_url"),
                    genre=result.get("genre"),
                    execution_time=result.get("execution_time", f"{time.time() - start_time:.2f}s"),
                )

    except HTTPException:
        raise
    except Exception as e:
        mode_name = "문서 읽기" if mode == "document_reading" else "손가락 인식"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{mode_name} 분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def finger_detection_health_check():
    """손가락 인식 및 문서 읽기 서비스 상태 확인"""
    from app.utils.language.generator import get_available_models
    
    available_models = get_available_models()
    
    return {
        "status": "healthy",
        "service": "Smart Document Analysis Service",
        "description": "손가락 가리키기 인식과 문서 읽기 기능을 통합한 멀티모드 분석 서비스",
        "available_models": available_models,
        "supported_models": SUPPORTED_FINGER_DETECTION_MODELS,
        "features": {
            "image_analysis": True,
            "finger_pointing_detection": True,
            "document_reading": True,
            "markdown_formatting": True,
            "multilingual_support": True,
            "reading_direction_detection": True,
            "object_recognition": True,
            "base64_image_input": True,
            "file_upload_input": True,
            "image_to_base64_converter": True,
            "gemini_integration": True
        },
        "supported_image_formats": ["JPEG", "PNG", "WebP", "GIF"],
        "max_image_size": "10MB (base64 encoded)",
        "analysis_modes": {
            "finger_detection": "손가락으로 가리킨 객체 인식 및 식별",
            "document_reading": "문서를 LLM이 자동으로 분석하여 적절한 읽기 순서로 마크다운 구조화"
        },
        "auto_detection_features": {
            "language_detection": "한국어, 영어, 일본어, 중국어, 아랍어 등 자동 감지",
            "document_type_detection": "일반문서, 만화, 소설, 신문 등 유형 자동 판별",
            "reading_direction_detection": "LLM이 언어와 문서 유형에 따라 자동 결정",
            "special_patterns": ["한국어/영어: 왼쪽→오른쪽", "일본만화: 오른쪽→왼쪽", "아랍어: RTL"]
        },
        "endpoints": [
            "GET /api/v1/finger-detection/models - 지원 모델 목록",
            "POST /api/v1/finger-detection/analyze - 멀티모드 이미지 분석 (finger_detection | document_reading)",
            "POST /api/v1/finger-detection/analyze-upload - 파일 업로드 + 모드 선택 분석",
            "POST /api/v1/finger-detection/convert-to-base64 - 이미지 파일을 Base64로 변환",
            "GET /api/v1/finger-detection/health - 서비스 상태 확인"
        ]
    }