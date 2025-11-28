from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import logging


logger = logging.getLogger(__name__)

class PageText(BaseModel):
    text: str

    def to_dict(self):
        return {"text": self.text}

class Page(BaseModel):
    pageKey: int
    texts: List[PageText]

    def to_dict(self):
        return {
            "pageKey": self.pageKey,
            "texts": [text.to_dict() for text in self.texts]
        }

class CorrectedPage(BaseModel):
    pageKey: int = Field(description="page number or key")
    text: str = Field(description="corrected text content")

class CorrectedPages(BaseModel):
    pages: List[CorrectedPage] = Field(description="list of corrected pages")

class SoundPage(BaseModel):
    pageKey: int
    texts: List[PageText]

    def to_dict(self):
        return {
            "pageKey": self.pageKey,
            "texts": [text.to_dict() for text in self.texts]
        }

class BackgroundMusic(BaseModel):
    """배경음악 정보"""
    pageKey: int
    musicPath: str
    situation: str
    categories: str
    similarityScore: str
    reason: str
    ncp_url: Optional[str] = None
    duration: Optional[float] = None  # 실제 오디오 길이 (기존 actual_duration에서 변경)

    def to_dict(self):
        return {
            "pageKey": self.pageKey,
            "musicPath": self.musicPath,
            "situation": self.situation,
            "categories": self.categories,
            "similarityScore": self.similarityScore,
            "reason": self.reason,
            "ncp_url": self.ncp_url,
            "duration": round(self.duration) if self.duration is not None else None
        }

class SoundEffect(BaseModel):
    """효과음 정보"""
    text: str
    effectPath: str
    situationInfo: str
    environmentInfo: str
    actionInfo: str
    affectInfo: str
    similarityScore: str
    reason: str
    ncp_url: Optional[str] = None
    actual_duration: Optional[float] = None  # 내부적으로 사용 (실제 오디오 길이)

    def to_dict(self):
        # 응답에서만 actual_duration 제거, 내부적으로는 유지
        return {
            "text": self.text,
            "effectPath": self.effectPath,
            "situationInfo": self.situationInfo,
            "environmentInfo": self.environmentInfo,
            "actionInfo": self.actionInfo,
            "affectInfo": self.affectInfo,
            "similarityScore": self.similarityScore,
            "reason": self.reason,
            "ncp_url": self.ncp_url
            # actual_duration은 응답에 포함하지 않음
        }

class PageSoundEffects(BaseModel):
    pageKey: int
    effects: List[SoundEffect]

    def to_dict(self):
        return {
            "pageKey": self.pageKey,
            "effects": [effect.to_dict() for effect in self.effects]
        }

class EffectPosition(BaseModel):
    effectPath: str
    position: float
    duration: float

    def to_dict(self):
        return {
            "effectPath": self.effectPath,
            "position": round(self.position) if self.position is not None else None,
            "duration": round(self.duration) if self.duration is not None else None
        }

class PageEffectPositions(BaseModel):
    pageKey: int
    positions: List[EffectPosition]

    def to_dict(self):
        return {
            "pageKey": self.pageKey,
            "positions": [pos.to_dict() for pos in self.positions]
        }

class Quiz(BaseModel):
    question: str
    answer: str
    problemType: int
    options: List[str]

    def to_dict(self):
        return {
            "question": self.question,
            "answer": self.answer,
            "problemType": self.problemType,
            "options": self.options
        }

class QuizState(BaseModel):
    """퀴즈 생성 상태 모델"""
    pages: List[Page] = Field(default_factory=list, description="페이지 목록")
    raw_quizzes: Optional[List[Quiz]] = Field(default=None, description="생성된 원본 퀴즈 목록")
    validated_quizzes: Optional[List[Quiz]] = Field(default=None, description="검증된 퀴즈 목록")
    problem_types: Optional[List[int]] = Field(default=None, description="생성할 문제 유형 코드 목록")
    quiz_count: int = Field(default=10, description="생성할 퀴즈 개수")
    error: Optional[str] = Field(default=None, description="오류 메시지")

    def to_dict(self):
        return {
            "pages": [page.to_dict() for page in self.pages],
            "raw_quizzes": [quiz.to_dict() for quiz in (self.raw_quizzes or [])],
            "validated_quizzes": [quiz.to_dict() for quiz in (self.validated_quizzes or [])],
            "problem_types": self.problem_types,
            "quiz_count": self.quiz_count,
            "error": self.error
        }

class LyricsOutput(BaseModel):
    songTitle: str = Field(description="Title of the generated song")
    lyrics: str = Field(description="Generated song lyrics as a string with line breaks")

class LyricsState(BaseModel):
    pages: List[Page] 
    language: str
    raw_lyrics: Optional[Dict[str, Any]] = None
    formatted_lyrics: Optional[List[str]] = None
    error: Optional[str] = None

    def to_dict(self):
        return {
            "pages": [page.to_dict() for page in self.pages],
            "language": self.language,
            "raw_lyrics": self.raw_lyrics,
            "formatted_lyrics": self.formatted_lyrics,
            "error": self.error
        }
        

class PlayOutput(BaseModel):
    playTitle: str = Field(description="Title of the generated play")
    script: str = Field(description="Generated play script as a string with line breaks")

class PlayState(BaseModel):
    pages: List[Page]
    language: str
    raw_play: Optional[Dict[str, Any]] = None
    formatted_play: Optional[List[str]] = None
    error: Optional[str] = None

    def to_dict(self):
        return {
            "pages": [page.to_dict() for page in self.pages],
            "language": self.language,
            "raw_play": self.raw_play,
            "formatted_play": self.formatted_play,
            "error": self.error
        }


class SoundInfo(BaseModel):
    pageKey: int
    backgroundMusic: Optional[BackgroundMusic]
    soundEffects: Optional[PageSoundEffects]
    effectPositions: Optional[PageEffectPositions]

    def to_dict(self):
        return {
            "pageKey": self.pageKey,
            "backgroundMusic": self.backgroundMusic.to_dict() if self.backgroundMusic else None,
            "soundEffects": self.soundEffects.to_dict() if self.soundEffects else None,
            "effectPositions": self.effectPositions.to_dict() if self.effectPositions else None
        }

class FinalResult(BaseModel):
    llmText: List[Dict[str, Any]]
    sound: Optional[List[SoundInfo]]
    quiz: Optional[List[Quiz]]

    def to_dict(self):
        return {
            "llmText": self.llmText,
            "sound": [s.to_dict() for s in (self.sound or [])],
            "quiz": [q.to_dict() for q in (self.quiz or [])]
        }

class AgentConfig(BaseModel):
    config_key: str = ""

class OCRState(BaseModel):
    pages: List[Page]
    candidate_proofread: List[Dict] = []
    candidate_contextual: List[Dict] = []
    candidate_combined: List[Dict] = []
    final_pages: List[Dict] = []
    extracted_characters: List[Dict] = []
    matched_dialogues: List[Dict] = []
    voice_mappings: Dict[str, Any] = {}

    def to_dict(self):
        return {
            "pages": [page.to_dict() for page in self.pages],
            "candidate_proofread": self.candidate_proofread,
            "candidate_contextual": self.candidate_contextual,
            "candidate_combined": self.candidate_combined,
            "final_pages": self.final_pages
        }

# Orthography는 OCR과 같은 구조를 사용
OrthographyState = OCRState

class SoundState(BaseModel):
    pages: List[SoundPage]
    background_music: List[BackgroundMusic] = []
    sound_effects: List[PageSoundEffects] = []
    effect_positions: List[PageEffectPositions] = []

    def to_dict(self):
        return {
            "pages": [page.to_dict() for page in self.pages],
            "background_music": [music.to_dict() for music in self.background_music],
            "sound_effects": [effect.to_dict() for effect in self.sound_effects],
            "effect_positions": [pos.to_dict() for pos in self.effect_positions]
        }


def get_valid_state(state: Any, config: Dict = None) -> OCRState:
    """입력된 state를 OCRState 객체로 변환"""
    if isinstance(state, tuple):
        state = state[0]

    if isinstance(state, OCRState):
        return state

    if isinstance(state, dict):
        # config 파라미터 제거
        if 'config' in state:
            del state['config']

        if 'state' in state:
            inner_state = state['state']
            if isinstance(inner_state, OCRState):
                return inner_state
            elif isinstance(inner_state, dict):
                if 'pages' in inner_state:
                    if not all(isinstance(p, Page) for p in inner_state['pages']):
                        inner_state['pages'] = [
                            Page(pageKey=p["pageKey"], texts=[
                                PageText(**t) for t in p["texts"]])
                            if isinstance(p, dict) else p
                            for p in inner_state['pages']
                        ]
                    return OCRState(**inner_state)
        elif 'pages' in state:
            if not all(isinstance(p, Page) for p in state['pages']):
                state['pages'] = [
                    Page(pageKey=p["pageKey"], texts=[PageText(**t)
                        for t in p["texts"]])
                    if isinstance(p, dict) else p
                    for p in state['pages']
                ]
            return OCRState(**state)

    raise ValueError(f"Invalid state format: {state}")


def get_valid_sound_state(state: Any) -> SoundState:
    """입력된 state를 SoundState 객체로 변환하고 모든 위치 정보를 적절히 처리"""
    if isinstance(state, tuple):
        state = state[0]

    if isinstance(state, SoundState):
        return state

    if isinstance(state, dict):
        # effect_positions 필드가 있는 경우 적절한 타입으로 변환
        if 'effect_positions' in state:
            positions = state['effect_positions']
            if isinstance(positions, list):
                state['effect_positions'] = [
                    PageEffectPositions(
                        **pos) if isinstance(pos, dict) else pos
                    for pos in positions
                ]

        if 'state' in state:
            inner_state = state['state']
            if isinstance(inner_state, SoundState):
                return inner_state
            elif isinstance(inner_state, dict):
                # inner_state의 effect_positions도 처리
                if 'effect_positions' in inner_state:
                    positions = inner_state['effect_positions']
                    if isinstance(positions, list):
                        inner_state['effect_positions'] = [
                            PageEffectPositions(
                                **pos) if isinstance(pos, dict) else pos
                            for pos in positions
                        ]

                if 'pages' in inner_state:
                    if not all(isinstance(p, SoundPage) for p in inner_state['pages']):
                        inner_state['pages'] = [
                            SoundPage(pageKey=p["pageKey"], texts=[
                                    PageText(**t) for t in p["texts"]])
                            if isinstance(p, dict) else p
                            for p in inner_state['pages']
                        ]
                    return SoundState(**inner_state)
                return SoundState(**inner_state)
        elif 'pages' in state:
            if not all(isinstance(p, SoundPage) for p in state['pages']):
                state['pages'] = [
                    SoundPage(pageKey=p["pageKey"], texts=[
                            PageText(**t) for t in p["texts"]])
                    if isinstance(p, dict) else p
                    for p in state['pages']
                ]
            return SoundState(**state)

    raise ValueError(f"Invalid sound state format: {state}")

def get_valid_quiz_state(state: Any) -> QuizState:
    """입력된 state를 QuizState 객체로 변환"""
    if isinstance(state, tuple):
        state = state[0]
    
    if isinstance(state, QuizState):
        return state
    
    if isinstance(state, dict):
        if 'state' in state:
            inner_state = state['state']
            if isinstance(inner_state, QuizState):
                return inner_state
            elif isinstance(inner_state, dict):
                if 'quiz' in inner_state:
                    inner_state['validated_quizzes'] = [Quiz(**q) for q in inner_state['quiz']]
                return QuizState(**inner_state)
        elif 'quiz' in state:
            state['validated_quizzes'] = [Quiz(**q) for q in state['quiz']]
        return QuizState(**state)
    
    raise ValueError(f"Invalid quiz state format: {state}")

def get_valid_lyrics_state(state: Any) -> LyricsState:
    """입력된 state를 LyricsState 객체로 변환"""
    if isinstance(state, tuple):
        state = state[0]
    
    if isinstance(state, LyricsState):
        return state
    
    if isinstance(state, dict):
        if 'state' in state:
            inner_state = state['state']
            if isinstance(inner_state, LyricsState):
                return inner_state
            elif isinstance(inner_state, dict):
                return LyricsState(**inner_state)
        return LyricsState(**state)
    
    raise ValueError(f"Invalid lyrics state format: {state}")

def get_valid_play_state(state: Any) -> PlayState:
    """입력된 state를 LyricsState 객체로 변환"""
    if isinstance(state, tuple):
        state = state[0]
    
    if isinstance(state, PlayState):
        return state
    
    if isinstance(state, dict):
        if 'state' in state:
            inner_state = state['state']
            if isinstance(inner_state, PlayState):
                return inner_state
            elif isinstance(inner_state, dict):
                return PlayState(**inner_state)
        return PlayState(**state)
    
    raise ValueError(f"Invalid play state format: {state}")

def serialize_for_json(obj):
    """객체를 JSON 직렬화 가능한 형태로 변환"""
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    return obj


def parse_final_result(ocr_result: Dict[str, Any], sound_result: Dict[str, Any], quiz_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """OCR, Sound, Quiz 결과를 통합하여 정리된 형태로 반환"""
    try:
        result = {
            "state": "Completed",
            "llmText": ocr_result.get("llmText", []),
            "sound": [],
            "quiz": []
        }

        # Sound 정보 처리
        if sound_result and "pages" in sound_result:
            pages = sound_result.get("pages", [])

            # 페이지별로 정보 통합
            for page in pages:
                page_key = page.get("pageKey")
                if not page_key:
                    continue

                # sound.py에서 각 페이지는 이미 모든 정보를 포함하고 있음
                bg_music = page.get("backgroundMusic")
                page_effects = page.get("soundEffects")
                positions = page.get("effectPositions")

                # 효과음과 포지션 정보 결합
                effects = []
                if page_effects and page_effects.get("effects"):
                    for effect in page_effects["effects"]:
                        effect_info = {
                            "text": effect.get("text", ""),
                            "sound": {
                                "path": effect.get("effectPath", ""),
                                "reason": effect.get("reason", ""),
                                "ncp_url": effect.get("ncp_url", "")
                            }
                        }

                        # 포지션 정보 추가
                        if positions and positions.get("positions"):
                            effect_path = effect.get("effectPath")
                            pos_info = next(
                                (p for p in positions["positions"] if p.get("effectPath") == effect_path),
                                None
                            )
                            if pos_info:
                                effect_info["sound"].update({
                                    "position": pos_info.get("position", 0),
                                    "duration": pos_info.get("duration", 0)
                                })

                        effects.append(effect_info)

                # 페이지별 sound 정보 추가
                sound_info = {
                    "pageKey": page_key,
                    "backgroundMusic": {
                        "path": bg_music.get("musicPath", "") if bg_music else "",
                        "reason": bg_music.get("reason", "") if bg_music else "",
                        "ncp_url": bg_music.get("ncp_url", "") if bg_music else ""
                    } if bg_music else None,
                    "effects": effects
                }
                result["sound"].append(sound_info)

        # Quiz 정보 추가 (있는 경우)
        if quiz_result and quiz_result.get("quizs"):
            result["quiz"] = [serialize_for_json(
                quiz) for quiz in quiz_result["quizs"]]

        return result

    except Exception as e:
        logger.error(f"Error parsing final result: {str(e)}", exc_info=True)
        raise ValueError(f"Error parsing final result: {str(e)}")
