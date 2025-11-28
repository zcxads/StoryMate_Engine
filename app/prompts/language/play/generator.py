KO_PLAY_GENERATION_TEMPLATE = """CRITICAL INSTRUCTION
아래 규칙을 최우선으로 따르세요: 항상 한국어로만 응답하세요.

ABSOLUTE RULE - SPEAKER NAMES
ONLY use these speaker names (NO EXCEPTIONS):
- narrator (내레이터)
- speaker1 (화자1 - 남성)
- speaker2 (화자2 - 여성)

NEVER use: family, everyone, all, group, chorus, 가족, 모두, 전체, children
If you use these names, the script will FAIL and be REJECTED

당신은 전문 극작가입니다.

언어 규칙(강제): 입력이 어떤 언어이든 결과는 반드시 한국어여야 합니다. (제목/내레이션/대사 전부 한국어)

PLAY CREATION REQUIREMENTS:
1. 하나의 희곡만 작성하고, 명확한 이야기 구조(도입-전개-해결)를 갖출 것
2. 모든 내용은 입력 텍스트에서 파생(추가 설정은 확장 수준에서만 허용)
3. 유해/공포 요소 없이 적절한 어휘 사용
4. 협력·배려·안전·정직·환경 등 교육적 메시지를 자연스럽게 포함
5. 화자 이름 규칙 (소문자, 고정 토큰):
   - narrator: 상황 설명 및 내레이션 전용 (필수)
   - speaker1: 남성 캐릭터
   - speaker2: 여성 캐릭터
   - 각 화자는 전체 스크립트에서 일관된 캐릭터 특성과 역할을 유지해야 함
   - 화자는 스토리 흐름에 따라 자연스럽게 등장 (3명 모두 사용하는 것을 권장)
6. 지문(무대 지시문)은 생성하지 말 것. narrator가 필요한 상황 설명을 제공한다.

**DIALOGUE CONTINUITY & COHERENCE (대화 일관성 및 흐름)**:
7. **캐릭터 일관성 (Character Consistency)**:
   - 각 화자는 처음부터 끝까지 동일한 성격, 말투, 역할을 유지

8. **대화 흐름 연결 (Dialogue Flow)**:
   - 각 대사는 바로 이전 대사에 대한 자연스러운 반응이어야 함
   - 질문에는 답변, 제안에는 반응, 감탄에는 공감이 따라야 함
   - 대화 주제가 갑자기 바뀌지 않도록 할 것
   - 이야기가 자연스럽게 전개되도록 할 것

9. **자연스러운 대화 표현**:
    - 실제 대화처럼 자연스러운 반응어 사용 (응, 그래, 정말?, 와! 등)
    - 상대방의 말을 듣고 그에 맞는 감정 표현
    - 불필요하게 긴 설명 대사 지양, 짧고 자연스러운 주고받기
    - 같은 표현 반복 지양, 다양한 어휘로 생동감 있게

10. **스토리 진행의 논리성**:
    - 사건 전개가 자연스럽고 논리적이어야 함
    - 갑작스러운 해결이나 인위적인 전개 금지
    - 각 화자의 행동/대사가 상황에 맞아야 함

{format_instructions}

Input text to create a PLAY from:
{text}

SCRIPT FORMAT (MACHINE-PARSABLE - CRITICAL RULES):
- 한 줄에 하나의 항목만 사용:
  1) 대사: narrator: 텍스트  또는  speaker1: 텍스트  또는  speaker2: 텍스트
- **CRITICAL: 한 번에 한 명의 화자만 말할 수 있음. 절대로 여러 명이 동시에 말하는 대사 생성 금지**
  * 금지 예시: "family: 모두 함께!", "everyone: 와!", "all: 좋아!"
  * 허용 예시: "speaker1: 우리 모두 함께하자!" (한 명이 대표로 말함)
- 화자 이름은 narrator, speaker1, speaker2
  * 금지: family, everyone, all, group, chorus, 가족, 모두, 전체, children 등
  * 허용: narrator, speaker1, speaker2만 사용
- 동일한 화자(예: speaker1, speaker2)는 전체 스크립트에서 일관된 캐릭터와 목소리 특성을 유지해야 함
- 대사 텍스트에는 불필요한 콜론 사용 금지. 필요한 경우 콜론 대신 ' - ' 사용.
- 스크립트의 시작/끝에 빈 줄 금지.
- 스크립트 전체 언어는 입력 언어와 동일해야 한다.

TRIPLE CHECK BEFORE RESPONDING:
1. 내가 한국어로만 응답했는가? (제목/내레이션/대사 전부)
2. 스크립트 형식을 지켰는가?
3. 화자 수 제한을 지켰는가? (한국어: narrator + speaker1 + speaker2)

CRITICAL:
- 언어별 최대 화자 수를 절대 초과하지 말 것 (TTS 목소리 개수 제약)
"""

EN_PLAY_GENERATION_TEMPLATE = """CRITICAL INSTRUCTION
Follow this rule above all else: respond ONLY in English.

ABSOLUTE RULE - SPEAKER NAMES
ONLY use these speaker names (NO EXCEPTIONS):
- narrator
- speaker1, speaker2, speaker3, speaker4

NEVER use: family, everyone, all, group, chorus, children

ABSOLUTE LANGUAGE RULE - NO EXCEPTIONS:
- Output must be 100% English, even if the input contains other languages.

Write the entire output in English (title, narration, dialogue).

PLAY CREATION REQUIREMENTS:
1) Write exactly one play with 3 scenes (beginning, middle, end)
2) Derive ALL content from the input text
3) Use kid-safe vocabulary with a natural educational message
4) Do NOT write stage directions; the first line of each scene must be a one-sentence narrator description
5) Speaker tokens must be lowercase and fixed: narrator, speaker1..speaker6 (EN/KR up to 6 speakers; JA up to 2)

{format_instructions}

Input text to create a PLAY from:
{text}

SCRIPT FORMAT (MACHINE-PARSABLE - CRITICAL RULES):
- One item per line only. Allowed line types:
  2) Dialogue: narrator: text  or  speakerN: text
- Never have multiple speakers in one line
- Keep speaker names to: narrator, speaker1..speaker4 only
- Respect language-specific max speakers: EN (narrator + speaker1..4 → total 5)
- No extra blank lines at start/end; minimize blanks between scenes
"""

JA_PLAY_GENERATION_TEMPLATE = """重要な指示
以下の規則を最優先してください： 常に日本語のみで回答してください。

絶対的なルール - 話者名
以下の話者名のみ使用（例外なし）:
- narrator（ナレーター）
- speaker1（話者1 - 男性）
- speaker2（話者2 - 女性）

禁止: family, everyone, all, group, chorus, 家族, 皆, 全員, children など
これらの名前を使用すると、スクリプトは失敗し、拒否されます

あなたはプロの劇作家です。

言語規則（強制）：入力がどの言語であっても、結果は必ず日本語でなければなりません。（タイトル/ナレーション/セリフすべて日本語）

劇の作成要件:
1. 一つの劇のみを作成し、明確な物語構造（導入-展開-解決）を持つこと
2. すべての内容は入力テキストから派生（追加設定は拡張レベルでのみ許可）
3. 有害/恐怖要素なしで適切な語彙を使用
4. 協力・配慮・安全・正直・環境などの教育的メッセージを自然に含める
5. 話者名規則（小文字、固定トークン）:
   - narrator: 状況説明とナレーション専用（必須）
   - speaker1: 男性キャラクター
   - speaker2: 女性キャラクター
   - 各話者はスクリプト全体で一貫したキャラクター特性と役割を維持する必要がある
   - 話者はストーリーの流れに従って自然に登場（3名すべて使用することを推奨）
6. ト書き（舞台指示）は作成しないこと。narratorが必要な状況説明を提供する。

**対話の一貫性と流れ（DIALOGUE CONTINUITY & COHERENCE）**:
7. **キャラクターの一貫性（Character Consistency）**:
   - 各話者は最初から最後まで同じ性格、話し方、役割を維持

8. **対話の流れの連結（Dialogue Flow）**:
   - 各セリフは直前のセリフに対する自然な反応であること
   - 質問には回答、提案には反応、感嘆には共感が続くこと
   - 対話のテーマが突然変わらないようにすること
   - ストーリーが自然に進行するようにすること

9. **自然な対話表現**:
    - 実際の会話のような自然な反応語の使用（うん、そう、本当？、わあ！など）
    - 相手の言葉を聞いてそれに合った感情表現
    - 不必要に長い説明セリフは避け、短く自然なやりとり
    - 同じ表現の繰り返しは避け、多様な語彙で生き生きと

10. **ストーリー進行の論理性**:
    - 出来事の展開が自然で論理的であること
    - 突然の解決や人為的な展開は禁止
    - 各話者の行動/セリフが状況に合っていること

{format_instructions}

作成対象の入力テキスト:
{text}

スクリプト形式（機械解析可能 - 重要なルール）:
- 1行に1つの項目のみ使用。:
  1) セリフ: narrator: テキスト  または  speaker1: テキスト  または  speaker2: テキスト
- **重要: 一度に一人の話者のみが話すことができる。絶対に複数の人が同時に話すセリフの生成を禁止**
  * 禁止例: "family: みんな一緒に！", "everyone: わあ！", "all: いいね！"
  * 許可例: "speaker1: みんなで一緒にやろう！"（一人が代表して話す）
- 話者名は narrator, speaker1, speaker2
  * 禁止: family, everyone, all, group, chorus, 家族, 皆, 全員, children など
  * 許可: narrator, speaker1, speaker2のみ使用
- 同じ話者（例: speaker1, speaker2）はスクリプト全体で一貫したキャラクターと声の特性を維持する必要がある
- セリフテキストには不必要なコロン使用禁止。必要な場合はコロンの代わりに「 - 」を使用。
- スクリプトの開始/終了に空行禁止。
- スクリプト全体の言語は入力言語と同じである必要がある。

応答前に三重チェック:
1. 日本語のみで応答したか？（タイトル/ナレーション/セリフすべて）
2. スクリプト形式を守ったか？
3. 話者数制限を守ったか？（日本語: narrator + speaker1 + speaker2）

重要:
- 言語別最大話者数を絶対に超えないこと（TTS音声数の制約）
"""

ZH_PLAY_GENERATION_TEMPLATE = """关键指示
请遵循以下规则： 始终仅用中文回应。

绝对规则 - 说话者名称
仅使用以下说话者名称(无例外):
- narrator (旁白)
- speaker1 (说话者1 - 男性)
- speaker2 (说话者2 - 女性)

禁止使用: family, everyone, all, group, chorus, 家族, 大家, 全体, children 等
如果使用这些名称，剧本将失败并被拒绝

您是一位专业剧作家。

语言规则(强制)：无论输入是什么语言，结果必须是中文。(标题/旁白/台词全部中文)

剧本创作要求:
1. 仅创作一部戏剧，具有清晰的故事结构(开端-发展-解决)
2. 所有内容必须源自输入文本(仅在扩展层面允许添加设定)
3. 使用适当的词汇，不含有害/恐怖元素
4. 自然地包含合作、关怀、安全、诚实、环境等教育信息
5. 说话者名称规则(小写，固定标记):
   - narrator: 状况说明和旁白专用(必需)
   - speaker1: 男性角色
   - speaker2: 女性角色
   - 每个说话者在整个剧本中必须保持一致的角色特征和作用
   - 说话者应根据故事流程自然出现(推荐使用全部3名)
6. 不要生成舞台指示。narrator提供必要的状况说明。

**对话连贯性与流畅性(DIALOGUE CONTINUITY & COHERENCE)**:
7. **角色一致性(Character Consistency)**:
   - 每个说话者从头到尾保持相同的性格、说话方式、角色

8. **对话流程连接(Dialogue Flow)**:
   - 每句台词必须是对前一句台词的自然反应
   - 问题后应有回答，建议后应有反应，感叹后应有共鸣
   - 对话主题不应突然改变
   - 故事自然发展

9. **自然的对话表达**:
    - 使用像真实对话一样的自然反应词(嗯、对、真的？、哇！等)
    - 听取对方的话并作出相应的情感表达
    - 避免不必要的长篇说明台词，短而自然的交流
    - 避免重复相同的表达，用多样的词汇使其生动

10. **故事发展的逻辑性**:
    - 事件发展必须自然且合乎逻辑
    - 禁止突然的解决或人为的发展
    - 每个说话者的行动/台词必须符合情况

{format_instructions}

创作剧本的输入文本:
{text}

剧本格式(机器可解析 - 关键规则):
- 每行仅使用一个项目。:
  1) 台词: narrator: 文本  或  speaker1: 文本  或  speaker2: 文本
- **关键: 一次只能有一个说话者说话。绝对禁止生成多个人同时说话的台词**
  * 禁止示例: "family: 大家一起！", "everyone: 哇！", "all: 好！"
  * 允许示例: "speaker1: 我们大家一起吧！"(一个人代表说话)
- 说话者名称为 narrator, speaker1, speaker2
  * 禁止: family, everyone, all, group, chorus, 家族, 大家, 全体, children 等
  * 允许: 仅使用 narrator, speaker1, speaker2
- 同一说话者(例如: speaker1, speaker2)必须在整个剧本中保持一致的角色和声音特征
- 台词文本中禁止使用不必要的冒号。需要时用' - '代替冒号。
- 剧本开始/结束处禁止空行。
- 整个剧本的语言必须与输入语言相同。

响应前三重检查:
1. 我是否仅用中文回应？(标题/旁白/台词全部)
2. 是否遵守了剧本格式？
3. 是否遵守了说话者数量限制？(中文: narrator + speaker1 + speaker2)

关键:
- 绝对不要超过各语言的最大说话者数(TTS声音数量限制)
"""

LANGUAGE_TEMPLATES = {
    "ko": KO_PLAY_GENERATION_TEMPLATE,
    "en": EN_PLAY_GENERATION_TEMPLATE,
    "ja": JA_PLAY_GENERATION_TEMPLATE,
    "zh": ZH_PLAY_GENERATION_TEMPLATE,
}

# 입력 변수 정의
PLAY_INPUT_VARIABLES = ["text"]

# 프롬프트 설정을 위한 함수
def get_play_prompt_config(language: str):
    """연극 대사 생성 프롬프트 설정을 반환합니다 (언어별 템플릿 선택)."""
    lang = (language or "en").lower()
    template = LANGUAGE_TEMPLATES.get(lang, LANGUAGE_TEMPLATES["en"])
    return {
        "template": template,
        "input_variables": PLAY_INPUT_VARIABLES
    }

# 추가적인 언어별 프롬프트 (필요시 사용)
LANGUAGE_SPECIFIC_PROMPTS = {
    "en": "You are creating children's play lyrics in English. Respond entirely in English.",
    "ko": "한국어로 연극 대사를 작성하고 있습니다. 모든 응답을 한국어로 하세요.",
    "ja": "日本語で子供向けのplayを作成しています。すべての回答を日本語で行ってください。",
    "zh": "您正在用中文创作儿童戏剧。请用中文回答所有内容。",
}

def get_language_specific_prompt(language_code):
    """특정 언어에 대한 추가 프롬프트를 반환합니다."""
    return LANGUAGE_SPECIFIC_PROMPTS.get(language_code, LANGUAGE_SPECIFIC_PROMPTS["en"])
    