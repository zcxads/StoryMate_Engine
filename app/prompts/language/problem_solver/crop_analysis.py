"""
LLM 기반 크롭 이미지 분석 프롬프트
"""

def get_crop_analysis_prompt(problem_number: str) -> str:
    """
    크롭된 이미지 분석을 위한 프롬프트 반환

    Args:
        problem_number: 분석할 문제 번호

    Returns:
        str: LLM 분석용 프롬프트
    """
    return f"""
이 이미지는 문제 {problem_number}번의 크롭된 이미지입니다.

다음을 분석해주세요:
1. 메인 문제 {problem_number}번이 완전히 포함되어 있는가?
2. 다른 문제의 일부(잘린 부분)가 포함되어 있는가?
3. 잘린 문제가 있다면 어느 위치에 있는가? (상단/하단/좌측/우측)

응답은 다음 JSON 형식으로만 해주세요:
{{
  "main_problem_complete": true/false,
  "has_partial_problems": true/false,
  "partial_problem_locations": ["top", "bottom", "left", "right"],
  "removal_suggestion": {{
    "top": 0,
    "bottom": 0,
    "left": 0,
    "right": 0
  }},
  "confidence": 0.0-1.0,
  "reasoning": "분석 근거"
}}

removal_suggestion의 값은 제거할 픽셀 수입니다.
"""