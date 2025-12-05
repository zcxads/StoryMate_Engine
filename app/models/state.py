from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class PageText(BaseModel):
    text: str

class Page(BaseModel):
    pageKey: int
    texts: List[PageText]

class Quiz(BaseModel):
    question: str
    answer: str
    problemType: int
    options: List[str]

class QuizState(BaseModel):
    """퀴즈 생성 상태 모델"""
    pages: List[Page] = Field(default_factory=list, description="페이지 목록")
    raw_quizzes: Optional[List[Quiz]] = Field(default=None, description="생성된 원본 퀴즈 목록")
    validated_quizzes: Optional[List[Quiz]] = Field(default=None, description="검증된 퀴즈 목록")
    problem_types: Optional[List[int]] = Field(default=None, description="생성할 문제 유형 코드 목록")
    quiz_count: int = Field(default=10, description="생성할 퀴즈 개수")
    error: Optional[str] = Field(default=None, description="오류 메시지")

class LyricsOutput(BaseModel):
    songTitle: str = Field(description="Title of the generated song")
    lyrics: str = Field(description="Generated song lyrics as a string with line breaks")

class LyricsState(BaseModel):
    pages: List[Page]
    language: str
    raw_lyrics: Optional[Dict[str, Any]] = None
    formatted_lyrics: Optional[List[str]] = None
    error: Optional[str] = None

class PlayOutput(BaseModel):
    playTitle: str = Field(description="Title of the generated play")
    script: str = Field(description="Generated play script as a string with line breaks")

class PlayState(BaseModel):
    pages: List[Page]
    language: str
    raw_play: Optional[Dict[str, Any]] = None
    formatted_play: Optional[List[str]] = None
    error: Optional[str] = None

class OCRState(BaseModel):
    pages: List[Page]
    candidate_proofread: List[Dict] = []
    candidate_contextual: List[Dict] = []
    candidate_combined: List[Dict] = []
    final_pages: List[Dict] = []
    extracted_characters: List[Dict] = []
    matched_dialogues: List[Dict] = []
    voice_mappings: Dict[str, Any] = {}

# Orthography는 OCR과 같은 구조를 사용
OrthographyState = OCRState


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
    """입력된 state를 PlayState 객체로 변환"""
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
