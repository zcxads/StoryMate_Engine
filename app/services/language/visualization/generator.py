import os
import time
import re
import io
import pandas as pd

from typing import Dict, Any, Optional, List
from app.models.language.visualization import (
    VisualizationRequest,
    VisualizationType,
    OutputFormat
)
from app.utils.language.generator import call_llm
from app.core.config import settings
from app.utils.logger.setup import setup_logger
from app.prompts.language.visualization import (
    get_table_prompt,
    get_chart_prompt
)
from app.services.language.language_detection.detector import detect_language_with_ai
from app.prompts.language.visualization.visualization_analysis import get_analysis_prompt
import base64
import json
import boto3
from datetime import datetime

logger = setup_logger("visualization_generator")

class VisualizationGenerator:
    """문서 시각화 생성기"""
    
    def __init__(self):
        self.output_dir = os.path.join(settings.output_dir, "visualization")
        os.makedirs(self.output_dir, exist_ok=True)

        # NCP S3 클라이언트 초기화
        self.s3_client = boto3.client(
            service_name=settings.naver_service_name,
            endpoint_url=settings.naver_endpoint_url,
            aws_access_key_id=settings.ncp_access_key,
            aws_secret_access_key=settings.ncp_secret_key
        )
    
    async def generate_visualization_from_text(self, request: VisualizationRequest) -> Dict[str, Any]:
        """
        일반 텍스트로부터 시각화를 생성합니다. (표/CSV 형태로 직접 구조화)

        Args:
            request: 시각화 요청 데이터

        Returns:
            Dict: 생성된 시각화 결과
        """
        try:
            logger.info(f"텍스트 시각화 생성 시작: {request.visualization_type.value}")
            logger.info("📝 일반 텍스트 처리 → 표 형태로 직접 구조화")

            # 텍스트를 표/CSV 형태로 직접 구조화 (JSON 단계 생략)
            structured_table = await self._structure_content_to_table(request.content, "text", request.visualization_type)
            request.content = structured_table

            return await self._generate_visualization_content(request)

        except Exception as e:
            logger.error(f"텍스트 시각화 생성 실패: {str(e)}")
            return {
                "status": "error",
                "error": f"텍스트 시각화 생성 중 오류가 발생했습니다: {str(e)}"
            }

    async def generate_visualization(self, request: VisualizationRequest, content_type: str = "file") -> Dict[str, Any]:
        """
        파일로부터 시각화를 생성합니다.

        Args:
            request: 시각화 요청 데이터
            content_type: 콘텐츠 타입 ("csv", "excel", "pdf", "image", "text")

        Returns:
            Dict: 생성된 시각화 결과
        """
        try:
            logger.info(f"파일 시각화 생성 시작: {request.visualization_type.value}, 타입: {content_type}")

            # 1단계: 표 형식 데이터 감지 시도
            is_table_format = self._detect_table_format(request.content)

            if content_type in ["csv", "excel"] or is_table_format:
                # CSV/Excel 또는 표 형식 PDF/이미지 - DataFrame으로 직접 처리
                logger.info(f"📊 표 형식 데이터 감지 - DataFrame으로 직접 처리 (타입: {content_type})")

                validation_result = self._validate_and_extract_data(request.content, request.visualization_type)
                if not validation_result["is_valid"]:
                    return {
                        "status": "error",
                        "error": validation_result["message"]
                    }

                # 중요: request.content는 원본 데이터를 유지
                # 다중 시각화 생성을 위해 원본 표 형식 데이터 필요

            else:
                # 표 형식이 아닌 PDF, Image, Text - 표/CSV 형태로 직접 구조화 (JSON 단계 생략)
                logger.info(f"📊 {content_type.upper()} 콘텐츠 → 표 형태로 직접 구조화")
                structured_table = await self._structure_content_to_table(request.content, content_type, request.visualization_type)
                request.content = structured_table

            return await self._generate_visualization_content(request)

        except Exception as e:
            logger.error(f"파일 시각화 생성 실패: {str(e)}")
            return {
                "status": "error",
                "error": f"파일 시각화 생성 중 오류가 발생했습니다: {str(e)}"
            }

    async def _generate_visualization_content(self, request: VisualizationRequest) -> Dict[str, Any]:
        """
        공통 시각화 콘텐츠 생성 로직

        Args:
            request: 시각화 요청 데이터

        Returns:
            Dict: 생성된 시각화 결과 (여러 시각화 포함 가능)
        """
        try:
            # 콘텐츠를 분석하여 여러 시각화 가능한 부분 추출
            visualizable_contents = await self._extract_visualizable_contents(request.content, request.visualization_type)

            if not visualizable_contents:
                logger.warning("시각화 가능한 콘텐츠를 찾을 수 없습니다")
                return {
                    "status": "error",
                    "error": "시각화 가능한 콘텐츠를 찾을 수 없습니다"
                }

            logger.info(f"시각화 가능한 콘텐츠 {len(visualizable_contents)}개 발견")

            # 각 콘텐츠에 대해 시각화 생성
            all_ncp_urls = []
            for idx, content_part in enumerate(visualizable_contents):
                logger.info(f"시각화 생성 중 ({idx + 1}/{len(visualizable_contents)})")

                # 프롬프트 생성
                prompt = await self._build_visualization_prompt_for_content(content_part, request.visualization_type)

                # LLM으로 시각화 콘텐츠 생성
                try:
                    content = await call_llm(
                        prompt=prompt,
                        model=request.model
                    )
                    # call_llm은 직접 문자열을 반환하므로 content.content를 사용
                    if hasattr(content, 'content'):
                        content = content.content
                    elif isinstance(content, str):
                        content = content
                    else:
                        content = str(content)
                except Exception as e:
                    logger.error(f"LLM 생성 실패 ({idx + 1}): {str(e)}")
                    continue

                # 후처리 및 포맷 변환
                result = await self._process_output(content, request)

                if result.get("ncp_url"):
                    all_ncp_urls.append(result["ncp_url"])

            if not all_ncp_urls:
                return {
                    "status": "error",
                    "error": "시각화 이미지 생성에 실패했습니다"
                }

            return {
                "model_used": request.model,
                "status": "success",
                "ncp_urls": all_ncp_urls
            }

        except Exception as e:
            error_msg = f"시각화 생성 중 오류: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    async def _extract_visualizable_contents(self, content: str, viz_type: VisualizationType) -> list:
        """
        콘텐츠에서 시각화 가능한 부분들을 모두 추출합니다.
        DataFrame으로 변환 가능한 경우 여러 관점의 시각화를 생성합니다.

        Args:
            content: 원본 콘텐츠
            viz_type: 시각화 타입

        Returns:
            list: 시각화 가능한 콘텐츠 목록
        """
        try:
            # 1. DataFrame으로 변환하여 다양한 시각화 생성 시도 (최우선)
            visualizations = await self._extract_multiple_visualizations(content, viz_type)
            if visualizations and len(visualizations) > 1:
                logger.info(f"✅ DataFrame 기반 다중 시각화: {len(visualizations)}개 추출")
                return visualizations

            # 2. 표 형식의 데이터를 찾기 (마크다운 테이블 등)
            tables = self._extract_tables_from_content(content)
            if tables:
                logger.info(f"📋 마크다운 테이블 발견: {len(tables)}개")
                return tables

            # 3. 분할할 수 없는 경우 전체 콘텐츠를 하나의 시각화로
            logger.info("ℹ️ 단일 콘텐츠로 시각화")
            return [content]

        except Exception as e:
            logger.error(f"❌ 시각화 가능한 콘텐츠 추출 실패: {str(e)}")
            return [content]

    async def _extract_multiple_visualizations(self, content: str, viz_type: VisualizationType) -> list:
        """
        데이터를 DataFrame으로 변환하여 여러 관점의 시각화를 추출합니다.
        모든 데이터 형식(CSV, Excel, PDF, 이미지, 텍스트)에 대응합니다.

        Returns:
            list: 시각화 가능한 콘텐츠 목록 (각 관점별)
        """
        try:
            # DataFrame 변환 시도
            df_result = self._extract_dataframe_from_text(content)
            if not df_result.get("success"):
                return []

            df = df_result["dataframe"]

            # 최소 2행, 2열 이상 필요
            if len(df) < 2 or len(df.columns) < 2:
                return []

            logger.info(f"DataFrame 파싱 성공: {df.shape[0]}행 x {df.shape[1]}열")
            logger.info(f"원본 DataFrame dtypes:\n{df.dtypes}")

            # 컬럼 타입 분석 및 자동 변환
            column_analysis = self._analyze_column_types(df)
            numeric_cols = column_analysis['numeric']
            categorical_cols = column_analysis['categorical']
            temporal_cols = column_analysis['temporal']

            # 수치형으로 감지된 컬럼을 numeric dtype으로 변환
            df = self._convert_numeric_columns(df, numeric_cols)

            logger.info(f"변환 후 DataFrame dtypes:\n{df.dtypes}")
            logger.info(f"수치형 컬럼: {numeric_cols}")
            logger.info(f"범주형 컬럼: {categorical_cols}")
            logger.info(f"시계열 컬럼: {temporal_cols}")

            # 시각화 가능한 조합이 있는지 확인
            if not numeric_cols:
                logger.info("수치형 컬럼이 없어 다중 시각화 불가")
                return []

            # 시각화 가능한 조합 생성
            visualizations = []

            # 1. 시계열 + 각 수치형 컬럼 (예: 년도별 판매량, 년도별 수익)
            if temporal_cols and numeric_cols:
                for time_col in temporal_cols[:1]:  # 첫 번째 시간 컬럼만 사용
                    for num_col in numeric_cols[:3]:  # 최대 3개 수치형 컬럼
                        subset = df[[time_col, num_col]].copy()

                        # 수치형 컬럼이 실제로 numeric dtype인지 확인 및 변환
                        if not pd.api.types.is_numeric_dtype(subset[num_col]):
                            subset[num_col] = pd.to_numeric(subset[num_col], errors='coerce')
                            logger.warning(f"⚠️ 시계열 집계 전 '{num_col}' 컬럼 numeric 변환")

                        # 시계열 데이터는 평균값으로 집계 (추이를 보기에 적합)
                        aggregated = subset.groupby(time_col)[num_col].mean().reset_index()

                        # 의미 있는 시각화 필터링: 최소 2개 이상의 시점 필요
                        if len(aggregated) < 2:
                            logger.info(f"⏭️ 시각화 제외 (단일 시점): {time_col} vs {num_col} - {len(aggregated)}개 시점")
                            continue

                        # 집계 결과 검증
                        logger.info(f"📊 시계열 집계 결과 ({time_col} vs {num_col}):")
                        logger.info(f"   {aggregated.to_string()}")

                        # CSV에 메타데이터 추가 (주석 형태로)
                        viz_content = f"# AGGREGATION: 평균 (mean) - {time_col}별 {num_col}의 평균값\n"
                        viz_content += aggregated.to_csv(index=False)
                        visualizations.append(viz_content)
                        logger.info(f"시계열 시각화 추가 (평균 집계): {time_col} vs {num_col}")

            # 2. 범주형 + 수치형 (예: 제품별 판매량, 지역별 수익)
            if categorical_cols and numeric_cols:
                for cat_col in categorical_cols[:2]:  # 최대 2개 범주형 컬럼
                    for num_col in numeric_cols[:2]:  # 최대 2개 수치형 컬럼
                        # 시계열과 중복되지 않도록
                        if cat_col not in temporal_cols:
                            subset = df[[cat_col, num_col]].copy()

                            # 수치형 컬럼이 실제로 numeric dtype인지 확인 및 변환
                            if not pd.api.types.is_numeric_dtype(subset[num_col]):
                                subset[num_col] = pd.to_numeric(subset[num_col], errors='coerce')
                                logger.warning(f"⚠️ 집계 전 '{num_col}' 컬럼 numeric 변환")

                            # 범주별 집계 (NaN 제외)
                            aggregated = subset.groupby(cat_col)[num_col].sum().reset_index()

                            # 의미 있는 시각화 필터링: 최소 2개 이상의 범주 필요
                            if len(aggregated) < 2:
                                logger.info(f"⏭️ 시각화 제외 (단일 범주): {cat_col} vs {num_col} - {len(aggregated)}개 범주")
                                continue

                            # 집계 결과 검증
                            logger.info(f"📊 집계 결과 ({cat_col} vs {num_col}):")
                            logger.info(f"   {aggregated.to_string()}")

                            # CSV에 메타데이터 추가 (주석 형태로)
                            viz_content = f"# AGGREGATION: 합계 (sum) - {cat_col}별 {num_col}의 합계\n"
                            viz_content += aggregated.to_csv(index=False)
                            visualizations.append(viz_content)
                            logger.info(f"범주형 시각화 추가 (합계 집계): {cat_col} vs {num_col}")

            # 시각화가 생성되지 않은 경우 빈 리스트 반환 (의미 없는 시각화 방지)
            if not visualizations:
                logger.info("⚠️ 의미 있는 시각화를 생성할 수 없습니다 (단일 범주/시점만 존재)")
                return []

            # 최대 10개로 제한
            # if len(visualizations) > 10:
            #     visualizations = visualizations[:10]
            #     logger.info(f"시각화 개수를 10개로 제한")

            return visualizations

        except Exception as e:
            logger.warning(f"다중 시각화 추출 실패: {str(e)}")
            return []

    def _extract_tables_from_content(self, content: str) -> list:
        """
        콘텐츠에서 표 형식의 데이터를 추출합니다.

        Args:
            content: 원본 콘텐츠

        Returns:
            list: 추출된 표 목록
        """
        tables = []
        lines = content.split('\n')
        current_table = []

        for line in lines:
            # 마크다운 테이블 라인 감지
            if '|' in line.strip() and line.strip().count('|') >= 2:
                current_table.append(line)
            else:
                # 테이블이 끝난 경우
                if current_table and len(current_table) >= 3:  # 최소 헤더 + 구분선 + 데이터 1행
                    tables.append('\n'.join(current_table))
                current_table = []

        # 마지막 테이블 처리
        if current_table and len(current_table) >= 3:
            tables.append('\n'.join(current_table))

        return tables

    async def _build_visualization_prompt_for_content(self, content: str, viz_type: VisualizationType) -> str:
        """
        특정 콘텐츠에 대한 시각화 프롬프트를 생성합니다.

        Args:
            content: 시각화할 콘텐츠
            viz_type: 시각화 타입

        Returns:
            str: 생성된 프롬프트
        """
        # AI 기반 언어 감지
        try:
            detection_result = await detect_language_with_ai(content)
            lang_code = detection_result.get("primary_language")
            confidence = detection_result.get("confidence", 0.0)
            logger.info(f"🌐 AI 언어 감지: {lang_code}, 신뢰도: {confidence:.2f}")
        except Exception as e:
            logger.warning(f"AI 언어 감지 실패, 기본값(en) 사용: {str(e)}")
            lang_code = 'en'

        # 언어별 프롬프트 선택
        if viz_type == VisualizationType.TABLE:
            base_prompt = get_table_prompt(lang_code)
        elif viz_type == VisualizationType.CHART:
            base_prompt = get_chart_prompt(lang_code)

        # 출력 형식 지정 (기본값: IMAGE_PNG)
        output_format = OutputFormat.IMAGE_PNG
        format_instruction = self._get_format_instruction(output_format)
        base_prompt += f"\n\n{format_instruction}"

        # 집계 메타데이터 확인
        aggregation_instruction = ""
        if content.startswith("# AGGREGATION:"):
            lines = content.split('\n')
            agg_line = lines[0]
            if "평균" in agg_line or "mean" in agg_line.lower():
                aggregation_instruction = "\n\n중요: 이 데이터는 평균값으로 집계되었습니다. 차트 제목에 반드시 '평균'을 포함하세요. (예: '연도별 평균 판매량 추이')"
            elif "합계" in agg_line or "sum" in agg_line.lower():
                aggregation_instruction = "\n\n중요: 이 데이터는 합계로 집계되었습니다. 차트 제목에 반드시 '합계' 또는 '총'을 포함하세요. (예: '제품별 총 판매량')"

        # 콘텐츠 추가
        full_prompt = f"{base_prompt}{aggregation_instruction}\n\n분석할 문서 내용:\n{content}"

        return full_prompt

    async def _build_visualization_prompt(self, request: VisualizationRequest) -> str:
        """시각화 프롬프트를 구성합니다. (하위 호환성을 위해 유지)"""
        return await self._build_visualization_prompt_for_content(request.content, request.visualization_type)
    
    def _get_format_instruction(self, output_format: OutputFormat) -> str:
        """출력 형식 지시사항"""
        instructions = {
            OutputFormat.IMAGE_PNG: "결과를 마크다운으로 생성한 후 PNG 이미지로 변환할 예정입니다."
        }
        return instructions.get(output_format, instructions[OutputFormat.IMAGE_PNG])
    
    async def _process_output(self, content: str, request: VisualizationRequest) -> Dict[str, Any]:
        """출력 콘텐츠를 후처리합니다."""
        
        result = {
            "content": content,
            "image_base64": None,
            "image_path": None
        }
        
        # 이미지 변환이 필요한 경우 (기본적으로 항상 이미지로 변환)
        output_format = OutputFormat.IMAGE_PNG
        if output_format in [OutputFormat.IMAGE_PNG]:
            try:
                image_result = await self._convert_to_image(content, request)
                result.update(image_result)
            except Exception as e:
                logger.warning(f"이미지 변환 실패 {str(e)}")
        
        return result
    
    async def _convert_to_image(self, content: str, request: VisualizationRequest) -> Dict[str, Any]:
        """콘텐츠를 이미지로 변환하고 NCP에 업로드"""

        # visualization 폴더가 없으면 생성
        os.makedirs(self.output_dir, exist_ok=True)

        # 임시 파일 경로 생성
        timestamp = int(time.time())
        filename = f"{request.visualization_type.value}_{timestamp}.png"
        image_path = os.path.join(self.output_dir, filename)

        try:
            # 시각화 타입별 렌더링 실행 (파일로)
            if request.visualization_type in [VisualizationType.TABLE, VisualizationType.CHART]:
                # 스타일 옵션 준비
                style_options = {
                    "figsize": (12, 8),
                    "dpi": 300,
                    "font_size": 12,
                    "renderer": "matplotlib"
                }

                # 요청 옵션 병합
                if request.image_options:
                    style_options.update(request.image_options)

                # 시각화 타입별 렌더링 실행
                if request.visualization_type == VisualizationType.TABLE:
                    from app.services.language.visualization.table_renderer import TableRenderer
                    renderer = TableRenderer()

                    # 표 데이터 처리 (제목 포함)
                    parsed_result = renderer.parse_csv_from_llm_response(content)
                    csv_data = parsed_result["csv_data"]
                    table_title = parsed_result.get("title")

                    # 제목이 있으면 style_options에 추가
                    if table_title:
                        style_options["title"] = table_title
                        logger.info(f"표 제목 추가: '{table_title}'")

                    # CSV 유효성 검증
                    renderer.validate_csv_data(csv_data)

                    # 표 이미지 파일 생성
                    await renderer.render_table_auto(csv_data, image_path, style_options)
                    logger.info(f"표 이미지 생성 완료: {image_path}")

                elif request.visualization_type == VisualizationType.CHART:
                    from app.services.language.visualization.chart_renderer import ChartRenderer
                    renderer = ChartRenderer()

                    # 차트 데이터 파싱 및 검증
                    renderer.validate_chart_data(content)

                    # 차트 이미지 파일 생성
                    await renderer.render_chart_auto(content, image_path, style_options)
                    logger.info(f"차트 이미지 생성 완료: {image_path}")

            # 파일이 실제로 생성되었는지 확인
            if not os.path.exists(image_path):
                raise ValueError(f"이미지 파일이 생성되지 않았습니다: {image_path}")

            # 로컬 파일을 읽어서 NCP에 업로드
            ncp_url = await self.upload_file_to_ncp(image_path, request.visualization_type.value)
            logger.info(f"시각화 이미지 NCP 업로드 완료: {ncp_url}")

            return {
                "content": f"![{request.visualization_type.value}]({ncp_url})",
                "image_base64": None,  # base64 대신 URL 사용
                "image_path": image_path,
                "ncp_url": ncp_url
            }

        except Exception as e:
            error_types = {"table": "표", "chart": "차트"}
            error_type = error_types.get(request.visualization_type.value, "시각화")
            logger.error(f"{error_type} 렌더링 실패: {str(e)}")
            raise e

        finally:
            # NCP 업로드 후 로컬 파일 자동 삭제
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    logger.info(f"로컬 이미지 파일 삭제 완료: {image_path}")
                except Exception as delete_error:
                    logger.warning(f"로컬 파일 삭제 실패: {delete_error}")
    
    def _validate_and_extract_data(self, content: str, viz_type: VisualizationType) -> Dict[str, Any]:
        """콘텐츠 검증 및 시각화 가능한 데이터 추출"""
        
        content_lower = content.lower()
        
        # 표/차트에 적합한 데이터 패턴 검사
        if viz_type in [VisualizationType.TABLE, VisualizationType.CHART]:
            # 먼저 마크다운 테이블 확인
            pipe_lines = [line for line in content.split('\n') if '|' in line.strip()]
            
            if len(pipe_lines) >= 3:  # 마크다운 테이블로 간주
                logger.info(f"마크다운 테이블 감지: {len(pipe_lines)}개 라인")
                table_data = '\n'.join(pipe_lines)

                # DataFrame 변환 시도
                df_result = self._extract_dataframe_from_text(table_data)
                if df_result["success"]:
                    df = df_result["dataframe"]
                    logger.info(f"✅ DataFrame 구조화 성공: {df.shape[0]}행 x {df.shape[1]}열")
                    logger.info(f"📊 컬럼 목록: {list(df.columns)}")
                    logger.info(f"🔍 DataFrame 상세 내용:\n{df.to_string()}")

                    # 변수 타입 분석 로그
                    column_analysis = self._analyze_column_types(df)
                    logger.info(f"🏷️ 변수 타입 분석:")
                    logger.info(f"  - 수치형 변수 (Y축용): {column_analysis['numeric']}")
                    logger.info(f"  - 범주형 변수 (X축/그룹용): {column_analysis['categorical']}")
                    logger.info(f"  - 시계열 변수: {column_analysis['temporal']}")
                    logger.info(f"  - 혼합형 변수: {column_analysis['mixed']}")

                    # LLM을 위한 포맷팅된 데이터 생성
                    formatted_data = self._format_dataframe_for_llm(df, viz_type)
                    return {
                        "is_valid": True,
                        "message": "DataFrame 구조화 성공",
                        "extracted_data": formatted_data
                    }
                else:
                    logger.warning(f"DataFrame 변환 실패, 원본 데이터 사용: {df_result['error']}")

                return {
                    "is_valid": True,
                    "message": "검증 통과",
                    "extracted_data": table_data
                }
            
            # 원본 데이터로 DataFrame 변환 먼저 시도
            df_result = self._extract_dataframe_from_text(content)

            # DataFrame 변환이 실패한 경우에만 구조화된 데이터 추출 시도
            if not df_result["success"]:
                logger.info("원본 데이터 DataFrame 변환 실패, 구조화된 데이터 추출 시도")
                extracted_data = self._extract_structured_data(content)

                if not extracted_data:
                    return {
                        "is_valid": False,
                        "message": "해당 컨텐츠는 제공할 수 없습니다."
                    }

                # 추출된 데이터로 DataFrame 변환 재시도
                df_result = self._extract_dataframe_from_text(extracted_data)
            if df_result["success"]:
                df = df_result["dataframe"]
                logger.info(f"✅ DataFrame 구조화 성공 (구조화된 데이터): {df.shape[0]}행 x {df.shape[1]}열")
                logger.info(f"📊 컬럼 목록: {list(df.columns)}")
                logger.info(f"📋 컬럼별 데이터 타입:")

                logger.info(f"🔍 DataFrame 상세 내용:\n{df.to_string()}")

                # 변수 타입 분석 로그
                column_analysis = self._analyze_column_types(df)
                logger.info(f"🏷️ 변수 타입 분석:")
                logger.info(f"  - 수치형 변수 (Y축용): {column_analysis['numeric']}")
                logger.info(f"  - 범주형 변수 (X축/그룹용): {column_analysis['categorical']}")
                logger.info(f"  - 시계열 변수: {column_analysis['temporal']}")
                logger.info(f"  - 혼합형 변수: {column_analysis['mixed']}")

                # LLM을 위한 포맷팅된 데이터 생성
                formatted_data = self._format_dataframe_for_llm(df, viz_type)
                return {
                    "is_valid": True,
                    "message": "DataFrame 구조화 성공",
                    "extracted_data": formatted_data
                }
            else:
                logger.info(f"DataFrame 변환 실패, 원본 추출 데이터 사용: {df_result['error']}")

            return {
                "is_valid": True,
                "message": "검증 통과",
                "extracted_data": extracted_data
            }
        
        return {"is_valid": True, "message": "검증 통과"}
    
    def _extract_structured_data(self, content: str) -> str:
        """혼합 문서에서 구조화된 데이터만 추출"""
        
        lines = content.split('\n')
        extracted_lines = []
        
        # 구조화된 데이터 패턴들
        data_patterns = [
            r'^\s*-\s*\d+년.*:\s*\d+',                    # - 2020년: 3만 대
            r'^\s*\d+[년월일].*:\s*\d+',                  # 2020년: 3만 대  
            r'^\s*[가-힣A-Za-z0-9\s]+:\s*\d+[가-힣\s]*', # 항목: 수치
            r'^\s*\|\s*[^|]+\s*\|\s*[^|]+\s*\|',          # | 항목 | 값 |
            r'^\s*\|\s*[^|]*\d+[^|]*\s*\|',               # | 숫자가 포함된 셀 |
            r'^\s*\|\s*[-\s]*\|\s*[-\s]*\|',              # | ----- | ----- | (구분선)
            r'^\s*[가-힣A-Za-z0-9\s]+\s+\d+[가-힣\s]*',  # 항목 수치
        ]
        
        # 마크다운 테이블 헤더 패턴 (테이블의 맥락 제공)
        table_header_patterns = [
            r'^\s*\|\s*구분\s*\|',     # | 구분 | ... |
            r'^\s*\|\s*항목\s*\|',     # | 항목 | ... |
            r'^\s*\|\s*[A-Za-z]+\s*\|', # | Feb | Mar | ... |
        ]
        
        # 제목이나 헤더 패턴 (맥락 제공용)
        title_patterns = [
            r'^[^:]*\d+~\d+년.*',  # 2020~2024년 국내 전기차...
            r'^.*추세$',           # ...추세
            r'^.*현황$',           # ...현황
            r'^.*데이터$',         # ...데이터
        ]
        
        # 제목 추출
        title_found = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 제목 패턴 확인
            if any(re.search(pattern, line) for pattern in title_patterns) and not title_found:
                extracted_lines.append(line)
                title_found = True
                continue
            
            # 마크다운 테이블 헤더 확인
            if any(re.search(pattern, line) for pattern in table_header_patterns):
                extracted_lines.append(line)
                continue
            
            # 데이터 패턴 확인
            if any(re.search(pattern, line) for pattern in data_patterns):
                extracted_lines.append(line)
                continue
        
        # 추출된 데이터가 있는지 확인
        if not extracted_lines:
            return ""
        
        extracted_content = '\n'.join(extracted_lines)
        
        # 마크다운 테이블인 경우 특별 처리
        table_lines = [line for line in lines if line.strip().startswith('|') and line.strip().endswith('|')]
        
        logger.info(f"전체 라인 수: {len(lines)}")
        logger.info(f"테이블 라인 감지: {len(table_lines)}개")
        
        if len(table_lines) >= 2:  # 헤더 + 최소 1개 데이터 행 (구분선 없어도 허용)
            logger.info(f"마크다운 테이블 감지: {len(table_lines)}개 라인")
            return '\n'.join(table_lines)
        
        # 최소 데이터 요구사항 확인
        data_lines = [line for line in extracted_lines if any(re.search(pattern, line) for pattern in data_patterns)]
        
        if len(data_lines) < 2:  # 최소 2개 데이터 포인트 필요
            return ""
        
        logger.info(f"구조화된 데이터 추출 완료: {len(data_lines)}개 데이터 포인트")
        return extracted_content

    def _clean_extracted_text(self, text: str) -> str:
        """
        추출된 텍스트에서 불필요한 메타데이터 제거
        - [페이지 N] 태그 제거
        - 제목 라인 제거 (표 형식 앞의 설명)
        - 마크다운 코드 블록 제거
        """
        lines = text.strip().split('\n')
        cleaned_lines = []

        for line in lines:
            line_stripped = line.strip()

            # 빈 라인 제거
            if not line_stripped:
                continue

            # [페이지 N] 태그 제거
            if re.match(r'^\[페이지\s+\d+\]$', line_stripped):
                logger.info(f"🧹 페이지 태그 제거: {line_stripped}")
                continue

            # 마크다운 코드 블록 구분자 제거
            if line_stripped in ['```', '```csv', '```tsv', '```table']:
                logger.info(f"🧹 코드 블록 태그 제거: {line_stripped}")
                continue

            # 제목으로 보이는 라인 제거 (구분자가 없고 짧은 라인)
            if (
                len(line_stripped) < 30 and  # 짧은 라인
                ',' not in line_stripped and  # 콤마 없음
                '\t' not in line_stripped and  # 탭 없음
                '  ' not in line_stripped and  # 연속 공백 없음
                '|' not in line_stripped and  # 파이프 없음
                not any(char.isdigit() for char in line_stripped)  # 숫자 없음 (데이터 아님)
            ):
                # 제목일 가능성이 높음
                logger.info(f"🧹 제목 라인 제거: {line_stripped}")
                continue

            cleaned_lines.append(line)

        cleaned_text = '\n'.join(cleaned_lines)
        logger.info(f"🧹 텍스트 정리 완료: {len(lines)}줄 → {len(cleaned_lines)}줄")

        return cleaned_text

    def _extract_dataframe_from_text(self, text: str) -> Dict[str, Any]:
        """텍스트에서 DataFrame 추출 시도"""
        try:
            # BOM 제거
            text = text.replace('\ufeff', '').strip()

            if not text:
                return {"success": False, "error": "빈 텍스트입니다"}

            # 페이지 태그 및 제목 라인 제거 (LLM 추출 결과 정리)
            text = self._clean_extracted_text(text)

            # 1. CSV 형식 감지 및 처리 (콤마로 구분된 데이터 우선)
            csv_result = self._try_parse_csv(text)
            if csv_result["success"]:
                return csv_result

            # 2. 탭 구분 데이터 처리
            if '\t' in text and text.count('\t') > 5:
                try:
                    logger.info("🔍 탭 구분 데이터 시도")
                    df = pd.read_csv(io.StringIO(text), sep='\t', header=0)
                    if df.shape[1] > 1:  # 최소 2개 이상의 컬럼
                        logger.info(f"✅ 탭 구분 파싱 성공: {df.shape}")
                        return {"success": True, "dataframe": df, "format": "tsv"}
                except Exception as tsv_error:
                    logger.warning(f"⚠️ 탭 구분 파싱 실패: {str(tsv_error)}")

            # 3. 마크다운 테이블 처리
            if '|' in text and text.count('|') > 3:
                try:
                    logger.info("🔍 마크다운 테이블 시도")
                    df = self._parse_markdown_table(text)
                    if df.shape[1] > 1:  # 최소 2개 이상의 컬럼
                        logger.info(f"✅ 마크다운 파싱 성공: {df.shape}")
                        return {"success": True, "dataframe": df, "format": "markdown"}
                except Exception as md_error:
                    logger.warning(f"⚠️ 마크다운 파싱 실패: {str(md_error)}")

            # 4. 공백 구분 데이터 처리
            if self._is_whitespace_separated(text):
                try:
                    logger.info("🔍 공백 구분 데이터 파싱 시도")
                    df = self._parse_whitespace_separated(text)
                    if df.shape[1] > 1:  # 최소 2개 이상의 컬럼
                        logger.info(f"✅ 공백 구분 파싱 성공: {df.shape}")
                        return {"success": True, "dataframe": df, "format": "whitespace"}
                except Exception as ws_error:
                    logger.warning(f"⚠️ 공백 구분 파싱 실패: {str(ws_error)}")

            logger.warning("⚠️ 모든 파싱 방법 실패")
            return {"success": False, "error": "구조화 가능한 데이터 형식을 찾을 수 없습니다"}

        except Exception as e:
            logger.warning(f"❌ DataFrame 추출 실패: {str(e)}")
            return {"success": False, "error": str(e)}

    def _try_parse_csv(self, text: str) -> Dict[str, Any]:
        """CSV 형식 파싱 시도"""
        try:
            lines = text.strip().split('\n')

            if len(lines) < 2:
                return {"success": False, "error": "라인 수 부족"}

            # 첫 번째 라인에서 콤마 개수 확인
            first_line = lines[0].strip()
            comma_count = first_line.count(',')

            # 콤마가 없으면 CSV가 아님
            if comma_count == 0:
                return {"success": False, "error": "콤마가 없음"}

            # pandas로 파싱 시도
            df = pd.read_csv(io.StringIO(text), header=0, encoding='utf-8-sig')

            # 최소 2개 이상의 컬럼이 있어야 함
            if df.shape[1] < 2:
                logger.warning(f"⚠️ 컬럼 수 부족: {df.shape[1]}개")
                return {"success": False, "error": f"컬럼 수 부족: {df.shape[1]}개"}

            # 첫 번째 컬럼명 검증 (이상한 컬럼명 체크)
            first_col = str(df.columns[0])
            if len(first_col) > 100 or '|' in first_col:
                logger.warning(f"⚠️ 비정상적인 컬럼명: {first_col[:50]}...")
                return {"success": False, "error": "비정상적인 컬럼명"}

            return {"success": True, "dataframe": df, "format": "csv"}

        except Exception as e:
            logger.warning(f"⚠️ CSV 파싱 실패: {str(e)}")
            return {"success": False, "error": str(e)}

    def _is_whitespace_separated(self, text: str) -> bool:
        """공백 구분 데이터인지 확인"""
        lines = text.strip().split('\n')
        logger.info(f"🔍 공백 구분 형식 확인 - 전체 라인 수: {len(lines)}")

        if len(lines) < 2:
            logger.info("❌ 공백 구분 확인 실패: 라인 수 부족")
            return False

        # 연속된 공백으로 구분된 열이 있는지 확인
        for i, line in enumerate(lines[:3]):
            whitespace_cols = re.split(r'\s{2,}', line.strip())
            logger.info(f"🔍 라인 {i+1}: '{line}' → 공백 분할 결과: {whitespace_cols} (컬럼 수: {len(whitespace_cols)})")
            if len(whitespace_cols) >= 2:
                logger.info("✅ 공백 구분 형식 확인됨")
                return True

        logger.info("❌ 공백 구분 형식 아님")
        return False

    def _parse_whitespace_separated(self, text: str) -> pd.DataFrame:
        """
        공백 구분 데이터를 DataFrame으로 파싱합니다.
        PyMuPDF 추출한 표 형식 데이터를 처리합니다.

        멀티라인 헤더(예: VQAv2 헤더 아래 val, test-dev 서브헤더) 지원
        표 구조만 추출 (캡션, 제목 등 자동 필터링)

        Args:
            text: 공백 구분 데이터 텍스트

        Returns:
            pd.DataFrame: 파싱된 DataFrame
        """
        lines = text.strip().split('\n')

        if len(lines) < 2:
            raise ValueError("최소 2줄 이상의 데이터가 필요합니다 (헤더 + 데이터)")

        # 빈 라인 제거
        lines = [line for line in lines if line.strip()]

        # 표 구조 영역 감지 및 추출
        table_lines = self._extract_table_structure(lines)

        if len(table_lines) < 2:
            raise ValueError("유효한 표 구조를 찾을 수 없습니다")

        logger.info(f"📋 표 구조 추출: {len(table_lines)}개 라인")

        # 첫 번째 라인을 헤더로 사용
        header_line = table_lines[0].strip()
        headers = re.split(r'\s{2,}', header_line)

        logger.info(f"📋 헤더: {headers} (컬럼 수: {len(headers)})")

        # 데이터 라인 파싱 (2번째 라인부터)
        # LLM이 정확히 추출한 데이터를 신뢰하여 모든 라인을 데이터로 처리
        data = []
        for i, line in enumerate(table_lines[1:], start=2):
            row = re.split(r'\s{2,}', line.strip())

            # 컬럼 수가 헤더와 일치하지 않으면 조정
            if len(row) < len(headers):
                # 부족한 경우 빈 값으로 채움
                row.extend([''] * (len(headers) - len(row)))
            elif len(row) > len(headers):
                # 초과하는 경우 잘라냄
                logger.warning(f"⚠️ 라인 {i}: 컬럼 수 초과 ({len(row)} > {len(headers)}), 잘라냄")
                logger.debug(f"   원본: {line.strip()}")
                logger.debug(f"   파싱: {row}")
                row = row[:len(headers)]

            data.append(row)

        # DataFrame 생성
        df = pd.DataFrame(data, columns=headers)

        logger.info(f"✅ 공백 구분 DataFrame 생성: {df.shape[0]}행 x {df.shape[1]}열")
        logger.info(f"📊 컬럼 목록: {list(df.columns)}")
        logger.info(f"📊 첫 3행:\n{df.head(3).to_string()}")

        return df

    def _extract_table_structure(self, lines: list) -> list:
        """
        라인들에서 표 구조 영역만 추출합니다.

        표의 특징:
        - 연속된 라인들이 일관된 컬럼 수 (2개 이상)를 가짐
        - 최소 3줄 이상 연속

        Args:
            lines: 전체 텍스트 라인 리스트

        Returns:
            list: 표 구조 라인들만 포함된 리스트
        """
        # 각 라인의 컬럼 수 계산
        line_column_counts = []
        for line in lines:
            cols = re.split(r'\s{2,}', line.strip())
            line_column_counts.append(len(cols))

        logger.info(f"🔍 각 라인별 컬럼 수: {line_column_counts}")

        # 가장 긴 연속된 표 구조 찾기
        best_start = 0
        best_end = 0
        best_col_count = 0

        current_start = 0
        current_col_count = line_column_counts[0] if line_column_counts else 0

        for i in range(len(line_column_counts)):
            col_count = line_column_counts[i]

            # 컬럼 수가 2개 미만이면 표가 아님
            if col_count < 2:
                # 이전 구간 평가
                if i - current_start >= 3 and current_col_count >= 2:
                    if i - current_start > best_end - best_start:
                        best_start = current_start
                        best_end = i
                        best_col_count = current_col_count

                # 새로운 구간 시작
                current_start = i + 1
                current_col_count = 0
                continue

            # 컬럼 수가 크게 변하면 (±2 이상) 새로운 구간 시작
            if current_col_count > 0 and abs(col_count - current_col_count) > 2:
                # 이전 구간 평가
                if i - current_start >= 3:
                    if i - current_start > best_end - best_start:
                        best_start = current_start
                        best_end = i
                        best_col_count = current_col_count

                # 새로운 구간 시작
                current_start = i
                current_col_count = col_count
            else:
                # 컬럼 수가 비슷하면 같은 구간
                if current_col_count == 0:
                    current_col_count = col_count

        # 마지막 구간 평가
        if len(line_column_counts) - current_start >= 3 and current_col_count >= 2:
            if len(line_column_counts) - current_start > best_end - best_start:
                best_start = current_start
                best_end = len(line_column_counts)
                best_col_count = current_col_count

        logger.info(f"📊 표 구조 감지: 라인 {best_start+1}~{best_end} (컬럼 수: {best_col_count})")

        # 표 구조 추출
        table_lines = lines[best_start:best_end]

        # 추출된 라인들 로깅 (전체 출력)
        logger.info(f"📝 추출된 표 구조 전체 ({len(table_lines)}개 라인):")
        for i, line in enumerate(table_lines, start=1):
            logger.info(f"   라인 {i}: '{line}'")

        return table_lines

    def _parse_markdown_table(self, text: str) -> pd.DataFrame:
        """마크다운 테이블 파싱"""
        lines = [line.strip() for line in text.strip().split('\n') if line.strip() and '|' in line]

        if len(lines) < 2:
            raise ValueError("유효한 마크다운 테이블이 아닙니다")

        # 헤더 추출
        headers = [col.strip() for col in lines[0].split('|')[1:-1]]  # 양끝 | 제거

        # 구분선 건너뛰기 (|----|----| 형태)
        data_lines = [line for line in lines[1:] if not re.match(r'^\s*\|[\s\-\|]*\|\s*$', line)]

        data = []
        for line in data_lines:
            row = [col.strip() for col in line.split('|')[1:-1]]  # 양끝 | 제거
            if len(row) == len(headers):
                data.append(row)

        return pd.DataFrame(data, columns=headers)

    def _detect_table_format(self, content: str) -> bool:
        """
        콘텐츠가 표 형식(CSV, TSV, 공백 구분 등)인지 감지합니다.

        Args:
            content: 분석할 텍스트 콘텐츠

        Returns:
            bool: 표 형식이면 True, 아니면 False
        """
        try:
            if not content or not content.strip():
                return False

            lines = content.strip().split('\n')

            # 최소 2줄 이상 필요 (헤더 + 데이터)
            if len(lines) < 2:
                return False

            structured_lines = 0
            for line in lines[:10]:  # 처음 10줄만 검사
                line = line.strip()
                if not line:
                    continue

                # 구분자 패턴 감지
                has_delimiter = (
                    ',' in line or      # CSV
                    '\t' in line or     # TSV
                    '|' in line or      # Markdown 테이블
                    '  ' in line        # 공백 구분 (2개 이상)
                )

                if has_delimiter:
                    structured_lines += 1

            # 50% 이상의 라인이 구조화되어 있으면 표 형식으로 판단
            structure_ratio = structured_lines / min(len([l for l in lines[:10] if l.strip()]), 10)
            is_table = structure_ratio >= 0.5

            if is_table:
                logger.info(f"✅ 표 형식 감지: {structured_lines}개 구조화 라인 / 구조 비율: {structure_ratio:.2f}")
            else:
                logger.info(f"❌ 표 형식 아님: {structured_lines}개 구조화 라인 / 구조 비율: {structure_ratio:.2f}")

            return is_table

        except Exception as e:
            logger.warning(f"⚠️ 표 형식 감지 실패: {str(e)}")
            return False

    def _convert_numeric_columns(self, df: pd.DataFrame, numeric_cols: list) -> pd.DataFrame:
        """수치형으로 감지된 컬럼을 numeric dtype으로 변환"""
        df_converted = df.copy()

        for col in numeric_cols:
            try:
                # 문자열을 숫자로 변환 (errors='coerce'로 변환 불가능한 값은 NaN)
                df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce')
                logger.info(f"✅ 컬럼 '{col}' → numeric 변환 완료 (dtype: {df_converted[col].dtype})")
            except Exception as e:
                logger.warning(f"⚠️ 컬럼 '{col}' numeric 변환 실패: {str(e)}")

        return df_converted

    def _analyze_column_types(self, df: pd.DataFrame) -> Dict[str, list]:
        """DataFrame 컬럼의 변수 타입을 분석"""
        analysis = {
            'numeric': [],      # 수치형 (Y축용)
            'categorical': [],  # 범주형 (X축/그룹용)
            'temporal': [],     # 시계열
            'mixed': []         # 혼합형
        }

        for col in df.columns:
            col_data = df[col].dropna()

            if len(col_data) == 0:
                continue

            # 시계열 확인을 먼저 수행 (연도 데이터가 숫자로 처리되는 것을 방지)
            if self._is_temporal_column(col_data):
                analysis['temporal'].append(col)
                continue

            # 고유값 비율 계산
            unique_count = len(col_data.unique())
            unique_ratio = unique_count / len(col_data)

            # 수치형 확인 (단, '-'는 결측값으로 처리)
            try:
                # '-'를 NaN으로 치환 후 numeric 변환 시도
                col_data_cleaned = col_data.replace(['-', '–', '—'], pd.NA)  # 다양한 대시 문자 처리
                numeric_converted = pd.to_numeric(col_data_cleaned, errors='coerce')

                # 원본 데이터에서 '-'가 아닌 값들 중 숫자로 변환 가능한 비율 계산
                non_dash_data = col_data[~col_data.isin(['-', '–', '—'])]
                if len(non_dash_data) > 0:
                    numeric_ratio = numeric_converted.notna().sum() / len(col_data)

                    # '-'를 제외한 값들의 숫자 변환 비율
                    if len(non_dash_data) > 0:
                        non_dash_numeric = pd.to_numeric(non_dash_data, errors='coerce')
                        non_dash_numeric_ratio = non_dash_numeric.notna().sum() / len(non_dash_data)
                    else:
                        non_dash_numeric_ratio = 0

                    # '-'를 제외한 값의 50% 이상이 숫자면 수치형으로 간주
                    if non_dash_numeric_ratio > 0.5:
                        # 숫자이지만 고유값이 적으면 범주형 (예: 분기=1,2)
                        if unique_count <= 10 and unique_ratio < 0.3:
                            analysis['categorical'].append(col)
                        else:
                            analysis['numeric'].append(col)
                        continue
            except:
                pass

            # 범주형 확인 (고유값이 적고 반복되는 패턴)
            if unique_ratio < 0.5 or unique_count <= 20:
                analysis['categorical'].append(col)
            else:
                analysis['mixed'].append(col)

        return analysis

    def _is_temporal_column(self, col_data) -> bool:
        """컬럼이 시계열 데이터인지 확인"""
        sample_values = col_data.astype(str).head(min(10, len(col_data)))

        # 연도 패턴 (2020, 2021년, etc.)
        year_patterns = [
            r'^\d{4}년?$',      # 2020, 2020년
            r'^\d{4}-\d{2}$',   # 2020-01
            r'^\d{4}/\d{2}$'    # 2020/01
        ]

        # 월 패턴 (1월, Jan, January, etc.)
        month_patterns = [
            r'^\d{1,2}월$',                    # 1월, 12월
            r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)$',  # 영어 월 축약
        ]

        # 날짜 패턴
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',    # 2020-01-01
            r'^\d{2}/\d{2}/\d{4}$',    # 01/01/2020
            r'^\d{1,2}/\d{1,2}$'       # 1/1, 12/31
        ]

        all_patterns = year_patterns + month_patterns + date_patterns

        # 연도 범위 확인 (1900-2100 사이의 4자리 숫자)
        year_range_matches = 0
        for value in sample_values:
            try:
                num_val = int(str(value).strip())
                if 1900 <= num_val <= 2100:
                    year_range_matches += 1
            except:
                pass

        # 패턴 매칭 확인
        pattern_matches = 0
        for value in sample_values:
            if any(re.match(pattern, str(value).strip()) for pattern in all_patterns):
                pattern_matches += 1

        # 패턴이 70% 이상 매치되거나, 연도 범위가 80% 이상 매치되면 시계열로 판단
        pattern_ratio = pattern_matches / len(sample_values) if len(sample_values) > 0 else 0
        year_ratio = year_range_matches / len(sample_values) if len(sample_values) > 0 else 0

        is_temporal = pattern_ratio > 0.7 or year_ratio > 0.8

        return is_temporal

    def _format_dataframe_for_llm(self, df: pd.DataFrame, viz_type: VisualizationType, aggregation_info: str = None) -> str:
        """데이터프레임을 LLM이 이해하기 쉬운 형식으로 변환"""

        # 변수 타입 분석
        column_analysis = self._analyze_column_types(df)

        # 기본 데이터 정보
        info = f"데이터 개요:\n"
        info += f"- 행 수: {len(df)}\n"
        info += f"- 열 수: {len(df.columns)}\n"
        info += f"- 열 이름: {', '.join(df.columns)}\n"

        # 집계 정보가 있는 경우 추가
        if aggregation_info:
            info += f"- 데이터 집계: {aggregation_info}\n"
        info += "\n"

        # 변수 타입 정보
        info += "변수 타입 분석:\n"
        info += f"- 범주형 변수 (X축/그룹용): {column_analysis['categorical']}\n"
        info += f"- 수치형 변수 (Y축용): {column_analysis['numeric']}\n"
        info += f"- 시계열 변수: {column_analysis['temporal']}\n\n"

        # 시각화 유형에 따른 데이터 형식
        if viz_type == VisualizationType.TABLE:
            # 표는 전체 데이터 포함
            formatted_data = info + "전체 데이터:\n" + df.to_string(index=False)

        elif viz_type == VisualizationType.CHART:
            # 차트는 수치 데이터 중심 + 실제 전체 데이터 포함
            formatted_data = info

            # 시각화 가이드 추가
            formatted_data += "차트 시각화 가이드:\n"
            if column_analysis['numeric']:
                formatted_data += f"- Y축으로 사용할 수치형 변수: {column_analysis['numeric']}\n"
            if column_analysis['categorical']:
                formatted_data += f"- X축/그룹으로 사용할 범주형 변수: {column_analysis['categorical']}\n"
            if column_analysis['temporal']:
                formatted_data += f"- 시계열 축으로 사용할 변수: {column_analysis['temporal']}\n"

            # 집계 정보가 있는 경우 차트 제목 생성 가이드 추가
            if aggregation_info:
                if "평균" in aggregation_info or "mean" in aggregation_info.lower():
                    formatted_data += f"- 차트 제목에 '평균'을 반드시 포함하세요 (예: '연도별 평균 판매량 추이')\n"
                elif "합계" in aggregation_info or "sum" in aggregation_info.lower():
                    formatted_data += f"- 차트 제목에 '합계' 또는 '총'을 반드시 포함하세요 (예: '제품별 총 판매량')\n"
            formatted_data += "\n"

            # 실제 전체 데이터 포함 (할루시네이션 방지를 위해 필수)
            formatted_data += "전체 실제 데이터 (반드시 이 데이터만 사용):\n" + df.to_string(index=False)

        return formatted_data

    async def _structure_content_to_table(self, content: str, content_type: str, viz_type: VisualizationType) -> str:
        """
        PDF, 이미지, 텍스트 콘텐츠를 표/CSV 형식으로 직접 구조화

        Args:
            content: 원본 콘텐츠
            content_type: 콘텐츠 타입 ("pdf", "image", "text")
            viz_type: 시각화 타입 (TABLE 또는 CHART)

        Returns:
            str: CSV 형식의 구조화된 데이터
        """
        try:
            # 콘텐츠 타입별 표 구조화 프롬프트 생성
            prompt = self._build_table_structuring_prompt(content, content_type, viz_type)

            # LLM으로 표/CSV 구조화
            from app.core.config import settings
            structured_response = await call_llm(
                prompt=prompt,
                model=settings.llm_visualization_model
            )

            # call_llm 응답 처리
            if hasattr(structured_response, 'content'):
                structured_content = structured_response.content
            elif isinstance(structured_response, str):
                structured_content = structured_response
            else:
                structured_content = str(structured_response)

            logger.info(f"표 형태 구조화 완료: {len(structured_content)} 문자")
            return structured_content

        except Exception as e:
            logger.error(f"표 구조화 실패: {str(e)}")
            # 구조화 실패 시 원본 콘텐츠 반환
            return content

    def _build_table_structuring_prompt(self, content: str, content_type: str, viz_type: VisualizationType) -> str:
        """콘텐츠 타입별 표/CSV 구조화 프롬프트 생성"""

        # 시각화 타입에 따른 기본 지시사항
        if viz_type == VisualizationType.TABLE:
            base_instruction = (
                "주어진 콘텐츠에서 데이터를 추출하여 **표(CSV) 형식**으로 구조화해주세요.\n\n"
                "출력 형식:\n"
                "- 첫 번째 줄: 컬럼명1,컬럼명2,컬럼명3...\n"
                "- 이후 줄: 데이터1,데이터2,데이터3...\n"
                "- 모든 셀에 내용 필수 (빈 셀은 '-'로 표시)\n"
                "- 쉼표가 포함된 내용은 공백으로 대체\n\n"
                "중요: 문서에 명시된 데이터만 사용하고, 추가 계산이나 새로운 컬럼을 생성하지 마세요."
            )
        else:  # CHART
            base_instruction = (
                "주어진 콘텐츠에서 차트로 시각화할 수 있는 데이터를 추출하여 **CSV 형식**으로 구조화해주세요.\n\n"
                "출력 형식:\n"
                "- 첫 번째 줄: 컬럼명1,컬럼명2\n"
                "- 이후 줄: 항목,값 (예: 2020년,3500)\n"
                "- 수치 데이터는 순수 숫자만 입력 (단위 제거)\n"
                "- 모든 셀에 내용 필수\n\n"
                "중요: 문서에 명시된 데이터만 사용하고, 계산이나 추정은 하지 마세요."
            )

        content_specific_prompts = {
            "pdf": (
                f"{base_instruction}\n\n"
                "PDF 문서에서 표, 데이터, 통계 정보를 추출하여 CSV로 변환해주세요.\n\n"
                f"PDF 내용:\n{content}"
            ),
            "image": (
                f"{base_instruction}\n\n"
                "이미지에서 표, 차트, 그래프의 데이터를 읽어서 CSV로 변환해주세요.\n\n"
                f"이미지 분석 결과:\n{content}"
            ),
            "text": (
                f"{base_instruction}\n\n"
                "텍스트에서 구조화 가능한 데이터를 추출하여 CSV로 변환해주세요.\n\n"
                f"텍스트 내용:\n{content}"
            )
        }

        return content_specific_prompts.get(content_type, content_specific_prompts["text"])

    async def upload_file_to_ncp(self, file_path: str, base_name: str) -> str:
        """
        로컬 파일을 NCP VISUAL 버킷에 업로드

        Args:
            file_path: 업로드할 파일 경로
            base_name: 파일명의 베이스 이름

        Returns:
            str: 업로드된 파일의 NCP URL
        """
        try:
            # 버킷명 확인 및 디버깅
            bucket_name = settings.naver_bucket_name
            visual_bucket_name = settings.naver_bucket_visual

            if not bucket_name:
                raise ValueError("NAVER_BUCKET_VISUAL 환경변수가 설정되지 않았습니다.")

            # 로컬 파일명 그대로 사용 (경로에서 파일명만 추출)
            filename = os.path.basename(file_path)

            date_folder = datetime.now().strftime("%Y%m%d")
            ncp_path = f"{visual_bucket_name}/{date_folder}/{filename}" 

            # 로컬 파일을 NCP에 업로드
            with open(file_path, 'rb') as file_data:
                self.s3_client.upload_fileobj(
                    file_data,
                    bucket_name,
                    ncp_path,
                )

                # 파일을 공개로 설정
                self.s3_client.put_object_acl(
                    Bucket=settings.naver_bucket_name, 
                    Key=ncp_path, 
                    ACL='public-read'
                )

            # NCP URL 생성 (엔드포인트 제외하고 경로만 반환)
            ncp_url = f"{bucket_name}/{visual_bucket_name}/{date_folder}/{filename}"

            logger.info(f"파일 NCP 업로드 완료: {ncp_url}")
            return ncp_url

        except Exception as e:
            logger.error(f"NCP 업로드 실패: {str(e)}")
            raise ValueError(f"파일을 NCP 버킷에 업로드하는 중 오류가 발생했습니다: {str(e)}")

    async def analyze_visualizations_with_tts(
        self,
        ncp_url: List[str],
        model: str = None,
        language: str = "ko"
    ) -> Dict[str, Any]:
        """
        시각화 이미지들을 분석하고 TTS를 생성합니다.

        Args:
            ncp_url: 분석할 시각화 이미지 NCP URL 목록
            model: 사용할 LLM 모델
            language: 분석 언어 (ko, en, ja, zh 등)

        Returns:
            Dict: 분석 결과 목록
        """
        try:
            if not model:
                model = settings.llm_visualization_model

            analyses = []

            for viz_url in ncp_url:
                try:
                    # 1. NCP URL에서 이미지 다운로드
                    image_bytes = await self._download_from_ncp(viz_url)

                    # 2. LLM으로 시각화 이미지 분석 (언어별)
                    analysis_text = await self._analyze_visualization_image(image_bytes, model, language)

                    # 3. 분석 텍스트로 TTS 생성 (언어별)
                    tts_url = await self._generate_tts_for_analysis(analysis_text, language)

                    analyses.append({
                        "analysis_text": analysis_text,
                        "ncp_url": tts_url
                    })
                    
                    logger.info(f"✅ 시각화 분석 완료: {viz_url}")

                except Exception as e:
                    logger.error(f"❌ 시각화 분석 실패 ({viz_url}): {str(e)}")
                    continue

            return {
                "success": True,
                "analyses": analyses
            }

        except Exception as e:
            logger.error(f"시각화 분석 처리 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _download_from_ncp(self, ncp_url: str) -> bytes:
        """NCP URL에서 이미지 다운로드"""
        try:
            import httpx

            # 전체 URL 구성
            full_url = f"{settings.naver_endpoint_url}/{ncp_url}"

            logger.info(f"🔽 이미지 다운로드 시도: {full_url}")

            async with httpx.AsyncClient() as client:
                response = await client.get(full_url)
                response.raise_for_status()

                logger.info(f"✅ 이미지 다운로드 완료: {len(response.content)} bytes")
                return response.content

        except Exception as e:
            logger.error(f"NCP 이미지 다운로드 실패: {str(e)}")
            raise ValueError(f"이미지 다운로드 실패: {str(e)}")


    async def _analyze_visualization_image(self, image_bytes: bytes, model: str, language: str = None) -> str:
        """LLM으로 시각화 이미지 분석"""
        try:
            # 이미지를 base64로 인코딩
            base64_image = base64.b64encode(image_bytes).decode('utf-8')

            # 이미지 형식 확인
            from PIL import Image
            image_file = io.BytesIO(image_bytes)
            image = Image.open(image_file)
            image_format = image.format.lower() if image.format else 'png'

            # 언어별 시각화 분석 프롬프트 (모듈화)
            prompt = get_analysis_prompt(language)

            # LangChain HumanMessage를 사용한 멀티모달 메시지 생성
            message_content = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/{image_format};base64,{base64_image}"
                    }
                }
            ]

            response = await call_llm(
                prompt=[{
                    "role": "user",
                    "content": message_content
                }],
                model=model,
                max_tokens=settings.openai_max_tokens
            )
            response_text = response.content if response and response.content else ""

            if not response_text.strip():
                raise Exception("시각화 분석 결과가 비어있습니다.")

            # JSON 파싱하여 analysis_text 필드만 추출
            try:
                import json
                import re

                # JSON 추출 시도
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    analysis_text = parsed.get("analysis_text", response_text)
                else:
                    # JSON이 아닌 경우 전체 텍스트 사용
                    analysis_text = response_text

            except Exception as parse_error:
                logger.warning(f"JSON 파싱 실패, 원본 텍스트 사용: {str(parse_error)}")
                analysis_text = response_text

            logger.info(f"✅ 시각화 분석 완료: {len(analysis_text)} 문자")
            return analysis_text.strip()

        except Exception as e:
            logger.error(f"시각화 이미지 분석 실패: {str(e)}")
            raise Exception(f"이미지 분석 실패: {str(e)}")

    async def _generate_tts_for_analysis(self, analysis_text: str, language: str = "ko") -> str:
        """분석 텍스트로 TTS 생성 및 NCP 업로드"""
        try:
            from app.services.voice.tts.generator import TTSService
            from app.models.voice.tts import SingleTTSRequest, GenderType

            # TTS 서비스 인스턴스
            tts_service = TTSService()

            # TTS 생성 요청 (config의 default_tts_provider 사용)
            tts_request = SingleTTSRequest(
                text=analysis_text,
                voice=None,  # provider에 따라 자동 선택
                gender_hint=GenderType.MALE
            )

            # TTS 생성
            tts_response = await tts_service.generate_single_tts(tts_request)

            if not tts_response.success or not tts_response.ncp_url:
                raise Exception("TTS 생성 실패")

            logger.info(f"✅ TTS 생성 완료: {tts_response.ncp_url}")
            return tts_response.ncp_url

        except Exception as e:
            logger.error(f"TTS 생성 실패: {str(e)}")
            raise Exception(f"TTS 생성 실패: {str(e)}")
