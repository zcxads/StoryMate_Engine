"""
이미지 기반 문제 해결 워크플로우 래퍼
"""

import time
import re
import json
from typing import Dict, Any, Union, TypedDict

from langgraph.graph import StateGraph, END

from app.models.language.explanation import ExplanationRequest
from app.services.language.explanation.solver import solve_problem_from_image
from app.utils.logger.setup import setup_logger
from app.core.config import settings
from app.services.language.workflow.base_graph import BaseWorkflowGraph
from app.prompts.language.quiz.similar_generator import get_similar_quiz_prompt
from app.utils.language.generator import call_llm

# 로거 설정
logger = setup_logger('explanation_workflow', 'logs/workflow')


# LangGraph State 정의
class ExplanationGraphState(TypedDict):
    """Explanation 워크플로우 상태"""
    model: str
    problem_image: str
    language: str
    problem_result: Dict[str, Any]
    genre_enum: Any
    final_result: Dict[str, Any]
    error: str
    start_time: float

# LangGraph 노드 함수들
async def solve_problem_node(graph_state: ExplanationGraphState) -> ExplanationGraphState:
    """문제 해결 노드"""
    try:
        logger.info("문제 해결 노드 시작")

        model = graph_state["model"]
        problem_image = graph_state["problem_image"]
        language = graph_state["language"]

        # 문제 해결
        problem_result = await solve_problem_from_image(problem_image, model, language)

        graph_state["problem_result"] = problem_result
        logger.info("문제 해결 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"문제 해결 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        return graph_state


async def detect_genre_node(graph_state: ExplanationGraphState) -> ExplanationGraphState:
    """장르 감지 노드"""
    try:
        logger.info("장르 감지 노드 시작")

        problem_result = graph_state.get("problem_result", {})
        model = graph_state["model"]
        language = graph_state["language"]

        # 장르 자동 감지
        genre_enum = None
        try:
            from app.services.language.content_category.analyzer import ContentCategoryAnalyzer
            from app.models.language.content_category import ContentCategoryRequest

            # 문제와 해설 텍스트 결합하여 장르 분석
            combined_text = f"{problem_result.get('answer')} {problem_result.get('solution')} {problem_result.get('concepts')}"

            analyzer = ContentCategoryAnalyzer()
            category_request = ContentCategoryRequest(
                llmText=[{"pageKey": 0, "texts": [{"text": combined_text}]}],
                model=model,
                language=language
            )

            category_result = await analyzer.analyze_content(category_request)
            genre_enum = category_result.genre
            logger.info(f"Auto-detected genre: {genre_enum.value}")
        except Exception as e:
            logger.warning(f"Failed to auto-detect genre: {str(e)}")

        graph_state["genre_enum"] = genre_enum
        logger.info("장르 감지 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"장르 감지 노드 오류: {str(e)}", exc_info=True)
        # 장르 감지 실패는 치명적이지 않으므로 계속 진행
        graph_state["genre_enum"] = None
        return graph_state


async def assemble_explanation_results_node(graph_state: ExplanationGraphState) -> ExplanationGraphState:
    """문제 해결 결과 조합 노드"""
    try:
        logger.info("문제 해결 결과 조합 노드 시작")

        problem_result = graph_state.get("problem_result", {})
        genre_enum = graph_state.get("genre_enum")
        model = graph_state["model"]
        start_time = graph_state["start_time"]

        # 실행 시간 계산
        execution_time = f"{time.time() - start_time:.2f}s"

        # 최종 응답 구성
        final_result = problem_result.copy()
        final_result.update({
            "genre": genre_enum,
            "model_used": model,
            "execution_time": execution_time,
            "status": "success" if not graph_state.get("error") else "error"
        })

        if graph_state.get("error"):
            final_result["error"] = graph_state["error"]

        graph_state["final_result"] = final_result
        logger.info(f"문제 해결 결과 조합 완료 - 실행시간: {execution_time}")
        return graph_state

    except Exception as e:
        logger.error(f"문제 해결 결과 조합 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        return graph_state


# LangGraph 워크플로우 클래스
class ExplanationWorkflowGraph(BaseWorkflowGraph):
    """Explanation LangGraph 워크플로우"""

    def __init__(self):
        super().__init__("explanation")

    def build_graph(self) -> StateGraph:
        """워크플로우 그래프 구성"""
        workflow = StateGraph(ExplanationGraphState)

        # 노드 추가
        workflow.add_node("solve_problem", solve_problem_node)
        workflow.add_node("detect_genre", detect_genre_node)
        workflow.add_node("assemble_results", assemble_explanation_results_node)

        # 엣지 정의
        workflow.set_entry_point("solve_problem")
        workflow.add_edge("solve_problem", "detect_genre")
        workflow.add_edge("detect_genre", "assemble_results")
        workflow.add_edge("assemble_results", END)

        return workflow


async def process_explanation_workflow_wrapper(request: Union[ExplanationRequest, Dict[str, Any]]) -> Dict[str, Any]:
    """
    API 요청을 입력받아 이미지 기반 문제를 해결하고 결과를 반환하는 wrapper 함수. (LangGraph 기반)

    Args:
        request: ExplanationRequest 객체 또는 딕셔너리 형태의 요청 데이터

    Returns:
        Dict[str, Any]: 문제 해결 결과를 포함한 응답 데이터
    """
    start_time = time.time()

    try:
        logger.info("LangGraph 기반 문제 해결 워크플로우 처리 시작")

        # 요청 데이터 추출
        if isinstance(request, dict):
            model = request.get("model")
            problem_image = request.get("problem")
            language = request.get("language")
        else:
            model = getattr(request, "model")
            problem_image = getattr(request, "problem")
            language = getattr(request, "language")
            # Pydantic 모델인 경우 dict로 변환
            if hasattr(request, 'model_dump'):
                request_dict = request.model_dump()
                model = request_dict.get("model")
                problem_image = request_dict.get("problem")
                language = request_dict.get("language")
            elif hasattr(request, 'dict'):
                request_dict = request.dict()
                model = request_dict.get("model")
                problem_image = request_dict.get("problem")
                language = request_dict.get("language")

        if not problem_image:
            raise ValueError("문제 이미지 데이터가 없습니다.")

        logger.info(f"문제 해결 시작 - 모델: {model}, 언어: {language}")

        # LangGraph 워크플로우 생성
        workflow_graph = ExplanationWorkflowGraph()

        # 초기 상태 준비
        initial_state: ExplanationGraphState = {
            "model": model,
            "problem_image": problem_image,
            "language": language,
            "problem_result": {},
            "genre_enum": None,
            "final_result": {},
            "error": "",
            "start_time": start_time
        }

        # 워크플로우 실행
        final_state = await workflow_graph.execute(initial_state)

        # 오류가 있으면 예외 발생
        if final_state.get("error"):
            raise Exception(final_state["error"])

        logger.info("문제 해결 워크플로우 처리 완료")
        return final_state.get("final_result", {})

    except Exception as e:
        execution_time = f"{time.time() - start_time:.2f}s"
        error_msg = f"문제 해결 워크플로우 실패: {str(e)}"
        logger.info(error_msg)

        # Exception을 그대로 전파하여 API에서 detail로 처리
        raise e


async def process_similar_quiz_workflow_wrapper(request: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    """
    이미지 기반 유사 문제 생성을 처리하는 wrapper 함수

    Args:
        request: 딕셔너리 형태의 요청 데이터

    Returns:
        Dict[str, Any]: 유사 문제 생성 결과를 포함한 응답 데이터

    Raises:
        Exception: 문제 생성 실패 시 에러 메시지와 함께 예외 발생
    """
    start_time = time.time()

    logger.info("유사 문제 생성 워크플로우 처리 시작")

    # 요청 데이터 추출
    if isinstance(request, dict):
        model = request.get("model", settings.llm_advanced_analysis_model)
        problem_image = request.get("problem")
        language = request.get("language")
    else:
        model = getattr(request, "model", settings.llm_advanced_analysis_model)
        problem_image = getattr(request, "problem")
        language = getattr(request, "language")

        # Pydantic 모델인 경우 dict로 변환
        if hasattr(request, 'model_dump'):
            request_dict = request.model_dump()
            model = request_dict.get("model", settings.llm_advanced_analysis_model)
            problem_image = request_dict.get("problem")
            language = request_dict.get("language")
        elif hasattr(request, 'dict'):
            request_dict = request.dict()
            model = request_dict.get("model", settings.llm_advanced_analysis_model)
            problem_image = request_dict.get("problem")
            language = request_dict.get("language")

    if not problem_image:
        raise ValueError("문제 이미지 데이터가 없습니다.")

    logger.info(f"유사 문제 생성 시작 - 모델: {model}, 언어: {language}")

    # 이미지에서 1문제 판단 및 유사 문제 생성
    result = await generate_similar_quiz_from_image(problem_image, model, language)

    # 실행 시간 계산
    execution_time = f"{time.time() - start_time:.2f}s"

    # 최종 응답 구성
    final_result = {
        "question": result.get("question", ""),
        "answer": result.get("answer", ""),
        "options": result.get("options", []),
        "explanation": result.get("explanation", ""),
        "execution_time": execution_time
    }

    logger.info(f"유사 문제 생성 워크플로우 처리 완료 - 실행시간: {execution_time}")
    return final_result


async def generate_similar_quiz_from_image(problem_image: str, model: str, language: str) -> Dict[str, Any]:
    """
    이미지에서 1문제만 있는지 판단하고 유사한 문제를 생성

    Args:
        problem_image: Base64 인코딩된 이미지 데이터
        model: 사용할 LLM 모델
        language: 응답 언어

    Returns:
        Dict[str, Any]: 생성된 유사 문제 정보

    Raises:
        Exception: 문제 생성 실패 시 에러 메시지와 함께 예외 발생
    """

    logger.info("이미지 분석 및 유사 문제 생성 시작...")

    # 프롬프트 생성 (모듈화된 함수 사용)
    prompt_text = get_similar_quiz_prompt(language)

    logger.info(f"모델 준비 완료 - {model}")

    # Base64 이미지 데이터 처리
    if problem_image.startswith('data:image'):
        problem_image = problem_image.split(',')[1]

    # 이미지와 텍스트를 포함한 메시지 생성
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{problem_image}"
                    }
                }
            ]
        }
    ]

    logger.info("LLM 호출 시작...")
    response = await call_llm(prompt=messages, model=model)

    logger.info("LLM 응답 수신 완료")
    response_text = response.content

    # JSON 응답 파싱 (파싱 실패 시 자동으로 Exception 발생)
    result = parse_quiz_response(response_text)

    logger.info(f"유사 문제 생성 완료 - 결과: {result}")

    return result


def validate_quiz_logic(quiz_data: Dict[str, Any]) -> Dict[str, Any]:
    """생성된 퀴즈의 논리적 일관성을 검증"""
    try:
        logger.info("퀴즈 논리적 검증 시작")

        question = quiz_data.get("question", "")
        options = quiz_data.get("options", [])

        validation_issues = []

        # 1. 기본 필드 검증
        if not question.strip():
            validation_issues.append("문제가 비어있음")

        # 2. 객관식 문제 검증
        if options and len(options) > 0:
            # 선택지 개수 검증 (최소 2개, 최대 5개)
            if len(options) < 2:
                validation_issues.append("선택지가 너무 적음 (최소 2개 필요)")
            elif len(options) > 5:
                validation_issues.append("선택지가 너무 많음 (최대 5개)")

        # 3. 수학 문제 검증 (간단한 패턴 매칭)
        if any(keyword in question.lower() for keyword in ['계산', '구하', 'calculate', 'find', '=', '+', '-', '*', '/', '×', '÷']):
            # 숫자가 있는지 확인
            numbers = re.findall(r'\d+(?:\.\d+)?', question)
            if not numbers:
                validation_issues.append("수학 문제에 구체적인 수치가 없음")

        # 4. 검증 결과 처리
        if validation_issues:
            logger.warning(f"논리적 검증에서 문제 발견: {validation_issues}")
            # 경미한 문제는 그대로 반환, 심각한 문제는 오류 표시
            serious_issues = [issue for issue in validation_issues
                            if any(keyword in issue for keyword in ['비어있음'])]

            if serious_issues:
                quiz_data["validation_error"] = f"논리적 오류 발견: {', '.join(serious_issues)}"
                logger.error(f"심각한 논리적 오류: {serious_issues}")
        else:
            logger.info("논리적 검증 통과")

        return quiz_data

    except Exception as e:
        logger.error(f"논리적 검증 중 오류: {str(e)}")
        quiz_data["validation_error"] = f"검증 중 오류 발생: {str(e)}"
        return quiz_data


def parse_quiz_response(response_text: str) -> Dict[str, Any]:
    """
    LLM 응답에서 JSON 데이터 추출 및 파싱

    Raises:
        Exception: JSON 파싱 실패 시 원본 텍스트를 에러 메시지로 raise
    """
    try:
        logger.info(f"LLM 응답 파싱 시작 - 응답 길이: {len(response_text)}")
        logger.debug(f"LLM 원본 응답: {response_text[:500]}...")

        # JSON 블록 찾기
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            logger.info("JSON 블록 형태에서 추출")
        else:
            # ```없이 JSON만 있는 경우
            json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.info("단순 JSON 형태에서 추출")
            else:
                logger.error("JSON 형식을 찾을 수 없음")
                # JSON이 없다는 것은 에러 메시지를 텍스트로 반환했다는 의미
                raise Exception(response_text.strip())

        logger.debug(f"추출된 JSON 문자열: {json_str}")

        # JSON 파싱
        result = json.loads(json_str)
        logger.info(f"최종 파싱 결과: {result}")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {str(e)}", exc_info=True)
        logger.error(f"파싱 실패 원본 텍스트: {response_text}")
        # JSON 파싱 실패 = 에러 메시지 텍스트로 간주
        raise Exception(response_text.strip())
    except Exception as e:
        # Exception이 이미 발생한 경우 그대로 전파
        raise
