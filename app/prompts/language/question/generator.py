"""
책 내용 기반 추천 질문 생성을 위한 프롬프트 템플릿 - 언어별 통합 관리
"""

from langchain_core.prompts import PromptTemplate

# 한국어 질문 생성 프롬프트
QUESTION_PROMPT_KO = """당신은 교육 전문가이자 질문 생성 전문가입니다.

**분석할 내용:**
{book_content}

**질문 생성 가이드라인:**
1. 내용을 바탕으로 {question_count}개의 교육적 질문을 생성하세요
2. 각 질문은 웹에서 검색하여 답을 찾을 수 있어야 합니다
3. 어린이의 호기심과 학습 동기를 자극하는 질문을 만드세요
4. 각 질문에 적절한 카테고리를 제공하세요
5. 각 질문에 대해 3-5개의 유용한 검색 키워드를 제공하세요

**중요: 반드시 한국어로만 응답하세요.**

**응답 형식 (JSON):**
[
  {{
    "question": "[한국어로 질문 작성]",
    "reason": "[한국어로 이유 작성]",
    "category": "[한국어로 카테고리 작성]",
    "search_keywords": ["키워드1", "키워드2", "키워드3"]
  }},
  ...
]

**질문 생성:**"""

# 영어 질문 생성 프롬프트
QUESTION_PROMPT_EN = """You are an educational expert and question generation specialist.

**Content to analyze:**
{book_content}

**Question Generation Guidelines:**
1. Generate {question_count} educational questions based on the content
2. Each question should be searchable on the web to find answers
3. Create questions that stimulate children's curiosity and learning motivation
4. Use appropriate categories for each question
5. Provide 3-5 useful search keywords for each question

**CRITICAL: You MUST respond ONLY in ENGLISH.**

**Response Format (JSON):**
[
  {{
    "question": "[Write question in English]",
    "reason": "[Write reason in English]",
    "category": "[Write category in English]",
    "search_keywords": ["keyword1", "keyword2", "keyword3"]
  }},
  ...
]

**Generate Questions:**"""

# 일본어 질문 생성 프롬프트
QUESTION_PROMPT_JA = """あなたは教育専門家であり、質問生成の専門家です。

**分析する内容:**
{book_content}

**質問生成ガイドライン:**
1. 内容に基づいて{question_count}個の教育的な質問を生成してください
2. 各質問はウェブで検索して答えを見つけられるようにする必要があります
3. 子供たちの好奇心と学習意欲を刺激する質問を作成してください
4. 各質問に適切なカテゴリーを提供してください
5. 各質問に対して3-5個の有用な検索キーワードを提供してください

**重要: 必ず日本語のみで回答してください。**

**回答形式 (JSON):**
[
  {{
    "question": "[日本語で質問を書く]",
    "reason": "[日本語で理由を書く]",
    "category": "[日本語でカテゴリーを書く]",
    "search_keywords": ["キーワード1", "キーワード2", "キーワード3"]
  }},
  ...
]

**質問を生成:**"""

# 중국어 질문 생성 프롬프트
QUESTION_PROMPT_ZH = """您是教育专家和问题生成专家。

**分析内容:**
{book_content}

**问题生成指南:**
1. 根据内容生成{question_count}个教育性问题
2. 每个问题应该可以在网上搜索找到答案
3. 创建能激发儿童好奇心和学习动机的问题
4. 为每个问题提供适当的类别
5. 为每个问题提供3-5个有用的搜索关键词

**重要: 必须仅用中文回答。**

**回答格式 (JSON):**
[
  {{
    "question": "[用中文写问题]",
    "reason": "[用中文写理由]",
    "category": "[用中文写类别]",
    "search_keywords": ["关键词1", "关键词2", "关键词3"]
  }},
  ...
]

**生成问题:**"""

QUESTION_INPUT_VARIABLES = ["book_content", "question_count"]

def get_question_prompt(language: str = "ko") -> PromptTemplate:
    """언어별 책 내용 기반 추천 질문 생성 프롬프트 템플릿을 반환합니다.

    Args:
        language: 언어 코드 (ko, en, ja, zh)

    Returns:
        PromptTemplate: 언어별 질문 생성 프롬프트
    """
    # 언어 코드 정규화
    lang = language.lower() if language else "ko"

    # 언어별 템플릿 선택
    if lang in ["en", "english", "영어"]:
        template = QUESTION_PROMPT_EN
    elif lang in ["ja", "japanese", "일본어", "日本語"]:
        template = QUESTION_PROMPT_JA
    elif lang in ["zh", "zh-cn", "zh-tw", "chinese", "중국어", "中文"]:
        template = QUESTION_PROMPT_ZH
    else:  # default: ko
        template = QUESTION_PROMPT_KO

    return PromptTemplate(
        input_variables=QUESTION_INPUT_VARIABLES,
        template=template
    )
