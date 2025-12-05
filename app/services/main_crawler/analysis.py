import os
import time
from collections import Counter
from typing import Dict, Any, List, Tuple
import boto3
from datetime import datetime

from app.core.config import settings
from app.utils.logger.setup import setup_logger
from app.utils.language.generator import call_llm
from app.services.language.language_detection.detector import detect_language_with_ai
from app.prompts.language.summary import get_summary_prompt

logger = setup_logger("crawler_analysis")

# 언어별 폰트 매핑 (우선순위 순서)
LANGUAGE_FONTS = {
    'ko': ['NanumGothic', 'Nanum Gothic', 'NanumBarunGothic', 'Malgun Gothic'],
    'ja': ['Noto Sans CJK JP', 'IPAGothic', 'MS Gothic', 'Yu Gothic', 'Noto Sans JP', 'NanumGothic'],
    'zh': ['Noto Sans CJK SC', 'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Noto Sans SC', 'NanumGothic'],
    'en': ['DejaVu Sans', 'Arial', 'Helvetica', 'Liberation Sans']
}


class CrawlerAnalysisService:
    """크롤러 분석 서비스 (요약 + 워드 클라우드)"""

    def __init__(self):
        self.output_dir = os.path.join(settings.output_dir, "crawler_analysis")
        os.makedirs(self.output_dir, exist_ok=True)

        # NCP S3 클라이언트 초기화
        self.s3_client = boto3.client(
            service_name=settings.naver_service_name,
            endpoint_url=settings.naver_endpoint_url,
            aws_access_key_id=settings.ncp_access_key,
            aws_secret_access_key=settings.ncp_secret_key
        )

    async def analyze_crawled_content(self, content: str, title: str) -> Dict[str, Any]:
        """
        크롤링된 콘텐츠를 분석합니다.

        Args:
            content: 크롤링된 본문 텍스트
            title: 페이지 제목 (선택)

        Returns:
            Dict: {
                "summary": "요약 텍스트",
                "ncp_url": "NCP URL"
            }
        """
        import asyncio

        try:
            total_start = time.time()
            logger.info("🚀 크롤링 콘텐츠 분석 시작")

            # 텍스트 길이 제한
            MAX_CONTENT_LENGTH = 5000  # 5,000자로 제한
            if len(content) > MAX_CONTENT_LENGTH:
                logger.warning(f"⚠️ 콘텐츠가 너무 깁니다 ({len(content)} 문자). {MAX_CONTENT_LENGTH}자로 제한합니다.")
                content = content[:MAX_CONTENT_LENGTH]

            # 0. AI 기반 언어 감지
            detection_result = await detect_language_with_ai(content)
            lang_code = detection_result.get("primary_language")
            confidence = detection_result.get("confidence", 0.0)
            logger.info(f"✅ [AI 언어감지] {lang_code}, 신뢰도: {confidence:.2f}")

            # 1, 2를 병렬 실행: 요약 생성 + 명사 추출
            step_start = time.time()
            summary_task = asyncio.create_task(self._generate_summary(content, title, lang_code))
            nouns_task = asyncio.create_task(self._extract_nouns(content, lang_code))

            summary, nouns = await asyncio.gather(summary_task, nouns_task)
            logger.info(f"✅ [병렬처리] {time.time() - step_start:.2f}초 | 요약: {len(summary)} 문자, 명사: {len(nouns)} 개")

            # 3. 불용어 제거
            filtered_nouns = self._remove_stopwords(nouns, lang_code)
            logger.info(f"✅ [불용어제거] {len(nouns)} → {len(filtered_nouns)} 개")

            # 4. KeyBERT로 키워드 스코어링
            step_start = time.time()
            keywords_scores = await self._score_keywords_with_keybert(content, filtered_nouns, lang_code)
            logger.info(f"✅ [키워드스코어링] {time.time() - step_start:.2f}초 | {len(keywords_scores)} 개")

            # 5, 6을 순차 실행: 가중치 변환 + 워드 클라우드 생성
            step_start = time.time()
            wordcloud_weights = self._convert_to_wordcloud_weights(keywords_scores)
            wordcloud_path = await self._generate_wordcloud(wordcloud_weights, lang_code)
            logger.info(f"✅ [워드클라우드] {time.time() - step_start:.2f}초 | {wordcloud_path}")

            # 7. NCP TMP 버킷에 업로드 (공개 모드)
            step_start = time.time()
            ncp_url = await self._upload_to_ncp_tmp(wordcloud_path)
            logger.info(f"✅ [NCP 업로드] {ncp_url}")

            total_time = time.time() - total_start
            logger.info(f"🎉 전체 분석 완료: {total_time:.2f}초")

            return {
                "summary": summary,
                "ncp_url": ncp_url
            }

        except Exception as e:
            logger.error(f"❌ 크롤링 콘텐츠 분석 실패: {str(e)}")
            raise Exception(f"분석 중 오류가 발생했습니다: {str(e)}")

    async def _generate_summary(self, content: str, title: str, lang_code: str) -> str:
        """언어별 프롬프트를 사용하여 크롤링 결과 요약 생성"""
        try:
            # 언어별 프롬프트 템플릿 가져오기
            prompt_template = get_summary_prompt(lang_code)

            # partial_variables로 page_count=""가 설정되어 있어서 전달하지 않아도 됨
            prompt = prompt_template.format(
                book_content=content
            )

            response = await call_llm(
                prompt=prompt,
                model=settings.default_llm_model
            )

            if hasattr(response, 'content'):
                summary = response.content
            else:
                summary = str(response)

            return summary.strip()

        except Exception as e:
            logger.error(f"요약 생성 실패: {str(e)}")
            raise Exception(f"요약 생성 중 오류: {str(e)}")

    async def _extract_nouns(self, content: str, lang_code: str) -> List[str]:
        """언어별 명사 추출 + 복합명사 결합"""
        try:
            nouns = []

            if lang_code == 'ko':
                # 한국어: Kiwipiepy
                try:
                    from kiwipiepy import Kiwi

                    kiwi = Kiwi()

                    # tokenize()로 단일 최적 분석 결과 획득
                    tokens = kiwi.tokenize(content)

                    # 명사 태그만 추출 (NNG: 일반명사, NNP: 고유명사, NNB: 의존명사)
                    nouns = [token.form for token in tokens
                            if token.tag in ['NNG', 'NNP', 'NNB'] and len(token.form) > 1]

                    # 복합명사 생성 (2-gram만, 속도 최적화)
                    compound_nouns = self._extract_compound_nouns(nouns, content, n_gram_range=(2, 2))
                    nouns.extend(compound_nouns)

                    logger.info(f"✅ Kiwipiepy 기반 명사 추출 완료: {len(nouns)} 개 명사")

                except Exception as kiwi_error:
                    logger.warning(f"⚠️ Kiwipiepy 사용 실패: {str(kiwi_error)}")
                    logger.info("LLM 기반 명사 추출로 대체합니다.")
                    nouns = await self._extract_nouns_with_llm(content, lang_code)

            elif lang_code == 'en':
                # 영어: nltk pos_tag
                import nltk

                # NLTK 리소스 다운로드
                try:
                    nltk.data.find('tokenizers/punkt_tab')
                except LookupError:
                    try:
                        logger.info("📥 NLTK punkt_tab 다운로드 중...")
                        nltk.download('punkt_tab', quiet=True)
                        logger.info("✅ punkt_tab 다운로드 완료")
                    except Exception as e:
                        logger.warning(f"punkt_tab 다운로드 실패, punkt로 재시도: {e}")
                        nltk.download('punkt', quiet=True)

                # NLTK 3.9+는 averaged_perceptron_tagger_eng 사용
                try:
                    nltk.data.find('taggers/averaged_perceptron_tagger_eng')
                except LookupError:
                    try:
                        logger.info("📥 NLTK averaged_perceptron_tagger_eng 다운로드 중...")
                        nltk.download('averaged_perceptron_tagger_eng', quiet=True)
                        logger.info("✅ averaged_perceptron_tagger_eng 다운로드 완료")
                    except Exception as e:
                        logger.warning(f"averaged_perceptron_tagger_eng 다운로드 실패, averaged_perceptron_tagger로 재시도: {e}")
                        nltk.download('averaged_perceptron_tagger', quiet=True)

                tokens = nltk.word_tokenize(content)
                pos_tags = nltk.pos_tag(tokens)

                # NN으로 시작하는 태그만 (명사)
                nouns = [word for word, tag in pos_tags if tag.startswith('NN')]

                # 복합명사 생성
                compound_nouns = self._extract_compound_nouns_english(pos_tags)
                nouns.extend(compound_nouns)

                logger.info(f"✅ nltk 기반 명사 추출 완료: {len(nouns)} 개")

            elif lang_code == 'ja':
                # 일본어: fugashi
                try:
                    import fugashi

                    # fugashi Tagger 초기화
                    tagger = fugashi.Tagger()

                    # 형태소 분석
                    words = tagger(content)

                    # 명사만 추출
                    for word in words:
                        if word.feature.pos1 == '名詞' and len(word.surface) > 1:
                            nouns.append(word.surface)

                    logger.info(f"✅ fugashi 기반 명사 추출 완료: {len(nouns)} 개")

                except Exception as fugashi_error:
                    logger.warning(f"⚠️ fugashi 사용 실패: {str(fugashi_error)}")
                    logger.info("LLM 기반 명사 추출로 대체합니다.")
                    nouns = await self._extract_nouns_with_llm(content, lang_code)

            elif lang_code == 'zh':
                # 중국어: jieba
                import jieba.posseg as pseg

                words = pseg.cut(content)
                nouns = [word for word, tag in words if tag.startswith('n')]

                logger.info(f"✅ jieba 기반 명사 추출 완료: {len(nouns)} 개")

            else:
                # 기타 언어: LLM 기반 추출
                logger.info(f"ℹ️ 지원하지 않는 언어({lang_code}): LLM 기반 명사 추출 사용")
                nouns = await self._extract_nouns_with_llm(content, lang_code)

            return nouns

        except Exception as e:
            logger.error(f"명사 추출 실패: {str(e)}")
            # 실패 시 LLM 기반 추출로 폴백
            return await self._extract_nouns_with_llm(content, lang_code)

    def _extract_compound_nouns(self, nouns: List[str], content: str, n_gram_range: Tuple[int, int] = (2, 2)) -> List[str]:
        """복합명사 추출 (한국어용 - N-gram)"""
        compound_nouns = []

        try:
            # 2-gram만 생성
            freq_dict = {}

            for i in range(len(nouns) - 1):
                candidate = ' '.join(nouns[i:i+2])

                # 본문에 실제로 등장하는지 확인
                if candidate in content:
                    freq = content.count(candidate)
                    if freq >= 2:  # 2회 이상 등장하는 것만
                        freq_dict[candidate] = freq

            # 빈도 순으로 정렬하여 상위 30개만
            compound_nouns = sorted(freq_dict.keys(), key=lambda x: freq_dict[x], reverse=True)[:30]

            logger.info(f"복합명사 생성: {len(compound_nouns)} 개")
            return compound_nouns

        except Exception as e:
            logger.warning(f"복합명사 추출 실패: {str(e)}")
            return []

    def _extract_compound_nouns_english(self, pos_tags: List[Tuple[str, str]]) -> List[str]:
        """복합명사 추출 (영어용 - 연속된 명사)"""
        compound_nouns = []

        try:
            current_compound = []

            for word, tag in pos_tags:
                if tag.startswith('NN'):
                    current_compound.append(word)
                else:
                    if len(current_compound) >= 2:
                        compound_nouns.append(' '.join(current_compound))
                    current_compound = []

            # 마지막 복합명사 처리
            if len(current_compound) >= 2:
                compound_nouns.append(' '.join(current_compound))

            logger.info(f"영어 복합명사 생성: {len(compound_nouns)} 개")
            return compound_nouns

        except Exception as e:
            logger.warning(f"영어 복합명사 추출 실패: {str(e)}")
            return []

    async def _extract_nouns_with_llm(self, content: str, lang_code: str) -> List[str]:
        """LLM을 사용한 명사 추출 (폴백용)"""
        try:
            prompt = f"""다음 텍스트에서 명사만 추출해주세요. 각 명사는 쉼표로 구분해주세요.

텍스트:
{content[:1500]}

명사 목록:"""

            response = await call_llm(
                prompt=prompt,
                model=settings.default_llm_model
            )

            if hasattr(response, 'content'):
                nouns_text = response.content
            elif isinstance(response, str):
                nouns_text = response
            else:
                nouns_text = str(response)

            # 파싱
            nouns = [n.strip() for n in nouns_text.split(',') if n.strip()]
            return nouns

        except Exception as e:
            logger.error(f"LLM 명사 추출 실패: {str(e)}")
            return []

    def _remove_stopwords(self, nouns: List[str], lang_code: str) -> List[str]:
        """불용어 제거 (stopwordsiso 라이브러리 사용)"""
        try:
            from stopwordsiso import stopwords as stopwords_iso

            # 언어 코드 매핑 (stopwordsiso는 ISO 639-1 코드 사용)
            lang_map = {
                'ko': 'ko',
                'en': 'en',
                'ja': 'ja',
                'zh': 'zh',
            }

            iso_lang = lang_map.get(lang_code, 'en')
            stopwords = stopwords_iso(iso_lang)

        except ImportError:
            logger.warning("stopwordsiso 라이브러리를 사용할 수 없습니다. 불용어 제거를 건너뜁니다.")
            stopwords = set()
        except Exception as e:
            logger.warning(f"불용어 로딩 실패: {str(e)}")
            stopwords = set()

        filtered = []
        for noun in nouns:
            # 소문자 변환 후 비교 (길이 2 이상만 유지)
            if noun.lower() not in stopwords and len(noun) > 1:
                filtered.append(noun)

        logger.info(f"불용어 제거: {len(nouns)} → {len(filtered)} 개")
        return filtered

    async def _score_keywords_with_keybert(self, content: str, nouns: List[str], lang_code: str, top_n: int = 30) -> Dict[str, float]:
        """하이브리드 키워드 스코어링 (의미 70% + 빈도 30%)"""
        try:
            from keybert import KeyBERT

            # 1. 빈도 점수 계산 (0-1 정규화)
            freq_counter = Counter(nouns)
            max_freq = max(freq_counter.values()) if freq_counter else 1
            frequency_scores = {word: count / max_freq for word, count in freq_counter.items()}

            # 2. KeyBERT 의미 점수 계산
            kw_model = KeyBERT(model='paraphrase-multilingual-MiniLM-L12-v2')

            # 명사 리스트를 후보로 제한
            candidates = list(set(nouns))[:200]  # 중복 제거 + 최대 200개

            # KeyBERT로 키워드 추출 (더 많이 추출 후 나중에 필터링)
            keywords = kw_model.extract_keywords(
                content,
                candidates=candidates,
                top_n=min(100, len(candidates)),  # 더 많이 추출
                diversity=0.3
            )

            # 의미 점수 딕셔너리로 변환
            semantic_scores = {kw: score for kw, score in keywords}

            # 3. 하이브리드 점수 계산 (의미 70% + 빈도 30%)
            hybrid_scores = {}
            for word in candidates:
                semantic_score = semantic_scores.get(word, 0.0)  # KeyBERT에 없으면 0
                frequency_score = frequency_scores.get(word, 0.0)

                # 가중 평균: 의미 70%, 빈도 30%
                hybrid_score = (semantic_score * 0.7) + (frequency_score * 0.3)
                hybrid_scores[word] = hybrid_score

            # 4. 상위 top_n 개만 선택
            sorted_keywords = dict(sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)[:top_n])

            # 5. 상위 키워드 로깅 (의미/빈도 분해)
            logger.info(f"✅ 하이브리드 스코어링 완료: {len(sorted_keywords)} 개 (의미 70% + 빈도 30%)")

            if sorted_keywords:
                logger.info("📊 상위 5개 키워드 상세:")
                for i, (word, hybrid_score) in enumerate(list(sorted_keywords.items())[:5], 1):
                    semantic = semantic_scores.get(word, 0.0)
                    frequency = frequency_scores.get(word, 0.0)
                    freq_count = freq_counter.get(word, 0)
                    logger.info(f"  {i}. '{word}': {hybrid_score:.3f} (의미={semantic:.3f}, 빈도={frequency:.3f}, 등장={freq_count}회)")

            return sorted_keywords

        except ImportError:
            logger.warning("KeyBERT를 사용할 수 없습니다. 빈도 기반으로 대체합니다.")
            return self._score_by_frequency(nouns, content)
        except Exception as e:
            logger.error(f"하이브리드 스코어링 실패: {str(e)}")
            return self._score_by_frequency(nouns, content)

    def _score_by_frequency(self, nouns: List[str], content: str) -> Dict[str, float]:
        """빈도 기반 스코어링 (폴백용)"""
        freq_counter = Counter(nouns)

        # 정규화
        max_freq = max(freq_counter.values()) if freq_counter else 1
        normalized = {word: count / max_freq for word, count in freq_counter.items()}

        # 상위 30개만
        sorted_keywords = dict(sorted(normalized.items(), key=lambda x: x[1], reverse=True)[:30])

        return sorted_keywords

    def _convert_to_wordcloud_weights(self, keywords_scores: Dict[str, float]) -> Dict[str, float]:
        """KeyBERT 점수를 워드 클라우드용 가중치로 변환"""
        # 공백을 언더스코어로 치환 (멀티워드 유지)
        converted = {}

        for keyword, score in keywords_scores.items():
            # 공백 → 언더스코어
            keyword_safe = keyword.replace(' ', '_')

            # 점수를 빈도로 변환 (1-100 범위)
            weight = int(score * 100) + 1

            converted[keyword_safe] = weight

        logger.info(f"워드 클라우드 가중치 변환 완료: {len(converted)} 개")
        return converted

    async def _generate_wordcloud(self, keywords_weights: Dict[str, float], lang_code: str) -> str:
        """키워드 가중치로 워드 클라우드 이미지 생성 (개선된 버전)"""
        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # 백엔드 설정

            # 언어별 폰트 설정
            font_path = self._get_font_for_language(lang_code)

            # 워드 클라우드 생성 (개선된 파라미터)
            wordcloud = WordCloud(
                font_path=font_path,
                width=1200,
                height=600,
                background_color='white',
                colormap='viridis',
                max_words=50,  # 최대 단어 수 제한
                min_font_size=12,  # 최소 폰트 크기
                relative_scaling=0.3,  # 상위어 편중 완화 (0: 빈도 무시, 1: 빈도만 고려)
                normalize_plurals=False,  # 복수형 정규화 비활성화
                collocations=False  # 중복 방지
            ).generate_from_frequencies(keywords_weights)

            # 이미지 저장
            timestamp = int(time.time())
            filename = f"wordcloud_{timestamp}.png"
            output_path = os.path.join(self.output_dir, filename)

            plt.figure(figsize=(12, 6))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)
            plt.savefig(output_path, dpi=200, bbox_inches='tight')
            plt.close()

            return output_path

        except Exception as e:
            logger.error(f"워드 클라우드 생성 실패: {str(e)}")
            raise Exception(f"워드 클라우드 생성 중 오류: {str(e)}")

    def _get_font_for_language(self, lang_code: str) -> str:
        """언어별 시스템 폰트 찾기 (matplotlib.font_manager 사용)"""
        try:
            import matplotlib.font_manager as fm

            # 시스템에 설치된 모든 폰트 목록
            available_fonts = [f.name for f in fm.fontManager.ttflist]

            # 언어별 폰트 우선순위
            target_fonts = LANGUAGE_FONTS.get(lang_code, LANGUAGE_FONTS['en'])

            # 우선순위대로 폰트 확인
            for font_name in target_fonts:
                if font_name in available_fonts:
                    logger.info(f"언어({lang_code}) 폰트 사용: {font_name}")

                    # 폰트 파일 경로 찾기
                    for font in fm.fontManager.ttflist:
                        if font.name == font_name:
                            return font.fname

            # 폰트를 찾지 못한 경우
            logger.warning(f"언어({lang_code})에 적합한 폰트를 찾지 못했습니다. 기본 폰트 사용")
            logger.info(f"사용 가능한 폰트 (일부): {sorted(set(available_fonts))[:10]}")
            return None

        except Exception as e:
            logger.error(f"폰트 검색 실패: {str(e)}")
            return None

    async def _upload_to_ncp_tmp(self, file_path: str) -> str:
        """
        로컬 파일을 NCP TMP 버킷에 업로드 (공개 모드)

        Args:
            file_path: 업로드할 파일 경로

        Returns:
            str: 업로드된 파일의 NCP URL
        """
        try:
            bucket_name = settings.naver_bucket_name

            if not bucket_name:
                raise ValueError("NAVER_BUCKET_NAME 환경변수가 설정되지 않았습니다.")

            # 파일명 추출
            filename = os.path.basename(file_path)

            # TMP 폴더에 날짜별로 저장
            date_folder = datetime.now().strftime("%Y%m%d")
            ncp_path = f"TMP/{date_folder}/{filename}"

            # NCP에 업로드
            with open(file_path, 'rb') as file_data:
                self.s3_client.upload_fileobj(
                    file_data,
                    bucket_name,
                    ncp_path
                )

                # 파일을 공개로 설정
                self.s3_client.put_object_acl(
                    Bucket=bucket_name,
                    Key=ncp_path,
                    ACL='public-read'
                )

            # NCP URL 생성
            ncp_url = f"{bucket_name}/TMP/{date_folder}/{filename}"

            logger.info(f"NCP TMP 업로드 완료: {ncp_url}")

            # 로컬 파일 삭제
            try:
                os.remove(file_path)
                logger.info(f"로컬 파일 삭제 완료: {file_path}")
            except Exception as delete_error:
                logger.warning(f"로컬 파일 삭제 실패: {delete_error}")

            return ncp_url

        except Exception as e:
            logger.error(f"NCP 업로드 실패: {str(e)}")
            raise ValueError(f"파일을 NCP 버킷에 업로드하는 중 오류가 발생했습니다: {str(e)}")
