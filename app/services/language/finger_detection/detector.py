import os
import time
import json
import base64
from typing import Dict, Any, Optional
from app.models.language.finger_detection import FingerDetectionRequest, DocumentReadingResponse
from app.utils.language.generator import call_llm
from app.core.config import settings
from app.utils.logger.setup import setup_logger
from app.prompts.language.finger_detection.detector import get_finger_detection_prompt
from app.core.messages import (
    FINGER_NO_FINGER_MESSAGE,
)
from app.prompts.language.finger_detection.document_reader import DocumentReadingPrompt

logger = setup_logger("finger_detection")

class FingerDetectionService:
    """손가락 가리키기 인식 서비스"""
    
    def __init__(self):
        self.output_dir = os.path.join(settings.output_dir, "finger_detection")
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def analyze_finger_pointing(self, request: FingerDetectionRequest) -> Dict[str, Any]:
        """
        손가락으로 가리킨 내용을 분석하거나 문서를 읽습니다.
        
        Args:
            request: 손가락 인식 또는 문서 읽기 요청 데이터
            
        Returns:
            Dict: 분석 결과
        """
        # 모드에 따라 분기
        mode = getattr(request, 'mode', 'finger_detection')
        
        if mode == 'document_reading':
            return await self.analyze_document_reading(request)
        else:
            return await self._analyze_finger_detection(request)
    
    async def _analyze_finger_detection(self, request: FingerDetectionRequest) -> Dict[str, Any]:
        """
        기존 손가락 인식 분석
        
        Args:
            request: 손가락 인식 요청 데이터
            
        Returns:
            Dict: 분석 결과
        """
        start_time = time.time()
        try:
            logger.info(f"손가락 인식 분석 시작: 모델={request.model}")
            
            # Base64 이미지 데이터 검증
            validation_result = self._validate_image_data(request.image_data)
            if not validation_result["is_valid"]:
                return {
                    "status": "error",
                    "error": validation_result["message"]
                }
            
            # 프롬프트 생성
            prompt = self._build_detection_prompt(request)
            
            # LLM으로 이미지 분석 수행
            try:
                # 이미지 데이터를 포함한 메시지 구성
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{request.image_data}"
                                }
                            }
                        ]
                    }
                ]
                
                # GPT-5 또는 다른 비전 모델로 분석
                result = await call_llm(
                    prompt=messages,
                    model=request.model
                )
                
                # 결과 처리
                if hasattr(result, 'content'):
                    analysis_result = result.content
                elif isinstance(result, str):
                    analysis_result = result
                else:
                    analysis_result = str(result)
                    
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"LLM 분석 실패: {str(e)}"
                }
            
            # 결과 후처리
            processed_result = await self._process_analysis_result(
                analysis_result,
                request,
                start_time
            )

            # 손가락 인식 실패 시 (message만 있는 경우) 바로 반환
            if "message" in processed_result and len(processed_result) == 1:
                logger.info(f"손가락 인식 실패 - 메시지만 반환: {processed_result.get('message')}")
                return processed_result

            # 장르 자동 감지
            genre_enum = None
            try:
                from app.services.language.content_category.analyzer import ContentCategoryAnalyzer
                from app.models.language.content_category import ContentCategoryRequest
                from app.models.language.content_category import Genre

                # 분석 결과 텍스트를 사용하여 장르 분석
                detected_text = processed_result.get("explanation", "")

                # 텍스트가 있는 경우에만 장르 분석 수행
                if detected_text and detected_text.strip():
                    analyzer = ContentCategoryAnalyzer()
                    category_request = ContentCategoryRequest(
                        llmText=[{"pageKey": 0, "texts": [{"text": detected_text}]}],
                        model=request.model,
                        language="ko"
                    )

                    category_result = await analyzer.analyze_content(category_request)
                    genre_enum = category_result.genre
                    logger.info(f"Auto-detected genre: {genre_enum.value}")
                else:
                    # 텍스트가 없으면 기본값 설정
                    genre_enum = Genre.PRACTICAL
                    logger.info("텍스트가 없어 기본 장르로 설정: practical")
            except Exception as e:
                # 장르 감지 실패 시 기본값으로 practical 설정
                from app.models.language.content_category import Genre
                genre_enum = Genre.PRACTICAL
                logger.warning(f"Failed to auto-detect genre, using default 'practical': {str(e)}")

            processed_result.update({
                "genre": genre_enum,
                "model_used": request.model,
                "status": "success"
            })

            logger.info(f"손가락 인식 분석 완료: {request.model}")
            return processed_result
            
        except Exception as e:
            error_msg = f"손가락 인식 분석 중 오류: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def _validate_image_data(self, image_data: str) -> Dict[str, Any]:
        """Base64 이미지 데이터를 검증합니다."""
        try:
            # Base64 디코딩 시도
            image_bytes = base64.b64decode(image_data)
            
            # 기본적인 이미지 형식 검증 (시작 바이트 확인)
            if not self._is_valid_image_format(image_bytes):
                return {
                    "is_valid": False,
                    "message": "지원되지 않는 이미지 형식입니다. JPEG, PNG, WebP, GIF 형식을 사용해주세요."
                }
            
            # 이미지 크기 검증 (10MB 제한)
            if len(image_bytes) > 10 * 1024 * 1024:
                return {
                    "is_valid": False,
                    "message": "이미지 크기가 10MB를 초과했습니다."
                }
            
            return {
                "is_valid": True,
                "message": "유효한 이미지 데이터입니다."
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "message": f"이미지 데이터 검증 실패: {str(e)}"
            }
    
    def _is_valid_image_format(self, image_bytes: bytes) -> bool:
        """이미지 형식을 검증합니다."""
        # JPEG
        if image_bytes.startswith(b'\xff\xd8\xff'):
            return True
        # PNG
        if image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            return True
        # WebP
        if image_bytes[8:12] == b'WEBP':
            return True
        # GIF
        if image_bytes.startswith((b'GIF87a', b'GIF89a')):
            return True
        
        return False
    
    def _build_detection_prompt(self, request: FingerDetectionRequest) -> str:
        """손가락 인식 프롬프트를 구성합니다."""

        # 요청된 언어에 맞는 프롬프트 반환
        language = getattr(request, 'language', 'ko')
        return get_finger_detection_prompt(language=language)
    
    def _clean_escape_characters(self, text: str) -> str:
        """응답 텍스트에서 모든 백슬래시 escape 패턴을 제거합니다."""
        if not text:
            return text
        
        # \" 패턴이 등장하면 \" 전체를 제거 (쌍따옴표까지 모두 제거)
        text = text.replace('\\"', '')
        
        return text.strip()
    
    def _add_line_breaks_after_periods(self, text: str) -> str:
        """마침표 기준으로 줄바꿈을 추가합니다."""
        if not text:
            return text
            
        import re
        
        text = re.sub(r"\.\s*", ".\n", text)
        
        return text.strip()

    async def _process_analysis_result(
        self,
        analysis_result: str,
        request: FingerDetectionRequest,
        start_time: float = None
    ) -> Dict[str, Any]:
        """분석 결과를 후처리합니다."""

        # 실행 시간 계산
        if start_time is not None:
            execution_time = f"{time.time() - start_time:.2f}s"
        else:
            execution_time = "0.00s"

        # escape 문자 제거
        cleaned_result = self._clean_escape_characters(analysis_result.strip())

        # JSON 파싱 시도 (새로운 구조화된 응답 형식)
        detected_word = None
        meaning = None
        explanation = None
        ncp_url = None

        try:
            # JSON 블록 추출
            json_str = None
            if "```json" in cleaned_result:
                json_start = cleaned_result.find("```json") + 7
                json_end = cleaned_result.find("```", json_start)
                if json_end > json_start:
                    json_str = cleaned_result[json_start:json_end].strip()

            # JSON 객체 찾기
            if not json_str:
                start_brace = cleaned_result.find("{")
                if start_brace != -1:
                    end_brace = cleaned_result.rfind("}")
                    if end_brace > start_brace:
                        json_str = cleaned_result[start_brace:end_brace + 1].strip()

            # 전체를 JSON으로 시도
            if not json_str:
                json_str = cleaned_result.strip()

            # JSON 파싱
            if json_str:
                parsed_data = json.loads(json_str)

                # 새로운 형식: status 필드 체크
                status = parsed_data.get("status")

                # Case 1: NO_FINGER
                if status == "NO_FINGER":
                    logger.info("손가락 없음 감지됨 - 재업로드 요청")
                    return {
                        "message": parsed_data.get("message", FINGER_NO_FINGER_MESSAGE)
                    }

                # Case 2: EMPTY_POINTING
                if status == "EMPTY_POINTING":
                    logger.info("허공 가리키기 감지됨 - 재업로드 요청")
                    return {
                        "message": parsed_data.get("message", FINGER_NO_FINGER_MESSAGE)
                    }

                # Case 3: 정상 감지된 경우
                detected_word = parsed_data.get("detected_word", "")
                is_meaningful = parsed_data.get("is_meaningful", True)  # 기본값 True
                meaning = parsed_data.get("meaning", "")
                explanation = parsed_data.get("explanation", "")

                # LLM이 판단한 의미 없는 단어 검증
                if not is_meaningful:
                    logger.warning(f"LLM이 의미 없는 단어로 판단: '{detected_word}' - 분석 실패 메시지 반환")
                    return {
                        "message": FINGER_NO_FINGER_MESSAGE
                    }

                # detected_word가 있으면 TTS 생성
                if detected_word:
                    ncp_url = await self._generate_pronunciation_tts(detected_word)

                # 마침표 기준 줄바꿈 추가
                formatted_explanation = self._add_line_breaks_after_periods(explanation)

                # 정상 결과 구조
                result = {
                    "detected_word": detected_word,
                    "meaning": meaning,
                    "explanation": formatted_explanation,
                    "ncp_url": ncp_url,
                    "execution_time": execution_time
                }

                return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {str(e)}")
            logger.error(f"응답 내용: {cleaned_result[:500]}")
        except Exception as e:
            logger.error(f"분석 결과 처리 중 오류: {str(e)}")

        # JSON 파싱 실패 시 기존 방식으로 처리
        formatted_result = self._add_line_breaks_after_periods(cleaned_result)

        # 정상 결과 구조 - 필수 필드만 포함
        result = {
            "detected_word": "인식 실패",
            "meaning": "의미를 파악할 수 없습니다",
            "explanation": formatted_result,
            "ncp_url": None,
            "execution_time": execution_time
        }

        return result

    async def _generate_pronunciation_tts(self, detected_word: str) -> Optional[str]:
        """감지된 단어/문장의 발음 TTS를 생성합니다."""
        try:
            from app.services.voice.tts.generator import TTSService
            from app.models.voice.tts import SingleTTSRequest, GenderType

            logger.info(f"TTS 생성 시작 - 단어: {detected_word}")

            # TTS 서비스 초기화
            tts_service = TTSService()

            # 단일 TTS 생성 요청 (config의 default_tts_provider 사용)
            tts_request = SingleTTSRequest(
                text=detected_word,
                voice=None,  # provider에 따라 자동 선택
                gender_hint=GenderType.MALE
            )

            # TTS 생성
            tts_response = await tts_service.generate_single_tts(tts_request)

            if tts_response.success and tts_response.ncp_url:
                logger.info(f"TTS 생성 성공 - URL: {tts_response.ncp_url}")
                return tts_response.ncp_url
            else:
                logger.warning(f"TTS 생성 실패: {tts_response.message}")
                return None

        except Exception as e:
            logger.error(f"TTS 생성 중 오류 발생: {str(e)}")
            return None
    
    async def analyze_document_reading(self, request: FingerDetectionRequest) -> Dict[str, Any]:
        """
        문서 읽기 및 구조화 분석을 수행합니다.
        
        Args:
            request: 문서 읽기 요청 데이터
            
        Returns:
            Dict: 문서 읽기 결과
        """
        start_time = time.time()
        
        try:
            logger.info(f"문서 읽기 분석 시작: 모델={request.model}")
            
            # Base64 이미지 데이터 검증
            validation_result = self._validate_image_data(request.image_data)
            if not validation_result["is_valid"]:
                return {
                    "status": "error",
                    "error": validation_result["message"]
                }
            
            # 문서 읽기 프롬프트 생성 (읽기 방향 적용)
            prompt_generator = DocumentReadingPrompt()
            prompt = prompt_generator.get_prompt()
            
            # LLM으로 문서 분석 수행
            try:
                # 이미지 데이터를 포함한 메시지 구성
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{request.image_data}"
                                }
                            }
                        ]
                    }
                ]
                
                # LLM으로 문서 분석
                result = await call_llm(
                    prompt=messages,
                    model=request.model
                )
                
                # 결과 처리
                if hasattr(result, 'content'):
                    analysis_result = result.content
                elif isinstance(result, str):
                    analysis_result = result
                else:
                    analysis_result = str(result)
                    
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"LLM 문서 분석 실패: {str(e)}"
                }
            
            # JSON 파싱 및 구조화된 결과 생성
            try:
                # JSON 블록 추출 (여러 패턴 지원)
                json_str = None
                
                # 패턴 1: ```json ... ``` 블록
                if "```json" in analysis_result:
                    json_start = analysis_result.find("```json") + 7
                    json_end = analysis_result.find("```", json_start)
                    if json_end > json_start:
                        json_str = analysis_result[json_start:json_end].strip()
                
                # 패턴 2: { ... } JSON 객체만 찾기
                if not json_str:
                    start_brace = analysis_result.find("{")
                    if start_brace != -1:
                        # 마지막 } 찾기
                        end_brace = analysis_result.rfind("}")
                        if end_brace > start_brace:
                            json_str = analysis_result[start_brace:end_brace + 1].strip()
                            logger.info(f"JSON 객체 추출 (패턴 2): {json_str[:300]}")
                
                # 패턴 3: 전체 응답을 JSON으로 시도
                if not json_str:
                    json_str = analysis_result.strip()
                    logger.info(f"전체 응답을 JSON으로 파싱 시도 (패턴 3): {json_str[:300]}")
                
                # JSON 파싱
                if not json_str:
                    raise ValueError("JSON 형태의 응답을 찾을 수 없습니다")
                    
                parsed_result = json.loads(json_str)
                
                # 실행 시간 계산
                execution_time = f"{time.time() - start_time:.2f}s"
                
                # escape 문자 제거 후 DocumentReadingResponse 형식으로 응답 생성
                cleaned_markdown = self._clean_escape_characters(parsed_result.get("markdown_content", ""))
                
                response = {
                    "markdown_content": cleaned_markdown,
                    "detected_language": parsed_result.get("detected_language"),
                    "document_type": parsed_result.get("document_type"),
                    "execution_time": execution_time,
                    "status": "success",
                    "model_used": request.model
                }
                
                logger.info(f"문서 읽기 분석 완료: 언어={response['detected_language']}, 유형={response['document_type']}, 소요시간={execution_time}")
                return response
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {e}")
                # JSON 파싱 실패 시 원문을 마크다운으로 처리 (escape 문자 제거 적용)
                execution_time = f"{time.time() - start_time:.2f}s"
                cleaned_analysis = self._clean_escape_characters(analysis_result)
                return {
                    "markdown_content": f"# 문서 내용\\n\\n{cleaned_analysis}",
                    "detected_language": "unknown",
                    "document_type": "unknown",
                    "execution_time": execution_time,
                    "status": "success",
                    "model_used": request.model
                }
                
        except Exception as e:
            error_msg = f"문서 읽기 분석 중 오류: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "execution_time": f"{time.time() - start_time:.2f}s"
            }