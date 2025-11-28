"""
문서에서 텍스트 추출 유틸리티 (PDF, TXT, Excel, CSV, 이미지 지원)
"""

import os
import io
import base64
import csv
from typing import Optional
import fitz  # PyMuPDF
import pandas as pd
from PIL import Image

from app.utils.language.generator import call_llm
from app.utils.logger.setup import setup_logger
from app.core.config import settings

logger = setup_logger('document_extractor', 'logs/document')

async def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    파일 내용에서 텍스트를 추출합니다.
    
    Args:
        file_content: 파일의 바이너리 내용
        filename: 파일명 (확장자 확인용)
        
    Returns:
        str: 추출된 텍스트
    """
    try:
        file_extension = os.path.splitext(filename.lower())[1]
        
        if file_extension == '.pdf':
            return await extract_text_from_pdf(file_content)
        elif file_extension == '.txt':
            return file_content.decode('utf-8', errors='ignore')
        elif file_extension in ['.xlsx', '.xls']:
            return extract_text_from_excel(file_content)
        elif file_extension == '.csv':
            return extract_text_from_csv(file_content)
        elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return await extract_text_from_image(file_content)
        else:
            # 지원되지 않는 파일 형식
            supported_formats = "PDF, TXT, Excel (XLSX, XLS), CSV, 이미지 (JPG, JPEG, PNG, GIF, BMP)"
            raise Exception(f"지원되지 않는 파일 형식: {file_extension}. 지원되는 형식: {supported_formats}")
                
    except Exception as e:
        logger.error(f"텍스트 추출 실패 - 파일: {filename}, 오류: {str(e)}")
        raise Exception(f"텍스트 추출 실패: {str(e)}")

async def extract_text_from_pdf(file_content: bytes) -> str:
    """
    PDF 파일에서 텍스트를 추출합니다. (PyMuPDF 표 추출 → 일반 텍스트 → LLM 처리)

    Args:
        file_content: PDF 파일의 바이너리 내용

    Returns:
        str: 추출된 텍스트
    """
    try:
        # 1. PyMuPDF로 표 추출 시도 (최우선)
        extracted_text = ""
        pdf_document = fitz.open("pdf", file_content)
        total_pages = len(pdf_document)

        try:
            logger.info(f"📊 PyMuPDF로 {total_pages} 페이지의 표 추출 시도")

            for page_num in range(total_pages):
                page = pdf_document[page_num]

                # find_tables()로 표 감지
                tables = page.find_tables()

                if tables and len(tables.tables) > 0:
                    logger.info(f"📋 페이지 {page_num + 1}: {len(tables.tables)}개 표 발견")

                    for table_idx, table in enumerate(tables.tables):
                        try:
                            # 표를 pandas DataFrame으로 변환
                            df = table.to_pandas()

                            if df is not None and not df.empty:
                                # DataFrame을 CSV 형식으로 변환
                                csv_text = df.to_csv(index=False, header=True)
                                extracted_text += csv_text + "\n"
                                logger.info(f"✅ 페이지 {page_num + 1}, 표 {table_idx + 1}: {df.shape[0]}행 x {df.shape[1]}열")
                        except Exception as table_error:
                            logger.warning(f"⚠️ 페이지 {page_num + 1}, 표 {table_idx + 1} 변환 실패: {str(table_error)}")
                            continue

            if extracted_text.strip():
                logger.info(f"✅ PyMuPDF 표 데이터 추출 완료: {len(extracted_text)} 문자")
                logger.info(f"📄 추출된 내용 미리보기:\n{extracted_text[:200]}")
                pdf_document.close()
                return extracted_text
            else:
                logger.info("ℹ️ PyMuPDF로 표를 찾을 수 없음, 일반 텍스트 추출 시도")

        except Exception as pymupdf_table_error:
            logger.warning(f"⚠️ PyMuPDF 표 추출 실패: {str(pymupdf_table_error)}")

        # 2. 표 추출 실패 시 PyMuPDF로 일반 텍스트 추출
        logger.info("📄 PyMuPDF로 일반 텍스트 추출 시도")

        # pdf_document가 이미 열려있으므로 재사용
        extracted_text = ""

        for page_num in range(total_pages):
            try:
                page = pdf_document[page_num]
                page_text = page.get_text()

                if page_text and page_text.strip():
                    extracted_text += f"{page_text}\n\n"
                    logger.debug(f"페이지 {page_num + 1}: {len(page_text)} 문자")

            except Exception as page_error:
                logger.warning(f"페이지 {page_num + 1} 실패: {str(page_error)}")
                continue

        pdf_document.close()

        if not extracted_text.strip():
            logger.warning("⚠️ PyMuPDF로도 텍스트 추출 실패. 스캔된 PDF로 추정됨.")

        # 스캔된 PDF의 경우 LLM 기반 이미지 처리로 전환
        try:
            logger.info(f"PDF 전체 {total_pages} 페이지를 이미지로 변환하여 LLM 처리 시도...")

            # PDF 문서를 다시 열기 (이미 닫혔을 수 있으므로)
            if pdf_document.is_closed:
                pdf_document = fitz.open("pdf", file_content)

            llm_extracted_text = ""

            # 모든 페이지를 이미지로 변환하여 LLM 처리
            for page_num in range(total_pages):
                try:
                    page = pdf_document[page_num]
                    # 해상도 조정 (속도와 품질의 균형)
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # 1.5배 확대
                    image_bytes = pix.tobytes("png")

                    # LLM을 사용한 텍스트 추출
                    page_text = await extract_text_from_image(image_bytes)

                    if page_text and page_text.strip():
                        # 표 형식 데이터 감지 (CSV, TSV, 공백 구분)
                        is_table_format = (
                            ',' in page_text or  # CSV
                            '\t' in page_text or  # TSV
                            '  ' in page_text  # 공백 구분 (2개 이상)
                        )

                        if is_table_format and total_pages == 1:
                            # 단일 페이지의 표 형식 데이터는 페이지 태그 없이 추가
                            llm_extracted_text += f"{page_text}\n\n"
                            logger.info(f"페이지 {page_num + 1}: 표 형식 데이터 감지 (페이지 태그 제외)")
                        else:
                            # 다중 페이지이거나 일반 텍스트는 페이지 태그 포함
                            llm_extracted_text += f"[페이지 {page_num + 1}]\n{page_text}\n\n"

                        logger.debug(f"페이지 {page_num + 1}: LLM으로 {len(page_text)} 문자 추출")
                    else:
                        logger.warning(f"페이지 {page_num + 1}: LLM으로도 텍스트 추출 실패")

                except Exception as page_llm_error:
                    logger.warning(f"페이지 {page_num + 1} LLM 처리 실패: {str(page_llm_error)}")
                    continue

            pdf_document.close()

            if llm_extracted_text.strip():
                logger.info(f"LLM 기반 PDF 처리 성공 - {len(llm_extracted_text)} 문자 추출 (전체 {total_pages} 페이지)")
                return llm_extracted_text.strip()
            else:
                raise Exception("LLM으로도 PDF에서 텍스트를 추출할 수 없습니다.")

        except Exception as llm_error:
            pdf_document.close()
            logger.error(f"LLM 기반 PDF 처리 실패: {str(llm_error)}")
            raise Exception(f"PDF에서 텍스트를 추출할 수 없습니다. 일반 텍스트 추출 및 LLM 처리 모두 실패했습니다.")

    except Exception as e:
        logger.error(f"❌ PDF 텍스트 추출 실패: {str(e)}")
        raise Exception(f"PDF 처리 실패: {str(e)}")

def extract_text_from_excel(file_content: bytes) -> str:
    """
    Excel 파일에서 텍스트를 추출합니다.

    Args:
        file_content: Excel 파일의 바이너리 내용

    Returns:
        str: 추출된 텍스트
    """
    try:
        excel_file = io.BytesIO(file_content)

        # 모든 시트 읽기
        excel_data = pd.read_excel(excel_file, sheet_name=None, header=None)

        extracted_text = []

        for sheet_name, df in excel_data.items():
            if not df.empty:
                # 시트명 추가
                extracted_text.append(f"[시트: {sheet_name}]")

                # 모든 셀의 값들을 문자열로 변환하고 결합
                for _, row in df.iterrows():
                    row_text = []
                    for cell in row:
                        if pd.notna(cell) and str(cell).strip():
                            row_text.append(str(cell).strip())

                    if row_text:
                        extracted_text.append(" | ".join(row_text))

                extracted_text.append("")  # 시트 간 공백

        result_text = "\n".join(extracted_text).strip()

        if not result_text:
            raise Exception("Excel 파일에서 텍스트를 추출할 수 없습니다.")

        logger.info(f"Excel 텍스트 추출 완료 - {len(result_text)} 문자, {len(excel_data)} 시트")
        return result_text

    except Exception as e:
        logger.error(f"Excel 텍스트 추출 실패: {str(e)}")
        raise Exception(f"Excel 처리 실패: {str(e)}")

async def extract_text_from_image(file_content: bytes) -> str:
    """
    이미지 파일에서 LLM을 사용하여 텍스트를 추출합니다.

    Args:
        file_content: 이미지 파일의 바이너리 내용

    Returns:
        str: 추출된 텍스트
    """
    try:
        # 이미지를 base64로 인코딩
        base64_image = base64.b64encode(file_content).decode('utf-8')

        # 이미지 형식 확인
        image_file = io.BytesIO(file_content)
        image = Image.open(image_file)
        image_format = image.format.lower() if image.format else 'jpeg'

        # LLM에 이미지 분석 요청
        prompt = """다음 이미지를 OCR 모드로 처리하여, 표(테이블) 구조의 데이터만 추출하세요. 아래 규칙을 반드시 지키세요.

1) 표 구조만 추출: 표, 차트, 그래프의 데이터만 전사합니다. 제목(Table 1., Figure 2. 등), 캡션, 일반 텍스트, 문단, 설명문은 제외합니다.

2) 표 감지 기준: 행과 열로 구성된 구조화된 데이터가 있는 경우만 추출합니다.

3) 원문 충실 전사:
   - 표 내의 모든 문자(대소문자, 공백, 구두점, 특수문자, 단위 등)를 수정/추정/번역 없이 그대로 출력
   - 숫자 값(29.6, 224M, 13.5 등)은 소수점, 단위, 하이픈까지 정확히 전사
   - 결측값을 나타내는 하이픈(-), 대시(–, —)도 그대로 유지

4) 완전성 보장 (매우 중요):
   - 표의 모든 행을 빠짐없이 추출하세요. 행 수를 반드시 확인하세요.
   - 표의 모든 열을 빠짐없이 추출하세요. 헤더와 데이터의 열 수가 일치해야 합니다.
   - 작은 글씨, 흐릿한 텍스트, 표 하단의 행도 모두 읽어주세요.

5) 멀티라인 헤더 처리 (매우 중요):
   - 헤더가 2줄 이상인 경우, 반드시 하나의 헤더 행으로 병합하세요.
   - 병합 규칙: 상위헤더와 하위헤더를 공백으로 연결 (예: "VQAv2 val", "OK-VQA test-dev")
   - 상위헤더가 없는 하위헤더는 그대로 사용
   - 병합 예시:
     원본:
       라인 1: Models  #Trainable Params  #Total Params  VQAv2           OK-VQA      GQA
       라인 2:                                            val  test-dev   test-dev    test-dev

     출력:
       Models  #Trainable Params  #Total Params  VQAv2 val  VQAv2 test-dev  OK-VQA test-dev  GQA test-dev

6) 공백/탭 보존:
   - 공백 구분 표의 경우: 열 사이의 공백 패턴(2개 이상 연속 공백)을 정확히 보존하세요.
   - 탭 구분 표의 경우: 탭(\t)으로 구분하여 출력하세요.
   - 원문의 줄바꿈을 그대로 유지하세요.

7) 방향/배치 처리: 회전/기울어짐/세로쓰기/작은 글씨도 읽어 좌→우, 상→하의 자연스러운 읽기 순서로 전사합니다.

8) 그래프/차트 데이터: 그래프/차트의 축/눈금/범례/데이터라벨의 텍스트만 전사합니다.

9) 언어 유지: 원문 언어를 유지하고 번역하거나 설명하지 않습니다.

10) 출력 형식:
    - 표 구조가 없다면: '표 구조를 찾을 수 없습니다.' 한 줄만 출력
    - 표 구조가 있다면: 설명/요약/추가 문구 없이 오직 표 데이터만 출력
    - 출력 전 검증: 추출한 행 수와 열 수가 원본 표와 일치하는지 반드시 확인하세요.

이미지 시작:"""

        # LangChain HumanMessage를 사용한 멀티모달 메시지 생성
        message_content = [
            {
                "type": "text",
                "text": prompt
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{image_format};base64,{base64_image}"
                }
            }
        ]

        logger.info("이미지 LLM 분석 시작...")

        response = await call_llm(
            prompt=[{
                "role": "user",
                "content": message_content
            }],
            model=settings.default_llm_model
        )
        extracted_text = response.content if response and response.content else ""

        if not extracted_text.strip() or "텍스트를 찾을 수 없습니다" in extracted_text:
            raise Exception("이미지에서 텍스트를 추출할 수 없습니다.")

        logger.info(f"이미지 LLM 텍스트 추출 완료 - {len(extracted_text)} 문자")
        return extracted_text.strip()

    except Exception as e:
        logger.error(f"이미지 LLM 텍스트 추출 실패: {str(e)}")
        raise Exception(f"이미지 처리 실패: {str(e)}")

def extract_text_from_csv(file_content: bytes) -> str:
    """
    CSV 파일에서 텍스트를 추출합니다.

    Args:
        file_content: CSV 파일의 바이너리 내용

    Returns:
        str: 추출된 텍스트
    """
    try:
        # CSV 파일 내용을 문자열로 변환
        csv_text = file_content.decode('utf-8-sig', errors='ignore')  # BOM 제거를 위해 utf-8-sig 사용
        if not csv_text:
            csv_text = file_content.decode('cp949', errors='ignore')  # 한국어 인코딩 시도

        csv_file = io.StringIO(csv_text)
        csv_reader = csv.reader(csv_file)

        extracted_lines = []
        row_count = 0

        for row in csv_reader:
            if row:  # 빈 행 제외
                # 각 셀의 값들을 " | "로 구분하여 결합
                row_text = []
                for cell in row:
                    if cell and cell.strip():
                        row_text.append(cell.strip())

                if row_text:
                    extracted_lines.append(" | ".join(row_text))
                    row_count += 1

        if not extracted_lines:
            raise Exception("CSV 파일에서 텍스트를 추출할 수 없습니다.")

        result_text = "\n".join(extracted_lines)

        return result_text

    except Exception as e:
        logger.error(f"CSV 텍스트 추출 실패: {str(e)}")
        raise Exception(f"CSV 처리 실패: {str(e)}")