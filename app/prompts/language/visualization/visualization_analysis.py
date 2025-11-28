"""
시각화 분석 프롬프트 모듈
언어별 시각화 분석 프롬프트를 관리합니다.
"""

from typing import Dict

class VisualizationAnalysisPrompts:
    """시각화 분석 프롬프트 클래스"""
    
    # 언어별 프롬프트 정의
    PROMPTS: Dict[str, str] = {
        "ko": """이 시각화를 분석하여 핵심 데이터와 인사이트를 JSON 형식으로 제공해주세요.

분석 내용:
- 시각화 유형과 주요 수치
- 데이터 트렌드와 패턴
- 주요 인사이트 (최댓값, 최솟값, 변화 추이)

**응답 형식 (반드시 JSON):**
{
    "analysis_text": "TTS로 읽어질 자연스러운 분석 설명 (200자 이내)"
}

**응답 예시:**
{
    "analysis_text": "이 차트는 분기별 총 판매량을 보여줍니다. 1분기에 56,300개로 최고치를 기록했으나, 2분기에는 50,400개로 약 10% 감소했습니다."
}

**중요: analysis_text는 마치 사람이 차트를 보고 설명하듯이 자연스럽고 간결하게 작성해주세요.**""",
        
        "en": """Analyze this visualization and explain the key data and insights.

Analysis should include:
- Visualization type and key figures
- Data trends and patterns
- Key insights (maximum, minimum, change trends)

**Important: Your response must be in plain text format. Explain naturally and concisely in sentences, not in JSON format.**""",
        
        "ja": """この可視化を分析し、主要なデータとインサイトを説明してください。

分析内容：
- 可視化タイプと主要数値
- データトレンドとパターン
- 主要インサイト（最大値、最小値、変化トレンド）

**重要：回答は必ずプレーンテキスト形式で作成してください。JSON形式ではなく、自然で簡潔な文章で説明してください。**""",
        
        "zh": """分析此可视化并解释关键数据和洞察。

分析内容：
- 可视化类型和主要数值
- 数据趋势和模式
- 主要洞察（最大值、最小值、变化趋势）

**重要：您的回答必须是纯文本格式。请用自然简洁的句子说明，而不是JSON格式。**"""
    }
    
    @classmethod
    def get_prompt(cls, language: str = "ko") -> str:
        """
        언어별 시각화 분석 프롬프트를 반환합니다.
        
        Args:
            language: 언어 코드 (ko, en, ja, zh, es, fr, de)
            
        Returns:
            str: 해당 언어의 프롬프트
        """
        return cls.PROMPTS.get(language, cls.PROMPTS["ko"])


# 편의 함수들
def get_analysis_prompt(language: str = "ko") -> str:
    """언어별 시각화 분석 프롬프트 반환 (편의 함수)"""
    return VisualizationAnalysisPrompts.get_prompt(language)

