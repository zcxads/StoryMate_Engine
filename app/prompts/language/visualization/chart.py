"""차트 시각화 언어별 프롬프트"""

# 한국어 프롬프트
CHART_PROMPT_KO = """주어진 문서에서 추출된 구조화된 데이터를 차트 데이터 CSV 형태로 변환해주세요.

**스마트 차트 타입 자동 선택 규칙**:

1. 시계열/추세 데이터 → LINE 차트:
- 데이터가 시간(기간, 월, 연도) 같은 연속적인 흐름을 가짐
- 형식: #CHART_TYPE:line

2. 범주별 비교 데이터 → BAR 차트:
- 데이터가 서로 다른 범주(지역, 주택유형, 그룹 등)로 구분됨
- 형식: #CHART_TYPE:bar

3. 비율/구성 데이터 → PIE 차트:
- 데이터가 전체 100% 중 일부 비율을 표현할 수 있음
- 형식: #CHART_TYPE:pie

핵심 요구사항:
1. **반드시 문서에 명시된 데이터만 사용** - 추가 계산이나 새로운 컬럼 생성 금지
2. 첫 번째 줄에 선택된 차트 타입을 명시: #CHART_TYPE:line|bar|pie
3. 두 번째 줄에 의미있는 차트 제목을 명시: #TITLE:데이터를 설명하는 제목
4. 세 번째 줄부터 CSV 데이터 (항목,값)
5. 모든 셀에 반드시 내용 입력 (빈 셀 금지)

**절대 금지사항**:
- 문서에 없는 새로운 컬럼 생성 금지
- 데이터 계산이나 추정 금지
- 문서에 없는 데이터 추가 금지"""

# 영어 프롬프트
CHART_PROMPT_EN = """Convert the structured data extracted from the document into CSV format for chart visualization.

**Smart Chart Type Selection Rules**:

1. Time-series/Trend Data → LINE Chart:
- Data has continuous flow over time (period, month, year)
- Format: #CHART_TYPE:line

2. Category Comparison Data → BAR Chart:
- Data is divided into different categories (region, type, group, etc.)
- Format: #CHART_TYPE:bar

3. Ratio/Composition Data → PIE Chart:
- Data can express proportions of a whole (100%)
- Format: #CHART_TYPE:pie

Core Requirements:
1. **Use only data explicitly stated in the document** - No additional calculations or new columns
2. First line: Specify chart type: #CHART_TYPE:line|bar|pie
3. Second line: Meaningful chart title: #TITLE:Title describing the data
4. From third line: CSV data (item,value)
5. All cells must have content (no empty cells)

**Strictly Prohibited**:
- Creating new columns not in the document
- Calculating or estimating data
- Adding data not in the document"""

# 일본어 프롬프트
CHART_PROMPT_JA = """文書から抽出された構造化データをチャートデータCSV形式に変換してください。

**スマートチャートタイプ自動選択ルール**:

1. 時系列/トレンドデータ → LINEチャート:
- データが時間（期間、月、年）のような連続的な流れを持つ
- 形式: #CHART_TYPE:line

2. カテゴリ別比較データ → BARチャート:
- データが異なるカテゴリ（地域、タイプ、グループなど）に分かれている
- 形式: #CHART_TYPE:bar

3. 比率/構成データ → PIEチャート:
- データが全体の100%の一部の比率を表現できる
- 形式: #CHART_TYPE:pie

核心要件:
1. **文書に明示されたデータのみ使用** - 追加計算や新しい列の作成禁止
2. 最初の行: チャートタイプを指定: #CHART_TYPE:line|bar|pie
3. 2行目: 意味のあるチャートタイトル: #TITLE:データを説明するタイトル
4. 3行目以降: CSVデータ (項目,値)
5. すべてのセルに必ず内容を入力 (空セル禁止)

**絶対禁止事項**:
- 文書にない新しい列の作成禁止
- データの計算や推定禁止
- 文書にないデータの追加禁止"""

# 중국어 프롬프트
CHART_PROMPT_ZH = """将从文档中提取的结构化数据转换为图表数据CSV格式。

**智能图表类型自动选择规则**:

1. 时间序列/趋势数据 → LINE图表:
- 数据具有时间（期间、月份、年份）等连续流动
- 格式: #CHART_TYPE:line

2. 类别比较数据 → BAR图表:
- 数据分为不同类别（地区、类型、组等）
- 格式: #CHART_TYPE:bar

3. 比例/组成数据 → PIE图表:
- 数据可以表示整体100%的部分比例
- 格式: #CHART_TYPE:pie

核心要求:
1. **仅使用文档中明确说明的数据** - 禁止额外计算或创建新列
2. 第一行: 指定图表类型: #CHART_TYPE:line|bar|pie
3. 第二行: 有意义的图表标题: #TITLE:描述数据的标题
4. 第三行起: CSV数据 (项目,值)
5. 所有单元格必须有内容 (禁止空单元格)

**严格禁止**:
- 创建文档中没有的新列
- 计算或估算数据
- 添加文档中没有的数据"""


def get_chart_prompt(lang_code: str = 'ko') -> str:
    """언어 코드에 따라 적절한 차트 프롬프트 반환"""
    prompts = {
        'ko': CHART_PROMPT_KO,
        'en': CHART_PROMPT_EN,
        'ja': CHART_PROMPT_JA,
        'zh': CHART_PROMPT_ZH,
        'zh-CN': CHART_PROMPT_ZH,
        'zh-TW': CHART_PROMPT_ZH,
    }
    return prompts.get(lang_code, CHART_PROMPT_EN)  # 기본값: 영어
