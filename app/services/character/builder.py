from typing import List, Optional, Dict, Any
from app.models.language.character import (
    UltraUserProfile, 
    ConversationMessage, 
    BookData, 
    InteractionStyle,
    MoodType
)


class PromptBuilder:
    """개인화된 프롬프트 생성 클래스"""
    
    def __init__(self):
        self.base_prompt_template = """당신은 사용자와 함께 성장하는 AI 캐릭터입니다.

사용자 프로필:
- 성격 (Big5): 개방성 {openness:.2f}, 성실성 {conscientiousness:.2f}, 외향성 {extraversion:.2f}, 친화성 {agreeableness:.2f}, 신경성 {neuroticism:.2f}
- 현재 기분: {current_mood}
- 선호 상호작용 스타일: {interaction_style}
- 스트레스 수준: {stress_level:.2f}
- 독서 노출 지수 (REI): {reading_exposure:.0f}

대화 맥락:
{conversation_context}

관련 독서 내용:
{book_context}

캐릭터 지침:
1. 사용자의 성격과 현재 상태에 맞는 톤과 스타일로 대화하세요
2. 독서 내용을 자연스럽게 대화에 연결하세요
3. 사용자의 성장과 학습을 격려하고 지지하세요
4. 깊이 있고 의미 있는 대화를 유도하세요
5. 사용자의 감정 상태를 고려하여 적절한 반응을 보이세요

사용자 메시지: {user_message}

위 정보를 바탕으로 개인화된 응답을 생성해주세요."""

    def build_personalized_prompt(
        self,
        user_profile: UltraUserProfile,
        conversation_history: List[ConversationMessage],
        book_content: Optional[BookData],
        current_message: str
    ) -> str:
        """개인화된 프롬프트 생성"""
        
        # 사용자 프로필 정보 추출
        big5 = user_profile.surveyLayer.big5
        dynamic_state = user_profile.dynamicStateLayer
        preference = user_profile.preferenceLayer
        text_exposure = user_profile.textExposureLayer
        
        # 대화 맥락 요약
        conversation_context = self._summarize_conversation(conversation_history)
        
        # 책 내용 컨텍스트 생성
        book_context = self._create_book_context(book_content)
        
        # 상호작용 스타일 결정
        interaction_style = self._determine_interaction_style(user_profile)
        
        # 프롬프트 생성
        prompt = self.base_prompt_template.format(
            openness=big5.O,
            conscientiousness=big5.C,
            extraversion=big5.E,
            agreeableness=big5.A,
            neuroticism=big5.N,
            current_mood=dynamic_state.mood.value,
            interaction_style=interaction_style,
            stress_level=dynamic_state.stress,
            reading_exposure=text_exposure.cumulativeREI,
            conversation_context=conversation_context,
            book_context=book_context,
            user_message=current_message
        )
        
        return prompt

    def _summarize_conversation(self, conversation_history: List[ConversationMessage]) -> str:
        """대화 히스토리 요약"""
        if not conversation_history:
            return "이전 대화가 없습니다."
        
        # 최근 5개 메시지만 사용
        recent_messages = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        
        context_parts = []
        for msg in recent_messages:
            role_kr = "사용자" if msg.role == "user" else "AI"
            context_parts.append(f"{role_kr}: {msg.content[:100]}...")
        
        return "\n".join(context_parts)

    def _create_book_context(self, book_content: Optional[BookData]) -> str:
        """책 내용 컨텍스트 생성"""
        if not book_content:
            return "현재 독서 중인 책이 없습니다."
        
        context_parts = []
        
        if book_content.currentReading:
            current = book_content.currentReading
            progress_percent = int((current.readingProgress or 0) * 100)
            context_parts.append(
                f"현재 읽는 책: '{current.title}' by {current.author or '알 수 없음'} "
                f"(진행률: {progress_percent}%)\n"
                f"내용 일부: {current.content[:200]}..."
            )
        
        if book_content.recentBooks:
            recent_titles = [book.title for book in book_content.recentBooks[:3]]
            context_parts.append(f"최근 읽은 책들: {', '.join(recent_titles)}")
        
        return "\n".join(context_parts) if context_parts else "독서 정보가 없습니다."

    def _determine_interaction_style(self, user_profile: UltraUserProfile) -> str:
        """사용자 프로필을 바탕으로 상호작용 스타일 결정"""
        if user_profile.preferenceLayer and user_profile.preferenceLayer.interactionStyle:
            return user_profile.preferenceLayer.interactionStyle.value
        
        # Big5 성격을 바탕으로 기본 스타일 추론
        big5 = user_profile.surveyLayer.big5
        
        if big5.E > 0.7 and big5.A > 0.6:
            return "supportive"
        elif big5.O > 0.7:
            return "humorous"
        elif big5.C > 0.7:
            return "concise"
        else:
            return "supportive"  # 기본값
