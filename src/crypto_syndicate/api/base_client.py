"""Base API Client with Token Bucket rate limiting, full-jitter exponential backoff,
and SQLite disk caching.
"""

import os
import time
import random
import logging
from typing import Optional, Dict, Any, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from crypto_syndicate.api.rate_limiter import TokenBucketRateLimiter
from crypto_syndicate.api.cache import SQLiteCache
from crypto_syndicate.config import (
    MAX_RETRIES,
    BASE_BACKOFF_SECONDS,
    MAX_BACKOFF_SECONDS,
    get_effective_data_mode,
)

logger = logging.getLogger("crypto_syndicate.api")


class APIClientError(Exception):
    """Base exception for all API client failures."""
    pass


class APIRequestError(APIClientError):
    """Raised for HTTP 400 and 422 client parameter errors."""
    pass


class APIAuthenticationError(APIClientError):
    """Raised for HTTP 401 unauthorized / invalid API key."""
    pass


class APIForbiddenError(APIClientError):
    """Raised for HTTP 403 forbidden / WAF block / plan tier restriction."""
    pass


class APINotFoundError(APIClientError):
    """Raised for HTTP 404 resource not found."""
    pass


class MaxRetriesExceededError(APIClientError):
    """Raised when all retry attempts are exhausted on transient errors."""
    pass


def parse_retry_after(header_val: Optional[str]) -> float:
    """Parses Retry-After header value in seconds."""
    if not header_val:
        return 0.0
    try:
        return max(0.0, float(header_val.strip()))
    except (ValueError, TypeError):
        return 0.0


class BaseAPIClient:
    """Unified HTTP client managing rate limiting, retries, and disk caching."""

    def __init__(
        self,
        provider: str,
        base_url: str,
        api_key: Optional[str] = None,
        rate_limiter: Optional[TokenBucketRateLimiter] = None,
        cache: Optional[SQLiteCache] = None,
        mock_mode: Optional[bool] = None,
        base_backoff_seconds: Optional[float] = None,
    ):
        self.provider = provider.lower().strip()
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""
        self.rate_limiter = rate_limiter
        self.cache = cache
        self.base_backoff_seconds = (
            base_backoff_seconds if base_backoff_seconds is not None else BASE_BACKOFF_SECONDS
        )

        # Determine mock mode: explicit flag takes precedence, else fallback to env resolution
        if mock_mode is not None:
            self.mock_mode = mock_mode
        else:
            try:
                effective = get_effective_data_mode()
                self.mock_mode = (effective == "mock") or (not self.api_key)
            except Exception:
                self.mock_mode = not bool(self.api_key)

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        })

    def _calculate_backoff(self, attempt: int, max_b: float = MAX_BACKOFF_SECONDS) -> float:
        """Calculates decorrelated jittered exponential backoff."""
        multiplier = 2 ** attempt
        capped_backoff = min(max_b, self.base_backoff_seconds * multiplier)
        jitter = random.uniform(0.5, 1.5)
        return capped_backoff * jitter

    def _execute_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json_data: Optional[Any] = None,
        ttl: Optional[float] = None,
        timeout: float = 30.0,
        raise_on_exhaustion: bool = True,
    ) -> Optional[Any]:
        """Executes an HTTP request with caching, rate limiting, and jittered retries."""
        # 1. Check disk cache first (GET only)
        endpoint = url.replace(self.base_url, "").lstrip("/")
        if method.upper() == "GET" and self.cache:
            cached = self.cache.get(self.provider, endpoint, params)
            if cached is not None:
                logger.debug("Cache hit for [%s] %s", self.provider, endpoint)
                return cached

        # 2. Retry loop
        last_exception: Optional[Exception] = None
        last_status_code: Optional[int] = None

        for attempt in range(MAX_RETRIES):
            # Rate limiting acquire
            if self.rate_limiter:
                self.rate_limiter.acquire(1.0)

            try:
                req_headers = dict(self.session.headers)
                if headers:
                    req_headers.update(headers)

                resp = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=req_headers,
                    data=data,
                    json=json_data,
                    timeout=timeout,
                )

                status = resp.status_code

                # Success
                if status == 200:
                    try:
                        res_json = resp.json()
                    except Exception:
                        res_json = resp.text

                    if self.cache and method.upper() == "GET":
                        self.cache.set(self.provider, endpoint, params, 200, res_json, ttl)
                    return res_json

                if status == 204:
                    return {}

                # Fast fail codes
                if status == 400 or status == 422:
                    raise APIRequestError(f"HTTP {status} client error from {self.provider}: {resp.text}")
                if status == 401:
                    raise APIAuthenticationError(f"HTTP 401 unauthorized from {self.provider}. Check API key.")
                if status == 403:
                    raise APIForbiddenError(f"HTTP 403 forbidden / WAF block from {self.provider}: {resp.text}")
                if status == 404:
                    raise APINotFoundError(f"HTTP 404 not found from {self.provider}: {url}")

                # Retryable status codes (429, 500, 502, 503, 504)
                if status in (429, 500, 502, 503, 504):
                    last_status_code = status
                    retry_after = parse_retry_after(resp.headers.get("Retry-After"))
                    backoff = max(retry_after, self._calculate_backoff(attempt))
                    logger.warning(
                        "[%s] HTTP %d on attempt %d/%d for %s. Sleeping %.2fs...",
                        self.provider, status, attempt + 1, MAX_RETRIES, url, backoff,
                    )
                    time.sleep(backoff)
                    continue

                # Any other unexpected status code
                raise APIClientError(f"Unexpected HTTP {status} from {self.provider}: {resp.text}")

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_exception = e
                backoff = self._calculate_backoff(attempt)
                logger.warning(
                    "[%s] Network error on attempt %d/%d: %s. Sleeping %.2fs...",
                    self.provider, attempt + 1, MAX_RETRIES, e, backoff,
                )
                time.sleep(backoff)
                continue

        # All retries exhausted
        logger.error("[%s] Exhausted %d retries for %s", self.provider, MAX_RETRIES, url)
        if raise_on_exhaustion:
            msg = f"Max retries ({MAX_RETRIES}) exceeded for {self.provider} ({url}). Last status: {last_status_code}"
            if last_exception:
                raise MaxRetriesExceededError(f"{msg}. Error: {last_exception}") from last_exception
            raise MaxRetriesExceededError(msg)
        return None

    def _request_with_retry(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        method: str = "GET",
    ) -> Optional[Any]:
        """Convenience method matching test harness signature, returning None on exhaustion."""
        try:
            return self._execute_request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                raise_on_exhaustion=False,
            )
        except (APIRequestError, APIAuthenticationError, APIForbiddenError, APINotFoundError, APIClientError):
            raise
        except Exception as e:
            logger.warning("Request failed: %s", e)
            return None
