import aiohttp
from app.utils.logger.setup import setup_logger
from typing import Any, Dict, Tuple, List

logger = setup_logger('vectordb', 'logs/vectordb')

async def get_similar_background_music(embedding: List[float], **kwargs) -> List[Dict[str, Any]]:
    """임베딩을 기반으로 유사한 배경음악을 검색합니다."""
    async with aiohttp.ClientSession() as session:
        try:
            response = await session.post(
                'http://175.209.197.38:6333/collections/bgm/points/search',
                json={
                    "vector": embedding,
                    "limit": 5,
                    "with_payload": [
                        "sentence",
                        "situation",
                        "categories"
                    ]
                }
            )
            result = await response.json()
            # logger.info(f"Qdrant 검색 결과: {result}")
            return result.get('result', [])
        except Exception as e:
            logger.error(f"유사 배경음악 검색 중 오류 발생: {str(e)}")
            return []


async def get_similar_effects(embedding: List[float]) -> List[Dict[str, Any]]:
    """임베딩을 기반으로 유사한 효과음을 검색합니다."""
    async with aiohttp.ClientSession() as session:
        try:
            response = await session.post(
                'http://175.209.197.38:6333/collections/effects/points/search',
                json={
                    "vector": embedding,
                    "limit": 5,
                    "with_payload": [
                        "sentence",
                        "situation",
                        "environment",
                        "affect",
                        "action"
                    ]
                }
            )
            result = await response.json()
            return result.get('result', [])
        except Exception as e:
            logger.error(f"Error in get_similar_effects: {str(e)}")
            return []
