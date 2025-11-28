import time
from app.utils.logger.setup import setup_logger
import asyncio
import functools
from contextlib import contextmanager
from typing import Dict, Any, Callable, TypeVar, ParamSpec

logger = setup_logger('timing')

T = TypeVar('T')
P = ParamSpec('P')


class TimingStats:
    def __init__(self):
        self._timings: Dict[str, float] = {}

    def add_timing(self, name: str, duration: float):
        self._timings[name] = duration

    def get_timings(self) -> Dict[str, float]:
        return self._timings.copy()

    def clear(self):
        self._timings.clear()


class TimingManager:
    def __init__(self):
        self._stats = TimingStats()

    @contextmanager
    def measure(self, name: str):
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            self._stats.add_timing(name, duration)
            logger.debug(f"Execution time for {name}: {duration:.4f} seconds")

    def get_stats(self) -> Dict[str, float]:
        return self._stats.get_timings()

    def clear_stats(self):
        self._stats.clear()


def add_timing_to_response(response: Any, timing_stats: Dict[str, float]) -> Any:
    """Helper function to add timing stats to response"""
    if hasattr(response, 'dict') and callable(response.dict):
        # Pydantic model
        response_dict = response.dict()
        response_dict['executionTimes'] = timing_stats

        # Update if the model has executionTimes field
        if hasattr(response, 'executionTimes'):
            response.executionTimes = timing_stats

    elif isinstance(response, dict):
        # Dictionary
        response['executionTimes'] = timing_stats

    return response


def timing_decorator(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator that measures execution time and adds it to response if possible"""
    @functools.wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        timing_manager = TimingManager()
        start_time = time.perf_counter()

        try:
            result = await func(*args, **kwargs)
        finally:
            end_time = time.perf_counter()
            timing_manager._stats.add_timing(
                func.__name__,
                end_time - start_time
            )

        # Add timing information without modifying original response structure
        return add_timing_to_response(result, timing_manager.get_stats())

    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        timing_manager = TimingManager()
        start_time = time.perf_counter()

        try:
            result = func(*args, **kwargs)
        finally:
            end_time = time.perf_counter()
            timing_manager._stats.add_timing(
                func.__name__,
                end_time - start_time
            )

        # Add timing information without modifying original response structure
        return add_timing_to_response(result, timing_manager.get_stats())

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
