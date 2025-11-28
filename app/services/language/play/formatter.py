import logging
import json
from typing import Dict, Any, List

from langsmith.run_helpers import traceable

logger = logging.getLogger(__name__)

@traceable(run_type="chain")
async def play_formatter(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """연극 대사 포매터 에이전트 - 연극 대사를 일관된 형식으로 구조화"""
    try:
        state = state.get("state", state)
        raw_play = state.get("raw_play") or {}
        # 간단 스키마(B안): playTitle, script 문자열을 우선 사용
        play_title = raw_play.get("playTitle")
        play_data = raw_play.get("script", "")

        def _normalize_play_dict(play_dict: Dict[str, Any]) -> Dict[str, Any]:
            title = play_dict.get("title") or ""
            characters = play_dict.get("characters") or []
            scenes = play_dict.get("scenes") or []
            moral = play_dict.get("moral") or ""

            # characters 정규화
            normalized_characters: List[Dict[str, Any]] = []
            for c in characters if isinstance(characters, list) else []:
                name = c.get("name") if isinstance(c, dict) else None
                desc = c.get("description") if isinstance(c, dict) else None
                if name:
                    normalized_characters.append({
                        "name": str(name).strip(),
                        "description": str(desc).strip() if isinstance(desc, str) else ""
                    })

            # scenes 정규화
            normalized_scenes: List[Dict[str, Any]] = []
            for s in scenes if isinstance(scenes, list) else []:
                if not isinstance(s, dict):
                    continue
                scene_no = s.get("scene")
                try:
                    scene_no = int(scene_no) if scene_no is not None else None
                except Exception:
                    scene_no = None
                stage = s.get("stage_direction") if isinstance(s.get("stage_direction"), str) else ""
                lines = s.get("lines") if isinstance(s.get("lines"), list) else []
                normalized_lines: List[Dict[str, str]] = []
                for ln in lines:
                    if isinstance(ln, dict):
                        ch = ln.get("character")
                        dl = ln.get("dialogue")
                        if isinstance(ch, str) and isinstance(dl, str):
                            normalized_lines.append({"character": ch.strip(), "dialogue": dl.strip()})
                normalized_scenes.append({
                    "scene": scene_no,
                    "stage_direction": stage,
                    "lines": normalized_lines
                })

            return {
                "title": title,
                "characters": normalized_characters,
                "scenes": normalized_scenes,
                "moral": moral
            }

        def _flatten_script(play_dict: Dict[str, Any]) -> List[str]:
            script: List[str] = []
            title = play_dict.get("title")
            if isinstance(title, str) and title.strip():
                script.append(f"[Title] {title.strip()}")

            # scene 구분 없이 모든 대사를 순차적으로 처리
            for s in play_dict.get("scenes", []):
                stage = s.get("stage_direction")
                if isinstance(stage, str) and stage.strip():
                    script.append(f"(Stage) {stage.strip()}")
                for ln in s.get("lines", []):
                    ch = ln.get("character")
                    dl = ln.get("dialogue")
                    if isinstance(ch, str) and isinstance(dl, str) and dl.strip():
                        # 긴 대사 안전 절단(선택적)
                        text = dl.strip()
                        if len(text) > 400:
                            text = text[:397] + "..."
                        script.append(f"{ch.strip()}: {text}")

            moral = play_dict.get("moral")
            if isinstance(moral, str) and moral.strip():
                script.append(f"[Moral] {moral.strip()}")
            return script

        formatted_play: List[str] = []

        # 1) JSON 우선 처리
        normalized: Dict[str, Any] = {}
        if isinstance(play_data, dict):
            normalized = _normalize_play_dict(play_data)
        elif isinstance(play_data, str):
            # 문자열이면 JSON 파싱 시도 → 실패 시 라인 파싱 폴백
            try:
                parsed = json.loads(play_data)
                if isinstance(parsed, dict):
                    normalized = _normalize_play_dict(parsed)
            except Exception:
                normalized = {}

        if normalized:
            formatted_play = _flatten_script(normalized)
            logger.info(f"JSON play normalized to {len(formatted_play)} lines")
        else:
            # 2) 문자열 폴백 처리(기존 로직 개선)
            text = play_data if isinstance(play_data, str) else ""
            lines = [ln.strip() for ln in text.strip().split('\n') if ln.strip()]

            for line in lines:
                # 무대 지시: '무대지시:' 또는 'Stage:' 접두사
                if line.startswith('무대지시:'):
                    content = line.split(':', 1)[1].strip() if ':' in line else ''
                    if content:
                        formatted_play.append(f"(Stage) {content}")
                    continue

                if line.startswith('Stage:'):
                    content = line.split(':', 1)[1].strip() if ':' in line else ''
                    if content:
                        formatted_play.append(f"(Stage) {content}")
                    continue

                # 교훈: '교훈:' 또는 'Moral:'
                if line.startswith('교훈:'):
                    content = line.split(':', 1)[1].strip() if ':' in line else ''
                    if content:
                        formatted_play.append(f"[Moral] {content}")
                    continue

                if line.startswith('Moral:'):
                    content = line.split(':', 1)[1].strip() if ':' in line else ''
                    if content:
                        formatted_play.append(f"[Moral] {content}")
                    continue

                # 대사: '이름: 내용' 패턴 우선 처리
                if ':' in line:
                    name_part, content_part = line.split(':', 1)
                    name_part = name_part.strip()
                    content_part = content_part.strip()
                    if name_part and content_part and len(name_part) <= 40:
                        formatted_play.append(f"{name_part}: {content_part}")
                        continue

                # 기타 라인은 그대로 유지
                formatted_play.append(line)

            logger.info(f"Plain text play converted to {len(formatted_play)} lines")

        # 제목이 있으면 최상단에 추가
        if isinstance(play_title, str) and play_title.strip():
            formatted_play = [f"[Title] {play_title.strip()}"] + formatted_play

        state["formatted_play"] = formatted_play
        return {"state": state}
        
    except Exception as e:
        logger.error(f"Error in play formatter: {str(e)}")
        state["error"] = str(e)
        return {"state": state}
