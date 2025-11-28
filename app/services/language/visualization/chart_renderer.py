import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import io
import os
import re
from typing import Dict, Any, Optional, Tuple
from app.utils.logger.setup import setup_logger

logger = setup_logger("chart_renderer")

class ChartRenderer:
    """CSV 데이터를 기반으로 차트 이미지를 생성하는 렌더러"""
    
    def __init__(self):
        self.setup_matplotlib()
    
    def setup_matplotlib(self):
        """matplotlib 한글 폰트 설정"""
        try:
            # 기본 설정 (한글 깨짐 방지)
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['figure.dpi'] = 100
            plt.rcParams['savefig.dpi'] = 300
            plt.rcParams['font.size'] = 12

            # 한글 폰트 확인
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            korean_fonts = ['NanumGothic', 'Nanum Gothic', 'NanumBarunGothic', 'Malgun Gothic']

            found_font = None
            for font in korean_fonts:
                if font in available_fonts:
                    found_font = font
                    break

            if found_font:
                plt.rcParams['font.family'] = found_font
            else:
                # 한글 폰트가 없으면 에러 메시지 출력
                plt.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']
                logger.error("❌ 한글 폰트를 찾을 수 없습니다. 한글이 깨져서 표시될 수 있습니다.")
                logger.error("사용 가능한 폰트 목록:")
                for font in sorted(set(available_fonts))[:20]:  # 처음 20개만 표시
                    logger.error(f"  - {font}")

        except Exception as e:
            logger.error(f"차트 폰트 설정 실패: {str(e)}")
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']
    
    async def render_multiple_charts(
        self, 
        chart_data: str, 
        output_path: str, 
        style_options: Dict[str, Any] = None
    ) -> str:
        """다중 차트 데이터를 파싱하여 여러 차트를 하나의 이미지로 생성"""
        try:
            # 차트 구분자로 분리
            chart_sections = chart_data.split("===CHART_SEPARATOR===")
            chart_sections = [section.strip() for section in chart_sections if section.strip()]
            
            if len(chart_sections) == 1:
                # 단일 차트인 경우 기존 방식 사용
                return await self.render_chart_matplotlib(chart_data, output_path, style_options)
            
            logger.info(f"다중 차트 감지: {len(chart_sections)}개 차트")
            
            # 차트 정보 파싱
            charts_info = []
            for i, section in enumerate(chart_sections):
                try:
                    chart_info = self.parse_chart_data(section)
                    if not chart_info["dataframe"].empty:
                        charts_info.append(chart_info)
                except Exception as e:
                    logger.warning(f"차트 {i+1} 파싱 실패: {str(e)}")
                    continue
            
            if not charts_info:
                raise ValueError("유효한 차트 데이터가 없습니다.")
            
            options = style_options or {}
            dpi = options.get("dpi", 300)
            font_size = options.get("font_size", 10)  # 다중 차트에서는 폰트 크기 축소
            
            # 차트 개수에 따른 레이아웃 결정
            num_charts = len(charts_info)
            if num_charts <= 2:
                rows, cols = 1, num_charts
                figsize = (12 * cols, 8)
            elif num_charts <= 4:
                rows, cols = 2, 2
                figsize = (16, 12)
            elif num_charts <= 6:
                rows, cols = 2, 3
                figsize = (18, 12)
            else:
                rows, cols = 3, 3
                figsize = (20, 15)
            
            # 서브플롯 생성
            fig, axes = plt.subplots(rows, cols, figsize=figsize)
            if num_charts == 1:
                axes = [axes]
            elif rows == 1 or cols == 1:
                axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
            else:
                axes = axes.flatten()
            
            # 각 차트 렌더링
            for i, chart_info in enumerate(charts_info):
                if i >= len(axes):  # 인덱스 범위 초과 방지
                    logger.warning(f"차트 {i+1} 인덱스 범위 초과, 건너뛰기")
                    break

                ax = axes[i]
                chart_type = chart_info["chart_type"]
                title = chart_info["title"]
                df = chart_info["dataframe"]

                # 차트 타입별 렌더링
                try:
                    if chart_type == "bar":
                        self._render_bar_chart(ax, df, title, font_size)
                    elif chart_type == "line":
                        self._render_line_chart(ax, df, title, font_size)
                    elif chart_type == "pie":
                        self._render_pie_chart(ax, df, title, font_size)
                    elif chart_type == "scatter":
                        self._render_scatter_chart(ax, df, title, font_size)
                    elif chart_type == "histogram":
                        self._render_histogram_chart(ax, df, title, font_size)
                    else:
                        # 기본값: 막대 차트
                        self._render_bar_chart(ax, df, title, font_size)
                except Exception as e:
                    logger.error(f"차트 {i+1} 렌더링 실패: {str(e)}")
                    # 오류 시 빈 차트로 표시
                    ax.text(0.5, 0.5, f'차트 렌더링 실패\n{str(e)}',
                           ha='center', va='center', transform=ax.transAxes,
                           fontfamily='NanumGothic', fontsize=font_size)

            # 빈 서브플롯 숨기기
            for i in range(len(charts_info), len(axes)):
                if i < len(axes):
                    axes[i].set_visible(False)
            
            # 출력 디렉토리 확인 및 생성
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"출력 디렉토리 생성: {output_dir}")
            
            # 이미지 저장
            try:
                # 다중 차트 레이아웃 조정
                plt.tight_layout(pad=3.0)
                plt.subplots_adjust(
                    left=0.08,
                    bottom=0.08,
                    right=0.95,
                    top=0.95,
                    wspace=0.3,  # 가로 간격
                    hspace=0.4   # 세로 간격
                )
                plt.savefig(
                    output_path,
                    dpi=dpi,
                    bbox_inches='tight',
                    facecolor='white',
                    edgecolor='none',
                    pad_inches=0.5
                )
                plt.close(fig)
                
                # 파일 생성 확인
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logger.info(f"✅ matplotlib 다중 차트 이미지 생성 완료: {output_path} ({file_size} bytes, {num_charts}개 차트)")
                    return output_path
                else:
                    raise FileNotFoundError(f"이미지 파일이 생성되지 않았습니다: {output_path}")
                    
            except Exception as save_error:
                plt.close(fig)
                logger.error(f"다중 차트 이미지 저장 실패: {str(save_error)}")
                raise
            
        except Exception as e:
            logger.error(f"다중 차트 렌더링 실패: {str(e)}")
            raise

    async def render_chart_matplotlib(
        self, 
        chart_data: str, 
        output_path: str, 
        style_options: Dict[str, Any] = None
    ) -> str:
        """matplotlib을 사용하여 차트 이미지 생성"""
        try:
            options = style_options or {}
            
            # 차트 데이터 파싱
            chart_info = self.parse_chart_data(chart_data)
            chart_type = chart_info["chart_type"]
            title = chart_info["title"]
            df = chart_info["dataframe"]
            
            if df.empty:
                raise ValueError("차트 데이터가 비어있습니다.")
            
            # 스타일 옵션 설정
            figsize = options.get("figsize", (12, 8))
            dpi = options.get("dpi", 300)
            font_size = options.get("font_size", 12)
            
            # 그림 생성
            fig, ax = plt.subplots(figsize=figsize)
            
            # 차트 타입별 렌더링
            if chart_type == "bar":
                self._render_bar_chart(ax, df, title, font_size)
            elif chart_type == "line":
                self._render_line_chart(ax, df, title, font_size)
            elif chart_type == "pie":
                self._render_pie_chart(ax, df, title, font_size)
            elif chart_type == "scatter":
                self._render_scatter_chart(ax, df, title, font_size)
            elif chart_type == "histogram":
                self._render_histogram_chart(ax, df, title, font_size)
            else:
                # 기본값: 막대 차트
                self._render_bar_chart(ax, df, title, font_size)
            
            # 출력 디렉토리 확인 및 생성
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"출력 디렉토리 생성: {output_dir}")
            
            # 이미지 저장
            try:
                # 레이아웃 조정 - 더 넉넉한 여백 설정
                plt.tight_layout(pad=2.0)  # 패딩 증가
                plt.subplots_adjust(
                    left=0.15,     # 왼쪽 여백
                    bottom=0.2,    # 아래쪽 여백 (X축 라벨용)
                    right=0.95,    # 오른쪽 여백
                    top=0.9        # 위쪽 여백 (타이틀용)
                )
                plt.savefig(
                    output_path,
                    dpi=dpi,
                    bbox_inches='tight',
                    facecolor='white',
                    edgecolor='none',
                    pad_inches=0.5  # 외부 패딩 증가
                )
                plt.close(fig)
                
                # 파일 생성 확인
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logger.info(f"✅ matplotlib 차트 이미지 생성 완료: {output_path} ({file_size} bytes)")
                    return output_path
                else:
                    raise FileNotFoundError(f"이미지 파일이 생성되지 않았습니다: {output_path}")
                    
            except Exception as save_error:
                plt.close(fig)  # 오류 시에도 figure 정리
                logger.error(f"차트 이미지 저장 실패: {str(save_error)}")
                raise
            
        except Exception as e:
            logger.error(f"matplotlib 차트 렌더링 실패: {str(e)}")
            raise
    
    def _process_axis_data(self, data, is_x_axis=True):
        """축 데이터 타입 처리 - matplotlib 경고 해결"""
        if is_x_axis:
            # X축: 항상 문자열로 처리 (카테고리형 데이터로 취급)
            try:
                # 문자열로 변환하되, NaN이나 None은 '미분류'로 처리
                str_data = data.astype(str).fillna('미분류')
                # 'nan' 문자열도 '미분류'로 대체
                str_data = str_data.replace(['nan', 'NaN', 'None'], '미분류')
                logger.info(f"X축 데이터를 문자열로 변환: {len(str_data)}개 항목")
                return str_data
            except Exception as e:
                logger.warning(f"X축 데이터 변환 실패, 기본값 사용: {str(e)}")
                return pd.Series(['항목1', '항목2', '항목3'][:len(data)])
        else:
            # Y축: 항상 숫자로 변환
            return pd.to_numeric(data, errors='coerce').fillna(0)

    def _render_bar_chart(self, ax, df, title, font_size):
        """막대 차트 렌더링"""
        if len(df.columns) < 2:
            ax.text(0.5, 0.5, '데이터가 부족합니다', ha='center', va='center',
                   transform=ax.transAxes, fontfamily='NanumGothic')
            return

        x_col, y_col = df.columns[0], df.columns[1]

        # 축 데이터 처리
        x_data = self._process_axis_data(df[x_col], is_x_axis=True)
        y_data = self._process_axis_data(df[y_col], is_x_axis=False)

        bars = ax.bar(x_data, y_data, color='#4a90e2', alpha=0.8)
        ax.set_title(title, fontsize=font_size + 4, fontweight='bold', fontfamily='NanumGothic', pad=20)
        ax.set_xlabel(x_col, fontsize=font_size, fontfamily='NanumGothic', labelpad=10)
        ax.set_ylabel(y_col, fontsize=font_size, fontfamily='NanumGothic', labelpad=10)
        
        # 값 라벨 추가 - 겹침 방지
        for bar, value in zip(bars, y_data):
            if value > 0:
                # 소수점 자동 판정 (정수면 .0f, 소수면 .2f)
                format_str = f'{value:,.0f}' if value == int(value) else f'{value:,.2f}'
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(y_data)*0.02,
                       format_str, ha='center', va='bottom', fontfamily='NanumGothic', fontsize=font_size-1)
        
        # 격자 추가
        ax.grid(True, alpha=0.3, zorder=0)
        # X축 라벨 회전 및 정렬 개선
        ax.tick_params(axis='x', rotation=45, labelsize=font_size-1)
        ax.tick_params(axis='y', labelsize=font_size-1)

        # Y축 포맷터 설정 (소수점 자동 판정)
        def y_axis_formatter(x, p):
            if x == int(x):
                return f'{int(x):,}'  # 정수면 소수점 없이
            else:
                return f'{x:,.2f}'    # 소수면 소수점 2자리까지
        ax.yaxis.set_major_formatter(plt.FuncFormatter(y_axis_formatter))
        
        # X축 라벨이 긴 경우 자동 조정
        labels = ax.get_xticklabels()
        if len(max([label.get_text() for label in labels], key=len)) > 8:
            ax.tick_params(axis='x', rotation=60)
    
    def _render_line_chart(self, ax, df, title, font_size):
        """선 차트 렌더링 - 시계열 다중 시리즈 지원"""
        if len(df.columns) < 2:
            ax.text(0.5, 0.5, '데이터가 부족합니다', ha='center', va='center',
                   transform=ax.transAxes, fontfamily='NanumGothic')
            return

        logger.info(f"🔍 라인 차트 렌더링 - DataFrame 모양: {df.shape}")
        logger.info(f"🔍 컬럼 목록: {list(df.columns)}")
        logger.info(f"🔍 데이터 미리보기:\n{df.head()}")

        # 첫 번째 컬럼을 X축으로 사용 (Year)
        x_col = df.columns[0]

        # 나머지 컬럼들을 Y값으로 사용 (Seoul, Busan, Incheon)
        y_cols = df.columns[1:]

        logger.info(f"🔍 X축 컬럼: {x_col}")
        logger.info(f"🔍 Y축 컬럼들: {list(y_cols)}")

        # X축 데이터 처리 및 정렬
        df_sorted = df.sort_values(x_col)
        x_values = df_sorted[x_col].tolist()

        # X축이 연도인지 확인하고 정수로 변환
        # X축을 문자열로 처리
        x_numeric = list(range(len(x_values)))  # 인덱스 사용
        x_labels = [str(x) for x in x_values]   # 라벨은 원본 문자열

        # 각 Y 컬럼에 대해 라인 그리기
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']

        for i, y_col in enumerate(y_cols):
            # Y값 처리 - 숫자로 변환
            y_values = []
            for val in df_sorted[y_col].tolist():
                try:
                    y_values.append(float(str(val).replace(',', '')))
                except:
                    y_values.append(0.0)

            color = colors[i % len(colors)]

            # 라인 그리기
            ax.plot(x_numeric, y_values, marker='o', linewidth=2, markersize=6,
                   color=color, label=str(y_col))

            # 각 포인트에 수치 라벨 추가 (소수점 자동 판정)
            for x_val, y_val in zip(x_numeric, y_values):
                # 소수점 자동 판정 (정수면 .0f, 소수면 .2f)
                format_str = f'{y_val:,.0f}' if y_val == int(y_val) else f'{y_val:,.2f}'
                ax.annotate(format_str, (x_val, y_val), textcoords="offset points",
                           xytext=(0, 10), ha='center', fontfamily='NanumGothic',
                           fontsize=font_size-2, color=color)

        # X축 설정 - 문자열 라벨 표시
        ax.set_xticks(x_numeric)
        ax.set_xticklabels(x_labels)

        # 범례 표시
        ax.legend(fontsize=font_size-1, loc='best')

        ax.set_title(title, fontsize=font_size + 4, fontweight='bold', fontfamily='NanumGothic', pad=20)
        ax.set_xlabel(x_col, fontsize=font_size, fontfamily='NanumGothic', labelpad=10)

        # Y축 라벨은 첫 번째 Y 컬럼명 사용 (단일 라벨)
        ax.set_ylabel(y_cols[0], fontsize=font_size, fontfamily='NanumGothic', labelpad=10)

        ax.grid(True, alpha=0.3, zorder=0)
        ax.tick_params(axis='x', rotation=0, labelsize=font_size-1)  # 연도는 회전하지 않음
        ax.tick_params(axis='y', labelsize=font_size-1)

        # Y축 포맷 설정 (소수점 자동 판정)
        def y_axis_formatter(x, p):
            if x == int(x):
                return f'{int(x):,}'  # 정수면 소수점 없이
            else:
                return f'{x:,.2f}'    # 소수면 소수점 2자리까지
        ax.yaxis.set_major_formatter(plt.FuncFormatter(y_axis_formatter))
    
    def _render_pie_chart(self, ax, df, title, font_size):
        """원형 차트 렌더링"""
        if len(df.columns) < 2:
            ax.text(0.5, 0.5, '데이터가 부족합니다', ha='center', va='center',
                   transform=ax.transAxes, fontfamily='NanumGothic')
            return

        x_col, y_col = df.columns[0], df.columns[1]

        # 축 데이터 처리
        x_data = self._process_axis_data(df[x_col], is_x_axis=True)
        y_data = self._process_axis_data(df[y_col], is_x_axis=False)
        
        # 0이 아닌 값만 표시
        non_zero_mask = y_data > 0
        labels = x_data[non_zero_mask]
        values = y_data[non_zero_mask]
        
        if len(values) == 0:
            ax.text(0.5, 0.5, '표시할 데이터가 없습니다', ha='center', va='center', 
                   transform=ax.transAxes, fontfamily='NanumGothic')
            return
        
        colors = plt.cm.Set3(range(len(values)))
        # 라벨이 길면 범례 사용, 짧으면 직접 표시
        max_label_length = max([len(str(label)) for label in labels])
        
        if max_label_length > 8 or len(labels) > 6:
            # 라벨이 길거나 많으면 범례 사용
            wedges, texts, autotexts = ax.pie(values, autopct='%1.1f%%', 
                                             startangle=90, colors=colors)
            ax.legend(wedges, labels, title="범례", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
                     fontsize=font_size-1, prop={'family': 'NanumGothic'})
        else:
            # 라벨이 짧으면 직접 표시
            wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                                             startangle=90, colors=colors)
            # 폰트 설정
            for text in texts:
                text.set_fontfamily('NanumGothic')
                text.set_fontsize(font_size-1)
        
        # 퍼센트 텍스트 폰트 설정
        for autotext in autotexts:
            autotext.set_fontfamily('NanumGothic')
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(font_size-1)
        
        ax.set_title(title, fontsize=font_size + 4, fontweight='bold', fontfamily='NanumGothic', pad=20)
    
    def _render_scatter_chart(self, ax, df, title, font_size):
        """산점도 렌더링"""
        if len(df.columns) < 2:
            ax.text(0.5, 0.5, '데이터가 부족합니다', ha='center', va='center',
                   transform=ax.transAxes, fontfamily='NanumGothic')
            return

        x_col, y_col = df.columns[0], df.columns[1]

        # 축 데이터 처리 (scatter는 양축 모두 숫자)
        x_data = self._process_axis_data(df[x_col], is_x_axis=False)  # 숫자로 처리
        y_data = self._process_axis_data(df[y_col], is_x_axis=False)
        
        ax.scatter(x_data, y_data, alpha=0.7, s=100, color='#2ecc71')
        ax.set_title(title, fontsize=font_size + 4, fontweight='bold', fontfamily='NanumGothic', pad=20)
        ax.set_xlabel(x_col, fontsize=font_size, fontfamily='NanumGothic', labelpad=10)
        ax.set_ylabel(y_col, fontsize=font_size, fontfamily='NanumGothic', labelpad=10)
        
        ax.grid(True, alpha=0.3, zorder=0)
        ax.tick_params(axis='x', labelsize=font_size-1)
        ax.tick_params(axis='y', labelsize=font_size-1)
    
    def _render_histogram_chart(self, ax, df, title, font_size):
        """히스토그램 렌더링"""
        y_col = df.columns[1]

        # 축 데이터 처리
        y_data = self._process_axis_data(df[y_col], is_x_axis=False).dropna()
        
        if len(y_data) == 0:
            ax.text(0.5, 0.5, '수치 데이터가 없습니다', ha='center', va='center',
                   transform=ax.transAxes, fontfamily='NanumGothic')
            return
        
        ax.hist(y_data, bins=min(len(y_data)//2 + 1, 20), alpha=0.7, color='#9b59b6', edgecolor='black')
        ax.set_title(title, fontsize=font_size + 4, fontweight='bold', fontfamily='NanumGothic', pad=20)
        ax.set_xlabel(y_col, fontsize=font_size, fontfamily='NanumGothic', labelpad=10)
        ax.set_ylabel('빈도', fontsize=font_size, fontfamily='NanumGothic', labelpad=10)
        
        ax.grid(True, alpha=0.3, zorder=0)
        ax.tick_params(axis='x', labelsize=font_size-1)
        ax.tick_params(axis='y', labelsize=font_size-1)
    
    def parse_chart_data(self, chart_data: str) -> Dict[str, Any]:
        """차트 데이터 파싱 (차트 타입, 제목, CSV 데이터 분리)"""
        try:
            lines = chart_data.strip().split('\n')

            chart_type = "bar"  # 기본값
            title = "차트"  # 기본값
            csv_lines = []

            for line in lines:
                line = line.strip()
                if not line:  # 빈 라인 건너뛰기
                    continue
                if line.startswith('#CHART_TYPE:'):
                    chart_type = line.replace('#CHART_TYPE:', '').strip().lower()
                elif line.startswith('#TITLE:'):
                    title = line.replace('#TITLE:', '').strip()
                elif line.startswith('#') or line.startswith('```'):
                    # 주석이나 마크다운 코드 블록 건너뛰기
                    continue
                elif ',' in line or '\t' in line or '|' in line:
                    # CSV, TSV, 또는 마크다운 테이블 데이터
                    csv_lines.append(line)
                elif len(line.split()) >= 2:
                    # 공백으로 구분된 데이터
                    csv_lines.append(line.replace(' ', ','))  # 공백을 콤마로 변환

            if not csv_lines:
                # 데이터가 없으면 전체 텍스트를 분석하여 구조화 데이터 추출 시도
                logger.warning("CSV 형식 데이터를 찾을 수 없음. 전체 텍스트에서 데이터 추출 시도")
                csv_lines = self._extract_data_from_text(chart_data)
                if not csv_lines:
                    raise ValueError("CSV 데이터를 찾을 수 없습니다.")
            
            csv_data = '\n'.join(csv_lines)
            
            # DataFrame 생성
            df = pd.read_csv(
                io.StringIO(csv_data),
                na_values=['', 'nan', 'NaN', 'NULL', 'null'],
                keep_default_na=False,
                on_bad_lines='skip',
                skipinitialspace=True,
                dtype=str
            )
            df = df.fillna('')
                        
            return {
                "chart_type": chart_type,
                "title": title,
                "dataframe": df
            }
            
        except Exception as e:
            logger.error(f"차트 데이터 파싱 실패: {str(e)}")
            # 파싱 실패 시 기본 DataFrame 반환
            return {
                "chart_type": "bar",
                "title": "차트 (데이터 파싱 실패)",
                "dataframe": pd.DataFrame({'오류': [str(e)], '값': [0]})
            }
    
    def validate_chart_data(self, chart_data: str) -> Tuple[bool, str]:
        """차트 데이터 유효성 검증"""
        try:
            chart_info = self.parse_chart_data(chart_data)
            df = chart_info["dataframe"]
            chart_type = chart_info["chart_type"]

            if df.empty:
                return False, "차트 데이터가 비어있습니다."

            if len(df.columns) < 2:
                # 컬럼이 부족한 경우 경고하지만 계속 진행
                logger.warning("컬럼이 2개 미만입니다. 기본 차트로 진행합니다.")
                return True, f"기본 차트 데이터: {chart_type} 차트, {len(df)}행 x {len(df.columns)}열"

            if len(df) < 1:
                return False, "최소 1개 이상의 데이터 행이 필요합니다."

            # 차트 타입별 검증 (관대하게)
            if chart_type in ["bar", "line", "scatter", "histogram"] and len(df.columns) >= 2:
                # 두 번째 컬럼에 수치 데이터가 있는지 확인
                y_col = df.columns[1]
                numeric_count = pd.to_numeric(df[y_col], errors='coerce').count()
                if numeric_count == 0:
                    logger.warning(f"{chart_type} 차트에 수치 데이터가 없습니다. 텍스트로 표시합니다.")

            return True, f"유효한 차트 데이터: {chart_type} 차트, {len(df)}행 x {len(df.columns)}열"

        except Exception as e:
            # 검증 실패해도 기본 차트로 진행
            logger.warning(f"차트 데이터 검증 경고: {str(e)}. 기본 차트로 진행합니다.")
            return True, f"기본 차트 생성 (검증 경고: {str(e)})"

    def _extract_data_from_text(self, text: str) -> list:
        """텍스트에서 구조화된 데이터 추출"""
        lines = []
        text_lines = text.strip().split('\n')

        for line in text_lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('```'):
                continue

            # 마크다운 테이블 감지
            if '|' in line and line.count('|') >= 2:
                # | 제거하고 콤마로 변환
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 2:
                    lines.append(','.join(parts))
            # 탭 구분
            elif '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    lines.append(','.join([p.strip() for p in parts]))
            # 공백 구분 (연속된 공백 2개 이상)
            elif len(line.split()) >= 2:
                parts = line.split()
                if len(parts) >= 2:
                    lines.append(','.join(parts))

        return lines
    
    async def render_chart_auto(
        self,
        chart_data: str,
        output_path: str,
        style_options: Dict[str, Any] = None
    ) -> str:
        """자동 차트 렌더링 - 단일 차트만 지원"""

        options = style_options or {}
        renderer = options.get("renderer", "matplotlib")  # 기본값: matplotlib

        try:
            # 다중 차트 구분자가 있다면 첫 번째 차트만 사용
            if "===CHART_SEPARATOR===" in chart_data:
                logger.info("다중 차트 데이터 감지, 첫 번째 차트만 사용")
                chart_sections = chart_data.split("===CHART_SEPARATOR===")
                chart_data = chart_sections[0].strip()  # 첫 번째 차트만 사용

            # 단일 차트 렌더링
            if renderer == "matplotlib":
                return await self.render_chart_matplotlib(chart_data, output_path, style_options)
            else:
                # 기본값으로 matplotlib 사용
                return await self.render_chart_matplotlib(chart_data, output_path, style_options)

        except Exception as e:
            logger.error(f"{renderer} 차트 렌더링 실패: {str(e)}")
            raise