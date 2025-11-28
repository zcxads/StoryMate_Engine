import asyncio
import time
from typing import List, Optional
from datetime import datetime

from app.models.language.character import (
    UltraUserProfile,
    ConversationMessage,
    BookData,
    GenerateResponseRequest,
    AnalyzeDevelopmentRequest,
    AIResponse,
    PersonalityShift,
    CharacterEvolution,
    ResponseMetadata,
    GenerateResponseResponse,
    DimensionAnalysis,
    DevelopmentDimensions,
    DevelopmentAnalysis,
    AnalyzeDevelopmentResponse
)
from app.services.character.builder import PromptBuilder
from app.utils.language.generator import call_llm
from app.core.config import settings
from app.utils.logger.setup import setup_logger

logger = setup_logger('character_generator')


class AIResponseGenerator:
    """AI 응답 생성 서비스"""
    
    def __init__(self):
        self.prompt_builder = PromptBuilder()
    
    async def generate_response(self, request: GenerateResponseRequest) -> GenerateResponseResponse:
        """개인화된 AI 응답 생성"""
        start_time = time.time()
        
        try:
            # 1. 개인화 프롬프트 생성
            prompt = self.prompt_builder.build_personalized_prompt(
                request.userProfile,
                request.conversationHistory,
                request.bookContent,
                request.currentMessage
            )
            
            # 2. LLM으로 응답 생성
            llm_response = await call_llm(
                prompt=prompt,
                model=settings.default_llm_model or "gemini"
            )
            
            # LLM 응답에서 텍스트 추출
            response_text = ""
            if hasattr(llm_response, 'content'):
                response_text = llm_response.content
            else:
                response_text = str(llm_response)
            
            # 3. 응답 톤 분석
            tone = self._analyze_tone(response_text, request.userProfile)
            
            # 4. 캐릭터 진화 계산
            character_evolution = self._calculate_character_evolution(
                request.conversationHistory,
                request.bookContent,
                request.userProfile
            )
            
            # 5. 메타데이터 생성
            processing_time = time.time() - start_time
            metadata = ResponseMetadata(
                processingTime=processing_time,
                tokensUsed=int(len(response_text.split()) * 1.3),  # 근사치를 정수로 변환
                modelUsed=settings.default_llm_model or "gemini",
                timestamp=datetime.now()
            )
            
            # 6. 응답 구성
            ai_response = AIResponse(
                content=response_text,
                tone=tone,
                confidence=0.85  # 기본값
            )
            
            return GenerateResponseResponse(
                response=ai_response,
                characterEvolution=character_evolution,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"AI 응답 생성 중 오류: {str(e)}")
            raise e
    
    def _analyze_tone(self, response_text: str, user_profile: UltraUserProfile) -> str:
        """응답 톤 분석"""
        # 간단한 톤 분석 로직
        text_lower = response_text.lower()
        
        if any(word in text_lower for word in ["축하", "훌륭", "멋져", "대단"]):
            return "encouraging"
        elif any(word in text_lower for word in ["궁금", "어떻게", "왜"]):
            return "curious"
        elif user_profile.preferenceLayer and user_profile.preferenceLayer.interactionStyle:
            return user_profile.preferenceLayer.interactionStyle.value
        else:
            return "supportive"
    
    def _calculate_character_evolution(
        self,
        conversation_history: List[ConversationMessage],
        book_content: Optional[BookData],
        user_profile: UltraUserProfile
    ) -> CharacterEvolution:
        """캐릭터 진화 정도 계산"""
        
        # 지식 성장 계산 (독서 노출과 대화 복잡도 기반)
        knowledge_growth = min(
            (user_profile.textExposureLayer.cumulativeREI / 10000) * 0.5 +
            (len(conversation_history) / 50) * 0.5,
            1.0
        )
        
        # 성격 변화 계산
        personality_shift = PersonalityShift(
            empathy=0.02 if user_profile.surveyLayer.big5.A > 0.6 else 0.01,
            intellectual=0.03 if book_content and book_content.currentReading else 0.01,
            creativity=0.02 if user_profile.surveyLayer.big5.O > 0.7 else 0.01,
            analytical=0.01,
            emotional=0.01
        )
        
        # 대화 성숙도 계산
        conversation_maturity = min(
            len(conversation_history) / 100,
            1.0
        )
        
        return CharacterEvolution(
            knowledgeGrowth=knowledge_growth,
            personalityShift=personality_shift,
            conversationMaturity=conversation_maturity
        )


class DevelopmentAnalyzer:
    """발달 분석 서비스"""
    
    def __init__(self):
        pass
    
    async def analyze_development(self, request: AnalyzeDevelopmentRequest) -> AnalyzeDevelopmentResponse:
        """발달 정도 분석"""
        start_time = time.time()
        
        try:
            # 1. 지식 축적 분석
            knowledge_analysis = self._analyze_knowledge_accumulation(
                request.userProfile, 
                request.bookContent
            )
            
            # 2. 대화 깊이 분석
            conversation_analysis = self._analyze_conversational_depth(
                request.conversationHistory
            )
            
            # 3. 감정 지능 분석
            emotional_analysis = self._analyze_emotional_intelligence(
                request.conversationHistory,
                request.userProfile
            )
            
            # 4. 종합 분석
            dimensions = DevelopmentDimensions(
                knowledgeAccumulation=knowledge_analysis,
                conversationalDepth=conversation_analysis,
                emotionalIntelligence=emotional_analysis
            )
            
            overall_growth = (
                knowledge_analysis.score + 
                conversation_analysis.score + 
                emotional_analysis.score
            ) / 3
            
            # 5. 캐릭터 특성 분석
            character_traits = self._analyze_character_traits(request.userProfile)
            
            # 6. 추천사항 생성
            recommendations = await self._generate_recommendations(
                request.userProfile,
                dimensions
            )
            
            # 7. 메타데이터 생성
            processing_time = time.time() - start_time
            metadata = ResponseMetadata(
                processingTime=processing_time,
                tokensUsed=int(500),  # 근사치를 정수로 변환
                modelUsed=settings.default_llm_model or "gemini",
                timestamp=datetime.now()
            )
            
            development_analysis = DevelopmentAnalysis(
                overallGrowth=overall_growth,
                dimensions=dimensions,
                characterTraits=character_traits
            )
            
            return AnalyzeDevelopmentResponse(
                developmentAnalysis=development_analysis,
                recommendations=recommendations,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"발달 분석 중 오류: {str(e)}")
            raise e
    
    def _analyze_knowledge_accumulation(
        self, 
        user_profile: UltraUserProfile, 
        book_content: Optional[BookData]
    ) -> DimensionAnalysis:
        """지식 축적 분석"""
        
        rei_score = min(user_profile.textExposureLayer.cumulativeREI / 10000, 1.0)
        book_score = 0.3 if book_content and book_content.currentReading else 0.0
        diversity_score = len(user_profile.textExposureLayer.sourceBreakdown) / 10
        
        score = (rei_score * 0.5 + book_score + diversity_score * 0.2)
        
        evidence = []
        if rei_score > 0.7:
            evidence.append("높은 독서 노출 지수")
        if book_content and book_content.currentReading:
            evidence.append("현재 활발한 독서 활동")
        if len(user_profile.textExposureLayer.sourceBreakdown) > 3:
            evidence.append("다양한 텍스트 소스 노출")
        
        trend = "increasing" if score > 0.6 else "stable"
        
        return DimensionAnalysis(
            score=min(score, 1.0),
            evidence=evidence,
            trend=trend
        )
    
    def _analyze_conversational_depth(
        self, 
        conversation_history: List[ConversationMessage]
    ) -> DimensionAnalysis:
        """대화 깊이 분석"""
        
        if not conversation_history:
            return DimensionAnalysis(
                score=0.0,
                evidence=["대화 기록 없음"],
                trend="stable"
            )
        
        # 대화 길이와 복잡도 분석
        avg_length = sum(len(msg.content) for msg in conversation_history) / len(conversation_history)
        complexity_score = min(avg_length / 100, 1.0)
        
        # 질문의 복잡도 분석
        user_messages = [msg for msg in conversation_history if msg.role == "user"]
        question_quality = sum(1 for msg in user_messages if any(word in msg.content for word in ["왜", "어떻게", "무엇", "언제"])) / max(len(user_messages), 1)
        
        score = (complexity_score * 0.6 + question_quality * 0.4)
        
        evidence = []
        if avg_length > 50:
            evidence.append("상세한 대화 내용")
        if question_quality > 0.3:
            evidence.append("깊이 있는 질문")
        if len(conversation_history) > 20:
            evidence.append("지속적인 대화 참여")
        
        trend = "increasing" if score > 0.5 else "stable"
        
        return DimensionAnalysis(
            score=min(score, 1.0),
            evidence=evidence,
            trend=trend
        )
    
    def _analyze_emotional_intelligence(
        self,
        conversation_history: List[ConversationMessage],
        user_profile: UltraUserProfile
    ) -> DimensionAnalysis:
        """감정 지능 분석"""
        
        # Big5 성격 기반 감정 지능 추정
        agreeableness = user_profile.surveyLayer.big5.A
        emotional_stability = 1 - user_profile.surveyLayer.big5.N
        
        personality_score = (agreeableness + emotional_stability) / 2
        
        # 대화에서 감정 표현 분석
        emotional_words = ["기쁘", "슬프", "화나", "놀라", "걱정", "감사", "사랑", "미안"]
        user_messages = [msg for msg in conversation_history if msg.role == "user"]
        
        emotional_expression = sum(
            1 for msg in user_messages 
            if any(word in msg.content for word in emotional_words)
        ) / max(len(user_messages), 1)
        
        score = (personality_score * 0.7 + emotional_expression * 0.3)
        
        evidence = []
        if agreeableness > 0.7:
            evidence.append("높은 친화성")
        if emotional_stability > 0.6:
            evidence.append("감정적 안정성")
        if emotional_expression > 0.2:
            evidence.append("풍부한 감정 표현")
        
        trend = "increasing" if score > 0.6 else "stable"
        
        return DimensionAnalysis(
            score=min(score, 1.0),
            evidence=evidence,
            trend=trend
        )
    
    def _analyze_character_traits(self, user_profile: UltraUserProfile) -> dict:
        """캐릭터 특성 분석"""
        
        big5 = user_profile.surveyLayer.big5
        
        dominant_traits = []
        emerging_traits = []
        weakening_traits = []
        
        # Big5 기반 특성 분석
        if big5.O > 0.7:
            dominant_traits.append("curious")
            emerging_traits.append("creative")
        if big5.C > 0.7:
            dominant_traits.append("organized")
        if big5.E > 0.7:
            dominant_traits.append("social")
        if big5.A > 0.7:
            dominant_traits.append("empathetic")
        if big5.N < 0.3:
            dominant_traits.append("stable")
        
        # 기본 특성 추가
        if not dominant_traits:
            dominant_traits = ["thoughtful", "learning-oriented"]
        
        emerging_traits.extend(["analytical", "growth-minded"])
        
        if big5.N > 0.7:
            weakening_traits.append("impulsive")
        
        return {
            "dominant": dominant_traits,
            "emerging": emerging_traits,
            "weakening": weakening_traits
        }
    
    async def _generate_recommendations(
        self,
        user_profile: UltraUserProfile,
        dimensions: DevelopmentDimensions
    ) -> List[str]:
        """개인화된 추천사항 생성"""
        
        recommendations = []
        
        # 지식 축적 기반 추천
        if dimensions.knowledgeAccumulation.score < 0.5:
            recommendations.append("더 다양한 장르의 책을 읽어보세요")
        elif dimensions.knowledgeAccumulation.score > 0.8:
            recommendations.append("전문 서적이나 학술 논문에 도전해보세요")
        
        # 대화 깊이 기반 추천
        if dimensions.conversationalDepth.score < 0.5:
            recommendations.append("더 구체적이고 깊이 있는 질문을 해보세요")
        
        # 감정 지능 기반 추천
        if dimensions.emotionalIntelligence.score < 0.5:
            recommendations.append("감정 표현과 공감 능력을 기를 수 있는 활동을 해보세요")
        
        # 성격 기반 추천
        big5 = user_profile.surveyLayer.big5
        if big5.O > 0.7:
            recommendations.append("창의적 사고를 자극하는 예술이나 철학서를 추천합니다")
        
        # 기본 추천사항
        if not recommendations:
            recommendations = [
                "꾸준한 독서와 깊이 있는 대화를 계속하세요",
                "다양한 관점에서 생각해보는 습관을 기르세요"
            ]
        
        return recommendations[:5]  # 최대 5개까지
