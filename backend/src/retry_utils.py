"""Retry utilities for robust error handling."""

import time
import logging
from typing import Any, Callable, Optional, TypeVar
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiply delay by this factor after each retry
        jitter: Add random jitter to delay
    """

    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f'{func.__name__} succeeded on attempt {attempt + 1}/{max_retries + 1}'
                        )
                    return result
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        # Calculate delay with optional jitter
                        actual_delay = delay
                        if jitter:
                            import random

                            actual_delay = delay * (0.5 + random.random())

                        logger.warning(
                            f'{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. '
                            f'Retrying in {actual_delay:.2f}s...'
                        )
                        time.sleep(actual_delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f'{func.__name__} failed after {max_retries + 1} attempts: {e}'
                        )

            return None

        return wrapper

    return decorator


class RateLimiter:
    """Rate limiter to respect server limits."""

    def __init__(self, requests_per_second: float = 1.0):
        """Initialize rate limiter."""
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0

    def wait_if_needed(self):
        """Wait if necessary to respect rate limit."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            logger.debug(f'Rate limiting: waiting {wait_time:.3f}s')
            time.sleep(wait_time)
        self.last_request_time = time.time()


def make_request_with_retry(
    func: Callable,
    *args,
    max_retries: int = 3,
    timeout: float = 30.0,
    **kwargs
) -> Optional[Any]:
    """
    Make a request with retry logic.

    Args:
        func: Function to call (e.g., requests.get)
        max_retries: Number of retries
        timeout: Request timeout
        args/kwargs: Arguments to pass to func

    Returns:
        Result from func or None if all retries failed
    """

    @retry_with_backoff(max_retries=max_retries)
    def _request():
        return func(*args, timeout=timeout, **kwargs)

    return _request()
