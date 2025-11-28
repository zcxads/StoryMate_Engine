"""
퀴즈 생성 프롬프트 템플릿
"""
import re
from typing import List

# 언어 감지를 위한 문자 패턴
LANGUAGE_PATTERNS = {
    "ko": r'[\uac00-\ud7a3]',  # 한국어 (한글)
    "ja": r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]',  # 일본어 (히라가나, 카타카나, 한자)
    "zh": r'[\u4e00-\u9fff]',  # 중국어 (한자)
    "zh-CN": r'[\u4e00-\u9fff]',  # 간체 중국어
    "zh-TW": r'[\u4e00-\u9fff]',  # 번체 중국어
    "en": r'[a-zA-Z]'  # 영어
}

def detect_primary_language(text: str) -> str:
    """텍스트에서 주요 언어를 감지하여 반환 (Unity rich text 태그 자동 제거)"""
    # Unity rich text 태그 제거
    from app.utils.process_text import strip_rich_text_tags
    cleaned_text = strip_rich_text_tags(text)

    if not cleaned_text or len(cleaned_text.strip()) == 0:
        return "en"

    # 각 언어별 문자 수 계산
    language_counts = {}

    for lang_code, pattern in LANGUAGE_PATTERNS.items():
        matches = re.findall(pattern, cleaned_text)
        language_counts[lang_code] = len(matches)

    # 가장 많은 문자를 가진 언어 반환
    if language_counts:
        primary_language = max(language_counts, key=language_counts.get)
        # 문자가 실제로 존재하는 경우만 반환
        if language_counts[primary_language] > 0:
            return primary_language

    # 기본값으로 영어 반환
    return "en"

# 한국어 퀴즈 생성 템플릿
QUIZ_GENERATION_TEMPLATE_KO = """당신은 교육 콘텐츠 전문가입니다. 아래 제공된 텍스트를 바탕으로 정확히 5개의 독특하고 서로 다른 퀴즈를 생성하세요. 각 퀴즈는 텍스트의 서로 다른 핵심 사실이나 개념에 초점을 맞춰야 하며, 두 개의 퀴즈가 같은 아이디어를 다뤄서는 안 됩니다.

중요한 요구사항:
1. 정확히 5개의 퀴즈를 생성하세요.
2. 아래 설명된 문제 유형 중에서 생성하세요.
3. 각 퀴즈는 텍스트의 명확히 구별되는 사실이나 개념을 바탕으로 해야 합니다.
4. 모든 답변 선택지는 모호하지 않고 텍스트에서 검증 가능해야 합니다.
5. 결과를 다음 JSON 형식으로 정확히 반환하세요:

[
    {{
        "question": "질문 내용",
        "problemType": 문제 유형 번호,
        "answer": "정답",
        "options": ["선택지 1", "선택지 2", ...]
    }},
    ...
]

옵션 형식 규칙:
- OX 문제(problemType 0): options는 반드시 ["O", "X"] 형식으로, answer는 "O" 또는 "X"로 설정
- 이지선다 문제(problemType 2): options는 정확히 2개의 서로 다른 선택지를 포함하고, answer는 그 중 하나와 정확히 일치
- 삼지선다 문제(problemType 3): options는 정확히 3개의 서로 다른 선택지를 포함하고, answer는 그 중 하나와 정확히 일치
- 사지선다 문제(problemType 4): options는 정확히 4개의 서로 다른 선택지를 포함하고, answer는 그 중 하나와 정확히 일치
- 오지선다 문제(problemType 5): options는 정확히 5개의 서로 다른 선택지를 포함하고, answer는 그 중 하나와 정확히 일치

지침:
- 명확하고 간단한 언어를 사용하세요.
- 학생이 이해하기 적절한 수준의 문제를 만드세요.
- 같은 아이디어를 반복하거나 다시 표현하지 마세요.
- 각 퀴즈는 텍스트의 고유한 측면을 다뤄야 합니다.

{format_instructions}

입력 텍스트:
{text}

문제 유형:
0: OX (참/거짓) 문제 - options: ["O", "X"], answer: "O" 또는 "X"
2: 이지선다 문제 - options: ["선택지1", "선택지2"], answer: 선택지 중 하나와 정확히 일치
3: 삼지선다 문제 - options: ["선택지1", "선택지2", "선택지3"], answer: 선택지 중 하나와 정확히 일치
4: 사지선다 문제 - options: ["선택지1", "선택지2", "선택지3", "선택지4"], answer: 선택지 중 하나와 정확히 일치
5: 오지선다 문제 - options: ["선택지1", "선택지2", "선택지3", "선택지4", "선택지5"], answer: 선택지 중 하나와 정확히 일치"""

# 영어 퀴즈 생성 템플릿
QUIZ_GENERATION_TEMPLATE_EN = """You are an expert educational content creator. Generate exactly 5 unique and distinct quizzes based on the text provided below. Each quiz must focus on a different key fact or concept from the text; no two quizzes should cover the same idea.

IMPORTANT REQUIREMENTS:
1. Produce exactly 5 quizzes.
2. Create quizzes according to the problem types described below.
3. Each quiz must be based on a clearly distinct fact or concept from the text.
4. Ensure that all answer options are unambiguous and verifiable from the text.
5. Return the result in the following JSON format exactly:

[
    {{
        "question": "Question content",
        "problemType": Problem type number,
        "answer": "Correct answer",
        "options": ["Option 1", "Option 2", ...]
    }},
    ...
]

Option Format Rules:
- OX question (problemType 0): options must be ["O", "X"] format, answer set to "O" or "X"
- Two-choice question (problemType 2): options contains exactly 2 different choices, answer matches one exactly
- Three-choice question (problemType 3): options contains exactly 3 different choices, answer matches one exactly
- Four-choice question (problemType 4): options contains exactly 4 different choices, answer matches one exactly
- Five-choice question (problemType 5): options contains exactly 5 different choices, answer matches one exactly

Guidelines:
- Use clear and simple language.
- Ensure questions are appropriate for student comprehension.
- Do not repeat or rephrase the same idea in multiple quizzes.
- Each quiz should cover a unique aspect of the text.

{format_instructions}

Input text:
{text}

Question Types:
0: OX (True/False) question - options: ["O", "X"], answer: "O" or "X"
2: Two-choice question - options: ["Option1", "Option2"], answer: exactly matches one of the options
3: Three-choice question - options: ["Option1", "Option2", "Option3"], answer: exactly matches one of the options
4: Four-choice question - options: ["Option1", "Option2", "Option3", "Option4"], answer: exactly matches one of the options
5: Five-choice question - options: ["Option1", "Option2", "Option3", "Option4", "Option5"], answer: exactly matches one of the options"""

# 일본어 퀴즈 생성 템플릿
QUIZ_GENERATION_TEMPLATE_JA = """あなたは教育コンテンツの専門家です。以下に提供されたテキストに基づいて、正確に5つのユニークで異なるクイズを生成してください。各クイズはテキストの異なる重要な事実や概念に焦点を当てる必要があり、2つのクイズが同じアイデアを扱ってはいけません。

重要な要件:
1. 正確に5つのクイズを作成してください。
2. 以下に説明する問題タイプの中から生成してください。
3. 各クイズはテキストの明確に区別される事実や概念に基づいている必要があります。
4. すべての回答選択肢は曖昧でなく、テキストから検証可能であることを確認してください。
5. 次のJSON形式で正確に結果を返してください:

[
    {{
        "question": "質問内容",
        "problemType": 問題タイプ番号,
        "answer": "正解",
        "options": ["選択肢1", "選択肢2", ...]
    }},
    ...
]

選択肢形式の規則:
- OX問題（problemType 0）: optionsは必ず["O", "X"]形式で、answerは"O"または"X"に設定
- 二択問題（problemType 2）: optionsは正確に2つの異なる選択肢を含み、answerはその中の1つと正確に一致
- 三択問題（problemType 3）: optionsは正確に3つの異なる選択肢を含み、answerはその中の1つと正確に一致
- 四択問題（problemType 4）: optionsは正確に4つの異なる選択肢を含み、answerはその中の1つと正確に一致
- 五択問題（problemType 5）: optionsは正確に5つの異なる選択肢を含み、answerはその中の1つと正確に一致

ガイドライン:
- 明確で簡単な言語を使用してください。
- 学生の理解に適したレベルの問題を作成してください。
- 同じアイデアを繰り返したり言い換えたりしないでください。
- 各クイズはテキストの独特な側面をカバーする必要があります。

{format_instructions}

入力テキスト:
{text}

問題タイプ:
0: OX（○/×）問題 - options: ["O", "X"], answer: "O"または"X"
2: 二択問題 - options: ["選択肢1", "選択肢2"], answer: 選択肢の1つと正確に一致
3: 三択問題 - options: ["選択肢1", "選択肢2", "選択肢3"], answer: 選択肢の1つと正確に一致
4: 四択問題 - options: ["選択肢1", "選択肢2", "選択肢3", "選択肢4"], answer: 選択肢の1つと正確に一致
5: 五択問題 - options: ["選択肢1", "選択肢2", "選択肢3", "選択肢4", "選択肢5"], answer: 選択肢の1つと正確に一致"""

# 중국어 퀴즈 생성 템플릿
QUIZ_GENERATION_TEMPLATE_ZH = """您是一位教育内容专家。请基于下面提供的文本生成恰好5个独特且不同的测验。每个测验必须专注于文本中不同的关键事实或概念；没有两个测验应该涵盖相同的想法。

重要要求:
1. 生成恰好5个测验。
2. 从下面描述的问题类型中创建测验。
3. 每个测验必须基于文本中明确不同的事实或概念。
4. 确保所有答案选项都是明确的，并且可以从文本中验证。
5. 请严格按照以下JSON格式返回结果：

[
    {{
        "question": "问题内容",
        "problemType": 问题类型编号,
        "answer": "正确答案",
        "options": ["选项1", "选项2", ...]
    }},
    ...
]

选项格式规则:
- 是非题（problemType 0）: options必须为["O", "X"]格式，answer设置为"O"或"X"
- 二选一题（problemType 2）: options包含正确的2个不同选项，answer与其中一个完全匹配
- 三选一题（problemType 3）: options包含正确的3个不同选项，answer与其中一个完全匹配
- 四选一题（problemType 4）: options包含正确的4个不同选项，answer与其中一个完全匹配
- 五选一题（problemType 5）: options包含正确的5个不同选项，answer与其中一个完全匹配

指导原则:
- 使用清晰简单的语言。
- 确保问题适合学生理解。
- 不要在多个测验中重复或重新表述相同的想法。
- 每个测验应该涵盖文本的独特方面。

{format_instructions}

输入文本:
{text}

问题类型:
0: 是非题 - options: ["O", "X"], answer: "O"或"X"
2: 二选一题 - options: ["选项1", "选项2"], answer: 与选项之一完全匹配
3: 三选一题 - options: ["选项1", "选项2", "选项3"], answer: 与选项之一完全匹配
4: 四选一题 - options: ["选项1", "选项2", "选项3", "选项4"], answer: 与选项之一完全匹配
5: 五选一题 - options: ["选项1", "选项2", "选项3", "选项4", "选项5"], answer: 与选项之一完全匹配"""

QUIZ_GENERATION_INPUT_VARIABLES = ["text"]

# 언어별 템플릿 매핑
LANGUAGE_TEMPLATES = {
    "ko": QUIZ_GENERATION_TEMPLATE_KO,
    "ja": QUIZ_GENERATION_TEMPLATE_JA,
    "zh": QUIZ_GENERATION_TEMPLATE_ZH,
    "zh-CN": QUIZ_GENERATION_TEMPLATE_ZH,
    "zh-TW": QUIZ_GENERATION_TEMPLATE_ZH,
    "en": QUIZ_GENERATION_TEMPLATE_EN
}

def get_quiz_generation_prompt_config(text: str = "", quiz_count: int = 10):
    """
    퀴즈 생성에 사용할 프롬프트 설정을 반환합니다.
    
    Args:
        text (str): 입력 텍스트
        quiz_count (int): 생성할 퀴즈 개수
    
    Returns:
        dict: 프롬프트 템플릿과 입력 변수 정보를 포함한 딕셔너리
    """
    # 텍스트 언어 감지
    lang = detect_primary_language(text)
    
    # 언어별 템플릿 선택
    if lang == "ko":
        template = QUIZ_GENERATION_TEMPLATE_KO.replace("정확히 5개의", f"정확히 {quiz_count}개의")
    elif lang in ["ja", "jp"]:
        template = QUIZ_GENERATION_TEMPLATE_JA.replace("正確に5つの", f"正確に{quiz_count}つの")
    elif lang in ["zh", "zh-CN", "zh-TW"]:
        template = QUIZ_GENERATION_TEMPLATE_ZH.replace("恰好5个", f"恰好{quiz_count}个")
    else:
        # 기본값은 영어
        template = QUIZ_GENERATION_TEMPLATE_EN.replace("exactly 5", f"exactly {quiz_count}")
    
    return {
        "template": template,
        "input_variables": ["text", "quiz_count"],
    }
