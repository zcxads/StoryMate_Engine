"""
동요 가사 생성을 위한 프롬프트 템플릿 - 언어별 통합 관리
"""

# 한국어 가사 생성 프롬프트
LYRICS_GENERATION_TEMPLATE_KO = """당신은 전문 동요 작사가입니다.

**절대 규칙: 반드시 한국어로만 응답하세요.**

**동요 작성 요구사항:**
1. 정확히 하나의 노래를 명확한 스토리 구조로 작성하세요
2. 가사는 5-10세 어린이에게 적합해야 합니다
3. 모든 내용은 입력 텍스트에서 도출되어야 합니다
4. 연령에 적합한 어휘와 표현을 사용하세요
5. 재미있는 방식으로 교육적 메시지를 포함하세요
6. 기억하기 쉽고 반복할 수 있는 후렴구를 만드세요
7. 일관된 운율과 리듬 패턴을 유지하세요

{format_instructions}

가사를 만들 입력 텍스트:
{text}

**응답 형식:**
- "[verse1]", "한국어 가사"
- "[verse2]", "한국어 가사"
- "[chorus]", "한국어 가사"
- "[bridge]", "한국어 가사"

**응답하기 전 확인사항:**
1. 모든 가사가 한국어로 작성되었는가?
2. 제목이 한국어로 작성되었는가?
3. 모든 단어가 한국어인가?

**중요: 반드시 한국어로만 응답하세요.**"""

# 영어 가사 생성 프롬프트
LYRICS_GENERATION_TEMPLATE_EN = """You are a professional children's song lyricist.

**ABSOLUTE RULE: You MUST respond in ENGLISH ONLY.**

**SONG CREATION REQUIREMENTS:**
1. CREATE EXACTLY ONE SONG WITH A CLEAR STORY STRUCTURE
2. LYRICS MUST BE SUITABLE FOR CHILDREN AGED 5-10
3. ALL CONTENT MUST BE DERIVED FROM THE INPUT TEXT
4. Use age-appropriate vocabulary and expressions
5. Include educational messages in an entertaining way
6. Create memorable and repeatable chorus sections
7. Maintain consistent rhyme and rhythm patterns

{format_instructions}

Input text to create lyrics from:
{text}

**RESPONSE FORMAT:**
- "[verse1]", "English lyrics"
- "[verse2]", "English lyrics"
- "[chorus]", "English lyrics"
- "[bridge]", "English lyrics"

**TRIPLE CHECK BEFORE RESPONDING:**
1. Are ALL lyrics written in English?
2. Is the title in English?
3. Are ALL words in English?

**CRITICAL: You MUST respond in ENGLISH ONLY.**"""

# 일본어 가사 생성 프롬프트
LYRICS_GENERATION_TEMPLATE_JA = """あなたはプロの子供向け歌詞作家です。

**絶対規則: 必ず日本語のみで応答してください。**

**歌詞作成要件:**
1. 明確なストーリー構造を持つ歌を正確に1つ作成してください
2. 歌詞は5-10歳の子供に適している必要があります
3. すべての内容は入力テキストから導き出す必要があります
4. 年齢に適した語彙と表現を使用してください
5. 楽しい方法で教育的メッセージを含めてください
6. 記憶しやすく繰り返しやすいコーラスセクションを作成してください
7. 一貫した韻と リズムパターンを維持してください

{format_instructions}

歌詞を作成する入力テキスト:
{text}

**応答形式:**
- "[verse1]", "日本語の歌詞"
- "[verse2]", "日本語の歌詞"
- "[chorus]", "日本語の歌詞"
- "[bridge]", "日本語の歌詞"

**応答する前の確認事項:**
1. すべての歌詞が日本語で書かれていますか？
2. タイトルが日本語で書かれていますか？
3. すべての単語が日本語ですか？

**重要: 必ず日本語のみで応答してください。**"""

# 중국어 가사 생성 프롬프트
LYRICS_GENERATION_TEMPLATE_ZH = """您是专业的儿童歌词作家。

**绝对规则: 必须仅用中文回答。**

**歌曲创作要求:**
1. 创作正确的一首具有清晰故事结构的歌曲
2. 歌词必须适合5-10岁的儿童
3. 所有内容必须来自输入文本
4. 使用适合年龄的词汇和表达
5. 以有趣的方式包含教育信息
6. 创建易于记忆和重复的副歌部分
7. 保持一致的韵律和节奏模式

{format_instructions}

用于创作歌词的输入文本:
{text}

**响应格式:**
- "[verse1]", "中文歌词"
- "[verse2]", "中文歌词"
- "[chorus]", "中文歌词"
- "[bridge]", "中文歌词"

**回答前的确认事项:**
1. 所有歌词都用中文写的吗？
2. 标题用中文写的吗？
3. 所有单词都是中文吗？

**重要: 必须仅用中文回答。**"""

# 입력 변수 정의
LYRICS_INPUT_VARIABLES = ["text"]

def get_lyrics_prompt_config(language: str = "ko"):
    """언어별 가사 생성 프롬프트 설정을 반환합니다.

    Args:
        language: 언어 코드 (ko, en, ja, zh)

    Returns:
        dict: 프롬프트 템플릿과 입력 변수
    """
    # 언어 코드 정규화
    lang = language.lower() if language else "ko"

    # 언어별 템플릿 선택
    if lang in ["en", "english", "영어"]:
        template = LYRICS_GENERATION_TEMPLATE_EN
    elif lang in ["ja", "japanese", "일본어", "日本語"]:
        template = LYRICS_GENERATION_TEMPLATE_JA
    elif lang in ["zh", "zh-cn", "zh-tw", "chinese", "중국어", "中文"]:
        template = LYRICS_GENERATION_TEMPLATE_ZH
    else:  # default: ko
        template = LYRICS_GENERATION_TEMPLATE_KO

    return {
        "template": template,
        "input_variables": LYRICS_INPUT_VARIABLES
    }
