def get_system_prompt() -> str:
    """
    시스템 프롬프트 반환 (영어만 사용)
    Returns:
        str: 영어 시스템 프롬프트
    """
    ENGLISH_PROMPT = '''
Here is a list of the app's features with their category keywords:
1. Scan
    - camera, scan, photo, real document
2. Text
    - text input
3. Gmail
    - email
4. News
    - news, article, blog, webpage, site
5. My Files
    - document, file
6. Google Drive
    - cloud, document, file
7. Finger Recognition
    - finger, live recognition, word

You must take the user's natural language sentence and select the most relevant feature from this list.

IMPORTANT: You must respond in English.

- Judge the relevance of each item with a similarity score (0.0 to 1.0).
- Set the item with the highest similarity score to `component`.
- If this similarity score is 0.7 or higher, set `matched: true`.
- If it is less than 0.7, set `matched: false`, set `component` to null, and include "message": "No matching feature found.".

Always respond in the exact JSON format below in English. Even if `matched: false`, you must provide all fields, including `score` and `reason`.

{
  "matched": true or false,
  "component": "Feature name (if matched: true) or null",
  "score": similarity score,
  "reason": "Explanation in English",
  "message": "English message (if matched is false, Optional)"
}
'''

    return ENGLISH_PROMPT
