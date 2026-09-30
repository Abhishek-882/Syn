"""SQLite disk cache for API requests with SHA-256 keying and tiered TTL.

Prevents redundant external requests, operates in WAL mode for safe multi-process
concurrency, and supports tiered TTL:
- Immutable historical blocks/transfers: Permanent (TTL ~year 2286)
- Semi-static token metadata/security: 24 hours
- Dynamic polling (launches, live swaps): 60 seconds
"""

import os
import time
import json
import sqlite3
import hashlib
import logging
from typing import Optional, Dict, Any, Tuple, Union

logger = logging.getLogger("crypto_syndicate.cache")

TTL_IMMUTABLE: float = 9999999999.0  # Sentinel for permanent historical records (~year 2286)
TTL_SEMI_STATIC: float = 86400.0     # 24 Hours
TTL_DYNAMIC: float = 60.0            # 1 Minute
TTL_DEFAULT: float = 300.0           # 5 Minutes


class SQLiteCache:
    """Thread-safe and process-safe SQLite disk cache with SHA-256 request hashing."""

    def __init__(self, db_path: str = ".cache/api_cache.db", default_ttl: float = TTL_DEFAULT):
        self.db_path = db_path
        self.default_ttl = default_ttl
        self._ensure_dir()
        self._init_db()

    def _ensure_dir(self) -> None:
        dir_name = os.path.dirname(self.db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def _init_db(self) -> None:
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS api_cache (
                        cache_key TEXT PRIMARY KEY,
                        provider TEXT NOT NULL,
                        endpoint TEXT NOT NULL,
                        params_hash TEXT NOT NULL,
                        status_code INTEGER NOT NULL,
                        response_body TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        expires_at REAL NOT NULL
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON api_cache(expires_at);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_provider ON api_cache(provider, endpoint);")
        except Exception as e:
            logger.warning("Failed to initialize SQLite cache table: %s", e)

    def generate_key(
        self,
        provider: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str]:
        """Generates deterministic SHA-256 cache key and params hash."""
        prov = provider.strip().lower()
        ep = endpoint.strip().lower().strip("/")

        cleaned_params = {}
        if params:
            for k, v in sorted(params.items()):
                if k.lower() not in ("token", "api_key", "x-route-key", "authorization", "_t", "nonce"):
                    cleaned_params[k] = v

        params_json = json.dumps(cleaned_params, sort_keys=True, separators=(",", ":"))
        params_hash = hashlib.sha256(params_json.encode("utf-8")).hexdigest()
        raw_key = f"{prov}:{ep}:{params_json}"
        cache_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return cache_key, params_hash

    def resolve_ttl(
        self,
        provider: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Determines tiered TTL based on endpoint characteristics."""
        ep = endpoint.strip().lower().strip("/")
        # Immutable endpoints
        if ep.startswith("transaction/") or ep == "account/metadata":
            return TTL_IMMUTABLE
        if ep == "account/transfer" and params and params.get("to_time"):
            try:
                if float(params["to_time"]) < time.time() - 3600:
                    return TTL_IMMUTABLE
            except (ValueError, TypeError):
                pass
        # Semi-static endpoints
        if ep.startswith("tokens/") or ep.startswith("token/holders"):
            return TTL_SEMI_STATIC
        # Dynamic polling endpoints
        if ep.startswith("rank/") or ep == "token/latest" or "new_pairs" in ep:
            return TTL_DYNAMIC
        return self.default_ttl

    def get(
        self,
        provider: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """Retrieves cached response if present and not expired."""
        cache_key, _ = self.generate_key(provider, endpoint, params)
        now = time.time()
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT response_body, expires_at FROM api_cache WHERE cache_key = ?",
                    (cache_key,),
                )
                row = cursor.fetchone()
                if row:
                    body, expires_at = row
                    if expires_at > now:
                        return json.loads(body)
                    else:
                        conn.execute("DELETE FROM api_cache WHERE cache_key = ?", (cache_key,))
        except Exception as e:
            logger.warning("Cache read failed for key %s: %s", cache_key, e)
        return None

    def set(
        self,
        provider: str,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        status_code: int,
        response_body: Union[str, Dict[str, Any], list],
        ttl: Optional[float] = None,
    ) -> str:
        """Saves a successful HTTP response to disk cache.

        Never caches HTTP errors (status_code != 200).
        """
        if status_code != 200:
            return ""

        cache_key, params_hash = self.generate_key(provider, endpoint, params)
        now = time.time()
        actual_ttl = ttl if ttl is not None else self.resolve_ttl(provider, endpoint, params)
        expires_at = now + actual_ttl if actual_ttl < TTL_IMMUTABLE else TTL_IMMUTABLE
        body_str = response_body if isinstance(response_body, str) else json.dumps(response_body)

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO api_cache 
                    (cache_key, provider, endpoint, params_hash, status_code, response_body, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cache_key,
                        provider.lower(),
                        endpoint.lower().strip("/"),
                        params_hash,
                        status_code,
                        body_str,
                        now,
                        expires_at,
                    ),
                )
        except Exception as e:
            logger.warning("Cache write failed for key %s: %s", cache_key, e)
        return cache_key

    def cleanup_expired(self) -> int:
        """Removes expired cache records while preserving immutable entries."""
        now = time.time()
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM api_cache WHERE expires_at <= ? AND expires_at < 9000000000.0",
                    (now,),
                )
                return cursor.rowcount
        except Exception as e:
            logger.warning("Cache cleanup failed: %s", e)
            return 0

    def clear(self) -> None:
        """Clears all entries from the cache."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM api_cache;")
        except Exception as e:
            logger.warning("Cache clear failed: %s", e)

    def close(self) -> None:
        """No persistent connection pool held; kept for Windows test cleanup compatibility."""
        pass

    def __enter__(self) -> "SQLiteCache":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
