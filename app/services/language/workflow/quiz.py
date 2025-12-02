from typing import List, Optional, Dict, Any, TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from app.models.state import QuizState, Page, PageText, get_valid_quiz_state
from app.services.language.quiz.generator import quiz_generator
from app.services.language.quiz.validator import quiz_validator
from app.utils.logger.setup import setup_logger
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
