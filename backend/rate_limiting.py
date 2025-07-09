#!/usr/bin/env python3
"""
Rate limiting module for the backend.
Contains the RateLimiter class and rate limiting functions.
"""

import asyncio
from collections import deque, defaultdict
from .config import (
    CHAT_RATE_LIMIT_REQUESTS,
    CHAT_RATE_LIMIT_WINDOW,
    FILE_UPLOAD_RATE_LIMIT_REQUESTS,
    FILE_UPLOAD_RATE_LIMIT_WINDOW,
    AUDIO_RATE_LIMIT_REQUESTS,
    AUDIO_RATE_LIMIT_WINDOW,
    AUTH_RATE_LIMIT_REQUESTS,
    AUTH_RATE_LIMIT_WINDOW,
)


class RateLimiter:
    """
    Rate limiter class for managing request limits per user.

    This class implements a sliding window rate limiting mechanism that tracks
    requests per user and enforces limits based on a configurable time window.

    :param max_requests: Maximum number of requests allowed in the time window.
    :type max_requests: int
    :param time_window: Time window in seconds.
    :type time_window: int
    """

    def __init__(self, max_requests: int = 60, time_window: int = 60) -> None:
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(deque)

    async def check_and_update(self, user_id: str) -> bool:
        now = asyncio.get_event_loop().time()
        user_requests = self.requests[user_id]

        # Remove old requests
        while user_requests and now - user_requests[0] > self.time_window:
            user_requests.popleft()

        if len(user_requests) >= self.max_requests:
            return False

        user_requests.append(now)
        return True


# Initialize different rate limiters for different operations
chat_rate_limiter = RateLimiter(CHAT_RATE_LIMIT_REQUESTS, CHAT_RATE_LIMIT_WINDOW)
file_upload_rate_limiter = RateLimiter(
    FILE_UPLOAD_RATE_LIMIT_REQUESTS, FILE_UPLOAD_RATE_LIMIT_WINDOW
)
audio_rate_limiter = RateLimiter(AUDIO_RATE_LIMIT_REQUESTS, AUDIO_RATE_LIMIT_WINDOW)
auth_rate_limiter = RateLimiter(AUTH_RATE_LIMIT_REQUESTS, AUTH_RATE_LIMIT_WINDOW)


async def check_rate_limit(user_id: str, operation_type: str = "chat") -> bool:
    """
    Check if a user has exceeded their rate limit for a specific operation.

    :param user_id: User identifier to check rate limit for.
    :type user_id: str
    :param operation_type: Type of operation to check rate limit for.
    :type operation_type: str
    :return: True if rate limit not exceeded, False otherwise.
    :rtype: bool
    """
    if operation_type == "chat":
        return await chat_rate_limiter.check_and_update(user_id)
    elif operation_type == "file_upload":
        return await file_upload_rate_limiter.check_and_update(user_id)
    elif operation_type == "audio":
        return await audio_rate_limiter.check_and_update(user_id)
    elif operation_type == "auth":
        return await auth_rate_limiter.check_and_update(user_id)
    else:
        # Default to chat rate limiter
        return await chat_rate_limiter.check_and_update(user_id)


def get_rate_limit_info(operation_type: str = "chat") -> dict:
    """
    Get rate limit information for a specific operation.

    :param operation_type: The type of operation (e.g., 'chat', 'file_upload', 'audio', 'auth').
    :type operation_type: str
    :return: Dictionary containing rate limit information.
    :rtype: dict
    """
    if operation_type == "chat":
        return {
            "max_requests": CHAT_RATE_LIMIT_REQUESTS,
            "time_window": CHAT_RATE_LIMIT_WINDOW,
            "requests_per_second": CHAT_RATE_LIMIT_REQUESTS / CHAT_RATE_LIMIT_WINDOW,
        }
    elif operation_type == "file_upload":
        return {
            "max_requests": FILE_UPLOAD_RATE_LIMIT_REQUESTS,
            "time_window": FILE_UPLOAD_RATE_LIMIT_WINDOW,
            "requests_per_second": FILE_UPLOAD_RATE_LIMIT_REQUESTS
            / FILE_UPLOAD_RATE_LIMIT_WINDOW,
        }
    elif operation_type == "audio":
        return {
            "max_requests": AUDIO_RATE_LIMIT_REQUESTS,
            "time_window": AUDIO_RATE_LIMIT_WINDOW,
            "requests_per_second": AUDIO_RATE_LIMIT_REQUESTS / AUDIO_RATE_LIMIT_WINDOW,
        }
    elif operation_type == "auth":
        return {
            "max_requests": AUTH_RATE_LIMIT_REQUESTS,
            "time_window": AUTH_RATE_LIMIT_WINDOW,
            "requests_per_second": AUTH_RATE_LIMIT_REQUESTS / AUTH_RATE_LIMIT_WINDOW,
        }
    else:
        return {
            "max_requests": CHAT_RATE_LIMIT_REQUESTS,
            "time_window": CHAT_RATE_LIMIT_WINDOW,
            "requests_per_second": CHAT_RATE_LIMIT_REQUESTS / CHAT_RATE_LIMIT_WINDOW,
        }
