from pydantic import RootModel
from typing import Dict, Any, List

from langsmith.run_helpers import traceable
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.models.state import Quiz
from app.prompts.language.quiz.generator import get_quiz_generation_prompt_config
from app.utils.language.generator import language_generator
from app.models.language.quiz import ProblemType
from app.utils.logger.setup import setup_logger

logger = setup_logger('quiz_generator', 'logs/services')

# 컨테이너 모델 정의 (리스트 형태의 Quiz를 감싸는 모델)
class QuizList(RootModel[List[Quiz]]):
    pass

@traceable(run_type="chain")
async def quiz_generator(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """퀴즈 생성 에이전트"""
    try:
        state = state.get("state", state)
        
        # 모든 페이지의 텍스트를 결합
        combined_text = " ".join([
            text["text"] 
            for page in state["pages"] 
            for text in page["texts"]
        ])
        
        # 출력 파서를 컨테이너 모델로 설정
        parser = JsonOutputParser(pydantic_object=QuizList)
        format_instructions = parser.get_format_instructions()
        
        # 문제 유형 처리
        problem_types = state.get("problem_types")
        problem_type_desc = ""
        
        if problem_types:
            problem_type_names = {
                ProblemType.OX: "OX(참/거짓) 문제",
                ProblemType.TWO_CHOICE: "이지선다 문제",
                ProblemType.THREE_CHOICE: "삼지선다 문제", 
                ProblemType.FOUR_CHOICE: "사지선다 문제",
                ProblemType.FIVE_CHOICE: "오지선다 문제"
            }
            
            problem_type_list = [f"{pt} ({problem_type_names.get(pt, '')})" for pt in problem_types]
            problem_type_desc = f"\n\n생성할 문제 유형: {', '.join(map(str, problem_type_list))}"
            logger.info(f"Generating quizzes with specific problem types: {problem_types}")
        
        # 요청된 퀴즈 개수 가져오기 (없으면 기본값 사용)
        quiz_count = state.get("quiz_count", 10)  # 기본값을 10으로 설정
        logger.info(f"Requested quiz count: {quiz_count}")
        
        # 문제 유형이 지정되고 그 수가 퀴즈 개수보다 적은 경우, 생성 개수를 더 많게 설정
        generation_count = quiz_count
        if problem_types:
            # 요청된 개수보다 더 많은 퀴즈를 생성하여 필터링 후에도 충분한 퀴즈가 남도록 함
            # 최소한 (quiz_count * 2)개 또는 quiz_count + 5개 중 더 큰 값을 사용
            generation_count = max(quiz_count * 2, quiz_count + 5)
            logger.info(f"Increasing generation count to {generation_count} to ensure enough quizzes after filtering")
        
        # 프롬프트 설정 가져오기 (텍스트를 전달하여 언어 감지)
        prompt_config = get_quiz_generation_prompt_config(combined_text, generation_count)
        template = prompt_config["template"]
        
        # 문제 유형 설명 추가
        if problem_type_desc:
            template = template + problem_type_desc
        
        prompt = PromptTemplate(
            template=template,
            input_variables=prompt_config["input_variables"],
            partial_variables={"format_instructions": format_instructions}
        )
        
        # LLM 체인 생성 및 실행
        chain = prompt | language_generator
        
        logger.info(f"Generating {generation_count} quizzes from text of length: {len(combined_text)}")
        
        # API 요청에서 모델을 받아서 사용
        model_name = kwargs.get("model", "gemini")
        
        result = await chain.ainvoke({
            "text": combined_text,
            "quiz_count": generation_count
        }, config={"model": model_name})
        
        # JSON 결과 파싱
        try:
            parsed_result = parser.parse(result.content)
        except Exception as parse_error:
            logger.error(f"JSON parsing error: {parse_error}")
            logger.error(f"Raw result: {result.content[:500]}...")
            raise
        
        # parsed_result가 list 또는 RootModel 인스턴스인지 처리
        if isinstance(parsed_result, list):
            quizzes = parsed_result
        else:
            quizzes = parsed_result.root if hasattr(parsed_result, 'root') else parsed_result
        
        logger.info(f"Generated {len(quizzes)} quizzes")
        
        # 변환: quizzes가 dict 목록인지 확인하고 Quiz 객체로 변환
        quiz_objects = []
        for quiz in quizzes:
            if isinstance(quiz, dict):
                # dict를 Quiz 객체로 변환
                try:
                    quiz_obj = Quiz(
                        question=quiz.get("question", ""),
                        answer=quiz.get("answer", ""),
                        problemType=quiz.get("problemType", 0),
                        options=quiz.get("options", [])
                    )
                    quiz_objects.append(quiz_obj)
                except Exception as e:
                    logger.error(f"Error converting dict to Quiz object: {e}")
                    continue
            else:
                # 이미 Quiz 객체인 경우
                quiz_objects.append(quiz)
        
        # Quiz 객체를 사용하여 필터링
        filtered_quizzes = []
        if problem_types and quiz_objects:
            # 문제 유형별로 그룹화
            quizzes_by_type = {}
            for quiz in quiz_objects:
                if quiz.problemType in problem_types:
                    if quiz.problemType not in quizzes_by_type:
                        quizzes_by_type[quiz.problemType] = []
                    quizzes_by_type[quiz.problemType].append(quiz)
            
            # 문제 유형 배열을 순회하면서 해당 유형의 퀴즈를 추가
            for ptype in problem_types:
                if ptype in quizzes_by_type and quizzes_by_type[ptype]:
                    filtered_quizzes.append(quizzes_by_type[ptype].pop(0))
            
            # 아직 필요한 개수에 도달하지 못했다면, 남은 퀴즈들도 추가
            remaining_count = quiz_count - len(filtered_quizzes)
            if remaining_count > 0:
                remaining_quizzes = []
                for ptype in quizzes_by_type:
                    remaining_quizzes.extend(quizzes_by_type[ptype])
                
                # 남은 퀴즈들도 추가 (최대 필요한 개수만큼)
                filtered_quizzes.extend(remaining_quizzes[:remaining_count])
            
            logger.info(f"Filtered to {len(filtered_quizzes)} quizzes with requested problem types")
            
            # 필터링 후에도 개수가 부족하면 다른 문제 유형의 퀴즈도 포함
            if len(filtered_quizzes) < quiz_count:
                other_quizzes = [q for q in quiz_objects if q not in filtered_quizzes]
                additional_count = min(len(other_quizzes), quiz_count - len(filtered_quizzes))
                filtered_quizzes.extend(other_quizzes[:additional_count])
                logger.info(f"Added {additional_count} additional quizzes to meet requested count")
        else:
            # 문제 유형 필터링이 없는 경우, 모든 퀴즈 사용
            filtered_quizzes = quiz_objects
        
        # 최종적으로 요청된 개수만큼의 퀴즈 선택
        selected_quizzes = filtered_quizzes[:quiz_count]
        logger.info(f"Selected {len(selected_quizzes)} quizzes from {len(filtered_quizzes)} filtered quizzes")
        
        # state에 선택된 퀴즈 저장 (추후 validator에서 유일성 체크)
        state["raw_quizzes"] = selected_quizzes
        
        return {"state": state}
        
    except Exception as e:
        logger.error(f"Error in quiz generator: {str(e)}", exc_info=True)
        state["error"] = str(e)
        return {"state": state}
