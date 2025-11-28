"""
Problem Solver 전용 프롬프트 생성 함수
"""

def create_problem_solving_prompt(language: str = "ko") -> str:
    """
    문제 해결을 위한 프롬프트를 언어별로 생성합니다.

    Args:
        language: 언어 코드 (ko, en, ja, zh)

    Returns:
        str: 생성된 프롬프트
    """
    prompts = {
        "ko": """이 이미지에 포함된 수학 문제를 분석하고 해결해주세요.

다음 형식으로 JSON 응답을 제공해주세요:

{
  "answer": "최종 답안 (숫자나 간단한 표현)",
  "solution": "단계별 풀이 과정 (명확하고 논리적으로)",
  "concepts": "이 문제에서 사용된 핵심 수학 개념들"
}

요구사항:
1. 정확한 계산과 논리적 추론
2. 단계별로 명확한 설명
3. 핵심 개념의 간결한 요약
4. 한국어로 응답
""",
        "en": """Please analyze and solve the math problem in this image.

Provide a JSON response in the following format:

{
  "answer": "Final answer (number or simple expression)",
  "solution": "Step-by-step solution process (clear and logical)",
  "concepts": "Key mathematical concepts used in this problem"
}

Requirements:
1. Accurate calculation and logical reasoning
2. Clear step-by-step explanation
3. Concise summary of key concepts
4. Respond in English
""",
        "ja": """この画像に含まれる数学問題を分析し、解決してください。

以下の形式でJSON応答を提供してください：

{
  "answer": "最終回答（数字または簡単な表現）",
  "solution": "段階的解法過程（明確で論理的に）",
  "concepts": "この問題で使用された重要な数学概念"
}

要件：
1. 正確な計算と論理的推論
2. 段階的で明確な説明
3. 重要概念の簡潔な要約
4. 日本語で応答
""",
        "zh": """请分析并解决这张图片中的数学问题。

请提供以下格式的JSON响应：

{
  "answer": "最终答案（数字或简单表达式）",
  "solution": "逐步解题过程（清晰且逻辑性强）",
  "concepts": "此问题中使用的关键数学概念"
}

要求：
1. 准确计算和逻辑推理
2. 逐步清晰说明
3. 关键概念的简洁总结
4. 用中文回答
"""
    }

    return prompts.get(language, prompts["ko"])