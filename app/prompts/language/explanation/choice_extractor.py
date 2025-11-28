"""
객관식 선택지 추출 프롬프트 모듈
"""

def create_choice_extraction_prompt(language: str) -> str:
    """
    이미지에서 객관식 선택지를 추출하기 위한 프롬프트 생성

    Args:
        language: 응답 언어 (ko, en, ja, zh)

    Returns:
        str: 해당 언어에 맞는 선택지 추출 프롬프트
    """
    
    prompts = {
        "ko": """이미지에서 객관식 문제의 선택지를 추출해주세요.

만약 객관식 문제가 아니라면 null을 반환하세요.
객관식 문제라면 각 선택지의 번호와 값을 JSON 형식으로 추출하세요.

**응답 형식:**
```json
{
    "options": [
        {"number": 1, "value": "선택지1의 값"},
        {"number": 2, "value": "선택지2의 값"},
        {"number": 3, "value": "선택지3의 값"}
    ]
}
```

또는 객관식이 아닌 경우:
```json
null
```

**중요**: JSON 형식으로만 응답하고, 다른 설명을 추가하지 마세요.""",

        "en": """Extract multiple choice options from the image.

If this is not a multiple choice question, return null.
If it is a multiple choice question, extract the number and value of each option in JSON format.

**Response Format:**
```json
{
    "options": [
        {"number": 1, "value": "option1 value"},
        {"number": 2, "value": "option2 value"},
        {"number": 3, "value": "option3 value"}
    ]
}
```

Or if not multiple choice:
```json
null
```

**Important**: Respond only in JSON format, do not add other explanations.""",

        "ja": """画像から選択肢問題の選択肢を抽出してください。

選択肢問題でない場合はnullを返してください。
選択肢問題の場合は、各選択肢の番号と値をJSON形式で抽出してください。

**応答形式:**
```json
{
    "options": [
        {"number": 1, "value": "選択肢1の値"},
        {"number": 2, "value": "選択肢2の値"},
        {"number": 3, "value": "選択肢3の値"}
    ]
}
```

または選択肢問題でない場合:
```json
null
```

**重要**: JSON形式でのみ応答し、他の説明を追加しないでください。""",

        "zh": """从图像中提取选择题的选项。

如果这不是选择题，请返回null。
如果是选择题，请以JSON格式提取每个选项的编号和值。

**响应格式:**
```json
{
    "options": [
        {"number": 1, "value": "选项1的值"},
        {"number": 2, "value": "选项2的值"},
        {"number": 3, "value": "选项3的值"}
    ]
}
```

或者如果不是选择题:
```json
null
```

**重要**: 仅以JSON格式响应，不要添加其他说明。"""
    }

    return prompts.get(language, prompts["ko"])
