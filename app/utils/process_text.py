import re
from typing import List, Tuple
from app.utils.logger.setup import setup_logger

logger = setup_logger('process_text', 'logs/utils')

def strip_rich_text_tags(text: str) -> str:
    """
    Unity Rich Text 태그를 모두 제거하여 순수 텍스트만 반환합니다.
    TTS나 음성 생성 시 태그가 읽히는 것을 방지하기 위해 사용합니다.

    일반적인 <>로 감싸진 텍스트는 그대로 유지하고, Unity에서 정의한 태그만 제거합니다.

    지원하는 태그:
    - <color=값>, </color> - 색상 태그
    - <size=값>, </size> - 크기 태그
    - <b>, </b> - 굵게
    - <i>, </i> - 기울임
    - <material=값>, </material> - 재질
    - <quad> - 이미지/아이콘
    - 기타 Unity Rich Text 태그들

    Args:
        text: Unity Rich Text 태그가 포함된 텍스트

    Returns:
        태그가 제거된 순수 텍스트

    Examples:
        >>> strip_rich_text_tags("<color=#FF0000>빨간색</color> 텍스트")
        '빨간색 텍스트'
        >>> strip_rich_text_tags("<size=30>제목</size> <size=20>본문</size>")
        '제목 본문'
        >>> strip_rich_text_tags("일반 <텍스트> 유지")
        '일반 <텍스트> 유지'
    """
    if not text:
        return text

    # Unity Rich Text 태그 패턴
    # 1. 닫는 태그: </color>, </size> 등
    # 2. 속성이 있는 여는 태그: <color=#FF0000>, <size=30> 등
    # 3. 속성이 없는 단독 태그: <b>, <i>, <quad/> 등

    # 닫는 태그 패턴
    closing_tag_pattern = r'</(?:color|size|b|i|material|quad|mark|s|u|sub|sup|pos|voffset|width|indent|line-height|line-indent|link|align|font|sprite|nobr|lowercase|uppercase|smallcaps|allcaps|mspace|cspace|alpha|space|page|br|style|noparse)>'

    # 속성이 있는 여는 태그 패턴 (<color=#FF0000>, <size=30> 등)
    opening_tag_with_attr_pattern = r'<(?:color|size|material|pos|voffset|width|indent|line-height|line-indent|link|align|font|sprite|mspace|cspace|alpha|style)=[^>]+>'

    # 속성이 없는 단독 태그 패턴 (<b>, <i>, <quad/> 등)
    standalone_tag_pattern = r'<(?:b|i|mark|s|u|sub|sup|quad|nobr|lowercase|uppercase|smallcaps|allcaps|space|page|br|noparse)\s*/?>'

    # 모든 Unity Rich Text 태그 제거 (순서대로 적용)
    clean_text = re.sub(closing_tag_pattern, '', text, flags=re.IGNORECASE)
    clean_text = re.sub(opening_tag_with_attr_pattern, '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(standalone_tag_pattern, '', clean_text, flags=re.IGNORECASE)

    # 태그 제거 후 생긴 불필요한 공백 정리
    clean_text = re.sub(r'\s+', ' ', clean_text)
    clean_text = clean_text.strip()

    return clean_text

def process_text(text: str) -> List[str]:
    """
    따옴표(일반 "..."와 일본어 「...」, 『...』를 포함)를 보호하고, 
    문장부호(. ! ? : 및 해당 중국어/일본어 문장부호)를 기준으로 문장을 분리하여 텍스트를 전처리합니다.
    단, 단일 개행은 공백으로 병합하고, 두 개 이상의 연속 개행은 단락 구분으로 유지합니다.
    또한, 문장 분리 후 닫는 따옴표로 끝나는 문장이 있을 경우,
    뒤의 문장이 따옴표로 시작하지 않으면 두 문장을 하나로 합칩니다.
    """
    def replace_contractions(text: str, is_reverse: bool = False) -> str:
        """영어 축약어를 임시 토큰으로 치환하거나 복원합니다."""
        patterns = {
            "I'll": "IllTMP", "it's": "itsTMP", "I've": "IveTMP", "I'm": "ImTMP",
            "I'd": "IdTMP", "you're": "youreTMP", "you've": "youveTMP", 
            "you'll": "youllTMP", "you'd": "youdTMP", "he's": "hesTMP",
            "he'll": "hellTMP", "he'd": "hedTMP", "she's": "shesTMP",
            "she'll": "shellTMP", "she'd": "shedTMP", "it'll": "itllTMP",
            "it'd": "itdTMP", "we're": "wereTMP", "we've": "weveTMP",
            "we'll": "wellTMP", "we'd": "wedTMP", "they're": "theyreTMP",
            "they've": "theyveTMP", "they'll": "theyllTMP", "they'd": "theydTMP",
            "that's": "thatsTMP", "that'll": "thatllTMP", "that'd": "thatdTMP",
            "who's": "whosTMP", "who'll": "whollTMP", "who'd": "whodTMP",
            "what's": "whatsTMP", "what're": "whatreTMP", "what'll": "whatllTMP",
            "what'd": "whatdTMP", "where's": "wheresTMP", "where'll": "wherellTMP",
            "where'd": "wheredTMP", "when's": "whensTMP", "when'll": "whenllTMP",
            "when'd": "whendTMP", "why's": "whysTMP", "why'll": "whyllTMP",
            "why'd": "whydTMP", "how's": "howsTMP", "how'll": "howllTMP",
            "how'd": "howdTMP", "ain't": "aintTMP", "aren't": "arentTMP",
            "can't": "cantTMP", "couldn't": "couldntTMP", "didn't": "didntTMP",
            "doesn't": "doesntTMP", "don't": "dontTMP", "hadn't": "hadntTMP",
            "hasn't": "hasntTMP", "haven't": "haventTMP", "isn't": "isntTMP",
            "mightn't": "mightntTMP", "mustn't": "mustntTMP", "needn't": "needntTMP",
            "shan't": "shantTMP", "shouldn't": "shouldntTMP", "wasn't": "wasntTMP",
            "weren't": "werentTMP", "won't": "wontTMP", "wouldn't": "wouldntTMP"
        }
        result = text
        if is_reverse:
            for orig, temp in patterns.items():
                result = result.replace(temp, orig)
        else:
            for orig, temp in patterns.items():
                pattern = re.compile(re.escape(orig), re.IGNORECASE)
                result = pattern.sub(temp, result)
        return result

    def process_quotes(text: str) -> Tuple[str, List[str]]:
        """
        일반 인용구("...")와 일본어 인용구(「...」, 『...』)를 찾아 토큰(QUOTE0, QUOTE1 등)으로 치환하고,
        원래 인용구 텍스트는 따로 저장합니다.
        인접한 인용구 토큰 사이에는 줄바꿈을 삽입하여 별도의 문장으로 처리하도록 합니다.
        """
        quotes = []
        # 영어 인용구와 일본어 인용구 모두 처리 (비탐욕적 매칭)
        quote_pattern = r'("([^"]+?)"|「[^」]+?」|『[^』]+?』)'
        def quote_handler(match):
            quote = match.group(0)
            quotes.append(quote)
            return f" QUOTE{len(quotes)-1} "
        protected_text = re.sub(quote_pattern, quote_handler, text)
        # 인접한 인용구 토큰 사이에 줄바꿈 삽입
        protected_text = re.sub(r'(QUOTE\d+)\s+(?=QUOTE\d+)', r'\1\n', protected_text)
        return protected_text, quotes

    def split_sentences(text: str) -> List[str]:
        """
        문장부호(. ! ? : 및 해당 중국어/일본어 문장부호)와 선택적 닫는 따옴표를 기준으로 문장을 분리합니다.
        """
        pattern = re.compile(r'.+?(?:[.。!！?？]+(?:["\'”’」』])?)(?=\s+|$)', re.DOTALL)
        sentences = pattern.findall(text)
        remainder = pattern.sub('', text).strip()
        if remainder:
            sentences.append(remainder)
        return [s.strip() for s in sentences if s.strip()]

    # --- 전처리 시작 ---
    text = re.sub(r'\n{2,}', '<<PARA_BREAK>>', text)  # 두 개 이상의 연속 개행은 단락 구분
    text = re.sub(r'\n', ' ', text)                     # 단일 개행은 공백으로 대체
    text = text.replace('<<PARA_BREAK>>', '\n')          # 단락 구분 복원
    
    text = re.sub(r'(\d+)\.', r'\1∮', text)             # 숫자 뒤 온점 보호 (3.14 -> 3∮14)

    # 약어 보호 - 단, 약어 뒤에 대문자가 오면 문장의 끝으로 간주
    common_abbrev = (r'(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Sr\.|Jr\.|Ph\.D\.|M\.D\.|B\.A\.|M\.A\.|'
                    r'D\.D\.S\.|Inc\.|Ltd\.|Corp\.|Co\.|St\.|Ave\.|Rd\.|Blvd\.|Apt\.|Gov\.|Rev\.|'
                    r'Gen\.|Col\.|Sgt\.|Capt\.|Lt\.|Sen\.|Rep\.|Jan\.|Feb\.|Mar\.|Apr\.|Jun\.|Jul\.|'
                    r'Aug\.|Sep\.|Sept\.|Oct\.|Nov\.|Dec\.|Sun\.|Mon\.|Tue\.|Wed\.|Thu\.|Fri\.|Sat\.|'
                    r'A\.M\.|P\.M\.|a\.m\.|p\.m\.|U\.S\.|U\.S\.A\.|U\.K\.|E\.U\.|i\.e\.|e\.g\.|'
                    r'vs\.|v\.|Fig\.|Vol\.|pp\.|ca\.|approx\.|alt\.|def\.|ex\.|int\.|min\.|max\.|'
                    r'viz\.|P\.O\.|Tel\.|Ext\.)')

    # 약어 뒤에 소문자나 숫자가 오는 경우만 보호 (대문자가 오면 새 문장)
    text = re.sub(rf'({common_abbrev})\s+(?=[a-z0-9])', lambda m: m.group(1).replace('.', '∮') + ' ', text)

    # etc. 특별 처리: etc. 뒤에 대문자가 오면 문장 끝으로 인식, 소문자면 보호
    text = re.sub(r'etc\.\s+(?=[a-z])', 'etc∮ ', text)
    
    text = replace_contractions(text)         # 축약어 치환
    text, quotes = process_quotes(text)         # 인용구 보호 처리
    
    paragraphs = text.split('\n')
    sentences = []
    for para in paragraphs:
        sentences.extend(split_sentences(para))
    
    # 닫는 따옴표(")로 끝나는 문장이 있고, 뒤의 문장이 따옴표로 시작하지 않으면 두 문장을 합침
    merged_sentences = []
    i = 0
    while i < len(sentences):
        current = sentences[i]
        if current.endswith('"') and (i + 1 < len(sentences)) and (not sentences[i+1].lstrip().startswith('"')):
            current = current + " " + sentences[i+1]
            i += 2
        else:
            i += 1
        merged_sentences.append(current.strip())
    
    restored_sentences = []
    for sent in merged_sentences:
        for i, quote in enumerate(quotes):
            sent = sent.replace(f"QUOTE{i}", quote)
        sent = replace_contractions(sent, is_reverse=True)
        sent = sent.replace('∮', '.')
        sent = re.sub(r'\n+', ' ', sent)
        restored_sentences.append(sent.strip())
        
    return restored_sentences
