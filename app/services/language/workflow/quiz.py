import json
import time
import re
from typing import List, Union, Optional, Dict, Any, TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from app.models.language.quiz import QuizRequest
from app.models.state import QuizState, Page, PageText, get_valid_quiz_state

from app.services.language.quiz.generator import quiz_generator
from app.services.language.quiz.validator import quiz_validator
from app.core.config import settings
from app.prompts.language.quiz.similar_generator import get_similar_quiz_prompt
from app.utils.logger.setup import setup_logger
from app.utils.language.generator import call_llm
from app.services.language.workflow.base_graph import BaseWorkflowGraph

# 환경 변수 로드
load_dotenv()

# 로거 설정
logger = setup_logger('quiz_workflow', 'logs/services')


# LangGraph State 정의
class QuizGraphState(TypedDict):
    """Quiz 워크플로우 상태"""
    state: Dict[str, Any]
    model: str
    problem_types: Optional[List[int]]
    quiz_count: int
    generator_result: Dict[str, Any]
    validator_result: Dict[str, Any]
    final_result: Dict[str, Any]
    error: str

# LangGraph 노드 함수들
async def generate_quiz_node(graph_state: QuizGraphState) -> QuizGraphState:
    """퀴즈 생성 노드"""
    try:
        logger.info("퀴즈 생성 노드 시작")

        model = graph_state["model"]
        state_data = graph_state["state"]

        # 퀴즈 생성
        generator_result = await quiz_generator({"state": state_data}, model=model)

        graph_state["generator_result"] = generator_result
        logger.info("퀴즈 생성 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"퀴즈 생성 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        return graph_state


async def validate_quiz_node(graph_state: QuizGraphState) -> QuizGraphState:
    """퀴즈 검증 노드"""
    try:
        logger.info("퀴즈 검증 노드 시작")

        model = graph_state["model"]
        generator_result = graph_state.get("generator_result", {})

        # 퀴즈 검증
        validator_result = await quiz_validator(generator_result, model=model)

        graph_state["validator_result"] = validator_result
        logger.info("퀴즈 검증 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"퀴즈 검증 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        return graph_state


async def assemble_quiz_results_node(graph_state: QuizGraphState) -> QuizGraphState:
    """퀴즈 결과 조합 노드"""
    try:
        logger.info("퀴즈 결과 조합 노드 시작")

        validator_result = graph_state.get("validator_result", {})

        # 최종 상태 가져오기
        final_state = get_valid_quiz_state(validator_result)

        # 응답 아이템 생성
        quizs = []
        for i, quiz in enumerate(final_state.validated_quizzes or []):
            quiz_item = {
                "id": str(i),
                "question": quiz.question,
                "answer": quiz.answer,
                "problemType": quiz.problemType,
                "options": quiz.options
            }
            quizs.append(quiz_item)

        graph_state["final_result"] = {
            "state": "Completed" if quizs else "Incompleted",
            "quizs": quizs
        }

        logger.info(f"퀴즈 결과 조합 완료 - 총 {len(quizs)}개 퀴즈")
        return graph_state

    except Exception as e:
        logger.error(f"퀴즈 결과 조합 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        graph_state["final_result"] = {
            "state": "Incompleted",
            "quizs": []
        }
        return graph_state


# LangGraph 워크플로우 클래스
class QuizWorkflowGraph(BaseWorkflowGraph):
    """Quiz LangGraph 워크플로우"""

    def __init__(self):
        super().__init__("quiz")

    def build_graph(self) -> StateGraph:
        """워크플로우 그래프 구성"""
        workflow = StateGraph(QuizGraphState)

        # 노드 추가
        workflow.add_node("generate_quiz", generate_quiz_node)
        workflow.add_node("validate_quiz", validate_quiz_node)
        workflow.add_node("assemble_results", assemble_quiz_results_node)

        # 엣지 정의
        workflow.set_entry_point("generate_quiz")
        workflow.add_edge("generate_quiz", "validate_quiz")
        workflow.add_edge("validate_quiz", "assemble_results")
        workflow.add_edge("assemble_results", END)

        return workflow


async def process_quiz_workflow(state: QuizState, model: str, problem_types: Optional[List[int]] = None, quiz_count: int = 10) -> dict:
    """퀴즈 생성 워크플로우 실행 (LangGraph 기반)"""
    try:
        logger.info(f"LangGraph 기반 퀴즈 생성 워크플로우 시작 - 퀴즈 수: {quiz_count}")

        # problemType 처리
        if problem_types:
            state.problem_types = problem_types
            logger.info(f"Using specified problem types: {problem_types}")

        # quiz_count 처리
        state.quiz_count = quiz_count

        # LangGraph 워크플로우 생성
        workflow_graph = QuizWorkflowGraph()

        # 초기 상태 준비
        initial_state: QuizGraphState = {
            "state": state.model_dump(),
            "model": model,
            "problem_types": problem_types,
            "quiz_count": quiz_count,
            "generator_result": {},
            "validator_result": {},
            "final_result": {},
            "error": ""
        }

        # 워크플로우 실행
        final_state = await workflow_graph.execute(initial_state)

        # 결과 반환
        if final_state.get("error"):
            logger.error(f"워크플로우 실행 중 오류 발생: {final_state['error']}")
            return {
                "state": "Incompleted",
                "quizs": []
            }

        return final_state.get("final_result", {
            "state": "Incompleted",
            "quizs": []
        })

    except Exception as e:
        logger.error(f"퀴즈 워크플로우 처리 중 오류 발생: {str(e)}", exc_info=True)
        return {
            "state": "Incompleted",
            "quizs": []
        }

async def process_similar_quiz_workflow_wrapper(request: Union[QuizRequest, Dict[str, Any]]) -> Dict[str, Any]:
    """
    이미지 기반 유사 문제 생성을 처리하는 wrapper 함수

    Args:
        request: QuizRequest 객체 또는 딕셔너리 형태의 요청 데이터

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
            import re
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

async def process_quiz_workflow_wrapper(request_data) -> dict:
    """API 요청을 처리하는 wrapper 함수"""
    try:
        # model 필드 추출
        model = request_data.get("model") if isinstance(request_data, dict) else getattr(request_data, "model")

        pages = []
        llm_text = request_data["llmText"] if isinstance(request_data, dict) else request_data.llmText

        # quizCount 가져오기 (기본값 10)
        quiz_count = request_data.get("quizCount", 10) if isinstance(request_data, dict) else getattr(request_data, "quizCount", 10)
        logger.info(f"Requested quiz count: {quiz_count}")

        # problemType 가져오기
        problem_types = None
        raw_problem_type = request_data.get("problemType") if isinstance(request_data, dict) else getattr(request_data, "problemType", None)

        if raw_problem_type is not None:
            # 단일 정수인 경우 리스트로 변환
            if isinstance(raw_problem_type, int):
                problem_types = [raw_problem_type]
            else:
                problem_types = raw_problem_type

            logger.info(f"Requested problem types: {problem_types}")

        for i, page in enumerate(llm_text):
            # page가 직접 텍스트 내용인 경우
            if "content" in page:
                # content를 text로 변환
                page_text = PageText(text=page["content"])
                texts = [page_text]
                pages.append(Page(pageKey=i, texts=texts))
            # page가 pageKey와 texts 구조인 경우
            elif "texts" in page:
                texts = [PageText(**text) for text in page["texts"]]
                pages.append(Page(pageKey=page["pageKey"], texts=texts))
            else:
                logger.warning(f"Unexpected page structure: {page}")
                continue

        # 상태 생성
        state = QuizState(pages=pages)

        # 워크플로우 실행 (model, problem_types, quiz_count 전달)
        result = await process_quiz_workflow(state, model=model, problem_types=problem_types, quiz_count=quiz_count)

        # 결과 반환 (제한 없음 - 모든 생성된 퀴즈 반환)
        return result
    except Exception as e:
        logger.error(f"퀴즈 워크플로우 래퍼 처리 중 오류 발생: {str(e)}", exc_info=True)
        return {
            "state": "Incompleted",
            "quizs": []
        }
