import logging
from typing import Dict, Any, List, Tuple

from langsmith.run_helpers import traceable

from app.models.state import Quiz
from app.models.language.quiz import ProblemType

logger = logging.getLogger(__name__)

# 다국어 참/거짓 답변 매핑
TRUE_FALSE_MAPPINGS = {
    # 한국어
    "참": "O", "거짓": "X", "맞음": "O", "틀림": "X", "정답": "O", "오답": "X",
    "맞다": "O", "틀리다": "X", "맞습니다": "O", "틀렸습니다": "X",
    # 영어
    "True": "O", "False": "X", "true": "O", "false": "X",
    "TRUE": "O", "FALSE": "X", "Correct": "O", "Incorrect": "X",
    "Yes": "O", "No": "X", "yes": "O", "no": "X",
    # 일본어
    "正しい": "O", "間違い": "X", "はい": "O", "いいえ": "X",
    "○": "O", "×": "X", "正解": "O", "不正解": "X",
    # 중국어
    "正确": "O", "错误": "X", "对": "O", "错": "X",
    "是": "O", "否": "X", "正確": "O", "錯誤": "X",
    # 기본 O/X
    "O": "O", "X": "X"
}

def normalize_true_false_answer(answer: str, options: List[str]) -> tuple[str, List[str]]:
    """참/거짓 답변을 O/X 형식으로 정규화"""
    # 답변 정규화
    normalized_answer = TRUE_FALSE_MAPPINGS.get(answer.strip(), answer.strip())
    
    # 옵션들도 정규화
    normalized_options = []
    for option in options:
        normalized_option = TRUE_FALSE_MAPPINGS.get(option.strip(), option.strip())
        normalized_options.append(normalized_option)
    
    # 중복 제거하고 O, X 순서로 정렬
    unique_options = list(set(normalized_options))
    if "O" in unique_options and "X" in unique_options:
        normalized_options = ["O", "X"]
    elif len(unique_options) >= 2:
        # O/X가 아닌 경우, 첫 번째를 O로, 두 번째를 X로 매핑
        first_option = unique_options[0]
        second_option = unique_options[1]
        if answer.strip() == options[0].strip():
            normalized_answer = "O"
        else:
            normalized_answer = "X"
        normalized_options = ["O", "X"]
    else:
        # 기본값
        normalized_options = ["O", "X"]
        if normalized_answer not in normalized_options:
            normalized_answer = "O"
    
    return normalized_answer, normalized_options

def validate_multi_choice_options(options: List[str], expected_count: int = 2) -> List[str]:
    """객관식 문제 옵션 검증 및 정리"""
    if not options:
        return []
    
    # 빈 문자열이나 None 제거
    clean_options = [opt.strip() for opt in options if opt and opt.strip()]
    
    # 중복 제거하면서 순서 유지
    seen = set()
    unique_options = []
    for opt in clean_options:
        if opt not in seen:
            seen.add(opt)
            unique_options.append(opt)
    
    # 지정된 개수만큼의 옵션이 있는지 확인
    if len(unique_options) >= expected_count:
        return unique_options[:expected_count]  # 요청된 개수만큼만 사용
    else:
        # 옵션이 부족한 경우, 추가 생성
        base_options = unique_options.copy()
        for i in range(expected_count - len(unique_options)):
            base_options.append(f"선택지 {len(base_options) + 1}")
        return base_options

@traceable(run_type="chain")
async def quiz_validator(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """퀴즈 검증 에이전트  
        - 각 퀴즈에 필수 필드가 있는지 검사  
        - 문제 유형 및 옵션의 일관성을 검사
        - 다국어 답변 형식을 정규화
        - 다양한 문제 유형(OX, 이지선다, 삼지선다, 사지선다 등) 처리
        - 최종 결과가 유일한(중복되지 않는) 퀴즈가 되도록 검증함  
    """
    try:
        state = state.get("state", state)
        raw_quizzes = state.get("raw_quizzes") or []
        logger.info(f"Raw quizzes before validation: {len(raw_quizzes)} quizzes found")

        validated_quizzes = []

        # 제한 제거: 모든 퀴즈 검증
        for i, quiz in enumerate(raw_quizzes):
            try:
                # 기본 필드 확인 - 객체 접근
                question = quiz.question if hasattr(quiz, 'question') else ""
                answer = quiz.answer if hasattr(quiz, 'answer') else ""
                problemType = quiz.problemType if hasattr(quiz, 'problemType') else 0
                options = quiz.options if hasattr(quiz, 'options') and quiz.options else []
                
                logger.info(f"Quiz {i} - Question: {question}, Answer: {answer}, ProblemType: {problemType}, Options: {options}")
                
                # 기본 검증
                if not question or not answer:
                    logger.warning(f"Quiz {i}: Missing question or answer")
                    continue
                
                # 지원되는 문제 유형인지 확인
                valid_problem_types = [pt.value for pt in ProblemType]
                if problemType not in valid_problem_types:
                    logger.warning(f"Quiz {i}: Invalid problem type {problemType}, setting to OX type")
                    problemType = ProblemType.OX
                
                # 문제 유형별 처리
                if problemType == ProblemType.OX:  # OX 문제
                    # 다국어 답변을 O/X로 정규화
                    normalized_answer, normalized_options = normalize_true_false_answer(answer, options)
                    logger.info(f"Quiz {i}: OX normalized - Answer: {normalized_answer}, Options: {normalized_options}")
                    answer = normalized_answer
                    options = normalized_options
                    
                elif problemType == ProblemType.TWO_CHOICE:  # 이지선다 문제
                    # 이지선다 옵션 검증
                    validated_options = validate_multi_choice_options(options, 2)
                    if len(validated_options) != 2:
                        logger.warning(f"Quiz {i}: Could not create valid two-choice options from {options}")
                        continue
                    
                    # 답변이 옵션에 있는지 확인
                    if answer not in validated_options:
                        logger.warning(f"Quiz {i}: Answer '{answer}' not in options {validated_options}, using first option")
                        answer = validated_options[0]
                    
                    options = validated_options
                    logger.info(f"Quiz {i}: Two-choice validated - Answer: {answer}, Options: {options}")
                
                elif problemType == ProblemType.THREE_CHOICE:  # 삼지선다 문제
                    # 삼지선다 옵션 검증
                    validated_options = validate_multi_choice_options(options, 3)
                    if len(validated_options) != 3:
                        logger.warning(f"Quiz {i}: Could not create valid three-choice options from {options}")
                        continue
                    
                    # 답변이 옵션에 있는지 확인
                    if answer not in validated_options:
                        logger.warning(f"Quiz {i}: Answer '{answer}' not in options {validated_options}, using first option")
                        answer = validated_options[0]
                    
                    options = validated_options
                    logger.info(f"Quiz {i}: Three-choice validated - Answer: {answer}, Options: {options}")
                
                elif problemType == ProblemType.FOUR_CHOICE:  # 사지선다 문제
                    # 사지선다 옵션 검증
                    validated_options = validate_multi_choice_options(options, 4)
                    if len(validated_options) != 4:
                        logger.warning(f"Quiz {i}: Could not create valid four-choice options from {options}")
                        continue
                    
                    # 답변이 옵션에 있는지 확인
                    if answer not in validated_options:
                        logger.warning(f"Quiz {i}: Answer '{answer}' not in options {validated_options}, using first option")
                        answer = validated_options[0]
                    
                    options = validated_options
                    logger.info(f"Quiz {i}: Four-choice validated - Answer: {answer}, Options: {options}")
                
                elif problemType == ProblemType.FIVE_CHOICE:  # 오지선다 문제
                    # 오지선다 옵션 검증
                    validated_options = validate_multi_choice_options(options, 5)
                    if len(validated_options) != 5:
                        logger.warning(f"Quiz {i}: Could not create valid five-choice options from {options}")
                        continue
                    
                    # 답변이 옵션에 있는지 확인
                    if answer not in validated_options:
                        logger.warning(f"Quiz {i}: Answer '{answer}' not in options {validated_options}, using first option")
                        answer = validated_options[0]
                    
                    options = validated_options
                    logger.info(f"Quiz {i}: Five-choice validated - Answer: {answer}, Options: {options}")
                
                # 최종 검증: 답변이 옵션에 있는지 확인
                if answer not in options:
                    logger.warning(f"Quiz {i}: Answer '{answer}' still not in options {options}")
                    continue
                
                validated_quiz = Quiz(
                    question=question,
                    answer=answer,
                    problemType=problemType,
                    options=options
                )
                
                validated_quizzes.append(validated_quiz)
                logger.info(f"Quiz {i}: Successfully validated")
                
            except Exception as e:
                logger.error(f"Error validating quiz {i}: {str(e)}", exc_info=True)
                continue

        logger.info(f"Validated quizzes: {[q.question for q in validated_quizzes]}")

        # 중복 질문 제거
        unique_questions = {}
        final_quizzes = []
        
        for quiz in validated_quizzes:
            if quiz.question not in unique_questions:
                unique_questions[quiz.question] = True
                final_quizzes.append(quiz)
        
        logger.info(f"Final unique quizzes count: {len(final_quizzes)}")
        
        if len(final_quizzes) == 0:
            error_msg = "No valid quizzes could be generated from the input text."
            logger.error(error_msg)
            state["error"] = error_msg
            return {"state": state}
        
        # 모든 퀴즈 사용 (제한 없음)
        state["validated_quizzes"] = final_quizzes
        logger.info(f"Validated {len(final_quizzes)} quizzes")
        
        return {"state": state}
        
    except Exception as e:
        logger.error(f"Error in quiz validator: {str(e)}", exc_info=True)
        state["error"] = str(e)
        return {"state": state}
