"""
웹 검색 결과 분석 및 요약 프롬프트 생성기
"""

from langchain.prompts import PromptTemplate

SEARCH_ANALYSIS_PROMPT = """
당신은 웹 검색 결과를 분석하여 질문에 대한 정확하고 유용한 답변을 제공하는 전문가입니다.

**질문:** {question}

**검색 키워드:** {search_keywords}

**검색 결과:**
{search_results}

위의 검색 결과를 바탕으로 다음과 같이 답변해주세요:

**요약:**
검색 결과의 핵심 내용을 2-3문장으로 간단히 요약해주세요.

**구조화된 답변:**
다음 JSON 형식으로 구조화된 답변을 제공해주세요:

```json
{{
  "direct_answer": "질문의 핵심에 대한 직접적이고 명확한 답변",
  "background_info": "관련된 중요한 배경 정보와 맥락",
  "interesting_facts": "흥미롭고 교육적인 추가 사실들",
  "easy_explanation": "어린이들이 쉽게 이해할 수 있는 비유나 설명",
  "key_concepts": ["핵심개념1", "핵심개념2", "핵심개념3"],
  "related_topics": ["관련주제1", "관련주제2", "관련주제3"]
}}
```

**주의사항:**
- 검색 결과에서 확인된 정보만 사용하세요
- 불확실한 정보는 "추정된다" 또는 "알려져 있다"와 같은 표현을 사용하세요
- 어린이 독자를 고려하여 쉽고 재미있게 설명하세요
- 출처가 명확하지 않은 정보는 언급하지 마세요
- JSON 형식을 정확히 지켜주세요
- 각 필드는 한국어로 작성해주세요

응답은 반드시 **요약:** 부분과 **구조화된 답변:** JSON 부분을 모두 포함해주세요.
"""

def create_search_analysis_prompt() -> PromptTemplate:
    """
    웹 검색 결과 분석 프롬프트 템플릿을 생성합니다.
    
    Returns:
        PromptTemplate: 검색 결과 분석용 프롬프트 템플릿
    """
    return PromptTemplate(
        input_variables=["question", "search_keywords", "search_results"],
        template=SEARCH_ANALYSIS_PROMPT
    ) 