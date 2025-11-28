"""
Content Category - 컨텐츠 생성 가능성 분석 프롬프트
"""

def get_content_category_analysis_prompt(language: str) -> str:
    """컨텐츠 카테고리 분석용 프롬프트를 반환합니다."""
    
    prompts = {
        "ko": """당신은 문서 분석 및 컨텐츠 생성 가능성 판단 전문가입니다. 
주어진 텍스트를 분석하여 어떤 종류의 컨텐츠로 변환 가능한지 판단해주세요.

# 문서 타입 분류

다음 중 하나로 문서를 분류하세요:
- **lyrics**: 노래 가사 (운율, 후렴구, 감정적 표현 등이 특징)
- **news**: 뉴스 기사 (사실 전달, 육하원칙, 객관적 정보 등이 특징)  
- **script**: 대본/시나리오 (대화, 캐릭터, 상황 설명 등이 특징)
- **statistics**: 통계 자료 (수치, 데이터, 비교 정보 등이 특징)
- **dummy_text**: 의미 없는 더미 텍스트
- **unknown**: 분류하기 어려운 문서

# 컨텐츠 장르 분류

**반드시 다음 6가지 장르 중 하나로 분류해야 합니다. null이나 unknown은 절대 허용되지 않습니다.**

- **science**: 자연과학, 사회과학, 응용과학 등 과학적 방법론과 지식체계를 다루는 분야
  - 물리학, 화학, 생물학, 수학, 통계학
  - 심리학, 사회학, 경제학
  - 의학, 공학
  - 과학사, 과학철학
  - **통계 데이터, 수치 분석, 비교 자료** (예: 월별 매출액, CSV/Excel 데이터, 통계 표)
  - 예시: 코스모스, 이기적 유전자, 사피엔스, 총, 균, 쇠, 미분적분학, 통계 데이터 시각화

- **history**: 과거의 사건, 인물, 사회를 연구하고 서술하는 분야
  - 정치사, 사회사, 문화사
  - 세계사, 한국사
  - 전기, 회고록
  - 고고학, 역사학 방법론
  - 예시: 조선왕조실록, 난중일기, 제2차 세계대전사, 스티브 잡스, 총독의 딸

- **philosophy**: 존재, 인식, 가치, 윤리 등 근본적 문제를 탐구하는 사상 분야
  - 형이상학, 인식론, 윤리학
  - 종교학, 신학
  - 정치철학, 사회철학
  - 동양철학, 서양철학
  - 사상가 연구
  - 예시: 국가, 니코마코스 윤리학, 논어, 존재와 시간, 정의란 무엇인가

- **literature**: 언어를 매체로 한 창작 및 문학 연구 분야
  - 소설, 시, 희곡, 수필
  - 문학이론, 문학비평
  - 언어학, 국어학
  - 작가론, 작품론
  - 번역학
  - 예시: 토지, 백년의 고독, 햄릿, 문학이론입문, 한국어 문법론

- **art**: 예술 창작, 문화 현상, 미적 경험을 다루는 분야
  - 미술, 음악, 연극, 영화
  - 예술사, 예술이론
  - 문화연구, 문화인류학
  - 미학, 예술철학
  - 대중문화, 민속학
  - 예시: 서양미술사, 음악의 역사, 한국의 전통문화, 영화란 무엇인가, K-POP의 힘

- **practical**: 실생활에 직접 적용 가능한 지식과 기술을 제공하는 분야
  - 자기계발, 성공학
  - 실용 기술서, 매뉴얼
  - 건강, 요리, 취미
  - 투자, 재테크
  - 어학서, 자격증서
  - 예시: 7가지 습관, 부의 추월차선, 파이썬 완전정복, 백종원의 요리비책, 토익 RC 특급

**중요**:
1. **통계 데이터, 수치 분석, 비교 자료가 포함된 경우** → **science**로 우선 분류
   - 예: 월별 매출액, 연도별 통계, CSV/Excel 데이터, 수치 비교표
2. 장르 분류가 어렵거나 애매한 경우 → **practical** (실용)로 분류
3. 여러 장르가 섞여 있는 경우 → 가장 비중이 큰 장르 선택, 판단 불가시 **practical**
4. null, unknown, 기타 등의 값은 절대 사용 금지

# 컨텐츠 생성 가능성 판단

각 기능별로 생성 가능 여부를 Boolean으로 판단하세요:

## 1. 노래 (song) - Boolean
- **true**: 시적 표현, 감정적 내용, 스토리가 있는 문서
- **false**: 건조한 통계, 기술적 설명서

## 2. 연극 (play) - Boolean
- **true**: **최소 1명 이상의 화자**가 존재하고 대화, 상황, 캐릭터, 드라마틱한 요소가 있는 문서
  - 예: 대화체 소설, 인터뷰, 토론 내용 등
- **false**: 화자가 없는 문서, 통계 데이터, 단순 나열 정보

## 3. 퀴즈 (quiz) - Boolean
- **true**: 학습 가능한 정보, 사실, 지식이 포함된 문서
- **false**: 더미 텍스트, 의미 없는 내용

## 4. 요약 (summary) - Boolean
- **true**: 의미 있는 모든 텍스트 (더미 텍스트 제외)
- **false**: 완전한 더미 텍스트, 무의미한 반복

## 5. 시각화 (visualization) - Boolean
- **true**: 수치 데이터, 통계, 비교 정보, 트렌드 등이 포함된 문서
- **false**: 순수 감정적 내용, 대화 중심 내용
- **visualization_option** (visualization이 true일 때):
  - **단순 텍스트 입력**의 경우 → 무조건 "table" (표로 시각화)
  - **파일 업로드**의 경우:
    - 현재 문서가 **표/테이블 형태**라면 → "chart" (차트로 변환 추천)
    - 현재 문서가 **차트/그래프 형태**라면 → "table" (표로 변환 추천)
  - **판단 기준**:
    - 표/테이블: 행과 열로 정리된 데이터, CSV/Excel 데이터, 목록 형태
    - 차트/그래프: 시각적 그래프, 차트 이미지, 트렌드 시각화 설명

# 더미 텍스트 및 단순 내용 처리

다음과 같은 경우 **모든 컨텐츠 생성이 불가능**합니다:

## 완전 무의미한 내용
- 같은 문장/단어가 계속 반복되는 텍스트 ("안녕 안녕 안녕...")
- "테스트", "aaa", "111", "ㅁㄴㅇㄹ" 등의 의미 없는 문자열
- 완전히 무작위한 문자열
- 빈 텍스트나 공백만 있는 경우

## 단순하고 짧은 내용 (의미가 있어도 컨텐츠 생성에는 부족)
- "안녕하세요"와 같은 단순한 인사말
- "오늘 날씨가 좋네요"와 같은 단순 문장
- "사과 바나나 포도"와 같은 단순 나열
- 한두 문장으로 이루어진 짧고 단순한 내용

## 판단 기준
- **완전 무의미하거나 단순한 내용**: 모든 기능 false + **genre는 "practical"로 설정**
- **충분한 내용량과 의미**: 여러 문장의 구체적이고 의미있는 내용만 컨텐츠 생성 가능

**중요**: 더미 텍스트, 단순한 내용, 짧은 문장 등 **어떤 경우라도 genre는 반드시 6가지 중 하나여야 하며**, 분류가 불가능하면 **"practical"로 설정**해야 합니다.

# 응답 형식

**중요: 반드시 아래 형태의 완전한 JSON 형식으로만 응답하세요. 다른 설명이나 텍스트는 포함하지 마세요.**

## 일반적인 경우:
```json
{
    "genre": "literature",
    "song": true,
    "play": true,
    "quiz": false,
    "summary": true,
    "visualization": false
}
```

## 시각화가 포함된 경우 (테이블 형태 → 차트 추천):
```json
{
    "genre": "science",
    "song": false,
    "play": false,
    "quiz": true,
    "summary": true,
    "visualization": true,
    "visualization_option": "chart"
}
```

**참고**: 통계 데이터나 수치 비교 자료가 있는 경우 genre는 "science"로 설정

## 시각화가 포함된 경우 (차트/그래프 형태 → 표 추천):
```json
{
    "genre": "science",
    "song": false,
    "play": false,
    "quiz": true,
    "summary": true,
    "visualization": true,
    "visualization_option": "table"
}
```

## 생성 불가능한 경우 (단순/짧은 내용, 더미 텍스트, 의미 없는 내용):
```json
{
    "genre": "practical",
    "song": false,
    "play": false,
    "quiz": false,
    "summary": false,
    "visualization": false
}
```

# 분석 기준

- **각 기능별로 Boolean 값** 설정 (true/false)
- **visualization이 true일 때**: `visualization_option` 설정 규칙
  - 현재 내용이 **표/테이블 형태** → "chart" (차트로 변환)
  - 현재 내용이 **차트/그래프 형태** → "table" (표로 변환)
  - **구분 방법**:
    - 표/테이블: 행렬 구조, CSV 데이터, Excel 형태, 목록
    - 차트/그래프: 이미지 차트, 그래프 설명, 시각화 자료
- **genre 필드**:
  - **반드시 6개 카테고리 중 하나로 설정** (science, history, philosophy, literature, art, practical)
  - **통계/수치 데이터 포함 시**: "science"로 우선 분류 (월별 매출액, CSV/Excel 데이터 등)
  - **분류가 어려운 경우**: "practical"로 설정
  - **null, unknown 절대 금지**
- **단순/짧은 내용 또는 더미 텍스트**: genre를 "practical"로 설정하고 모든 기능을 false로 설정

텍스트를 신중히 분석하고 각 기능별 생성 가능성을 Boolean으로 정확히 판단해주세요.

**주의사항**:
1. **genre는 반드시 6가지 중 하나여야 하며, null이나 unknown은 절대 사용할 수 없습니다.**
2. **통계 데이터나 수치 분석이 포함된 경우 → "science"로 우선 분류** (월별 매출액, CSV/Excel 파일 등)
3. 단순하거나 짧은 내용, 더미 텍스트의 경우 genre를 "practical"로 설정하고 모든 기능을 false로 설정해주세요.
4. 장르 분류가 애매한 경우 가장 가까운 장르를 선택하되, 완전히 판단할 수 없으면 "practical"을 사용하세요.
5. **어떤 입력이 들어와도 genre 필드는 항상 6가지 장르 중 하나의 값을 가져야 합니다.**""",

        "en": """You are an expert in document analysis and content generation possibility assessment.
Please analyze the given text and determine what types of content can be generated from it.

# Content Genre Classification

**You must classify the content into one of the following 6 genres. Null or unknown values are absolutely not allowed.**

- **science**: Natural sciences, social sciences, applied sciences, and fields dealing with scientific methodology and knowledge systems
  - Physics, chemistry, biology, mathematics, statistics
  - Psychology, sociology, economics
  - Medicine, engineering
  - History of science, philosophy of science
  - **Statistical data, numerical analysis, comparative data** (e.g., monthly sales figures, CSV/Excel data, statistical tables)
  - Examples: Cosmos, The Selfish Gene, Sapiens, Guns, Germs, and Steel, Calculus, statistical data visualization

- **history**: Fields that study and document past events, figures, and societies
  - Political history, social history, cultural history
  - World history, regional history
  - Biographies, memoirs
  - Archaeology, historical methodology
  - Examples: Historical chronicles, diaries, WWII history, Steve Jobs biography

- **philosophy**: Fields exploring fundamental questions about existence, knowledge, values, and ethics
  - Metaphysics, epistemology, ethics
  - Religious studies, theology
  - Political philosophy, social philosophy
  - Eastern philosophy, Western philosophy
  - Studies of thinkers
  - Examples: The Republic, Nicomachean Ethics, Analects, Being and Time, Justice

- **literature**: Creative works and literary studies using language as a medium
  - Novels, poetry, plays, essays
  - Literary theory, literary criticism
  - Linguistics
  - Author studies, work analysis
  - Translation studies
  - Examples: Land, One Hundred Years of Solitude, Hamlet, Introduction to Literary Theory

- **art**: Fields dealing with artistic creation, cultural phenomena, and aesthetic experiences
  - Fine arts, music, theater, film
  - Art history, art theory
  - Cultural studies, cultural anthropology
  - Aesthetics, philosophy of art
  - Popular culture, folklore
  - Examples: Western Art History, History of Music, Traditional Culture, What is Cinema, The Power of K-POP

- **practical**: Fields providing knowledge and skills directly applicable to everyday life
  - Self-improvement, success studies
  - Practical technical books, manuals
  - Health, cooking, hobbies
  - Investment, financial management
  - Language books, certification guides
  - Examples: 7 Habits, Rich Dad Poor Dad, Python Complete Guide, Cooking Recipes, TOEIC Guide

**Important**:
1. **When statistical data, numerical analysis, or comparative data is included** → **Classify as science first**
   - Examples: monthly sales figures, yearly statistics, CSV/Excel data, numerical comparison tables
2. If genre classification is difficult or ambiguous → Classify as **practical**
3. If multiple genres are mixed → Choose the most dominant genre, if uncertain use **practical**
4. Absolutely prohibited to use null, unknown, or other values

# Content Generation Possibility Assessment

Judge the feasibility of generating each type of content as Boolean:

## 1. Song (song) - Boolean
- **true**: Documents with poetic expression, emotional content, stories
- **false**: Dry statistics, technical manuals

## 2. Play (play) - Boolean
- **true**: Documents with **at least 1 speaker** and dialogue, situations, characters, dramatic elements
  - Examples: Dialogue novels, interviews, debate transcripts
- **false**: Documents with no speakers, statistical data, simple enumerated information

## 3. Quiz (quiz) - Boolean
- **true**: Documents containing learnable information, facts, knowledge
- **false**: Dummy text, meaningless content

## 4. Summary (summary) - Boolean
- **true**: All meaningful text (except dummy text)
- **false**: Complete dummy text, meaningless repetition

## 5. Visualization (visualization) - Boolean
- **true**: Documents containing numerical data, statistics, comparative information, trends
- **false**: Pure emotional content, dialogue-centered content
- **visualization_option** (when visualization is true):
  - For **plain text input** → Always use "table" (visualize as table)
  - For **file upload**:
    - If current document is **table/tabular format** → "chart" (recommend converting to chart)
    - If current document is **chart/graph format** → "table" (recommend converting to table)
  - **Distinction criteria**:
    - Table/tabular: Row-column structured data, CSV data, Excel format, lists
    - Chart/graph: Visual graphs, chart images, trend visualization descriptions

# Dummy Text and Simple Content Handling

In the following cases, **all content generation is impossible**:

## Completely Meaningless Content
- Text with repeated sentences/words ("hello hello hello...")
- Meaningless strings like "test", "aaa", "111", "asdf"
- Completely random character strings
- Empty text or only whitespace

## Simple and Short Content (insufficient for content generation even if meaningful)
- Simple greetings like "Hello"
- Simple sentences like "The weather is nice today"
- Simple enumerations like "apple banana grape"
- Short and simple content consisting of one or two sentences

## Judgment Criteria
- **Completely meaningless or simple content**: All features false + **set genre to "practical"**
- **Sufficient content and meaning**: Only multiple sentences with specific meaningful content can generate content

**Important**: For dummy text, simple content, short sentences, etc., **genre must always be one of the 6 genres**, and if classification is impossible, **set to "practical"**.

# Response Format

**IMPORTANT: You must respond ONLY in complete JSON format as shown below. Do not include any other explanations or text.**

## General case:
```json
{
    "genre": "literature",
    "song": true,
    "play": true,
    "quiz": false,
    "summary": true,
    "visualization": false
}
```

## With visualization (table format → recommend chart):
```json
{
    "genre": "science",
    "song": false,
    "play": false,
    "quiz": true,
    "summary": true,
    "visualization": true,
    "visualization_option": "chart"
}
```

**Note**: When statistical data or numerical comparison data is present, set genre to "science"

## With visualization (chart/graph format → recommend table):
```json
{
    "genre": "science",
    "song": false,
    "play": false,
    "quiz": true,
    "summary": true,
    "visualization": true,
    "visualization_option": "table"
}
```

## Cannot generate content (simple/short content, dummy text, meaningless content):
```json
{
    "genre": "practical",
    "song": false,
    "play": false,
    "quiz": false,
    "summary": false,
    "visualization": false
}
```

# Analysis Criteria

- **Set Boolean values for each feature** (true/false)
- **When visualization is true**: Set `visualization_option` according to rules
  - Current content is **table/tabular format** → "chart" (convert to chart)
  - Current content is **chart/graph format** → "table" (convert to table)
  - **Distinction method**:
    - Table/tabular: Row-column structure, CSV data, Excel format, lists
    - Chart/graph: Image charts, graph descriptions, visualization materials
- **genre field**:
  - **Must be set to one of 6 categories** (science, history, philosophy, literature, art, practical)
  - **When statistical/numerical data is included**: Classify as "science" first (monthly sales, CSV/Excel data, etc.)
  - **When classification is difficult**: Set to "practical"
  - **Absolutely prohibited: null, unknown**
- **Simple/short content or dummy text**: Set genre to "practical" and all features to false

Please carefully analyze the text and accurately judge each content generation possibility as Boolean.

**Important Notes**:
1. **Genre must be one of 6 categories, null or unknown are absolutely not allowed.**
2. **When statistical data or numerical analysis is included → Classify as "science" first** (monthly sales, CSV/Excel files, etc.)
3. For simple or short content, dummy text, set genre to "practical" and all features to false.
4. When genre classification is ambiguous, choose the closest genre, but if completely uncertain, use "practical".
5. **No matter what input is given, genre field must always have one of the 6 genre values.**""",

        "ja": """あなたは文書分析とコンテンツ生成可能性判断の専門家です。
与えられたテキストを分析し、どのような種類のコンテンツに変換可能かを判断してください。

# コンテンツジャンル分類

**以下の6つのジャンルのいずれかに必ず分類してください。nullやunknownは絶対に許可されません。**

- **science**: 自然科学、社会科学、応用科学など、科学的方法論と知識体系を扱う分野
  - 物理学、化学、生物学、数学、統計学
  - 心理学、社会学、経済学
  - 医学、工学
  - 科学史、科学哲学
  - **統計データ、数値分析、比較資料** (例: 月別売上高、CSV/Excelデータ、統計表)
  - 例: コスモス、利己的な遺伝子、サピエンス全史、銃・病原菌・鉄、微分積分学、統計データ可視化

- **history**: 過去の出来事、人物、社会を研究し記述する分野
  - 政治史、社会史、文化史
  - 世界史、地域史
  - 伝記、回顧録
  - 考古学、歴史学方法論
  - 例: 歴史記録、日記、第二次世界大戦史、スティーブ・ジョブズ伝記

- **philosophy**: 存在、認識、価値、倫理などの根本的問題を探求する思想分野
  - 形而上学、認識論、倫理学
  - 宗教学、神学
  - 政治哲学、社会哲学
  - 東洋哲学、西洋哲学
  - 思想家研究
  - 例: 国家、ニコマコス倫理学、論語、存在と時間、正義論

- **literature**: 言語を媒体とした創作および文学研究分野
  - 小説、詩、戯曲、随筆
  - 文学理論、文学批評
  - 言語学
  - 作家論、作品論
  - 翻訳学
  - 例: 土、百年の孤独、ハムレット、文学理論入門

- **art**: 芸術創作、文化現象、美的経験を扱う分野
  - 美術、音楽、演劇、映画
  - 芸術史、芸術理論
  - 文化研究、文化人類学
  - 美学、芸術哲学
  - 大衆文化、民俗学
  - 例: 西洋美術史、音楽の歴史、伝統文化、映画とは何か、K-POPの力

- **practical**: 実生活に直接適用可能な知識と技術を提供する分野
  - 自己啓発、成功学
  - 実用技術書、マニュアル
  - 健康、料理、趣味
  - 投資、資産管理
  - 語学書、資格書
  - 例: 7つの習慣、金持ち父さん貧乏父さん、Python完全ガイド、料理レシピ、TOEIC対策

**重要**:
1. **統計データ、数値分析、比較資料が含まれる場合** → **scienceに優先的に分類**
   - 例: 月別売上高、年度別統計、CSV/Excelデータ、数値比較表
2. ジャンル分類が難しいまたは曖昧な場合 → **practical**(実用)に分類
3. 複数のジャンルが混在する場合 → 最も比重の大きいジャンルを選択、判断不可時は**practical**
4. null、unknown、その他の値は絶対使用禁止

# コンテンツ生成可能性判断

機能別に生成可能かどうかをBooleanで判断してください:

## 1. 歌 (song) - Boolean
- **true**: 詩的表現、感情的内容、ストーリーがある文書
- **false**: 乾燥した統計、技術的説明書

## 2. 演劇 (play) - Boolean
- **true**: **最低1人以上の話者**が存在し、対話、状況、キャラクター、ドラマチックな要素がある文書
  - 例: 対話体小説、インタビュー、討論内容など
- **false**: 話者がない文書、統計データ、単純な列挙情報

## 3. クイズ (quiz) - Boolean
- **true**: 学習可能な情報、事実、知識が含まれる文書
- **false**: ダミーテキスト、無意味な内容

## 4. 要約 (summary) - Boolean
- **true**: 意味のあるすべてのテキスト (ダミーテキスト除く)
- **false**: 完全なダミーテキスト、無意味な繰り返し

## 5. 可視化 (visualization) - Boolean
- **true**: 数値データ、統計、比較情報、トレンドなどが含まれる文書
- **false**: 純粋に感情的な内容、対話中心の内容
- **visualization_option** (visualizationがtrueの場合):
  - **単純テキスト入力**の場合 → 必ず "table" (表で可視化)
  - **ファイルアップロード**の場合:
    - 現在の文書が**表/テーブル形式**なら → "chart" (チャートに変換推奨)
    - 現在の文書が**チャート/グラフ形式**なら → "table" (表に変換推奨)
  - **判断基準**:
    - 表/テーブル: 行と列で整理されたデータ、CSV/Excelデータ、リスト形式
    - チャート/グラフ: 視覚的グラフ、チャート画像、トレンド可視化説明

# ダミーテキストおよび単純な内容の処理

以下のような場合、**すべてのコンテンツ生成が不可能**です:

## 完全に無意味な内容
- 同じ文章/単語が繰り返されるテキスト ("こんにちは こんにちは こんにちは...")
- "テスト"、"aaa"、"111"、"あいうえお"などの無意味な文字列
- 完全にランダムな文字列
- 空のテキストまたは空白のみの場合

## 単純で短い内容 (意味があってもコンテンツ生成には不足)
- "こんにちは"のような単純な挨拶
- "今日はいい天気ですね"のような単純な文章
- "りんご バナナ ぶどう"のような単純な列挙
- 一つか二つの文で構成された短く単純な内容

## 判断基準
- **完全に無意味または単純な内容**: すべての機能false + **genreは"practical"に設定**
- **十分な内容量と意味**: 複数の文の具体的で意味のある内容のみコンテンツ生成可能

**重要**: ダミーテキスト、単純な内容、短い文章など、**どのような場合でもgenreは必ず6つのうちの1つでなければならず**、分類が不可能なら**"practical"に設定**する必要があります。

# 応答形式

**重要: 必ず以下の形式の完全なJSON形式でのみ応答してください。他の説明やテキストは含めないでください。**

## 一般的な場合:
```json
{
    "genre": "literature",
    "song": true,
    "play": true,
    "quiz": false,
    "summary": true,
    "visualization": false
}
```

## 可視化が含まれる場合 (テーブル形式 → チャート推奨):
```json
{
    "genre": "science",
    "song": false,
    "play": false,
    "quiz": true,
    "summary": true,
    "visualization": true,
    "visualization_option": "chart"
}
```

**注**: 統計データや数値比較資料がある場合、genreは"science"に設定

## 可視化が含まれる場合 (チャート/グラフ形式 → 表推奨):
```json
{
    "genre": "science",
    "song": false,
    "play": false,
    "quiz": true,
    "summary": true,
    "visualization": true,
    "visualization_option": "table"
}
```

## コンテンツ生成不可能な場合 (単純/短い内容、ダミーテキスト、無意味な内容):
```json
{
    "genre": "practical",
    "song": false,
    "play": false,
    "quiz": false,
    "summary": false,
    "visualization": false
}
```

# 分析基準

- **各機能別にBoolean値**を設定 (true/false)
- **visualizationがtrueの場合**: `visualization_option`を設定ルールに従って設定
  - 現在の内容が**表/テーブル形式** → "chart" (チャートに変換)
  - 現在の内容が**チャート/グラフ形式** → "table" (表に変換)
  - **区別方法**:
    - 表/テーブル: 行列構造、CSVデータ、Excel形式、リスト
    - チャート/グラフ: 画像チャート、グラフ説明、可視化資料
- **genreフィールド**:
  - **必ず6つのカテゴリーのいずれかに設定** (science, history, philosophy, literature, art, practical)
  - **統計/数値データ含む場合**: "science"に優先的に分類 (月別売上高、CSV/Excelデータなど)
  - **分類が難しい場合**: "practical"に設定
  - **null、unknown絶対禁止**
- **単純/短い内容またはダミーテキスト**: genreを"practical"に設定し、すべての機能をfalseに設定

テキストを慎重に分析し、各機能別の生成可能性をBooleanで正確に判断してください。

**注意事項**:
1. **genreは必ず6つのうちの1つでなければならず、nullやunknownは絶対に使用できません。**
2. **統計データや数値分析が含まれる場合 → "science"に優先的に分類** (月別売上高、CSV/Excelファイルなど)
3. 単純または短い内容、ダミーテキストの場合、genreを"practical"に設定し、すべての機能をfalseに設定してください。
4. ジャンル分類が曖昧な場合、最も近いジャンルを選択しますが、完全に判断できない場合は"practical"を使用してください。
5. **どのような入力が来ても、genreフィールドは常に6つのジャンルのうちの1つの値を持たなければなりません。**""",

        "zh": """您是文档分析和内容生成可能性判断的专家。
请分析给定的文本，判断可以生成哪些类型的内容。

# 内容类型分类

**必须将内容分类为以下6个类型之一。绝对不允许使用null或unknown值。**

- **science**: 自然科学、社会科学、应用科学等涉及科学方法论和知识体系的领域
  - 物理学、化学、生物学、数学、统计学
  - 心理学、社会学、经济学
  - 医学、工程学
  - 科学史、科学哲学
  - **统计数据、数值分析、比较资料** (例: 月度销售额、CSV/Excel数据、统计表)
  - 示例: 宇宙、自私的基因、人类简史、枪炮病菌与钢铁、微积分、统计数据可视化

- **history**: 研究和记述过去事件、人物、社会的领域
  - 政治史、社会史、文化史
  - 世界史、地区史
  - 传记、回忆录
  - 考古学、历史学方法论
  - 示例: 历史记录、日记、二战史、史蒂夫·乔布斯传

- **philosophy**: 探索存在、认识、价值、伦理等根本问题的思想领域
  - 形而上学、认识论、伦理学
  - 宗教学、神学
  - 政治哲学、社会哲学
  - 东方哲学、西方哲学
  - 思想家研究
  - 示例: 理想国、尼各马可伦理学、论语、存在与时间、正义论

- **literature**: 以语言为媒介的创作及文学研究领域
  - 小说、诗歌、戏剧、散文
  - 文学理论、文学批评
  - 语言学
  - 作家论、作品论
  - 翻译学
  - 示例: 土地、百年孤独、哈姆雷特、文学理论导论

- **art**: 涉及艺术创作、文化现象、美学体验的领域
  - 美术、音乐、戏剧、电影
  - 艺术史、艺术理论
  - 文化研究、文化人类学
  - 美学、艺术哲学
  - 大众文化、民俗学
  - 示例: 西方艺术史、音乐史、传统文化、电影是什么、K-POP的力量

- **practical**: 提供可直接应用于日常生活的知识和技能的领域
  - 自我提升、成功学
  - 实用技术书、手册
  - 健康、烹饪、爱好
  - 投资、理财
  - 语言书、资格证书
  - 示例: 高效能人士的七个习惯、富爸爸穷爸爸、Python完全指南、烹饪食谱、托业指南

**重要**:
1. **包含统计数据、数值分析、比较资料时** → **优先分类为science**
   - 例: 月度销售额、年度统计、CSV/Excel数据、数值比较表
2. 类型分类困难或模糊时 → 分类为**practical**(实用)
3. 多个类型混合时 → 选择占比最大的类型，无法判断时使用**practical**
4. 绝对禁止使用null、unknown或其他值

# 内容生成可能性判断

按功能判断是否可以生成为Boolean值:

## 1. 歌曲 (song) - Boolean
- **true**: 具有诗意表达、情感内容、故事的文档
- **false**: 枯燥的统计、技术说明书

## 2. 戏剧 (play) - Boolean
- **true**: 存在**至少1个以上说话者**且具有对话、情境、角色、戏剧元素的文档
  - 例: 对话体小说、访谈、辩论内容等
- **false**: 没有说话者的文档、统计数据、简单列举信息

## 3. 测验 (quiz) - Boolean
- **true**: 包含可学习信息、事实、知识的文档
- **false**: 虚拟文本、无意义内容

## 4. 摘要 (summary) - Boolean
- **true**: 所有有意义的文本 (虚拟文本除外)
- **false**: 完全的虚拟文本、无意义重复

## 5. 可视化 (visualization) - Boolean
- **true**: 包含数值数据、统计、比较信息、趋势等的文档
- **false**: 纯粹情感内容、以对话为中心的内容
- **visualization_option** (当visualization为true时):
  - **纯文本输入**的情况 → 必须使用 "table" (以表格形式可视化)
  - **文件上传**的情况:
    - 如果当前文档是**表格/表单格式** → "chart" (建议转换为图表)
    - 如果当前文档是**图表/图形格式** → "table" (建议转换为表格)
  - **判断标准**:
    - 表格/表单: 按行列组织的数据、CSV/Excel数据、列表形式
    - 图表/图形: 视觉图表、图表图像、趋势可视化说明

# 虚拟文本和简单内容处理

以下情况下，**所有内容生成都不可能**:

## 完全无意义的内容
- 相同句子/单词重复的文本 ("你好 你好 你好...")
- "测试"、"aaa"、"111"、"asdf"等无意义字符串
- 完全随机的字符串
- 空文本或仅有空格

## 简单且短的内容 (即使有意义也不足以生成内容)
- "你好"等简单问候语
- "今天天气不错"等简单句子
- "苹果 香蕉 葡萄"等简单列举
- 由一两句话组成的简短内容

## 判断标准
- **完全无意义或简单内容**: 所有功能false + **genre设置为"practical"**
- **足够的内容量和意义**: 只有多句具体有意义的内容才能生成内容

**重要**: 虚拟文本、简单内容、短句等，**无论何种情况genre都必须是6个类型之一**，如果无法分类则**设置为"practical"**。

# 响应格式

**重要: 必须仅以下面所示的完整JSON格式响应。不要包含其他说明或文本。**

## 一般情况:
```json
{
    "genre": "literature",
    "song": true,
    "play": true,
    "quiz": false,
    "summary": true,
    "visualization": false
}
```

## 包含可视化的情况 (表格格式 → 推荐图表):
```json
{
    "genre": "science",
    "song": false,
    "play": false,
    "quiz": true,
    "summary": true,
    "visualization": true,
    "visualization_option": "chart"
}
```

**注**: 存在统计数据或数值比较资料时，genre设置为"science"

## 包含可视化的情况 (图表/图形格式 → 推荐表格):
```json
{
    "genre": "science",
    "song": false,
    "play": false,
    "quiz": true,
    "summary": true,
    "visualization": true,
    "visualization_option": "table"
}
```

## 无法生成内容的情况 (简单/短内容、虚拟文本、无意义内容):
```json
{
    "genre": "practical",
    "song": false,
    "play": false,
    "quiz": false,
    "summary": false,
    "visualization": false
}
```

# 分析标准

- **为每个功能设置Boolean值** (true/false)
- **当visualization为true时**: 根据规则设置`visualization_option`
  - 当前内容是**表格/表单格式** → "chart" (转换为图表)
  - 当前内容是**图表/图形格式** → "table" (转换为表格)
  - **区分方法**:
    - 表格/表单: 行列结构、CSV数据、Excel格式、列表
    - 图表/图形: 图像图表、图表说明、可视化材料
- **genre字段**:
  - **必须设置为6个类别之一** (science, history, philosophy, literature, art, practical)
  - **包含统计/数值数据时**: 优先分类为"science" (月度销售额、CSV/Excel数据等)
  - **分类困难时**: 设置为"practical"
  - **绝对禁止: null、unknown**
- **简单/短内容或虚拟文本**: 将genre设置为"practical"，所有功能设为false

请仔细分析文本，准确判断每个内容生成可能性为Boolean值。

**注意事项**:
1. **genre必须是6个类别之一，绝对不允许使用null或unknown。**
2. **包含统计数据或数值分析时 → 优先分类为"science"** (月度销售额、CSV/Excel文件等)
3. 对于简单或短内容、虚拟文本，将genre设置为"practical"，所有功能设为false。
4. 类型分类模糊时选择最接近的类型，但完全无法判断时使用"practical"。
5. **无论输入什么，genre字段必须始终具有6个类型之一的值。**"""
    }

    return prompts.get(language, prompts["ko"])