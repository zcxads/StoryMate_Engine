"""시각화 프롬프트 모듈"""

from .table import get_table_prompt
from .chart import get_chart_prompt

__all__ = [
    "get_table_prompt",
    "get_chart_prompt"
]