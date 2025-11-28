import logging
from typing import Dict, Any

from langsmith.run_helpers import traceable

logger = logging.getLogger(__name__)

@traceable(run_type="chain")
async def lyrics_formatter(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """노래 가사 포매터 에이전트 - 노래를 일관된 형식으로 구조화"""
    try:
        state = state.get("state", state)
        raw_lyrics = state.get("raw_lyrics") or {}
        lyrics_text = raw_lyrics.get("lyrics", "")
        formatted_lyrics = []
        
        # 가사가 문자열인 경우 처리
        if isinstance(lyrics_text, str):
            # 줄 단위로 분리
            lines = lyrics_text.strip().split('\n')
            
            # 각 줄 추가
            for line in lines:
                line = line.strip()
                if not line:  # 빈 줄 건너뛰기
                    continue
                    
                # 섹션 헤더 처리
                if line.startswith('후렴:') or line.startswith('1절:') or line.startswith('2절:') or line.startswith('다리:'):
                    parts = line.split(':', 1)
                    section_name = parts[0].strip()
                    content = parts[1].strip() if len(parts) > 1 else ""
                    
                    if section_name == '후렴':
                        formatted_lyrics.append('[Chorus]')
                    elif section_name == '1절':
                        formatted_lyrics.append('[Verse 1]')
                    elif section_name == '2절':
                        formatted_lyrics.append('[Verse 2]')
                    elif section_name == '다리':
                        formatted_lyrics.append('[Bridge]')
                        
                    # 섹션 이름 다음의 내용이 있는 경우 추가
                    if content:
                        formatted_lyrics.append(content)
                else:
                    formatted_lyrics.append(line)
            
            logger.info(f"String lyrics converted to {len(formatted_lyrics)} lines")
        else:
            # 기존 딕셔너리 형태 처리 (하위 호환성 유지)
            lyrics_dict = lyrics_text if isinstance(lyrics_text, dict) else {}
            
            # 필수 섹션 순서 정의
            section_order = [
                ("verse1", "Verse 1"),
                ("chorus", "Chorus"),
                ("verse2", "Verse 2"),
                ("bridge", "Bridge"),
                ("chorus", "Chorus")  # 마지막에 코러스 반복
            ]
            
            # 각 섹션 처리
            for section_key, section_label in section_order:
                if section_key in lyrics_dict:
                    formatted_lyrics.append(f"[{section_label}]")
                    lines = lyrics_dict[section_key]
                    if isinstance(lines, list):
                        formatted_lyrics.extend(lines)
                    else:
                        logger.warning(f"Section {section_key} is not a list of lines")
        
        state["formatted_lyrics"] = formatted_lyrics
        logger.info(f"Formatted {len(formatted_lyrics)} lines of lyrics")
        
        return {"state": state}
        
    except Exception as e:
        logger.error(f"Error in lyrics formatter: {str(e)}")
        state["error"] = str(e)
        return {"state": state}
