import aiohttp
from app.utils.logger.setup import setup_logger
from typing import Any, Dict, Tuple, List

logger = setup_logger('embedding', 'logs/embedding')

async def get_embedding(text: str, **kwargs) -> List[float]:
    """텍스트의 임베딩을 가져옵니다."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://175.209.197.38:8008/embed',
            json={
                "inputs": text,
                "normalize": True,
                "prompt_name": None,
                "truncate": False,
                "truncation_direction": "Right"
            }
        ) as response:
            result = await response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            elif isinstance(result, dict) and 'data' in result:
                if isinstance(result['data'], list) and len(result['data']) > 0:
                    if isinstance(result['data'][0], list):
                        return result['data'][0]
                    return result['data']
            logger.error(f"예상치 못한 임베딩 응답 형식: {result}")
            raise ValueError(f"잘못된 임베딩 응답 형식: {result}")
