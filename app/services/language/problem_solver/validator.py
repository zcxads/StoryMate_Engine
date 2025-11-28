"""
문제 이미지 유효성 검증 서비스
"""

import base64
import os
from typing import Dict, Any

from app.models.language.problem_solver import ProblemValidationResult, ProblemType
from app.prompts.language.problem_solver import get_problem_validation_prompt
from app.utils.logger.setup import setup_logger
from app.core.config import settings

logger = setup_logger('problem_validator', 'logs/services')
logger.setLevel(10)  # DEBUG 레벨로 설정

class ProblemImageValidator:
    """문제 이미지 유효성 검증 클래스"""
    
    def __init__(self):
        self.validation_prompt = get_problem_validation_prompt()

    async def validate_problem_image(
        self,
        image_base64: str,
        model: str = settings.llm_advanced_analysis_model
    ) -> ProblemValidationResult:
        """
        문제 이미지 유효성 검증

        Args:
            image_base64: Base64 인코딩된 이미지 데이터
            model: 사용할 모델

        Returns:
            ProblemValidationResult: 검증 결과
        """
        try:
            from app.utils.language.generator import call_llm

            logger.info(f"문제 이미지 검증 시작 - 모델: {model}")

            # Base64 이미지 데이터 처리
            if image_base64.startswith('data:image'):
                image_base64 = image_base64.split(',')[1]

            # 이미지와 텍스트를 포함한 메시지 생성
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.validation_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]

            logger.info("LLM 검증 호출 시작...")

            # LLM 호출 - call_llm 사용
            response = await call_llm(prompt=messages, model=model)
            result_text = response.content if response.content else ""
            
            logger.info("문제 이미지 검증 완료")
            
            # 응답 파싱 및 검증 결과 생성
            validation_result = self._parse_validation_response(result_text)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"문제 이미지 검증 중 오류 발생: {str(e)}", exc_info=True)
            return self._create_error_validation_result(str(e))
    
    def _parse_validation_response(self, response_text: str) -> ProblemValidationResult:
        """검증 응답 파싱"""
        try:
            import json
            import re
                        
            # 빈 응답 처리 - 기본적으로 정상 처리
            if not response_text or response_text.strip() == "":
                logger.warning("빈 응답 수신, 기본적으로 정상 처리")
                return ProblemValidationResult(
                    is_valid=True,
                    problem_type=ProblemType.VALID_SINGLE,
                    confidence=0.5,
                    message="",
                    details={"empty_response": True, "fallback": "empty_default_valid"}
                )
            
            # JSON 블록 추출
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                # 직접 JSON 형태 추출 시도
                json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                else:
                    logger.error(f"JSON 형식을 찾을 수 없음: {response_text}")
                    raise ValueError(f"JSON 형식을 찾을 수 없습니다: {response_text}")
            
            # 빈 JSON 문자열 처리
            if not json_str:
                logger.error("JSON 문자열이 비어있음")
                raise ValueError("JSON 문자열이 비어있음")
            
            # JSON 파싱
            try:
                parsed = json.loads(json_str)
                logger.info(f"JSON 파싱 성공: {parsed}")
            except json.JSONDecodeError as je:
                logger.error(f"JSON 파싱 실패: {je}")
                logger.info("파싱 실패 시 기본적으로 정상 처리")
                # JSON 파싱 실패 시 기본적으로 정상 문제로 처리
                return ProblemValidationResult(
                    is_valid=True,
                    problem_type=ProblemType.VALID_SINGLE,
                    confidence=0.7,
                    message="",
                    details={"json_error": str(je), "raw_response": response_text, "fallback": "default_valid"}
                )
            
            # 문제 유형 매핑 (기존 세부 카테고리는 INVALID로 통합)
            original_type = parsed.get('problem_type', 'valid_single')  # 기본값을 valid_single로 변경
            logger.info(f"파싱된 문제 유형: {original_type}")
            
            # LLM 판단 결과를 신뢰하여 처리
            if original_type == 'invalid':
                problem_type = ProblemType.INVALID
                logger.info("LLM이 invalid로 판단하여 비정상 처리")
            else:
                # valid_single 또는 기타 경우는 정상 처리
                problem_type = ProblemType.VALID_SINGLE
                logger.info("LLM이 정상으로 판단하여 정상 처리")
            
            confidence = float(parsed.get('confidence', 0.5))
            details = parsed.get('details', {})
            
            # 유효성 및 메시지 결정
            is_valid = problem_type == ProblemType.VALID_SINGLE
            message = self._get_user_message(problem_type) if not is_valid else ""
            
            return ProblemValidationResult(
                is_valid=is_valid,
                problem_type=problem_type,
                confidence=confidence,
                message=message,
                details=details
            )
            
        except Exception as e:
            logger.error(f"검증 응답 파싱 실패: {str(e)}")
            logger.error(f"원본 응답 텍스트: {response_text}")
            return self._create_error_validation_result(str(e))
    
    def _get_user_message(self, problem_type: ProblemType) -> str:
        """문제 유형에 따른 사용자 메시지 반환 (비정상적인 경우 통일된 메시지)"""
        # 모든 비정상적인 경우에 대해 통일된 메시지 반환
        return "한 문제만 찍어서 업로드해주세요."
    
    def _create_error_validation_result(self, error_message: str) -> ProblemValidationResult:
        """오류 시 기본 검증 결과 생성 - 기본적으로 정상 처리"""
        logger.info(f"오류 발생으로 기본적으로 정상 처리: {error_message}")
        return ProblemValidationResult(
            is_valid=True,
            problem_type=ProblemType.VALID_SINGLE,
            confidence=0.6,
            message="",
            details={"error": error_message, "fallback": "error_default_valid"}
        )

    async def validate_multiple_images(
        self,
        images: list,
        model: str = settings.llm_advanced_analysis_model
    ) -> ProblemValidationResult:
        """
        다중 이미지에서 독립적인 문제 여부 검증
        온전한 문제가 1개 있으면 풀이 진행, 온전한 문제가 2개 이상이면 재업로드 요청

        Args:
            images: Base64 인코딩된 이미지 데이터 리스트
            model: 사용할 모델

        Returns:
            ProblemValidationResult: 검증 결과
        """
        try:
            logger.info(f"다중 이미지 검증 시작 - 이미지 수: {len(images)}, 모델: {model}")

            # 각 이미지에 대해 검증하고 완전한 문제와 불완전한 문제 구분
            complete_problems = 0  # 온전한 문제 개수
            validation_details = []

            for i, image_base64 in enumerate(images):
                logger.info(f"이미지 {i+1}/{len(images)} 검증 중...")

                # 개별 이미지 검증
                validation_result = await self.validate_problem_image(image_base64, model)

                # 검증 결과 저장
                image_detail = {
                    "image_index": i+1,
                    "is_valid": validation_result.is_valid,
                    "problem_type": validation_result.problem_type.value,
                    "confidence": validation_result.confidence
                }
                validation_details.append(image_detail)

                # 정상적인 단일 문제로 인식되면 완전한 문제로 카운트
                if validation_result.is_valid and validation_result.problem_type == ProblemType.VALID_SINGLE:
                    complete_problems += 1
                    logger.info(f"이미지 {i+1}: 온전한 문제로 감지됨 (총 {complete_problems}개)")
                else:
                    logger.info(f"이미지 {i+1}: 불완전한 문제 또는 비문제로 감지됨")

            logger.info(f"온전한 문제 총 개수: {complete_problems}")

            # 온전한 문제가 2개 이상이면 재업로드 요청
            if complete_problems >= 2:
                logger.info("여러 개의 온전한 문제가 감지됨 - 재업로드 요청")
                return ProblemValidationResult(
                    is_valid=False,
                    problem_type=ProblemType.INVALID,
                    confidence=0.9,
                    message="한 문제만 찍어서 업로드해주세요.",
                    details={
                        "complete_problems_count": complete_problems,
                        "total_images": len(images),
                        "reason": "multiple_complete_problems",
                        "validation_details": validation_details
                    }
                )
            elif complete_problems == 1:
                # 온전한 문제가 1개 있으면 정상 처리 (잘린 문제가 있어도 상관없음)
                logger.info("온전한 문제 1개 감지됨 - 정상 처리 (잘린 문제 무시)")
                return ProblemValidationResult(
                    is_valid=True,
                    problem_type=ProblemType.VALID_SINGLE,
                    confidence=0.8,
                    message="",
                    details={
                        "complete_problems_count": complete_problems,
                        "total_images": len(images),
                        "reason": "single_complete_problem_detected",
                        "validation_details": validation_details
                    }
                )
            else:
                # 온전한 문제가 0개면 재업로드 요청
                logger.info("온전한 문제가 없음 - 재업로드 요청")
                return ProblemValidationResult(
                    is_valid=False,
                    problem_type=ProblemType.INVALID,
                    confidence=0.8,
                    message="한 문제만 찍어서 업로드해주세요.",
                    details={
                        "complete_problems_count": complete_problems,
                        "total_images": len(images),
                        "reason": "no_complete_problems",
                        "validation_details": validation_details
                    }
                )

        except Exception as e:
            logger.error(f"다중 이미지 검증 중 오류 발생: {str(e)}", exc_info=True)
            # 오류 발생 시 기본적으로 정상 처리 (보수적 접근)
            return ProblemValidationResult(
                is_valid=True,
                problem_type=ProblemType.VALID_SINGLE,
                confidence=0.6,
                message="",
                details={"error": str(e), "fallback": "multi_image_error_default_valid"}
            )