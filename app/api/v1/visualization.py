from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
import os
import time
from app.models.language.visualization import (
    VisualizationRequest,
    VisualizationGenerateRequest,
    VisualizationResponse,
    VisualizationContent,
    VisualizationError,
    SupportedVisualizationModelsResponse,
    FileTextExtractionResponse,
    SUPPORTED_VISUALIZATION_MODELS,
    VisualizationType,
    VisualizationCategory,
    OutputFormat,
)
from app.services.language.visualization.generator import VisualizationGenerator
from app.core.config import settings
from app.utils.logger.setup import setup_logger

logger = setup_logger("visualization_api")
router = APIRouter(prefix="/visualization")

# 통합 텍스트 추출 함수 임포트
from app.utils.document.text_extractor import extract_text_from_file

ERROR_MESSAGE = "시각화 콘텐츠를 제공할 수 없습니다."

def get_file_type_category(file_extension: str) -> str:
    """파일 확장자를 기반으로 파일 타입 카테고리 반환"""
    if file_extension == 'csv':
        return 'csv'
    elif file_extension in ['xlsx', 'xls']:
        return 'excel'
    elif file_extension == 'pdf':
        return 'pdf'
    elif file_extension in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp']:
        return 'image'
    elif file_extension == 'txt':
        return 'txt'
    else:
        return 'unknown'

async def determine_visualization_category_from_content(content: str, content_type: str) -> VisualizationCategory:
    """콘텐츠를 분석하여 역변환할 시각화 타입 결정"""
    try:
        # 텍스트 내용 분석
        text_lower = content.lower()

        # 표 형태 패턴 감지 (이 경우 차트로 변환)
        table_patterns = [
            '|',  # 파이프로 구분된 표
            '\t',  # 탭으로 구분된 표
            'table', '표',
            'row', '행', 'column', '열',
            'cell', '셀',
        ]

        # 차트 형태 패턴 감지 (이 경우 표로 변환)
        chart_patterns = [
            'chart', '차트', 'graph', '그래프',
            'bar', '막대', 'line', '선', 'pie', '원형',
            'x축', 'y축', 'x-axis', 'y-axis',
            'data point', '데이터 포인트'
        ]

        # 구조적 패턴 분석
        lines = content.split('\n')

        # CSV/표 형태 구조 감지
        structured_lines = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 구분자 패턴 감지: 콤마, 탭, 파이프, 또는 연속된 공백(2개 이상)
            has_delimiter = (
                ',' in line or
                '\t' in line or
                '|' in line or
                '  ' in line  # 2개 이상의 연속 공백 (공백 구분 표)
            )

            if has_delimiter:
                structured_lines += 1

        structure_ratio = structured_lines / max(len([l for l in lines if l.strip()]), 1)

        # 키워드 점수 계산
        table_score = sum(1 for pattern in table_patterns if pattern in text_lower)
        chart_score = sum(1 for pattern in chart_patterns if pattern in text_lower)

        # 구조적 패턴이 강하면 표 형태로 판단 (차트로 변환)
        if structure_ratio > 0.5:
            table_score += 3

        logger.info(f"📊 콘텐츠 분석 ({content_type}) - 표 점수: {table_score}, 차트 점수: {chart_score}, 구조 비율: {structure_ratio:.2f}")
        logger.info(f"📄 콘텐츠 보기: {content}")
        logger.info(f"📈 구조화된 라인 수: {structured_lines} / 전체 라인 수: {len([l for l in lines if l.strip()])}")

        # 파일 타입별 명확한 전략
        if content_type == "text":
            # 텍스트 입력은 무조건 표로 시각화
            logger.info("📋 텍스트 입력 → 표로 시각화 (강제)")
            return VisualizationCategory.TABLE

        elif content_type in ["csv", "excel"]:
            # CSV/Excel은 데이터 파일이므로 차트로 시각화
            logger.info(f"📊 {content_type.upper()} 파일 (데이터) → 차트로 시각화")
            return VisualizationCategory.CHART

        elif content_type == "pdf":
            # PDF는 표 형태 데이터면 차트로 시각화
            if table_score > chart_score or structure_ratio > 0.5:
                logger.info(f"📊 PDF 표 형태 데이터 감지 → 차트로 시각화")
                return VisualizationCategory.CHART
            else:
                logger.info(f"📋 PDF 차트 형태 감지 → 표로 추출")
                return VisualizationCategory.TABLE

        elif content_type == "image":
            # 이미지: 표 형태면 차트로 시각화, 차트면 표로 추출
            if table_score > chart_score or structure_ratio > 0.5:
                logger.info("📊 이미지 표 형태 데이터 감지 → 차트로 시각화")
                return VisualizationCategory.CHART
            else:
                logger.info("📋 이미지 차트 감지 → 표로 추출")
                return VisualizationCategory.TABLE

        else:
            # 기타: 표 형태 데이터면 차트로 시각화
            if table_score > chart_score or structure_ratio > 0.5:
                logger.info(f"📊 표 형태 데이터 감지 ({content_type}) → 차트로 시각화")
                return VisualizationCategory.CHART
            else:
                logger.info(f"📋 차트 형태 감지 ({content_type}) → 표로 추출")
                return VisualizationCategory.TABLE

    except Exception as e:
        logger.warning(f"⚠️ 콘텐츠 타입 분석 실패, 기본값 사용: {str(e)}")
        # 기본값 전략: 텍스트만 표, 나머지는 차트
        if content_type == "text":
            logger.info("📋 텍스트 (기본값) → 표로 시각화")
            return VisualizationCategory.TABLE
        else:
            # CSV, Excel, PDF, Image 등 모든 파일은 차트로 시각화
            logger.info(f"📊 {content_type.upper()} (기본값) → 차트로 시각화")
            return VisualizationCategory.CHART

@router.get("/models", response_model=SupportedVisualizationModelsResponse)
async def get_supported_models() -> SupportedVisualizationModelsResponse:
    """
    시각화에서 지원되는 AI 모델 목록을 반환합니다.

    Returns:
        SupportedVisualizationModelsResponse: 지원되는 모델 목록과 기본 모델 정보
    """
    from app.core.config import settings
    return SupportedVisualizationModelsResponse(
        supported_models=SUPPORTED_VISUALIZATION_MODELS,
        default_model=settings.default_llm_model,
        total_count=len(SUPPORTED_VISUALIZATION_MODELS)
    )

@router.post("/generate", response_model=VisualizationResponse)
async def generate_visualization(
    model: str = Form(default=None),
    language: str = Form(default="ko"),
    text: str = Form(None),
    file: UploadFile = File(None)
):
    """
    텍스트 또는 파일을 사용하여 시각화를 생성합니다.

    Args:
        text: 시각화할 텍스트 내용 (선택적) - 항상 표 형식으로 시각화
        model: 사용할 LLM 모델
        file: 업로드할 파일 (선택적) - 표 이미지는 차트로, 차트 이미지는 표로 변환

    Returns:
        VisualizationResponse: 생성된 시각화 결과
    """
    start_time = time.time()

    try:
        # 모델이 지정되지 않은 경우 기본 모델 사용
        if not model:
            model = settings.default_llm_model

        # text와 file 중 하나는 반드시 제공되어야 함
        if not text and not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="text 또는 file 중 하나는 반드시 제공되어야 합니다."
            )

        # 입력 방식에 따른 처리 분기
        content_type = "text"  # 기본값
        if file:
            # 파일 업로드된 경우 - 파일 타입별 처리
            file_extension = file.filename.split('.')[-1].lower() if file.filename else ''
            file_type = get_file_type_category(file_extension)
            content_type = file_type  # 파일 타입을 content_type으로 설정

            logger.info(f"📁 파일 업로드 처리: {file.filename}, 확장자: {file_extension}, 타입: {file_type}")

            # 통합 텍스트 추출 함수 사용
            try:
                if file_type == 'unknown':
                    supported_extensions = ['csv', 'xlsx', 'xls', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp', 'txt']
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"지원되지 않는 파일 형식: {file_extension}. 지원되는 형식: {', '.join(supported_extensions)}"
                    )

                # 파일 내용 읽기
                file_content = await file.read()

                # 통합 텍스트 추출 함수 사용
                text = await extract_text_from_file(file_content, file.filename)

            except Exception as extract_error:
                logger.error(f"파일 텍스트 추출 실패: {str(extract_error)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"파일 처리 중 오류가 발생했습니다: {str(extract_error)}"
                )
        else:
            # 텍스트 입력된 경우 - 일반 텍스트로 처리
            logger.info("📝 텍스트 입력 처리: 일반 텍스트로 시각화 생성")
            content_type = "text"
            # text는 이미 제공된 상태이므로 추가 처리 불필요

        # 콘텐츠 내용을 분석하여 시각화 카테고리 자동 결정
        category_enum = await determine_visualization_category_from_content(text, content_type)
        logger.info(f"🔄 {content_type} 콘텐츠 분석 완료: {category_enum.value} 형식으로 시각화")

        # 내부 요청 객체 생성
        internal_request = VisualizationRequest(
            content=text,
            category=category_enum,
            model=model
        )

        # 시각화 생성기 초기화
        generator = VisualizationGenerator()

        # 콘텐츠 타입에 따른 시각화 생성 메서드 선택
        if file:
            # 파일 업로드된 경우 - 콘텐츠 타입별 처리
            logger.info(f"📁 파일 기반 시각화 생성: {content_type}")
            result = await generator.generate_visualization(internal_request, content_type)
        else:
            # 텍스트 입력된 경우 - 표/CSV 형태로 직접 구조화
            logger.info("📝 텍스트 기반 시각화 생성 (표 형태 직접 구조화)")
            result = await generator.generate_visualization_from_text(internal_request)

        # 시각화 생성 실패인 경우 500 에러 처리
        if result.get("status") == "error":
            logger.error(f"시각화 생성 실패")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ERROR_MESSAGE
            )

        # NCP URL 목록이 비어있거나 생성되지 않은 경우 500 에러 처리
        viz_ncp_urls = result.get("ncp_urls", [])
        if not viz_ncp_urls or len(viz_ncp_urls) == 0:
            logger.error(f"시각화 이미지 생성 실패: ncp_urls={viz_ncp_urls}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ERROR_MESSAGE
            )

        logger.info(f"✅ 시각화 이미지 생성 완료: {len(viz_ncp_urls)}개")

        # 시각화 이미지 분석 및 TTS 생성
        analysis_texts = []
        tts_ncp_urls = []

        try:
            logger.info(f"🔍 시각화 분석 및 TTS 생성 시작 (언어: {language})")

            # 시각화 분석 및 TTS 생성
            analysis_result = await generator.analyze_visualizations_with_tts(
                ncp_url=viz_ncp_urls,
                model=model,
                language=language
            )

            if analysis_result.get("success"):
                analyses = analysis_result.get("analyses", [])
                analysis_texts = [a.get("analysis_text", "") for a in analyses]
                tts_ncp_urls = [a.get("ncp_url", "") for a in analyses]
                logger.info(f"✅ 시각화 분석 및 TTS 생성 완료: {len(analysis_texts)}개")
            else:
                logger.warning(f"⚠️ 시각화 분석 실패: {analysis_result.get('error', 'Unknown error')}")

        except Exception as analysis_error:
            logger.error(f"❌ 시각화 분석 중 오류 발생: {str(analysis_error)}")
            # 분석 실패해도 시각화 이미지는 반환

        # 실행 시간 계산
        execution_time = f"{time.time() - start_time:.2f}s"

        # Genre 자동 분류
        from app.models.language.content_category import Genre
        genre_enum = None

        # 자동 장르 분류 시도
        try:
            from app.services.language.content_category.analyzer import ContentCategoryAnalyzer
            from app.models.language.content_category import ContentCategoryRequest

            # 텍스트가 있는 경우에만 장르 분석 수행
            if text and text.strip():
                # 콘텐츠 카테고리 분석 요청 생성
                analyzer = ContentCategoryAnalyzer()
                category_request = ContentCategoryRequest(
                    llmText=[{"pageKey": 0, "texts": [{"text": text}]}],
                    model=model,
                    language=language
                )

                # 장르 분석
                category_result = await analyzer.analyze_content(category_request)
                genre_enum = category_result.genre

                if genre_enum:
                    logger.info(f"✅ 장르 자동 분류: {genre_enum.value}")
                else:
                    # 장르가 없으면 기본값 설정
                    genre_enum = Genre.PRACTICAL
                    logger.info("⚠️ 장르 분류 결과 없음, 기본값 'practical' 사용")
            else:
                # 텍스트가 없으면 기본값 설정
                genre_enum = Genre.PRACTICAL
                logger.info("⚠️ 텍스트 없음, 기본 장르 'practical' 사용")

        except Exception as e:
            # 장르 감지 실패 시 기본값으로 practical 설정
            genre_enum = Genre.PRACTICAL
            logger.warning(f"⚠️ 장르 자동 분류 실패, 기본값 'practical' 사용: {str(e)}")

        # contents 배열 구성 (순서 보장)
        contents = []
        max_length = max(len(viz_ncp_urls), len(analysis_texts), len(tts_ncp_urls))

        for i in range(max_length):
            content_item = VisualizationContent(
                viz_ncp_url=viz_ncp_urls[i] if i < len(viz_ncp_urls) else "",
                analysis_text=analysis_texts[i] if i < len(analysis_texts) else "",
                tts_ncp_url=tts_ncp_urls[i] if i < len(tts_ncp_urls) else ""
            )
            contents.append(content_item)

        return VisualizationResponse(
            visualization_type=internal_request.visualization_type.value,
            genre=genre_enum.value if genre_enum else "practical",
            execution_time=execution_time,
            contents=contents
        )

    except HTTPException:
        # HTTPException은 그대로 재발생
        raise
    except Exception as e:
        logger.error(f"시각화 API 내부 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"시각화 처리 중 내부 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def visualization_health_check():
    """시각화 서비스 상태 확인"""
    from app.utils.language.generator import get_available_models

    available_models = get_available_models()

    # 시각화 출력 디렉토리 확인
    viz_output_dir = os.path.join(settings.output_dir, "visualization")
    os.makedirs(viz_output_dir, exist_ok=True)

    return {
        "status": "healthy",
        "service": "Visualization",
        "description": "문서 시각화 생성 서비스",
        "available_models": available_models,
        "supported_models": SUPPORTED_VISUALIZATION_MODELS,
        "visualization_types": [vt.value for vt in VisualizationType],
        "visualization_categories": [vc.value for vc in VisualizationCategory],
        "output_directory": viz_output_dir,
        "features": {
            "unified_generation": True,
            "table_generation": True,
            "chart_generation": True,
            "text_input": True,
            "file_upload": True,
            "csv_excel_support": True,
            "markdown_to_image": True,
            "html_to_image": True,
            "file_download": True,
            "visualization_analysis": True,
            "tts_generation": True
        }
    }