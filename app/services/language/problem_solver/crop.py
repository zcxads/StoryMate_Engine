"""
OpenCV 및 Google Vision OCR 기반 문제 검출 및 적응형 크롭 서비스
"""

import cv2
import numpy as np
import base64
import re
import os
import time
from typing import List, Dict, Any
from PIL import Image
from io import BytesIO
from google.cloud import vision

from app.utils.logger.setup import setup_logger
from app.core.config import settings

logger = setup_logger('opencv_detector', 'logs/services')

class ProblemDetector:
    """문제 검출 및 적응형 크롭 시스템"""

    def __init__(self):
        self.debug = True

    def _decode_base64_image(self, base64_str: str) -> np.ndarray:
        """base64 이미지를 OpenCV 형식으로 디코딩"""
        try:
            # base64 prefix 제거
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]

            # 디코딩
            image_data = base64.b64decode(base64_str)
            image = Image.open(BytesIO(image_data))

            # RGB로 변환 후 OpenCV 형식(BGR)으로 변환
            image_rgb = np.array(image.convert('RGB'))
            image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

            logger.info(f"이미지 디코딩 완료 - 크기: {image_bgr.shape}")
            return image_bgr

        except Exception as e:
            logger.error(f"이미지 디코딩 실패: {str(e)}")
            raise ValueError(f"이미지 디코딩 실패: {str(e)}")

    # =================================================================
    # 메인 엔트리포인트 - detect_and_segment_problems
    # =================================================================

    async def detect_and_segment_problems(self, image_base64: str) -> Dict[str, Any]:
        """
        문제 검출 및 분할 - 적응형 크롭 시스템 사용

        Args:
            image_base64: Base64 인코딩된 이미지

        Returns:
            Dict: 검출된 문제들의 정보 (problem_number, file_path, execution_time)
        """
        try:
            start_time = time.time()
            logger.info("🔍 문제 검출 및 분할 시작")

            # 적응형 크롭 시스템으로 문제 검출
            cropped_problems = await self.adaptive_crop_problems(image_base64)

            if not cropped_problems:
                return {
                    'file_path': None,
                    'execution_time': f"{time.time() - start_time:.3f}초",
                    'error': '문제를 찾을 수 없습니다'
                }

            # 결과 포맷팅 - 간소화된 응답
            formatted_problems = []
            for i, problem in enumerate(cropped_problems):
                # PNG 파일 저장
                png_info = await self._save_cropped_image_to_file(
                    problem['crop_image_base64'],
                    problem['problem_number']
                )

                formatted_problem = {
                    'file_path': png_info['filepath']
                }
                formatted_problems.append(formatted_problem)

            # 처리 시간 계산
            processing_time = time.time() - start_time

            result = {
                'file_path': formatted_problems[0]['file_path'] if formatted_problems else None,
                'execution_time': f"{processing_time:.3f}초"
            }

            logger.info(f"✅ 문제 검출 완료 - 총 {len(formatted_problems)}개 문제")
            return result

        except Exception as e:
            logger.error(f"문제 검출 실패: {str(e)}")
            return {
                'file_path': None,
                'execution_time': f"{time.time() - start_time:.3f}초",
                'error': str(e)
            }

    async def _save_cropped_image_to_file(self, image_base64: str, problem_number: str) -> Dict[str, str]:
        """크롭된 이미지를 파일로 저장"""
        try:
            import os
            from datetime import datetime

            # 저장 디렉토리 생성
            
            output_dir = os.path.join(settings.output_dir, "detected_problems")
            os.makedirs(output_dir, exist_ok=True)

            # 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"problem_{problem_number}_{timestamp}.png"
            filepath = os.path.join(output_dir, filename)

            # base64를 이미지로 변환하여 저장
            image_data = base64.b64decode(image_base64)
            with open(filepath, 'wb') as f:
                f.write(image_data)

            # 파일 크기 계산
            file_size = os.path.getsize(filepath)
            file_size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"

            logger.info(f"📄 파일 저장 완료: {filepath}")

            return {
                'filename': filename,
                'filepath': filepath,
                'file_size': file_size_str,
                # 'download_url': f'/problem-solver/download-detected/{filename}'
            }

        except Exception as e:
            logger.error(f"파일 저장 실패: {str(e)}")
            return {
                'filename': 'save_failed.png',
                'filepath': '',
                'file_size': '0 KB',
                'download_url': ''
            }

    # =================================================================
    # 적응형 크롭 시스템 (Google Vision OCR 기반)
    # =================================================================

    async def adaptive_crop_problems(self, image_base64: str, target_problems: List[str] = None) -> List[Dict[str, Any]]:
        """
        적응형 크롭 시스템 - 문제별 크기가 자동으로 조정됨

        Args:
            image_base64: Base64 인코딩된 이미지
            target_problems: 크롭할 특정 문제 번호들 (예: ["29", "30"])

        Returns:
            List[Dict]: 크롭된 문제들의 정보
        """
        try:
            logger.info("🔍 적응형 크롭 시스템 시작")

            # 1️⃣ Google Vision OCR로 텍스트와 좌표 추출
            ocr_results = await self._extract_text_with_coordinates(image_base64)
            if not ocr_results:
                logger.error("OCR 결과가 비어있습니다")
                return []

            # 2️⃣ 문제 번호 후보 찾기
            problem_anchors = self._find_problem_anchors(ocr_results, target_problems)
            if not problem_anchors:
                logger.error("문제 번호를 찾을 수 없습니다")
                return []

            # 3️⃣ 컬럼 감지 및 가로 범위 결정
            columns = self._detect_columns(ocr_results)

            # 4️⃣ 각 문제별 적응형 크롭 영역 계산
            image = self._decode_base64_image(image_base64)
            cropped_problems = []

            for anchor in problem_anchors:
                logger.info(f"📐 문제 {anchor['problem_number']} 크롭 영역 계산 중...")

                # 가로 범위 결정 (컬럼 기반)
                horizontal_bounds = self._calculate_horizontal_bounds(anchor, columns)

                # 세로 범위 결정 (텍스트 밀도 + 다음 문제 감지)
                vertical_bounds = self._calculate_vertical_bounds(anchor, ocr_results, image)

                # 후보 크롭 생성
                crop_coords = {
                    'x': horizontal_bounds['left'],
                    'y': vertical_bounds['top'],
                    'width': horizontal_bounds['right'] - horizontal_bounds['left'],
                    'height': vertical_bounds['bottom'] - vertical_bounds['top']
                }

                # 5️⃣ 최종 크롭 실행
                final_crop = self._execute_crop(image, crop_coords)
                if final_crop:
                    cropped_problems.append({
                        'problem_number': anchor['problem_number'],
                        'crop_image_base64': final_crop,
                        'anchor_confidence': anchor['confidence'],
                        'coordinates': crop_coords,  # 품질 점수 계산용
                        'ocr_results': ocr_results
                    })
                    logger.info(f"✅ 문제 {anchor['problem_number']} 크롭 완료")
                else:
                    logger.error(f"❌ 문제 {anchor['problem_number']} 크롭 실패 - 좌표: {crop_coords}")
                    logger.error(f"   이미지 크기: {image.shape}")

            logger.info(f"🎯 적응형 크롭 완료 - 총 {len(cropped_problems)}개 문제 처리")

            # 품질 검증 및 최적 문제 선택
            best_problem = self._select_best_problem(cropped_problems, image)
            if best_problem:
                logger.info(f"✅ 최적 문제 선택: {best_problem['problem_number']}")

                # 6️⃣ LLM 기반 후처리 - 잘린 문제 부분 제거
                post_processed_problem = await self._post_process_crop_with_llm(best_problem)

                return [post_processed_problem]  # 후처리된 1개 문제 반환
            else:
                logger.warning("⚠️ 완전한 문제를 찾을 수 없습니다")
                return []

        except Exception as e:
            logger.error(f"적응형 크롭 시스템 오류: {str(e)}")
            return []

    async def _extract_text_with_coordinates(self, image_base64: str) -> List[Dict[str, Any]]:
        """Google Vision OCR로 텍스트와 좌표 추출"""
        try:
            # Google Vision API 클라이언트 초기화
            client = vision.ImageAnnotatorClient.from_service_account_json(
                "app/credentials/arboreal-drake-448508-u0-56129f74214a.json"
            )

            # Base64 이미지 준비
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]

            image_content = base64.b64decode(image_base64)
            image = vision.Image(content=image_content)

            # OCR 실행 (문서 텍스트 감지)
            response = client.document_text_detection(image=image)

            if response.error.message:
                raise Exception(f"Google Vision API 오류: {response.error.message}")

            # 결과 파싱
            ocr_results = []
            if response.full_text_annotation:
                for page in response.full_text_annotation.pages:
                    for block in page.blocks:
                        for paragraph in block.paragraphs:
                            for word in paragraph.words:
                                # 단어의 텍스트 추출
                                word_text = ''.join([symbol.text for symbol in word.symbols])

                                # 바운딩 박스 추출
                                vertices = word.bounding_box.vertices
                                x_coords = [vertex.x for vertex in vertices]
                                y_coords = [vertex.y for vertex in vertices]

                                bbox = {
                                    'x': min(x_coords),
                                    'y': min(y_coords),
                                    'width': max(x_coords) - min(x_coords),
                                    'height': max(y_coords) - min(y_coords)
                                }

                                ocr_results.append({
                                    'text': word_text,
                                    'bbox': bbox,
                                    'confidence': word.confidence if hasattr(word, 'confidence') else 0.9
                                })

            logger.info(f"📝 OCR 완료 - {len(ocr_results)}개 단어 추출")
            return ocr_results

        except Exception as e:
            logger.error(f"Google Vision OCR 실패: {str(e)}")
            return []

    def _find_problem_anchors(self, ocr_results: List[Dict], target_problems: List[str] = None) -> List[Dict[str, Any]]:
        """문제 번호 시작점(anchor) 찾기 - "1.", "11.", "29.", "30." 형식만 검출"""
        try:
            anchors = []
            # 엄격한 패턴: 숫자 + 마침표 형태만 (마침표 필수)
            problem_pattern = re.compile(r'^(\d+)\.$')  # "1.", "11.", "29.", "30." 형태만

            for result in ocr_results:
                text = result['text'].strip()
                match = problem_pattern.match(text)

                if match:
                    problem_num = match.group(1)

                    # 특정 문제만 크롭하는 경우 필터링
                    if target_problems and problem_num not in target_problems:
                        continue

                    anchors.append({
                        'problem_number': problem_num,
                        'text': text,
                        'position': {
                            'x': result['bbox']['x'],
                            'y': result['bbox']['y'],
                            'width': result['bbox']['width'],
                            'height': result['bbox']['height']
                        },
                        'confidence': result['confidence']
                    })

                    logger.info(f"🎯 문제 번호 발견: {problem_num} at ({result['bbox']['x']}, {result['bbox']['y']})")

            # 위에서 아래 순서로 정렬
            anchors.sort(key=lambda x: x['position']['y'])

            logger.info(f"📍 총 {len(anchors)}개 문제 번호 anchor 발견")
            return anchors

        except Exception as e:
            logger.error(f"문제 번호 anchor 찾기 실패: {str(e)}")
            return []

    def _detect_columns(self, ocr_results: List[Dict]) -> List[Dict[str, Any]]:
        """컬럼 감지 - 가로 범위 결정을 위함"""
        try:
            # X 좌표별로 텍스트 그룹화
            x_positions = [result['bbox']['x'] for result in ocr_results]

            if not x_positions:
                return []

            # X 좌표 클러스터링 (간단한 방법)
            x_positions.sort()
            clusters = []
            current_cluster = [x_positions[0]]

            threshold = 100  # 100px 이내는 같은 컬럼으로 간주

            for x in x_positions[1:]:
                if x - current_cluster[-1] <= threshold:
                    current_cluster.append(x)
                else:
                    clusters.append(current_cluster)
                    current_cluster = [x]

            clusters.append(current_cluster)

            # 각 클러스터의 범위 계산
            columns = []
            for i, cluster in enumerate(clusters):
                if len(cluster) >= 2:  # 최소 2개 이상의 텍스트가 있는 클러스터 (조건 완화)
                    columns.append({
                        'column_id': i,
                        'left_bound': min(cluster) - 30,  # 여백 추가
                        'right_bound': max(cluster) + 400,  # 텍스트가 확장될 수 있는 범위 (증가)
                        'text_count': len(cluster)
                    })

            logger.info(f"📊 컬럼 감지 완료 - {len(columns)}개 컬럼")
            for col in columns:
                logger.info(f"  컬럼 {col['column_id']}: x={col['left_bound']}~{col['right_bound']} (텍스트 {col['text_count']}개)")

            return columns

        except Exception as e:
            logger.error(f"컬럼 감지 실패: {str(e)}")
            return []

    def _calculate_horizontal_bounds(self, anchor: Dict, columns: List[Dict]) -> Dict[str, int]:
        """문제의 가로 범위 계산 (컬럼 기반)"""
        try:
            anchor_x = anchor['position']['x']

            # 문제 번호가 속한 컬럼 찾기
            target_column = None
            for column in columns:
                if column['left_bound'] <= anchor_x <= column['right_bound']:
                    target_column = column
                    break

            if target_column:
                # 컬럼 범위 사용
                left_bound = target_column['left_bound']
                right_bound = target_column['right_bound']
                logger.info(f"  📐 컬럼 기반 가로 범위: {left_bound} ~ {right_bound}")
            else:
                # 컬럼을 찾지 못한 경우 기본값 사용 (더 넓은 범위)
                left_bound = max(0, anchor_x - 50)
                right_bound = anchor_x + 600  # 범위 증가
                logger.info(f"  📐 기본 가로 범위: {left_bound} ~ {right_bound}")

            return {
                'left': left_bound,
                'right': right_bound,
                'column_id': target_column['column_id'] if target_column else -1
            }

        except Exception as e:
            logger.error(f"가로 범위 계산 실패: {str(e)}")
            return {'left': 0, 'right': 400, 'column_id': -1}

    def _calculate_vertical_bounds(self, anchor: Dict, ocr_results: List[Dict], image: np.ndarray) -> Dict[str, int]:
        """문제의 세로 범위 계산 (텍스트 밀도 + 다음 문제 감지)"""
        try:
            anchor_y = anchor['position']['y']
            problem_num = int(anchor['problem_number'])
            height = image.shape[0]

            # 다음 문제 번호 찾기
            next_problem_y = None
            next_problem_pattern = re.compile(rf'^{problem_num + 1}\.$')  # 마침표 필수로 통일

            for result in ocr_results:
                if next_problem_pattern.match(result['text'].strip()):
                    next_problem_y = result['bbox']['y']
                    logger.info(f"  🔍 다음 문제 {problem_num + 1} 발견 at y={next_problem_y}")
                    break

            # 시작점 설정
            top_bound = max(0, anchor_y - 10)  # 문제 번호 위 여백

            # 끝점 계산
            if next_problem_y:
                # 다음 문제가 있는 경우 - 위치 검증 필요
                if next_problem_y > anchor_y:
                    # 다음 문제가 아래쪽에 있는 정상적인 경우
                    bottom_bound = next_problem_y - 20  # 다음 문제 전 여백
                    method = 'next_problem'
                    logger.info(f"  📏 다음 문제 기준 세로 범위: {top_bound} ~ {bottom_bound}")
                else:
                    # 다음 문제가 위쪽에 있는 비정상적인 경우 - 텍스트 밀도 분석 사용
                    logger.warning(f"  ⚠️ 다음 문제 {problem_num + 1}이 현재 문제보다 위에 있음 (y={next_problem_y} < {anchor_y})")
                    bottom_bound = self._analyze_text_density_end(anchor, ocr_results, image)
                    method = 'text_density_fallback'
                    logger.info(f"  📏 텍스트 밀도 기준으로 변경: {top_bound} ~ {bottom_bound}")
            else:
                # 다음 문제가 없는 경우 텍스트 밀도 분석
                bottom_bound = self._analyze_text_density_end(anchor, ocr_results, image)
                method = 'text_density'
                logger.info(f"  📏 텍스트 밀도 기준 세로 범위: {top_bound} ~ {bottom_bound}")

            # 최종 안전 검증: bottom이 top보다 작거나 같으면 기본값 사용
            if bottom_bound <= top_bound:
                logger.warning(f"  ⚠️ 비정상적인 세로 범위 감지: top={top_bound}, bottom={bottom_bound}")
                bottom_bound = anchor_y + 200  # 기본 높이 사용
                method = 'safety_fallback'
                logger.info(f"  🔧 안전 기본값으로 보정: {top_bound} ~ {bottom_bound}")

            return {
                'top': top_bound,
                'bottom': min(height, bottom_bound),
                'method': method
            }

        except Exception as e:
            logger.error(f"세로 범위 계산 실패: {str(e)}")
            anchor_y = anchor['position']['y']
            return {
                'top': max(0, anchor_y - 10),
                'bottom': min(image.shape[0], anchor_y + 300),
                'method': 'fallback'
            }

    def _analyze_text_density_end(self, anchor: Dict, ocr_results: List[Dict], image: np.ndarray) -> int:
        """텍스트 밀도 분석으로 문제 끝점 찾기"""
        try:
            anchor_y = anchor['position']['y']
            height = image.shape[0]

            # 문제 번호 아래쪽 영역의 텍스트들 수집
            texts_below = []
            for result in ocr_results:
                text_y = result['bbox']['y']
                if text_y > anchor_y:  # 문제 번호 아래에 있는 텍스트만
                    texts_below.append({
                        'y': text_y,
                        'height': result['bbox']['height']
                    })

            if not texts_below:
                return min(height, anchor_y + 300)  # 기본값

            # Y 좌표로 정렬
            texts_below.sort(key=lambda x: x['y'])

            # 빈 공간 분석 (연속된 텍스트 간 간격 계산)
            large_gap_threshold = 80  # 80px 이상 간격을 큰 빈 공간으로 간주

            for i in range(len(texts_below) - 1):
                current_bottom = texts_below[i]['y'] + texts_below[i]['height']
                next_top = texts_below[i + 1]['y']
                gap = next_top - current_bottom

                if gap > large_gap_threshold:
                    logger.info(f"  🔍 큰 빈 공간 발견: y={current_bottom}~{next_top} (간격: {gap}px)")
                    end_point = current_bottom + 20  # 빈 공간 시작점에서 여백 추가

                    # 안전 검증: 끝점이 시작점보다 작은 경우 방지
                    if end_point <= anchor_y:
                        logger.warning(f"  ⚠️ 빈 공간 기준 끝점이 비정상: {end_point} <= {anchor_y}")
                        return anchor_y + 200  # 기본 높이 사용

                    return end_point

            # 빈 공간을 찾지 못한 경우 마지막 텍스트 위치 사용
            last_text = texts_below[-1]
            end_y = last_text['y'] + last_text['height'] + 30

            # 안전 검증: 끝점이 시작점보다 작은 경우 방지
            if end_y <= anchor_y:
                logger.warning(f"  ⚠️ 텍스트 밀도 분석 결과가 비정상: end_y={end_y} <= anchor_y={anchor_y}")
                end_y = anchor_y + 200  # 기본 높이 사용

            logger.info(f"  📏 마지막 텍스트 기준 끝점: {end_y}")
            return min(height, end_y)

        except Exception as e:
            logger.error(f"텍스트 밀도 분석 실패: {str(e)}")
            return min(image.shape[0], anchor['position']['y'] + 300)

    def _select_best_problem(self, cropped_problems: List[Dict], original_image: np.ndarray) -> Dict:
        """크롭된 문제들 중에서 가장 완전한 1개 문제 선택 - 신뢰도 우선 고려"""
        try:
            if not cropped_problems:
                return None

            logger.info("🔍 크롭 품질 검증 시작")
            scored_problems = []

            for problem in cropped_problems:
                # 품질 점수와 신뢰도를 종합적으로 고려
                quality_score = self._calculate_problem_quality_score(problem, original_image)
                anchor_confidence = problem.get('anchor_confidence', 0.0)

                # 최종 점수 = 품질 점수 (70%) + 앵커 신뢰도 (30%)
                final_score = quality_score * 0.7 + anchor_confidence * 0.3

                scored_problems.append({
                    'problem': problem,
                    'quality_score': quality_score,
                    'anchor_confidence': anchor_confidence,
                    'final_score': final_score
                })

                logger.info(f"  문제 {problem['problem_number']}: 품질 {quality_score:.2f} + 신뢰도 {anchor_confidence:.2f} = 최종 {final_score:.2f}")

            # 최종 점수가 가장 높은 문제 선택 (threshold 없이)
            if scored_problems:
                best = max(scored_problems, key=lambda x: x['final_score'])
                logger.info(f"✅ 최적 문제 선택: {best['problem']['problem_number']} (최종 점수: {best['final_score']:.2f})")
                return best['problem']

            return None

        except Exception as e:
            logger.error(f"최적 문제 선택 실패: {str(e)}")
            # 실패 시 첫 번째 문제 반환
            return cropped_problems[0] if cropped_problems else None

    def _calculate_problem_quality_score(self, problem: Dict, original_image: np.ndarray) -> float:
        """문제 크롭의 품질 점수 계산 (0.0-1.0)"""
        try:
            coords = problem['coordinates']
            x, y, width, height = coords['x'], coords['y'], coords['width'], coords['height']

            score = 0.0
            max_score = 100.0

            # 1. 위치 점수 (30점) - 이미지 경계에서 잘린 정도
            img_height, img_width = original_image.shape[:2]

            position_score = 30
            # 가장자리 여백 확인
            margin_threshold = 10
            if x < margin_threshold:  # 왼쪽 가장자리
                position_score -= 5
            if y < margin_threshold:  # 상단 가장자리
                position_score -= 5
            if x + width > img_width - margin_threshold:  # 오른쪽 가장자리
                position_score -= 5
            if y + height > img_height - margin_threshold:  # 하단 가장자리
                position_score -= 5

            score += max(0, position_score)

            # 2. 종횡비 점수 (40점) - 일반적인 문제 비율
            aspect_ratio = width / height if height > 0 else 0
            optimal_ratio = 1.4  # 일반적인 문제 비율 (가로가 약간 김)

            ratio_score = 40
            if 0.8 <= aspect_ratio <= 2.0:  # 합리적인 비율 범위
                ratio_diff = abs(aspect_ratio - optimal_ratio)
                ratio_score = 40 * max(0, 1 - ratio_diff)
            else:
                ratio_score = 0  # 비정상적인 비율

            score += ratio_score

            # 3. OCR 기반 텍스트 밀도 점수 (30점) - 크롭 영역 내 실제 텍스트 양
            crop_region = (x, y, x + width, y + height)
            ocr_results = problem.get('ocr_results', [])
            density_score = self._calculate_text_density_score(crop_region, original_image, ocr_results)
            score += density_score

            # 최종 점수 정규화 (0.0-1.0)
            final_score = min(1.0, score / max_score)

            logger.debug(f"  문제 {problem['problem_number']} 품질 분석:")
            logger.debug(f"    위치: {position_score:.1f}점")
            logger.debug(f"    비율: {aspect_ratio:.2f} -> {ratio_score:.1f}점")
            logger.debug(f"    밀도: {density_score:.1f}점")
            logger.debug(f"    최종: {final_score:.2f}")

            return final_score

        except Exception as e:
            logger.error(f"품질 점수 계산 실패: {str(e)}")
            return 0.0

    def _calculate_text_density_score(self, crop_region: tuple, original_image: np.ndarray, ocr_results: List[Dict]) -> float:
        """OCR 결과를 활용한 텍스트 밀도 점수 계산 (0-30점)"""
        try:
            x1, y1, x2, y2 = crop_region
            width = x2 - x1
            height = y2 - y1
            total_area = width * height

            if total_area <= 0:
                return 0.0

            # 크롭 영역 내 OCR 텍스트 영역 계산
            text_area = 0
            text_blocks_in_crop = 0
            total_text_confidence = 0

            for text_result in ocr_results:
                text_bbox = text_result.get('bbox', {})
                text_x = text_bbox.get('x', 0)
                text_y = text_bbox.get('y', 0)
                text_width = text_bbox.get('width', 0)
                text_height = text_bbox.get('height', 0)
                text_confidence = text_result.get('confidence', 0.0)

                # 텍스트 블록의 경계 좌표
                text_x1, text_y1 = text_x, text_y
                text_x2, text_y2 = text_x + text_width, text_y + text_height

                # 크롭 영역과 교집합 계산
                overlap_x1 = max(x1, text_x1)
                overlap_y1 = max(y1, text_y1)
                overlap_x2 = min(x2, text_x2)
                overlap_y2 = min(y2, text_y2)

                if overlap_x1 < overlap_x2 and overlap_y1 < overlap_y2:
                    overlap_area = (overlap_x2 - overlap_x1) * (overlap_y2 - overlap_y1)
                    text_area += overlap_area
                    text_blocks_in_crop += 1
                    total_text_confidence += text_confidence

            # 텍스트 밀도 비율 계산
            if text_area > 0 and text_blocks_in_crop > 0:
                text_density_ratio = min(text_area / total_area, 1.0)  # 최대 100%로 제한
                avg_confidence = total_text_confidence / text_blocks_in_crop

                # 텍스트 밀도에 따른 기본 점수 계산
                if text_density_ratio >= 0.15:  # 15% 이상 텍스트
                    base_score = 28.0 + (text_density_ratio - 0.15) * 20  # 28-30점
                elif text_density_ratio >= 0.10:  # 10-15% 텍스트
                    base_score = 24.0 + (text_density_ratio - 0.10) * 80  # 24-28점
                elif text_density_ratio >= 0.05:  # 5-10% 텍스트
                    base_score = 18.0 + (text_density_ratio - 0.05) * 120  # 18-24점
                elif text_density_ratio >= 0.02:  # 2-5% 텍스트
                    base_score = 10.0 + (text_density_ratio - 0.02) * 267  # 10-18점
                else:  # 2% 미만 텍스트
                    base_score = text_density_ratio * 500  # 0-10점

                # OCR 신뢰도에 따른 가중치 적용
                confidence_weight = 0.8 + (avg_confidence * 0.2)  # 0.8-1.0 범위
                score = base_score * confidence_weight

                # 텍스트 블록 수에 따른 보너스 (더 많은 텍스트 블록 = 더 완전한 문제)
                if text_blocks_in_crop >= 15:
                    score += 2.0
                elif text_blocks_in_crop >= 10:
                    score += 1.5
                elif text_blocks_in_crop >= 5:
                    score += 1.0

                return min(score, 30.0)
            else:
                # OCR 결과가 없거나 크롭 영역 내 텍스트가 없는 경우
                return 2.0

        except Exception as e:
            logger.error(f"OCR 기반 텍스트 밀도 점수 계산 중 오류: {str(e)}")
            return 10.0

    def _execute_crop(self, image: np.ndarray, coords: Dict[str, int]) -> str:
        """실제 이미지 크롭 실행 및 base64 반환"""
        try:
            x, y, width, height = coords['x'], coords['y'], coords['width'], coords['height']

            # 이미지 범위 검증
            img_height, img_width = image.shape[:2]
            x = max(0, min(x, img_width - 1))
            y = max(0, min(y, img_height - 1))
            width = min(width, img_width - x)
            height = min(height, img_height - y)

            # 최소 크기 검증 (너무 작은 크롭 방지) - 조건 완화
            if width < 50 or height < 50:
                logger.error(f"크롭 영역이 너무 작습니다: {width}x{height}")
                logger.error(f"원본 좌표: x={coords['x']}, y={coords['y']}, w={coords['width']}, h={coords['height']}")
                return ""

            # 크롭 실행
            cropped = image[y:y+height, x:x+width]

            # 빈 이미지 검증
            if cropped.size == 0:
                logger.error(f"크롭 결과가 빈 이미지입니다: {width}x{height} @ ({x},{y})")
                return ""

            # 이미지 유효성 검증
            if len(cropped.shape) < 2:
                logger.error(f"크롭 결과가 유효하지 않은 이미지입니다: shape={cropped.shape}")
                return ""

            # base64로 인코딩
            success, buffer = cv2.imencode('.png', cropped)
            if not success:
                logger.error(f"이미지 인코딩 실패: {width}x{height} @ ({x},{y})")
                return ""

            crop_base64 = base64.b64encode(buffer).decode('utf-8')

            logger.info(f"✂️ 크롭 실행 완료: {width}x{height} @ ({x},{y})")

            return crop_base64

        except Exception as e:
            logger.error(f"크롭 실행 실패: {str(e)}")
            return ""

    async def _post_process_crop_with_llm(self, problem_data: Dict) -> Dict:
        """LLM 기반 크롭 이미지 후처리 - 잘린 문제 부분 제거"""
        try:
            logger.info(f"🧠 LLM 기반 후처리 시작 - 문제 {problem_data['problem_number']}")

            crop_base64 = problem_data['crop_image_base64']

            # LLM으로 잘린 문제 영역 분석
            analysis_result = await self._analyze_crop_with_llm(crop_base64, problem_data['problem_number'])

            if analysis_result['has_partial_problems']:
                logger.info(f"📏 잘린 문제 감지됨 - 제거 영역: {analysis_result['removal_areas']}")

                # 잘린 부분 제거
                cleaned_crop = await self._remove_partial_problems(crop_base64, analysis_result['removal_areas'])

                if cleaned_crop:
                    problem_data['crop_image_base64'] = cleaned_crop
                    logger.info(f"✅ 후처리 완료 - 잘린 부분 제거")
                else:
                    logger.warning("⚠️ 후처리 실패 - 원본 크롭 유지")
            else:
                logger.info(f"✅ 후처리 완료 - 잘린 문제 없음")

            return problem_data

        except Exception as e:
            logger.error(f"LLM 후처리 중 오류: {str(e)}")
            return problem_data  # 실패 시 원본 반환

    async def _analyze_crop_with_llm(self, crop_base64: str, problem_number: str) -> Dict:
        """LLM으로 크롭 이미지 분석하여 잘린 문제 영역 탐지"""
        try:
            from app.utils.language.generator import call_llm
            import base64
            import io
            from PIL import Image

            # Base64 이미지를 PIL Image로 변환
            image_data = base64.b64decode(crop_base64)
            pil_image = Image.open(io.BytesIO(image_data))

            # 외부 프롬프트 파일에서 분석 프롬프트 가져오기
            from app.prompts.language.problem_solver.crop_analysis import get_crop_analysis_prompt
            analysis_prompt = get_crop_analysis_prompt(problem_number)

            # LLM 분석 실행 - call_llm 사용
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": analysis_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{crop_base64}"}
                        }
                    ]
                }
            ]

            response = await call_llm(prompt=messages, model=settings.llm_ocr_problem_solver_model)

            # 응답 파싱
            import json
            result_text = response.content.strip()

            # JSON 추출 (코드 블록 제거)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            analysis_result = json.loads(result_text)

            logger.info(f"  🔍 LLM 분석 결과: 신뢰도 {analysis_result['confidence']:.2f}, 잘린 문제: {analysis_result['has_partial_problems']}")

            return {
                'has_partial_problems': analysis_result.get('has_partial_problems', False),
                'removal_areas': analysis_result.get('removal_suggestion', {}),
                'confidence': analysis_result.get('confidence', 0.0),
                'reasoning': analysis_result.get('reasoning', '')
            }

        except Exception as e:
            logger.error(f"LLM 분석 실패: {str(e)}")
            return {
                'has_partial_problems': False,
                'removal_areas': {},
                'confidence': 0.0,
                'reasoning': 'Analysis failed'
            }

    async def _remove_partial_problems(self, crop_base64: str, removal_areas: Dict) -> str:
        """잘린 문제 영역을 실제로 제거하여 새로운 크롭 이미지 생성"""
        try:
            import base64
            import cv2
            import numpy as np
            from PIL import Image
            import io

            # Base64를 OpenCV 이미지로 변환
            image_data = base64.b64decode(crop_base64)
            pil_image = Image.open(io.BytesIO(image_data))
            cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            original_height, original_width = cv_image.shape[:2]

            # 제거할 영역 계산
            top_remove = max(0, min(removal_areas.get('top', 0), original_height // 3))
            bottom_remove = max(0, min(removal_areas.get('bottom', 0), original_height // 3))
            left_remove = max(0, min(removal_areas.get('left', 0), original_width // 3))
            right_remove = max(0, min(removal_areas.get('right', 0), original_width // 3))

            logger.info(f"  ✂️ 제거 영역: top={top_remove}, bottom={bottom_remove}, left={left_remove}, right={right_remove}")

            # 새로운 크롭 영역 계산
            new_top = top_remove
            new_bottom = original_height - bottom_remove
            new_left = left_remove
            new_right = original_width - right_remove

            # 유효성 검증
            if new_bottom <= new_top or new_right <= new_left:
                logger.error("제거 후 유효하지 않은 크기")
                return ""

            # 최소 크기 검증
            final_width = new_right - new_left
            final_height = new_bottom - new_top

            if final_width < 100 or final_height < 100:
                logger.error(f"제거 후 크기가 너무 작음: {final_width}x{final_height}")
                return ""

            # 이미지 크롭
            cleaned_image = cv_image[new_top:new_bottom, new_left:new_right]

            # Base64로 인코딩
            success, buffer = cv2.imencode('.png', cleaned_image)
            if not success:
                logger.error("후처리된 이미지 인코딩 실패")
                return ""

            cleaned_base64 = base64.b64encode(buffer).decode('utf-8')

            logger.info(f"  ✅ 후처리 완료: {original_width}x{original_height} → {final_width}x{final_height}")

            return cleaned_base64

        except Exception as e:
            logger.error(f"잘린 문제 제거 실패: {str(e)}")
            return ""
