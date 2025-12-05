"""
손가락 인식 프롬프트 템플릿 - 언어별 통합 관리
"""

# 한국어 프롬프트
FINGER_DETECTION_PROMPT_KO = """이미지를 분석하기 전에 반드시 다음 질문에 답해주세요:

**필수 확인 질문: 이 이미지에 사람의 손가락이 보입니까?**

이미지를 자세히 보고 사람의 손가락 (특히 검지손가락)이 실제로 보이는지 확인하세요.

**환각 방지 중요 원칙:**
**절대로 이미지에 실제로 보이지 않는 텍스트나 단어를 만들어내지 마세요!**
**반드시 이미지에서 실제로 읽을 수 있는 텍스트만 검출하세요!**
**추측이나 상상으로 단어를 생성하는 것은 절대 금지입니다!**

**분석 순서:**

**단계 1: 이미지의 모든 텍스트를 먼저 추출**
- 이미지에서 실제로 보이는 모든 텍스트/단어를 먼저 확인하세요
- 텍스트가 전혀 없다면 → Case 2 (EMPTY_POINTING) 반환

**단계 2: 손가락 확인**
- 손가락이 보이지 않으면 → Case 1 (NO_FINGER) 반환

**단계 3: 손가락이 가리키는 텍스트 매칭**
- 단계 1에서 추출한 실제 텍스트 중에서만 선택
- 손가락이 가리키는 위치와 가장 가까운 텍스트 선택

**Case 1 - 손가락이 명확하게 보이지 않는 경우만 해당:**
{
    "status": "NO_FINGER",
    "message": "손가락을 인식할 수 없습니다. 명확하게 손가락으로 가리키는 이미지를 다시 업로드해주세요."
}
- **매우 엄격하게 판단**: 손가락이 조금이라도 보이면 이 케이스가 아닙니다
- 사람의 손가락이 전혀 보이지 않거나, 손가락인지 불명확한 경우만 해당

**Case 2 - 이미지에 읽을 수 있는 텍스트가 전혀 없는 경우:**
{
    "status": "EMPTY_POINTING",
    "message": "손가락을 인식할 수 없습니다. 명확하게 손가락으로 가리키는 이미지를 다시 업로드해주세요."
}
- **이미지를 스캔하여 실제로 읽을 수 있는 텍스트/단어가 있는지 확인**
- 텍스트가 전혀 없거나, 손가락이 빈 공간만 가리키는 경우만 해당
- **중요**: 텍스트가 없는데 단어를 만들어내지 마세요!

**Case 3 - 손가락이 보이고 이미지에 텍스트가 있는 경우:**

**핵심 원칙: 이미지에서 실제로 보이는 텍스트 중에서만 선택합니다.**

**정확한 분석 순서:**
1. **이미지의 모든 실제 텍스트를 먼저 추출** (매우 중요!)
   - 이 단계에서 추출된 텍스트만 사용 가능
   - 추출된 텍스트가 없으면 EMPTY_POINTING 반환

2. **손가락 끝(fingertip)의 정확한 픽셀 좌표를 식별**

3. **추출된 실제 텍스트 중에서 손가락과 가장 가까운 단어 선택**
   - **1순위**: 손가락 방향 연장선 상에 있으면서 손가락 끝에서 가까운 단어
   - **2순위**: 손가락 끝에서 매우 가까운(50픽셀 이내) 단어
   - 손가락 끝에서 150픽셀을 초과하는 단어는 선택하지 말 것

4. **검증 단계**
   - 선택한 단어가 실제로 이미지에 존재하는지 재확인
   - 손가락이 실제로 가리키는 방향에 있는지 확인
   - 손가락 끝에서 너무 멀지 않은지 확인 (150픽셀 이내)
   - 조건을 만족하면 해당 단어 검출, 만족하지 않으면 EMPTY_POINTING

**절대 규칙:**
- **이미지에 실제로 존재하지 않는 텍스트를 절대로 생성하지 마세요!**
- **반드시 이미지에서 읽을 수 있는 텍스트만 검출하세요!**
- **손가락 방향과 거리를 모두 고려하여 가장 적합한 단어를 선택**
- **손가락 방향 밖에 있는 단어는 가까워도 선택하지 말 것**
- **150픽셀을 초과하는 단어는 선택하지 말 것**
- **NO_FINGER와 EMPTY_POINTING은 매우 예외적인 케이스로만 사용**

분석 후 다음 JSON 형식으로 응답:
{
    "detected_word": "가리킨 정확한 단일 단어만",
    "is_meaningful": true,
    "meaning": "검출된 단어의 사전적 뜻만 간결하게 (반드시 한국어로)",
    "explanation": "해당 단어에 대한 자세한 설명 (문맥, 사용법, 예시, 어원 등 포함, 반드시 한국어로)"
}

**explanation 작성 시 절대 규칙 (매우 중요!):**
- **순수하게 detected_word 자체의 사전적 의미와 용법만 설명**
- **마치 국어사전이나 영어사전을 작성하듯이 그 단어만 설명**
- **"손가락", "가리키는", "가리킨", "이미지", "포인팅", "사진" 등의 메타 표현 절대 사용 금지**
- **올바른 예시: "가리킨" → "'가리키다'의 과거형으로, 손이나 물건으로 특정 대상을 지시하는 행위를 의미합니다. 예: 그는 지도에서 목적지를 가리켰다."**
- **금지 예시: "손가락이 가리킨 단어는...", "이미지에서 가리킨 부분은...", "포인팅한 텍스트는..."**

**최종 자기 검증 (반드시 수행!):**
응답하기 전에 스스로에게 질문하세요:
"내 explanation이 단어 자체를 사전처럼 설명하는가? 아니면 손가락/이미지 상황을 설명하는가?"
→ 만약 상황을 설명하고 있다면, 이는 환각입니다! 즉시 EMPTY_POINTING을 반환하세요!

**중요: detected_word는 원본 언어 그대로, meaning과 explanation은 반드시 한국어로 작성하세요.**

**절대 규칙:**
1. **모든 응답은 반드시 유효한 JSON 형식**이어야 합니다
2. JSON 외 다른 텍스트를 포함하지 마세요
3. **detected_word는 반드시 하나의 단어만** (공백 포함 절대 금지)
4. **문장이나 구문 검출 시 즉시 재분석** 하여 단일 단어만 추출"""

# 영어 프롬프트
FINGER_DETECTION_PROMPT_EN = """Before analyzing the image, please answer the following question:

**Required confirmation: Do you see a human finger in this image?**

Look carefully at the image to determine if a human finger (especially the index finger) is actually visible.

**CRITICAL ANTI-HALLUCINATION PRINCIPLES:**
**NEVER create or invent text/words that are NOT actually visible in the image!**
**ONLY detect text that you can actually READ in the image!**
**Creating words by guessing or imagination is ABSOLUTELY FORBIDDEN!**

**Analysis Steps:**

**Step 1: Extract ALL text from the image FIRST**
- Identify ALL actual text/words that are actually visible in the image
- If there is NO text at all → Return Case 2 (EMPTY_POINTING)

**Step 2: Check for finger**
- If no finger is visible → Return Case 1 (NO_FINGER)

**Step 3: Match finger to actual text**
- Select ONLY from the real text extracted in Step 1
- Choose the text closest to where the finger is pointing

**Case 1 - Finger is clearly NOT visible:**
{
    "status": "NO_FINGER",
    "message": "Cannot detect finger. Please upload image with clear finger pointing."
}
- **Very strict judgment**: If you can see even a slight finger, this is NOT this case
- Only applies when human finger is completely invisible or unclear

**Case 2 - Image has NO readable text at all:**
{
    "status": "EMPTY_POINTING",
    "message": "Cannot detect finger. Please upload image with clear finger pointing."
}
- **Scan the image to verify if there is any readable text/words**
- Only applies when there is no text, or finger points at empty space
- **CRITICAL**: If there's no text, do NOT invent words!

**Case 3 - Finger is visible AND image has text:**

**Core Principle: Select ONLY from text actually visible in the image.**

**Exact Analysis Steps:**
1. **Extract ALL actual text from the image FIRST** (VERY IMPORTANT!)
   - Only text extracted in this step can be used
   - If no text extracted, return EMPTY_POINTING

2. **Identify the exact pixel coordinates of the fingertip**

3. **Select the word closest to the finger from extracted real text**
   - **Priority 1**: Word on the finger direction extension line and close to fingertip
   - **Priority 2**: Word very close to fingertip (within 50 pixels)
   - Do not select words beyond 150 pixels from fingertip

4. **Verification Step**
   - Re-confirm the selected word actually EXISTS in the image
   - Confirm it is in the actual pointing direction
   - Confirm it is not too far from fingertip (within 150 pixels)
   - If conditions met, detect that word; otherwise EMPTY_POINTING

**Absolute Rules:**
- **NEVER generate text that does NOT exist in the image!**
- **ONLY detect text that you can actually READ in the image!**
- **Consider both finger direction and distance to select the most appropriate word**
- **Do not select words outside the finger direction even if close**
- **Do not select words beyond 150 pixels**
- **NO_FINGER and EMPTY_POINTING are only for exceptional cases**

Step 2: Judgment and Response

**Case A - Finger pointing at empty space**
Respond exactly in this format:
"EMPTY_POINTING: Please point at a word or object in the document."

**Case B - Finger pointing at meaningful content**
Respond in the following JSON format:
{
    "detected_word": "exact single word only",
    "is_meaningful": true or false (determine if the word is meaningful),
    "meaning": "dictionary definition only (MUST be in English)",
    "explanation": "detailed explanation (context, usage, examples, etymology, etc., MUST be in English)"
}

**Explanation Writing Rules (EXTREMELY IMPORTANT!):**
- **Explain ONLY the dictionary meaning and usage of detected_word itself**
- **Write as if you are writing a dictionary or encyclopedia entry for that word**
- **ABSOLUTELY FORBIDDEN to use meta expressions like "finger", "pointing", "pointed", "image", "photo", "picture"**
- **Correct example: "pointing" → "The present participle of 'point', meaning to indicate or direct attention to something with a finger or object. Example: She was pointing at the map."**
- **FORBIDDEN example: "The word the finger is pointing at...", "The text indicated in the image...", "What the finger pointed to..."**

**Final Self-Verification (MUST PERFORM!):**
Before responding, ask yourself:
"Is my explanation describing the word itself like a dictionary? Or is it describing the finger/image situation?"
→ If describing the situation, this is a hallucination! Return EMPTY_POINTING immediately!

**Important: detected_word should be in its original language, but meaning and explanation MUST be written in English.**

**Absolute Rules:**
1. **First, find** the human finger (index finger) in the image
2. **If no finger visible** do not analyze any content, immediately respond with "NO_FINGER"
3. **Only if finger clearly visible** analyze the pointing content
4. **detected_word MUST be only one word** (spaces absolutely forbidden)
5. **If sentence or phrase detected, immediately reanalyze** to extract only single word"""

# 일본어 프롬프트
FINGER_DETECTION_PROMPT_JA = """画像を分析する前に、必ず次の質問に答えてください:

**必須確認質問: この画像に人の指が見えますか?**

画像をよく見て、人の指(特に人差し指)が実際に見えるかどうかを確認してください。

**幻覚防止の重要原則:**
**画像に実際に見えないテキストや単語を絶対に作り出さないでください!**
**画像で実際に読めるテキストのみを検出してください!**
**推測や想像で単語を生成することは絶対禁止です!**

**分析手順:**

**ステップ1: 画像のすべてのテキストをまず抽出**
- 画像で実際に見えるすべてのテキスト/単語をまず確認してください
- テキストが全くなければ → ケース2 (EMPTY_POINTING) を返す

**ステップ2: 指の確認**
- 指が見えなければ → ケース1 (NO_FINGER) を返す

**ステップ3: 指が指している実際のテキストとマッチング**
- ステップ1で抽出した実際のテキストの中からのみ選択
- 指が指している位置に最も近いテキストを選択

**ケース1 - 指が明確に見えない場合のみ該当:**
{
    "status": "NO_FINGER",
    "message": "指を認識できません。指で指している画像を再度アップロードしてください。"
}
- **非常に厳格な判断**: 指が少しでも見えれば、このケースではありません
- 人の指が全く見えないか、指かどうか不明確な場合のみ該当

**ケース2 - 画像に読めるテキストが全くない場合:**
{
    "status": "EMPTY_POINTING",
    "message": "指を認識できません。指で指している画像を再度アップロードしてください。"
}
- **画像をスキャンして実際に読めるテキスト/単語があるか確認**
- テキストが全くないか、指が空白スペースのみを指している場合のみ該当
- **重要**: テキストがないのに単語を作り出さないでください!

**ケース3 - 指が見えて画像にテキストがある場合:**

**核心原則: 画像で実際に見えるテキストの中からのみ選択します。**

**正確な分析手順:**
1. **画像のすべての実際のテキストをまず抽出** (非常に重要!)
   - このステップで抽出されたテキストのみ使用可能
   - 抽出されたテキストがなければEMPTY_POINTINGを返す

2. **指先(fingertip)の正確なピクセル座標を識別**

3. **抽出された実際のテキストの中から指に最も近い単語を選択**
   - **優先順位1**: 指の方向延長線上にあり、指先から近い単語
   - **優先順位2**: 指先から非常に近い(50ピクセル以内)単語
   - 指先から150ピクセルを超える単語は選択しない

4. **検証ステップ**
   - 選択した単語が実際に画像に存在するか再確認
   - 指が実際に指している方向にあるか確認
   - 指先から遠すぎないか確認（150ピクセル以内）
   - 条件を満たせばその単語を検出、満たさなければEMPTY_POINTING

**絶対ルール:**
- **画像に実際に存在しないテキストを絶対に生成しないでください!**
- **画像で読めるテキストのみを検出してください!**
- **指の方向と距離の両方を考慮して最も適切な単語を選択**
- **指の方向外にある単語は近くても選択しない**
- **150ピクセルを超える単語は選択しない**
- **NO_FINGERとEMPTY_POINTINGは非常に例外的なケースのみ使用**

ステップ2: 指が見える場合の判断と応答

**ケースA - 指が空を指している場合**
正確にこの形式で応答:
"EMPTY_POINTING: ドキュメント内の単語またはオブジェクトを指してください。"

**ケースB - 指が意味のある内容を指している場合**
必ず次のJSON形式で応答:
{
    "detected_word": "指した正確な単一単語のみ",
    "is_meaningful": true または false（その単語が意味を持つかの判定）、
    "meaning": "検出された単語の辞書的意味のみ（必ず日本語で）",
    "explanation": "その単語に関する詳細な説明（文脈、使用法、例、語源などを含む、必ず日本語で）"
}

**explanation作成時の絶対ルール（非常に重要!):**
- **detected_word自体の純粋な辞書的意味と用法のみを説明**
- **まるで国語辞典や辞書を作成するようにその単語だけを説明**
- **「指」「指している」「指した」「画像」「写真」などのメタ表現は絶対使用禁止**
- **正しい例: "指した" → "『指す』の過去形で、手や物で特定の対象を示す行為を意味します。例: 彼は地図で目的地を指した。"**
- **禁止例: "指が指した単語は...", "画像で指した部分は...", "ポイントしたテキストは..."**

**最終自己検証（必ず実行!):**
応答する前に自分に質問してください:
"私のexplanationは単語自体を辞書のように説明していますか? それとも指/画像の状況を説明していますか?"
→ もし状況を説明している場合、これは幻覚です! 直ちにEMPTY_POINTINGを返してください!

**重要: detected_wordは元の言語そのまま、meaningとexplanationは必ず日本語で書いてください。**

**絶対ルール:**
1. **必ず最初に**画像から人の指(人差し指)を探してください
2. **指が見えない場合**内容分析は一切せず、すぐに「NO_FINGER」応答
3. **指が明確に見える場合のみ**指している内容を分析してください
4. **detected_wordは必ず1つの単語のみ**(スペース含有は絶対禁止)
5. **文またはフレーズ検出時はすぐに再分析**して単一単語のみを抽出"""

# 중국어 프롬프트
FINGER_DETECTION_PROMPT_ZH = """在分析图像之前，请务必回答以下问题:

**必须确认的问题: 这张图像中能看到人的手指吗?**

请仔细查看图像，确认是否能看到人的手指(特别是食指)。

**防止幻觉的重要原则:**
**绝对不要创造或编造图像中实际不存在的文本或单词!**
**只检测图像中实际可以阅读的文本!**
**绝对禁止通过猜测或想象生成单词!**

**分析步骤:**

**步骤1: 首先提取图像中的所有文本**
- 先确认图像中实际可见的所有文本/单词
- 如果完全没有文本 → 返回情况2 (EMPTY_POINTING)

**步骤2: 确认手指**
- 如果看不到手指 → 返回情况1 (NO_FINGER)

**步骤3: 将手指与实际文本匹配**
- 只从步骤1提取的实际文本中选择
- 选择最接近手指指向位置的文本

**情况1 - 手指明确不可见:**
{
    "status": "NO_FINGER",
    "message": "无法识别手指。请上传用手指指着的图像。"
}
- **非常严格的判断**: 如果能看到一点点手指，就不是这种情况
- 仅适用于完全看不到人的手指或手指不清楚的情况

**情况2 - 图像中完全没有可读文本:**
{
    "status": "EMPTY_POINTING",
    "message": "无法识别手指。请上传用手指指着的图像。"
}
- **扫描图像以确认是否有任何可读文本/单词**
- 仅适用于完全没有文本或手指只指向空白区域的情况
- **重要**: 没有文本时不要编造单词!

**情况3 - 手指可见且图像中有文本:**

**核心原则: 只从图像中实际可见的文本中选择。**

**准确的分析步骤:**
1. **首先提取图像中所有实际文本** (非常重要!)
   - 只能使用此步骤提取的文本
   - 如果没有提取到文本，返回EMPTY_POINTING

2. **识别指尖(fingertip)的精确像素坐标**

3. **从提取的实际文本中选择最接近手指的单词**
   - **优先级1**: 在手指方向延长线上且距离指尖近的单词
   - **优先级2**: 距离指尖非常近(50像素以内)的单词
   - 不要选择距离指尖超过150像素的单词

4. **验证步骤**
   - 再次确认所选单词确实存在于图像中
   - 确认是否在手指实际指向的方向
   - 确认距离指尖不太远（150像素以内）
   - 如果满足条件则检测该单词，否则EMPTY_POINTING

**绝对规则:**
- **绝对不要生成图像中不存在的文本!**
- **只检测图像中可以阅读的文本!**
- **同时考虑手指方向和距离来选择最合适的单词**
- **不要选择手指方向之外的单词，即使很近**
- **不要选择超过150像素的单词**
- **NO_FINGER和EMPTY_POINTING仅用于非常特殊的情况**

步骤2: 看到手指时的判断和响应

**情况A - 手指指向空中**
请按以下格式准确回应:
"EMPTY_POINTING: 请指向文档中的单词或对象。"

**情况B - 手指指向有意义的内容**
必须以以下JSON格式回应:
{
    "detected_word": "仅指向的确切单个单词",
    "is_meaningful": true 或 false（判断该词是否有意义）,
    "meaning": "仅检测到的单词的词典意义（必须用中文）",
    "explanation": "对该单词的详细说明（包括上下文、用法、例子、词源等，必须用中文）"
}

**explanation编写的绝对规则（非常重要!):**
- **仅解释detected_word本身的纯粹词典含义和用法**
- **就像编写词典或百科全书条目一样只解释该单词**
- **绝对禁止使用"手指"、"指着"、"指向"、"图像"、"照片"等元表达**
- **正确示例: "指着" → "'指'的进行时，意思是用手或物体指示特定对象的行为。例: 他指着地图上的目的地。"**
- **禁止示例: "手指指着的单词是...", "图像中指着的部分是...", "指向的文本是..."**

**最终自我验证（必须执行!):**
在回应之前问自己:
"我的explanation是在像词典一样解释单词本身吗? 还是在描述手指/图像的情况?"
→ 如果在描述情况，这是幻觉! 立即返回EMPTY_POINTING!

**重要: detected_word使用原始语言，meaning和explanation必须用中文书写。**

**绝对规则:**
1. **必须首先**在图像中查找人的手指(食指)
2. **如果看不到手指**，不要进行任何内容分析，立即"NO_FINGER"响应
3. **只有明确看到手指时**才分析指向的内容
4. **detected_word必须仅为一个单词**(绝对禁止包含空格)
5. **检测到句子或短语时立即重新分析**，仅提取单个单词"""


def get_finger_detection_prompt(language: str = "ko") -> str:
    """
    언어별 손가락 인식 프롬프트를 반환합니다.

    Args:
        language: 응답 언어 코드 (ko, en, ja, zh)

    Returns:
        str: 언어별 손가락 인식 프롬프트
    """
    # 언어 코드 정규화
    lang = language.lower() if language else "ko"

    # 언어별 프롬프트 선택
    if lang in ["en", "english", "영어"]:
        return FINGER_DETECTION_PROMPT_EN
    elif lang in ["ja", "japanese", "일본어", "日本語"]:
        return FINGER_DETECTION_PROMPT_JA
    elif lang in ["zh", "zh-cn", "zh-tw", "chinese", "중국어", "中文"]:
        return FINGER_DETECTION_PROMPT_ZH
    else:  # default: ko
        return FINGER_DETECTION_PROMPT_KO
