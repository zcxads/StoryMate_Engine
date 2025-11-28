"""
유사 문제 생성 프롬프트 템플릿
"""

# 한국어 유사 문제 생성 템플릿
SIMILAR_QUIZ_GENERATION_TEMPLATE_KO = """당신은 교육 전문가입니다. 업로드된 이미지를 분석하여 다음 작업을 수행해주세요:

**중요 전제조건**:
- 이미지에 정확히 **1문제만** 있어야 합니다
- 문제가 불완전하거나 일부가 잘려있으면 안 됩니다
- 위 조건을 만족하지 않으면 JSON을 생성하지 말고 에러 메시지만 텍스트로 반환하세요:
  * 1문제보다 많은 경우: "한 문제만 찍어서 업로드해주세요."
  * 문제가 불완전하거나 잘려있는 경우: "문제가 불완전하거나 일부가 잘려있어 분석할 수 없습니다."

**정확히 1문제가 있는 경우**: 그 문제와 유사한 새로운 문제를 생성
   - **문제 유형 판단**: 업로드된 문제가 객관식인지 주관식인지 자동으로 판단
     * 객관식 문제: 선택지가 있는 문제 (OX, 다지선다 등)
     * 주관식 문제: 선택지가 없고 답을 직접 작성하는 문제
   - **도형/그림 문제 처리**:
     * 원본 문제에 도형, 그래프, 차트, 그림 등이 포함되어 있다면
     * 해당 시각적 요소의 핵심 개념만 추출하여 텍스트 기반 문제로 변환
     * 예: 삼각형 넓이 구하기 → 구체적인 수치가 주어진 텍스트 문제로 변환
     * 예: 그래프 해석 → 표나 수치 데이터 해석 문제로 변환
   - **동일한 유형으로 생성**: 원본과 같은 유형의 유사 문제 생성 (단, 텍스트 기반으로 변환)
   - **같은 난이도 유지**: 원본 문제와 유사한 난이도
   - **다른 소재나 상황으로 변경**: 새로운 내용이지만 비슷한 구조
   - **논리적 검증 필수**:
     * 생성된 문제의 조건들이 논리적으로 일관성이 있는지 확인
     * 제시된 데이터로 정답을 도출할 수 있는지 검증
     * 수학 문제의 경우 계산 과정과 결과를 재검토
     * 객관식 문제의 경우 정답 외의 선택지가 명확히 오답인지 확인

**응답 형식** (JSON):
```json
{
    "question": "생성된 유사 문제",
    "options": ["1: 선택지1", "2: 선택지2", "3: 선택지3", "4: 선택지4"]
}
```

**options 필드 규칙**:
- **객관식 문제**: 선택지 배열 제공 (예: ["1: 가", "2: 나", "3: 다", "4: 라"])
- **주관식 문제**: 빈 배열 제공 (예: [])

**중요**: JSON 형식으로만 응답하며, 다른 설명은 추가하지 마세요."""

# 영어 유사 문제 생성 템플릿
SIMILAR_QUIZ_GENERATION_TEMPLATE_EN = """You are an education expert. Please analyze the uploaded image and perform the following tasks:

**Important Prerequisites**:
- The image must contain exactly **1 problem only**
- The problem must not be incomplete or cut off
- If these conditions are not met, do NOT generate JSON. Instead, return only an error message as plain text:
  * If more than 1 problem: "Please upload an image with only one problem."
  * If the problem is incomplete or cut off: "The problem is incomplete or partially cut off and cannot be analyzed."

**If there is exactly 1 problem**: Generate a new similar problem
   - **Determine problem type**: Automatically identify if the uploaded problem is multiple-choice or open-ended
     * Multiple-choice: Problems with given options (True/False, multiple choice, etc.)
     * Open-ended: Problems requiring written answers without given options
   - **Handle geometric/visual problems**:
     * If the original problem contains diagrams, graphs, charts, or visual elements
     * Extract only the core concept and convert to text-based problem format
     * Example: Triangle area calculation → Convert to text-based problem with specific numerical values
     * Example: Graph interpretation → Convert to table or numerical data interpretation problem
   - **Generate same type**: Create a similar problem of the same type as the original (but convert to text-based format)
   - **Maintain difficulty level**: Keep similar difficulty as the original problem
   - **Change content**: Use different materials or situations but similar structure
   - **Logical verification required**:
     * Verify that the conditions in the generated problem are logically consistent
     * Confirm that the correct answer can be derived from the provided data
     * For math problems, double-check calculation process and results
     * For multiple-choice problems, ensure incorrect options are clearly wrong

**Response Format** (JSON):
```json
{
    "question": "Generated similar problem",
    "options": ["1: Option1", "2: Option2", "3: Option3", "4: Option4"]
}
```

**Options field rules**:
- **Multiple-choice problems**: Provide options array (e.g., ["1: A", "2: B", "3: C", "4: D"])
- **Open-ended problems**: Provide empty array (e.g., [])

**Important**: Respond only in JSON format without additional explanations."""

# 일본어 유사 문제 생성 템플릿
SIMILAR_QUIZ_GENERATION_TEMPLATE_JA = """あなたは教育専門家です。アップロードされた画像を分析して、次の作業を実行してください：

**重要な前提条件**:
- 画像には正確に**1問だけ**含まれている必要があります
- 問題が不完全または切れていてはいけません
- これらの条件を満たしていない場合、JSONを生成せず、エラーメッセージのみをプレーンテキストで返してください：
  * 1問より多い場合: "1問だけ撮影してアップロードしてください。"
  * 問題が不完全または切れている場合: "問題が不完全または一部が切れているため解答できません。"

**正確に1問がある場合**: その問題と類似した新しい問題を生成
   - **問題タイプの判定**: アップロードされた問題が選択式か記述式かを自動判定
     * 選択式問題: 選択肢がある問題（○×、多肢選択など）
     * 記述式問題: 選択肢がなく答えを直接書く問題
   - **図形/画像問題の処理**:
     * 元の問題に図形、グラフ、チャート、画像などが含まれている場合
     * その視覚的要素の核心概念のみを抽出してテキストベースの問題に変換
     * 例: 三角形の面積を求める → 具体的な数値が与えられたテキスト問題に変換
     * 例: グラフ解釈 → 表や数値データ解釈問題に変換
   - **同じタイプで生成**: 元の問題と同じタイプの類似問題を生成（ただし、テキストベースに変換）
   - **同じ難易度を維持**: 元の問題と類似した難易度
   - **異なる素材や状況に変更**: 新しい内容だが類似した構造
   - **論理的検証必須**:
     * 生成された問題の条件が論理的に一貫性があるか確認
     * 提示されたデータで正解を導出できるか検証
     * 数学問題の場合、計算過程と結果を再検討
     * 選択式問題の場合、正解以外の選択肢が明確に不正解か確認

**応答形式** (JSON):
```json
{
    "question": "生成された類似問題",
    "options": ["1: 選択肢1", "2: 選択肢2", "3: 選択肢3", "4: 選択肢4"]
}
```

**options フィールド規則**:
- **選択式問題**: 選択肢配列を提供（例: ["1: あ", "2: い", "3: う", "4: え"]）
- **記述式問題**: 空配列を提供（例: []）

**重要**: JSON形式でのみ応答し、他の説明は追加しないでください。"""

# 중국어 유사 문제 생성 템플릿
SIMILAR_QUIZ_GENERATION_TEMPLATE_ZH = """您是一位教育专家。请分析上传的图像并执行以下任务：

**重要前提条件**:
- 图像中必须恰好包含**1个问题**
- 问题不能不完整或被截断
- 如果不满足这些条件，请不要生成JSON，而是仅返回错误消息的纯文本：
  * 如果超过1个问题: "请上传只包含一个问题的图像。"
  * 如果问题不完整或被截断: "问题不完整或部分被截断，无法分析。"

**如果恰好有1个问题**: 生成一个新的类似问题
   - **判断问题类型**: 自动识别上传的问题是选择题还是主观题
     * 选择题: 有给定选项的问题（判断题、多项选择等）
     * 主观题: 需要书面答案而没有给定选项的问题
   - **处理几何/视觉问题**:
     * 如果原始问题包含图表、图形、图表或视觉元素
     * 仅提取核心概念并转换为基于文本的问题格式
     * 例: 三角形面积计算 → 转换为具有特定数值的基于文本的问题
     * 例: 图表解释 → 转换为表格或数值数据解释问题
   - **生成相同类型**: 创建与原始问题相同类型的类似问题（但转换为基于文本的格式）
   - **保持难度水平**: 保持与原始问题相似的难度
   - **更改内容**: 使用不同的材料或情况但相似的结构
   - **需要逻辑验证**:
     * 验证生成问题中的条件在逻辑上是否一致
     * 确认可以从提供的数据中得出正确答案
     * 对于数学问题，仔细检查计算过程和结果
     * 对于选择题，确保错误选项明显错误

**响应格式** (JSON):
```json
{
    "question": "生成的类似问题",
    "options": ["1: 选项1", "2: 选项2", "3: 选项3", "4: 选项4"]
}
```

**options 字段规则**:
- **选择题**: 提供选项数组（例: ["1: A", "2: B", "3: C", "4: D"]）
- **主观题**: 提供空数组（例: []）

**重要**: 仅以JSON格式响应，不要添加额外说明。"""

# 언어별 템플릿 매핑
LANGUAGE_TEMPLATES = {
    "ko": SIMILAR_QUIZ_GENERATION_TEMPLATE_KO,
    "en": SIMILAR_QUIZ_GENERATION_TEMPLATE_EN,
    "ja": SIMILAR_QUIZ_GENERATION_TEMPLATE_JA,
    "zh": SIMILAR_QUIZ_GENERATION_TEMPLATE_ZH,
    "zh-CN": SIMILAR_QUIZ_GENERATION_TEMPLATE_ZH,
    "zh-TW": SIMILAR_QUIZ_GENERATION_TEMPLATE_ZH,
}

def get_similar_quiz_prompt(language: str = "ko") -> str:
    """
    유사 문제 생성을 위한 프롬프트를 반환합니다.

    Args:
        language: 언어 코드 (ko, en, ja, zh)

    Returns:
        str: 해당 언어의 유사 문제 생성 프롬프트
    """
    return LANGUAGE_TEMPLATES.get(language, LANGUAGE_TEMPLATES["ko"])
