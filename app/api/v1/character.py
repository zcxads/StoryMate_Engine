from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.utils.logger.setup import setup_logger
import asyncio
from datetime import datetime

from app.models.language.character import (
    GenerateResponseRequest,
    AnalyzeDevelopmentRequest,
    GenerateResponseResponse,
    AnalyzeDevelopmentResponse,
    CharacterStateResponse,
    CharacterState,
    CharacterPersonality,
    EvolutionChange,
    KnowledgeArea,
    HealthCheckResponse,
    ErrorResponse
)
from app.services.character.generator import AIResponseGenerator, DevelopmentAnalyzer
from app.core.config import settings

# 로거 설정
logger = setup_logger('character')

# 라우터 생성
router = APIRouter(prefix="/character")

# 서비스 인스턴스
ai_generator = AIResponseGenerator()
development_analyzer = DevelopmentAnalyzer()


@router.post(
    "/generate",
    response_model=GenerateResponseResponse,
    summary="AI 캐릭터 응답 생성",
    description="사용자 프로필, 대화 기록, 책 내용을 바탕으로 개인화된 AI 캐릭터 응답을 생성합니다."
)
async def generate_response(request: GenerateResponseRequest):
    """AI 캐릭터 응답 생성"""
    try:
        logger.info(f"AI 응답 생성 요청 - 사용자 ID: {request.userProfile.meta.userId}")
        
        # AI 응답 생성
        response = await ai_generator.generate_response(request)
        
        logger.info(f"AI 응답 생성 완료 - 처리 시간: {response.metadata.processingTime:.2f}초")
        return response
        
    except Exception as e:
        logger.error(f"AI 응답 생성 중 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"AI 응답 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post(
    "/development/analyze",
    response_model=AnalyzeDevelopmentResponse,
    summary="발달 정도 분석",
    description="대화 기록과 독서 내용을 기반으로 사용자의 발달 정도를 분석합니다."
)
async def analyze_development(request: AnalyzeDevelopmentRequest):
    """발달 정도 분석"""
    try:
        logger.info(f"발달 분석 요청 - 사용자 ID: {request.userProfile.meta.userId}")
        
        # 발달 분석 실행
        analysis = await development_analyzer.analyze_development(request)
        
        logger.info(f"발달 분석 완료 - 전체 성장도: {analysis.developmentAnalysis.overallGrowth:.2f}")
        return analysis
        
    except Exception as e:
        logger.error(f"발달 분석 중 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"발달 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/state/character/{user_id}",
    response_model=CharacterStateResponse,
    summary="캐릭터 상태 조회",
    description="특정 사용자의 AI 캐릭터 현재 상태를 조회합니다."
)
async def get_character_state(user_id: int):
    """캐릭터 상태 조회"""
    try:
        logger.info(f"캐릭터 상태 조회 - 사용자 ID: {user_id}")
        
        # 임시 데이터 (실제로는 데이터베이스에서 조회)
        character_state = CharacterState(
            currentPersonality=CharacterPersonality(
                traits=["curious", "supportive", "analytical"],
                dominantMood="encouraging",
                communicationStyle="thoughtful"
            ),
            evolutionHistory=[
                EvolutionChange(
                    date="2024-01-01",
                    changes=["increased empathy", "more analytical"],
                    trigger="philosophy book discussion"
                )
            ],
            knowledgeAreas=[
                KnowledgeArea(domain="literature", proficiency=0.8),
                KnowledgeArea(domain="philosophy", proficiency=0.6),
                KnowledgeArea(domain="science", proficiency=0.7)
            ]
        )
        
        response = CharacterStateResponse(
            characterState=character_state,
            lastUpdated=datetime.now()
        )
        
        logger.info(f"캐릭터 상태 조회 완료 - 사용자 ID: {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"캐릭터 상태 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"캐릭터 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="캐릭터 서비스 상태 확인",
    description="AI 캐릭터 서비스의 상태를 확인합니다."
)
async def health_check():
    """캐릭터 서비스 헬스체크"""
    try:
        # 서비스 상태 확인
        services_status = {
            "ai_generator": True,
            "development_analyzer": True,
            "llm_service": bool(settings.openai_api_key or settings.gemini_api_key),
            "prompt_builder": True
        }
        
        all_healthy = all(services_status.values())
        
        return HealthCheckResponse(
            status="healthy" if all_healthy else "degraded",
            timestamp=datetime.now(),
            services=services_status,
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"헬스체크 중 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"헬스체크 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/",
    summary="캐릭터 서비스 정보",
    description="AI 캐릭터 서비스의 기본 정보를 반환합니다."
)
async def get_service_info():
    """캐릭터 서비스 정보"""
    return {
        "service": "AI Character Service",
        "version": "1.0.0",
        "description": "개인화된 AI 캐릭터 응답 생성 및 발달 분석 서비스",
        "endpoints": [
            "/character/generate-response - AI 응답 생성",
            "/character/analyze-development - 발달 분석",
            "/character/character-state/{user_id} - 캐릭터 상태 조회",
            "/character/health - 서비스 상태 확인"
        ],
        "features": [
            "개인화된 AI 응답 생성",
            "사용자 발달 정도 분석",
            "캐릭터 진화 추적",
            "독서 내용 기반 대화",
            "성격 기반 상호작용 스타일"
        ]
    }
