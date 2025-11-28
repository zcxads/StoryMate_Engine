"""표 시각화 언어별 프롬프트"""

# 한국어 프롬프트
TABLE_PROMPT_KO = """주어진 문서에서 추출된 구조화된 데이터를 정확히 그대로 CSV 표로 변환하고, 적절한 제목을 생성해주세요.

핵심 요구사항:
1. **반드시 문서에 명시된 정보만 사용** - 추가 계산이나 새로운 컬럼 생성 절대 금지
2. 문서의 구조 그대로 반영
3. 빈 셀은 절대 허용하지 않음 (정보가 없으면 "-" 명시)
4. 첫 번째 줄은 명확한 열 헤더(컬럼명)
5. 각 행은 완전한 데이터 세트로 구성

**출력 형식 (JSON)**:
```json
{
  "title": "표의 내용을 설명하는 간결한 제목",
  "csv_data": "컬럼1,컬럼2\\n데이터1,데이터2\\n..."
}
```

**절대 금지**:
- 문서에 없는 모든 추가 컬럼 생성 금지
- 계산, 추정, 예측 금지"""

# 영어 프롬프트
TABLE_PROMPT_EN = """Convert the structured data extracted from the document into a CSV table exactly as is, and generate an appropriate title.

Core Requirements:
1. **Use only information explicitly stated in the document** - Absolutely no additional calculations or new columns
2. Reflect the document structure as is
3. No empty cells allowed (use "-" if information is missing)
4. First line: Clear column headers
5. Each row: Complete data set

**Output Format (JSON)**:
```json
{
  "title": "Concise title describing the table content",
  "csv_data": "Column1,Column2\\nData1,Data2\\n..."
}
```

**Strictly Prohibited**:
- Creating any additional columns not in the document
- Calculations, estimations, predictions"""

# 일본어 프롬프트
TABLE_PROMPT_JA = """文書から抽出された構造化データを正確にそのままCSV表に変換し、適切なタイトルを生成してください。

核心要件:
1. **文書に明示された情報のみ使用** - 追加計算や新しい列の作成は絶対禁止
2. 文書の構造をそのまま反映
3. 空セルは絶対に許可しない（情報がない場合は「-」を明示）
4. 最初の行: 明確な列ヘッダー
5. 各行: 完全なデータセット

**出力形式 (JSON)**:
```json
{
  "title": "表の内容を説明する簡潔なタイトル",
  "csv_data": "列1,列2\\nデータ1,データ2\\n..."
}
```

**絶対禁止**:
- 文書にないすべての追加列の作成禁止
- 計算、推定、予測禁止"""

# 중국어 프롬프트
TABLE_PROMPT_ZH = """将从文档中提取的结构化数据准确地转换为CSV表格，并生成适当的标题。

核心要求:
1. **仅使用文档中明确说明的信息** - 绝对禁止额外计算或创建新列
2. 准确反映文档结构
3. 绝对不允许空单元格（如果没有信息，请标明"-"）
4. 第一行: 明确的列标题
5. 每行: 完整的数据集

**输出格式 (JSON)**:
```json
{
  "title": "描述表格内容的简洁标题",
  "csv_data": "列1,列2\\n数据1,数据2\\n..."
}
```

**严格禁止**:
- 创建文档中没有的所有额外列
- 计算、估算、预测"""


def get_table_prompt(lang_code: str = 'ko') -> str:
    """언어 코드에 따라 적절한 표 프롬프트 반환"""
    prompts = {
        'ko': TABLE_PROMPT_KO,
        'en': TABLE_PROMPT_EN,
        'ja': TABLE_PROMPT_JA,
        'zh': TABLE_PROMPT_ZH,
        'zh-CN': TABLE_PROMPT_ZH,
        'zh-TW': TABLE_PROMPT_ZH,
    }
    return prompts.get(lang_code, TABLE_PROMPT_EN)  # 기본값: 영어
