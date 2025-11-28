from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MoodType(str, Enum):
    ELATED = "elated"
    HAPPY = "happy"
    CALM = "calm"
    NEUTRAL = "neutral"
    SAD = "sad"
    ANGRY = "angry"
    ANXIOUS = "anxious"


class InteractionStyle(str, Enum):
    SUPPORTIVE = "supportive"
    SKEPTICAL = "skeptical"
    HUMOROUS = "humorous"
    CONCISE = "concise"
    VERBOSE = "verbose"


class AnalysisType(str, Enum):
    QUICK = "quick"
    COMPREHENSIVE = "comprehensive"


# UltraUserProfile 스키마 정의
class Big5(BaseModel):
    O: float = Field(ge=0, le=1, description="Openness")
    C: float = Field(ge=0, le=1, description="Conscientiousness")
    E: float = Field(ge=0, le=1, description="Extraversion")
    A: float = Field(ge=0, le=1, description="Agreeableness")
    N: float = Field(ge=0, le=1, description="Neuroticism")


class MFQ(BaseModel):
    care: int = Field(ge=0, le=100)
    fairness: int = Field(ge=0, le=100)
    loyalty: int = Field(ge=0, le=100)
    authority: int = Field(ge=0, le=100)
    purity: int = Field(ge=0, le=100)


class Values(BaseModel):
    mfq: MFQ
    schwartz: Optional[Dict[str, int]] = None
    politicalAxis: Optional[float] = Field(None, ge=-1, le=1)


class Meta(BaseModel):
    userId: int = Field(ge=1)
    schemaVersion: str = Field(pattern=r"^0\.9$")
    locale: str = "ko-KR"
    createdAt: Optional[datetime] = None
    lastUpdated: datetime
    privacyLevel: str = Field(
        default="raw", pattern="^(raw|pseudonym|aggregated)$")


class SurveyLayer(BaseModel):
    big5: Big5
    values: Values
    bdi: Optional[int] = Field(None, ge=0, le=63)
    stai: Optional[int] = Field(None, ge=20, le=80)
    mmse: Optional[int] = Field(None, ge=0, le=30)
    iq: Optional[float] = Field(None, ge=50, le=160)
    creativityTtct: Optional[float] = Field(None, ge=0)
    gpa: Optional[float] = Field(None, ge=0, le=4.5)
    languageLevelCEFR: Optional[str] = Field(
        None, pattern="^(A1|A2|B1|B2|C1|C2)$")
    bmi: Optional[float] = Field(None, ge=10, le=60)
    bloodPressure: Optional[str] = Field(
        None, pattern=r"^[0-9]{2,3}\/[0-9]{2,3}$")
    hrv: Optional[float] = Field(None, ge=10, le=200)
    lastSurveyDate: str


class ExposureSource(BaseModel):
    count: int = Field(ge=0)
    pages: int = Field(ge=0)
    minutes: float = Field(ge=0)
    rei: float = Field(ge=0)


class SentimentTriplet(BaseModel):
    pos: float = Field(ge=0, le=1)
    neu: float = Field(ge=0, le=1)
    neg: float = Field(ge=0, le=1)


class TopicVector(BaseModel):
    topicId: str
    weight: float = Field(ge=0)
    vecKey: str


class StylisticExposure(BaseModel):
    avgSentenceLength: Optional[float] = None
    lexicalRichness: Optional[float] = None
    formalityIndex: Optional[float] = None
    sentimentBalance: Optional[SentimentTriplet] = None


class TextExposureLayer(BaseModel):
    cumulativeREI: float
    daysTracked: Optional[int] = Field(None, ge=1)
    sourceBreakdown: Dict[str, ExposureSource]
    topicVectors: List[TopicVector]
    stylisticExposure: Optional[StylisticExposure] = None
    lastReadingSync: Optional[datetime] = None


class WritingStyle(BaseModel):
    formality: Optional[float] = None
    readabilityFRE: Optional[float] = None
    tone: Optional[SentimentTriplet] = None
    argumentationScore: Optional[float] = None


class RecentCorpusStats(BaseModel):
    contexts: Optional[List[str]] = None
    last30dTokens: Optional[int] = None
    codeRatio: Optional[float] = Field(None, ge=0, le=1)


class TextProductionLayer(BaseModel):
    totalWords: int = Field(ge=0)
    averageWordsPerDay: Optional[float] = None
    writingStyle: Optional[WritingStyle] = None
    recentCorpusStats: Optional[RecentCorpusStats] = None
    languageSwitchRatio: Optional[float] = Field(None, ge=0, le=1)


class DynamicStateLayer(BaseModel):
    mood: MoodType
    stress: float = Field(ge=0, le=1)
    energy: Optional[float] = Field(None, ge=0, le=1)
    fatigue: Optional[float] = Field(None, ge=0, le=1)
    contextTags: List[str]
    updatedAt: datetime


class PreferenceLayer(BaseModel):
    contentGenresLiked: Optional[List[str]] = None
    contentGenresDisliked: Optional[List[str]] = None
    interactionStyle: Optional[InteractionStyle] = None
    topicAvoidList: Optional[List[str]] = None
    languageTonePreference: str = Field(
        default="neutral", pattern="^(casual|formal|neutral)$")


class Goal(BaseModel):
    id: str
    title: str
    due: str  # date format
    progress: float = Field(ge=0, le=1)
    tags: Optional[List[str]] = None


class GoalLayer(BaseModel):
    activeGoals: Optional[List[Goal]] = None
    habitStreaks: Optional[Dict[str, int]] = None


class UltraUserProfile(BaseModel):
    meta: Meta
    surveyLayer: SurveyLayer
    textExposureLayer: TextExposureLayer
    textProductionLayer: Optional[TextProductionLayer] = None
    dynamicStateLayer: DynamicStateLayer
    preferenceLayer: Optional[PreferenceLayer] = None
    goalLayer: Optional[GoalLayer] = None


# 대화 관련 모델
class ConversationMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str
    timestamp: datetime


class BookContent(BaseModel):
    title: str
    author: Optional[str] = None
    genre: Optional[str] = None
    content: str
    readingProgress: Optional[float] = Field(None, ge=0, le=1)


class RecentBook(BaseModel):
    title: str
    summary: Optional[str] = None
    personalNotes: Optional[str] = None


class BookData(BaseModel):
    currentReading: Optional[BookContent] = None
    recentBooks: Optional[List[RecentBook]] = None


# API Request 모델들
class GenerateResponseRequest(BaseModel):
    userProfile: UltraUserProfile
    conversationHistory: List[ConversationMessage]
    bookContent: Optional[BookData] = None
    currentMessage: str


class AnalyzeDevelopmentRequest(BaseModel):
    userProfile: UltraUserProfile
    conversationHistory: List[ConversationMessage]
    bookContent: Optional[BookData] = None
    analysisType: AnalysisType = AnalysisType.COMPREHENSIVE


class AIResponse(BaseModel):
    content: str
    tone: str
    confidence: float = Field(ge=0, le=1)


class PersonalityShift(BaseModel):
    empathy: Optional[float] = None
    intellectual: Optional[float] = None
    creativity: Optional[float] = None
    analytical: Optional[float] = None
    emotional: Optional[float] = None


class CharacterEvolution(BaseModel):
    knowledgeGrowth: float = Field(ge=0, le=1)
    personalityShift: PersonalityShift
    conversationMaturity: float = Field(ge=0, le=1)


class ResponseMetadata(BaseModel):
    processingTime: float
    tokensUsed: int
    modelUsed: str = "gpt-4"
    timestamp: datetime = Field(default_factory=datetime.now)


class GenerateResponseResponse(BaseModel):
    response: AIResponse
    characterEvolution: CharacterEvolution
    metadata: ResponseMetadata


class DimensionAnalysis(BaseModel):
    score: float = Field(ge=0, le=1)
    evidence: List[str]
    trend: str = Field(pattern="^(increasing|decreasing|stable)$")


class DevelopmentDimensions(BaseModel):
    knowledgeAccumulation: DimensionAnalysis
    conversationalDepth: DimensionAnalysis
    emotionalIntelligence: DimensionAnalysis


class DevelopmentAnalysis(BaseModel):
    overallGrowth: float = Field(ge=0, le=1)
    dimensions: DevelopmentDimensions
    characterTraits: Dict[str, List[str]] = Field(
        description="dominant, emerging, weakening traits"
    )


class AnalyzeDevelopmentResponse(BaseModel):
    developmentAnalysis: DevelopmentAnalysis
    recommendations: List[str]
    metadata: ResponseMetadata


class CharacterPersonality(BaseModel):
    traits: List[str]
    dominantMood: str
    communicationStyle: str


class EvolutionChange(BaseModel):
    date: str
    changes: List[str]
    trigger: str


class KnowledgeArea(BaseModel):
    domain: str
    proficiency: float = Field(ge=0, le=1)


class CharacterState(BaseModel):
    currentPersonality: CharacterPersonality
    evolutionHistory: List[EvolutionChange]
    knowledgeAreas: List[KnowledgeArea]


class CharacterStateResponse(BaseModel):
    characterState: CharacterState
    lastUpdated: datetime = Field(default_factory=datetime.now)


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Dict[str, bool]
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None
