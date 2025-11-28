import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import plotly.graph_objects as go
import plotly.io as pio
import io
import os
import re
from typing import Dict, Any, Optional, Tuple
from app.utils.logger.setup import setup_logger

logger = setup_logger("table_renderer")

class TableRenderer:
    """CSV 데이터를 기반으로 표 이미지를 생성하는 렌더러"""
    
    def __init__(self):
        self.setup_matplotlib()
    
    def setup_matplotlib(self):
        """matplotlib NanumGothic 폰트 고정 설정"""
        try:
            logger.info("NanumGothic 폰트 설정 시작...")
            
            # 1. 기본 설정 (한글 깨짐 방지)
            plt.rcParams['axes.unicode_minus'] = False
            
            # 2. MalgunGothic 폰트 강제 설정
            plt.rcParams['font.family'] = 'NanumGothic'
            
            # 3. 추가 설정
            plt.rcParams['figure.dpi'] = 100
            plt.rcParams['savefig.dpi'] = 300
            plt.rcParams['font.size'] = 12
            
            logger.info("✅ NanumGothic 폰트 설정 완료")
            
        except Exception as e:
            logger.error(f"NanumGothic 폰트 설정 실패: {str(e)}")
            # 최소한의 안전 설정
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['font.family'] = 'NanumGothic'
    
    
    
    async def render_table_matplotlib(
        self, 
        csv_data: str, 
        output_path: str, 
        style_options: Dict[str, Any] = None
    ) -> str:
        """matplotlib을 사용하여 표 이미지 생성"""
        try:
            options = style_options or {}
            
            # MalgunGothic 폰트 강제 설정
            plt.rcParams['font.family'] = 'NanumGothic'
            plt.rcParams['axes.unicode_minus'] = False
            
            # CSV 데이터를 DataFrame으로 변환 (NaN 처리 + 필드 수 오류 방지)
            df = pd.read_csv(
                io.StringIO(csv_data), 
                na_values=['', 'nan', 'NaN', 'NULL', 'null'], 
                keep_default_na=False,
                on_bad_lines='skip',  # 필드 수가 맞지 않는 행 스킵
                skipinitialspace=True,  # 앞뒤 공백 제거
                dtype=str  # 모든 데이터를 문자열로 처리
            )
            # NaN 값을 빈 문자열로 대체
            df = df.fillna('')
            
            if df.empty:
                raise ValueError("CSV 데이터가 비어있습니다.")
            
            # 스타일 옵션 설정 - 깔끔한 렌더링을 위한 개선
            figsize = options.get("figsize", (14, max(8, len(df) * 1.2)))  # 동적 크기 조정
            dpi = options.get("dpi", 300)
            font_size = options.get("font_size", 11)  # 약간 작게 조정
            header_color = options.get("header_color", "#4a90e2")  # 더 진한 헤더
            cell_color = options.get("cell_color", "#f8f9fa")  # 약간 회색 배경
            border_color = options.get("border_color", "#dee2e6")  # 더 선명한 경계
            
            # 그림 생성
            fig, ax = plt.subplots(figsize=figsize)
            ax.axis('tight')
            ax.axis('off')
            
            # 긴 텍스트 자동 줄바꿈 처리
            wrapped_data = []
            max_chars_per_line = 25  # 한 줄 최대 문자 수
            
            for row in df.values:
                wrapped_row = []
                for cell in row:
                    cell_str = str(cell)
                    if len(cell_str) > max_chars_per_line:
                        # 긴 텍스트를 여러 줄로 분할
                        wrapped_text = self._wrap_text_korean(cell_str, max_chars_per_line)
                        wrapped_row.append(wrapped_text)
                    else:
                        wrapped_row.append(cell_str)
                wrapped_data.append(wrapped_row)
            
            # 컬럼명도 줄바꿈 처리
            wrapped_columns = []
            for col in df.columns:
                col_str = str(col)
                if len(col_str) > max_chars_per_line:
                    wrapped_col = self._wrap_text_korean(col_str, max_chars_per_line)
                    wrapped_columns.append(wrapped_col)
                else:
                    wrapped_columns.append(col_str)
            
            # 표 생성 - 개선된 설정
            table = ax.table(
                cellText=wrapped_data,
                colLabels=wrapped_columns,
                cellLoc='left',  # 왼쪽 정렬로 가독성 향상
                loc='center',
                colColours=[header_color] * len(df.columns)
            )
            
            # 표 스타일링 - 향상된 설정
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)
            table.scale(1.5, 2.5)  # 더 넉넉한 셀 크기
            
            # 각 셀 스타일링 - 향상된 가독성
            for i in range(len(df.columns)):
                # 헤더 셀 스타일링
                header_cell = table[(0, i)]
                header_cell.set_facecolor(header_color)
                header_cell.set_text_props(
                    weight='bold', 
                    fontfamily='NanumGothic',
                    color='white',  # 흰색 텍스트로 대비 향상
                    ha='center',    # 가로 가운데 정렬
                    va='center'     # 세로 가운데 정렬
                )
                header_cell.set_edgecolor('#ffffff')
                header_cell.set_linewidth(1.5)
            
            # 데이터 셀 스타일링
            for i in range(1, len(df) + 1):
                for j in range(len(df.columns)):
                    data_cell = table[(i, j)]
                    data_cell.set_facecolor(cell_color)
                    data_cell.set_edgecolor(border_color)
                    data_cell.set_linewidth(1)
                    data_cell.set_text_props(
                        fontfamily='NanumGothic',
                        color='#2c3e50',  # 진한 회색 텍스트
                        ha='left',        # 왼쪽 정렬
                        va='center',      # 세로 가운데 정렬
                        wrap=True        # 텍스트 랩핑 활성화
                    )
                    
                    # 셀 패딩 추가
                    data_cell.PAD = 0.05
            
            # 제목 추가 (선택사항) - NanumGothic 폰트 명시
            title = options.get("title")
            if title:
                plt.title(title, fontsize=font_size + 4, fontweight='bold', pad=20, fontfamily='NanumGothic')
            
            # 출력 디렉토리 확인 및 생성
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"출력 디렉토리 생성: {output_dir}")
            
            # 이미지 저장
            try:
                plt.savefig(
                    output_path,
                    dpi=dpi,
                    bbox_inches='tight',
                    facecolor='white',
                    edgecolor='none',
                    pad_inches=0.2
                )
                plt.close(fig)
                
                # 파일 생성 확인
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logger.info(f"✅ matplotlib 표 이미지 생성 완료: {output_path} ({file_size} bytes)")
                    return output_path
                else:
                    raise FileNotFoundError(f"이미지 파일이 생성되지 않았습니다: {output_path}")
                    
            except Exception as save_error:
                plt.close(fig)  # 오류 시에도 figure 정리
                logger.error(f"이미지 저장 실패: {str(save_error)}")
                raise
            
        except Exception as e:
            logger.error(f"matplotlib 표 렌더링 실패: {str(e)}")
            raise
    
    async def render_table_plotly(
        self, 
        csv_data: str, 
        output_path: str, 
        style_options: Dict[str, Any] = None
    ) -> str:
        """plotly를 사용하여 표 이미지 생성"""
        try:
            options = style_options or {}
            
            # CSV 데이터를 DataFrame으로 변환 (NaN 처리 + 필드 수 오류 방지)
            df = pd.read_csv(
                io.StringIO(csv_data), 
                na_values=['', 'nan', 'NaN', 'NULL', 'null'], 
                keep_default_na=False,
                on_bad_lines='skip',  # 필드 수가 맞지 않는 행 스킵
                skipinitialspace=True,  # 앞뒤 공백 제거
                dtype=str  # 모든 데이터를 문자열로 처리
            )
            # NaN 값을 빈 문자열로 대체
            df = df.fillna('')
            
            if df.empty:
                raise ValueError("CSV 데이터가 비어있습니다.")
            
            # 스타일 옵션 설정
            width = options.get("width", 800)
            height = options.get("height", 600)
            font_size = options.get("font_size", 14)
            header_color = options.get("header_color", "#2E86AB")
            cell_color = options.get("cell_color", "#F8F9FA")
            
            # Plotly 표 생성 - NanumGothic 폰트 적용
            fig = go.Figure(data=[go.Table(
                header=dict(
                    values=list(df.columns),
                    fill_color=header_color,
                    font=dict(color='white', size=font_size + 2, family='NanumGothic'),
                    align="center",
                    height=40
                ),
                cells=dict(
                    values=[df[col] for col in df.columns],
                    fill_color=cell_color,
                    font=dict(color='black', size=font_size, family='NanumGothic'),
                    align="center",
                    height=35
                )
            )])
            
            # 레이아웃 설정 - NanumGothic 폰트 적용
            title = options.get("title", "데이터 표")
            fig.update_layout(
                title=dict(
                    text=title,
                    font=dict(size=font_size + 6, family="NanumGothic"),
                    x=0.5
                ),
                width=width,
                height=height,
                margin=dict(l=20, r=20, t=60, b=20),
                font=dict(family="NanumGothic")
            )
            
            # 출력 디렉토리 확인 및 생성
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"출력 디렉토리 생성: {output_dir}")
            
            # 이미지 저장
            try:
                pio.write_image(fig, output_path, format='png', engine='kaleido')
                
                # 파일 생성 확인
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logger.info(f"✅ plotly 표 이미지 생성 완료: {output_path} ({file_size} bytes)")
                    return output_path
                else:
                    raise FileNotFoundError(f"이미지 파일이 생성되지 않았습니다: {output_path}")
                    
            except Exception as save_error:
                logger.error(f"plotly 이미지 저장 실패: {str(save_error)}")
                raise
            
        except Exception as e:
            logger.error(f"plotly 표 렌더링 실패: {str(e)}")
            raise
    
    async def render_table_seaborn(
        self, 
        csv_data: str, 
        output_path: str, 
        style_options: Dict[str, Any] = None
    ) -> str:
        """seaborn을 사용하여 히트맵 스타일 표 생성"""
        try:
            options = style_options or {}
            
            # MalgunGothic 폰트 강제 설정
            plt.rcParams['font.family'] = 'NanumGothic'
            plt.rcParams['axes.unicode_minus'] = False
            
            # CSV 데이터를 DataFrame으로 변환 (NaN 처리 + 필드 수 오류 방지)
            df = pd.read_csv(
                io.StringIO(csv_data), 
                na_values=['', 'nan', 'NaN', 'NULL', 'null'], 
                keep_default_na=False,
                on_bad_lines='skip',  # 필드 수가 맞지 않는 행 스킵
                skipinitialspace=True,  # 앞뒤 공백 제거
                dtype=str  # 모든 데이터를 문자열로 처리
            )
            # NaN 값을 빈 문자열로 대체
            df = df.fillna('')
            
            if df.empty:
                raise ValueError("CSV 데이터가 비어있습니다.")
            
            # 수치 데이터만 추출하여 히트맵 생성
            numeric_columns = df.select_dtypes(include=['number']).columns
            
            if len(numeric_columns) > 0:
                # 수치 데이터가 있는 경우 히트맵
                figsize = options.get("figsize", (10, 8))
                
                plt.figure(figsize=figsize)
                sns.heatmap(
                    df[numeric_columns], 
                    annot=True, 
                    fmt='.1f', 
                    cmap='Blues',
                    cbar_kws={'label': '값'}
                )
                
                title = options.get("title", "데이터 히트맵")
                plt.title(title, fontsize=16, fontweight='bold', fontfamily='NanumGothic')
                plt.tight_layout()
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close()
            else:
                # 수치 데이터가 없는 경우 일반 표로 fallback
                return await self.render_table_matplotlib(csv_data, output_path, style_options)
            
            logger.info(f"seaborn 히트맵 표 생성 완료: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"seaborn 표 렌더링 실패: {str(e)}")
            # matplotlib으로 fallback
            return await self.render_table_matplotlib(csv_data, output_path, style_options)
    
    def parse_csv_from_llm_response(self, llm_response: str) -> Dict[str, str]:
        """
        LLM 응답에서 CSV 데이터 및 제목 추출

        Returns:
            Dict: {"title": "표 제목", "csv_data": "CSV 데이터"}
        """
        try:
            import json

            # 1. JSON 형식 응답 파싱 시도 (새로운 형식)
            try:
                # JSON 코드 블록에서 추출 시도
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', llm_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # JSON 코드 블록 없이 바로 JSON인 경우
                    json_match = re.search(r'\{.*"title".*"csv_data".*\}', llm_response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        raise ValueError("JSON 형식을 찾을 수 없습니다.")

                parsed_json = json.loads(json_str)

                if "title" in parsed_json and "csv_data" in parsed_json:
                    title = parsed_json["title"].strip()
                    csv_data = parsed_json["csv_data"].strip()

                    # CSV 데이터 검증
                    test_df = pd.read_csv(
                        io.StringIO(csv_data),
                        na_values=['', 'nan', 'NaN', 'NULL', 'null'],
                        keep_default_na=False,
                        on_bad_lines='skip',
                        skipinitialspace=True,
                        dtype=str
                    )
                    test_df = test_df.fillna('')

                    if test_df.empty:
                        raise ValueError("파싱된 CSV 데이터가 비어있습니다.")

                    logger.info(f"✅ JSON 형식 파싱 성공 - 제목: '{title}', 데이터: {len(test_df)}행 x {len(test_df.columns)}열")
                    return {"title": title, "csv_data": csv_data}

            except (ValueError, json.JSONDecodeError, KeyError) as json_error:
                logger.info(f"JSON 파싱 실패, 기존 CSV 방식으로 시도: {str(json_error)}")

            # 2. 기존 CSV 형식 파싱 (하위 호환성)
            lines = llm_response.strip().split('\n')
            csv_lines = []

            for line in lines:
                line = line.strip()
                # CSV 형태의 줄만 추출 (쉼표 포함하고 비어있지 않음)
                if ',' in line and line and not line.startswith('#'):
                    # 마크다운 문법 제거
                    line = line.replace('|', '').replace('*', '').replace('#', '')
                    line = line.strip()

                    # 쉼표가 포함된 데이터에서 발생하는 필드 수 문제 해결
                    if line:
                        # 간단한 필드 정제: 연속된 쉼표 제거
                        line = re.sub(r',+', ',', line)  # 연속 쉼표 제거
                        line = line.strip(',')  # 앞뒤 쉼표 제거
                        if line and ',' in line:
                            csv_lines.append(line)

            if not csv_lines:
                raise ValueError("LLM 응답에서 유효한 CSV 데이터를 찾을 수 없습니다.")

            csv_data = '\n'.join(csv_lines)

            # DataFrame으로 파싱 테스트
            test_df = pd.read_csv(
                io.StringIO(csv_data),
                na_values=['', 'nan', 'NaN', 'NULL', 'null'],
                keep_default_na=False,
                on_bad_lines='skip',
                skipinitialspace=True,
                dtype=str
            )
            test_df = test_df.fillna('')

            if test_df.empty:
                raise ValueError("파싱된 CSV 데이터가 비어있습니다.")

            logger.info(f"CSV 파싱 성공 (제목 없음): {len(test_df)}행 x {len(test_df.columns)}열")
            return {"title": None, "csv_data": csv_data}

        except Exception as e:
            logger.error(f"CSV 파싱 실패: {str(e)}")
            logger.error(f"원본 LLM 응답: {llm_response[:300]}...")
            raise
    
    def _wrap_text_korean(self, text: str, max_chars: int) -> str:
        """한국어 텍스트를 지정된 길이로 줄바꿈"""
        if len(text) <= max_chars:
            return text
        
        lines = []
        current_line = ""
        words = text.split()
        
        for word in words:
            # 단어가 너무 길면 강제로 자름
            if len(word) > max_chars:
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                # 긴 단어를 여러 줄로 분할
                while len(word) > max_chars:
                    lines.append(word[:max_chars])
                    word = word[max_chars:]
                if word:
                    current_line = word
            else:
                # 현재 줄에 단어를 추가할 수 있는지 확인
                test_line = current_line + (" " if current_line else "") + word
                if len(test_line) <= max_chars:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return "\n".join(lines)
    
    def validate_csv_data(self, csv_data: str) -> Tuple[bool, str]:
        """CSV 데이터 유효성 검증 (빈 셀 검증 포함)"""
        try:
            # CSV 데이터를 DataFrame으로 변환 (NaN 처리 + 필드 수 오류 방지)
            df = pd.read_csv(
                io.StringIO(csv_data), 
                na_values=['', 'nan', 'NaN', 'NULL', 'null'], 
                keep_default_na=False,
                on_bad_lines='skip',  # 필드 수가 맞지 않는 행 스킵
                skipinitialspace=True,  # 앞뒤 공백 제거
                dtype=str  # 모든 데이터를 문자열로 처리
            )
            # NaN 값을 빈 문자열로 대체
            df = df.fillna('')
            
            if df.empty:
                return False, "CSV 데이터가 비어있습니다."
            
            if len(df.columns) < 2:
                return False, "최소 2개 이상의 컬럼이 필요합니다."
            
            if len(df) < 1:
                return False, "최소 1개 이상의 데이터 행이 필요합니다."
            
            # 빈 셀 검증
            empty_cells = []
            for i, row in df.iterrows():
                for j, col in enumerate(df.columns):
                    cell_value = str(row[col]).strip()
                    if not cell_value:  # 빈 셀 발견
                        empty_cells.append(f"행{i+1}-{col}")
            
            if empty_cells:
                empty_count = len(empty_cells)
                total_cells = len(df) * len(df.columns)
                warning_msg = f"빈 셀 {empty_count}개 발견 (전체 {total_cells}개 중): {', '.join(empty_cells[:5])}"
                if empty_count > 5:
                    warning_msg += f" 등 {empty_count}개"
                logger.warning(warning_msg)
                
                # 빈 셀이 30% 이상이면 검증 실패
                if empty_count / total_cells > 0.3:
                    return False, f"빈 셀이 너무 많습니다 ({empty_count}/{total_cells}). 데이터 품질을 개선해주세요."
            
            return True, f"유효한 CSV 데이터: {len(df)}행 x {len(df.columns)}열 (빈 셀: {len(empty_cells)}개)"
            
        except Exception as e:
            return False, f"CSV 파싱 오류: {str(e)}"
    
    async def render_table_auto(
        self, 
        csv_data: str, 
        output_path: str, 
        style_options: Dict[str, Any] = None
    ) -> str:
        """가장 적합한 방식으로 자동 표 렌더링"""
        
        options = style_options or {}
        renderer = options.get("renderer", "matplotlib")  # 기본값: matplotlib
        
        try:
            if renderer == "plotly":
                return await self.render_table_plotly(csv_data, output_path, style_options)
            elif renderer == "seaborn":
                return await self.render_table_seaborn(csv_data, output_path, style_options)
            else:  # matplotlib (기본값)
                return await self.render_table_matplotlib(csv_data, output_path, style_options)
                
        except Exception as e:
            logger.warning(f"{renderer} 렌더링 실패, matplotlib으로 fallback: {str(e)}")
            # fallback to matplotlib
            if renderer != "matplotlib":
                return await self.render_table_matplotlib(csv_data, output_path, style_options)
            else:
                raise