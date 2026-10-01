"""Configuration management for Crypto Syndicate Research System.

Strictly resolves API credentials and operational settings from environment variables.
Never hardcodes credentials in any file.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("crypto_syndicate.config")


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


# Credentials — Strictly resolved from environment variables
GMGN_API_KEY: Optional[str] = os.getenv("GMGN_API_KEY", "").strip() or None
SOLSCAN_API_KEY: Optional[str] = os.getenv("SOLSCAN_API_KEY", "").strip() or None

# Operational Mode ('live', 'mock', 'auto')
# Checked against both DATA_MODE and CRYPTO_DATA_MODE for compatibility
DATA_MODE: str = os.getenv("CRYPTO_DATA_MODE", os.getenv("DATA_MODE", "auto")).lower()
CRYPTO_DATA_MODE: str = DATA_MODE

# Rate Limiting & Resilience Defaults
GMGN_RATE_LIMIT_RPS: float = float(os.getenv("GMGN_RATE_LIMIT_RPS", "1.0"))
SOLSCAN_RATE_LIMIT_RPS: float = float(os.getenv("SOLSCAN_RATE_LIMIT_RPS", "10.0"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "5"))
BASE_BACKOFF_SECONDS: float = float(os.getenv("BASE_BACKOFF_SECONDS", "1.0"))
MAX_BACKOFF_SECONDS: float = float(os.getenv("MAX_BACKOFF_SECONDS", "30.0"))

# SQLite Cache Configuration
CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() in ("1", "true", "yes")
CACHE_DB_PATH: str = os.getenv("CACHE_DB_PATH", ".cache/api_cache.db")
DEFAULT_CACHE_TTL_SECONDS: float = float(os.getenv("CACHE_TTL_SECONDS", "300.0"))
CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))

# Daemon & Polling Intervals
POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
HEARTBEAT_INTERVAL_SECONDS: int = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "60"))

# Turbo Scanner Configuration
KEEPER_SCAN_INTERVAL: int = int(os.getenv("KEEPER_SCAN_INTERVAL", "15"))
KEEPER_EXPANSION_INTERVAL: int = int(os.getenv("KEEPER_EXPANSION_INTERVAL", "120"))
DEPLOYER_MIN_PROFIT_USD: float = float(os.getenv("DEPLOYER_MIN_PROFIT_USD", "5.0"))
DEPLOYER_BATCH_COUNT: int = int(os.getenv("DEPLOYER_BATCH_COUNT", "5"))
SOLSCAN_JWT_TOKEN: Optional[str] = (
    os.getenv("SOLSCAN_JWT_TOKEN", "").strip()
    or os.getenv("SOLSCAN_API_KEY", "").strip()
    or None
)

# File Logging Paths
LOG_DIR: str = os.getenv("LOG_DIR", "logs")
ALERTS_LOG_PATH: str = os.getenv("ALERTS_LOG_PATH", os.path.join(LOG_DIR, "alerts.log"))
ALERTS_JSONL_PATH: str = os.getenv("ALERTS_JSONL_PATH", os.path.join(LOG_DIR, "alerts.jsonl"))
HEARTBEAT_LOG_PATH: str = os.getenv("HEARTBEAT_LOG_PATH", os.path.join(LOG_DIR, "heartbeat.log"))

# Discovery & Pattern Heuristics
SUSPICION_THRESHOLD: float = float(os.getenv("SUSPICION_THRESHOLD", "50.0"))
EARLY_ENTRY_WINDOW_SECONDS: int = int(os.getenv("EARLY_ENTRY_WINDOW_SECONDS", "120"))


def mask_credential(key: Optional[str]) -> str:
    """Safely masks API keys for logging and display without leaking raw secrets."""
    if not key:
        return "<NOT_SET>"
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


def get_effective_data_mode() -> str:
    """Resolves the effective data mode ('live' or 'mock').

    In 'auto' mode, automatically falls back to deterministic offline 'mock' fixtures
    if API keys are missing.
    """
    mode = os.getenv("CRYPTO_DATA_MODE", os.getenv("DATA_MODE", "auto")).lower()
    gmgn_key = os.getenv("GMGN_API_KEY", "").strip() or None
    solscan_key = os.getenv("SOLSCAN_API_KEY", "").strip() or None

    if mode == "mock":
        return "mock"
    if mode == "live":
        if not gmgn_key or not solscan_key:
            raise ConfigurationError(
                "DATA_MODE is 'live' but GMGN_API_KEY or SOLSCAN_API_KEY is not set in environment."
            )
        return "live"
    # mode == 'auto'
    if gmgn_key and solscan_key:
        return "live"
    logger.info(
        "API keys not fully detected in environment (GMGN: %s, Solscan: %s). "
        "Running in deterministic offline mock mode.",
        mask_credential(gmgn_key),
        mask_credential(solscan_key),
    )
    return "mock"


@dataclass(frozen=True)
class AppConfig:
    """Container for application runtime configuration."""
    gmgn_api_key: Optional[str] = GMGN_API_KEY
    solscan_api_key: Optional[str] = SOLSCAN_API_KEY
    crypto_data_mode: str = DATA_MODE
    gmgn_rate_limit_rps: float = GMGN_RATE_LIMIT_RPS
    solscan_rate_limit_rps: float = SOLSCAN_RATE_LIMIT_RPS
    max_retries: int = MAX_RETRIES
    base_backoff_seconds: float = BASE_BACKOFF_SECONDS
    max_backoff_seconds: float = MAX_BACKOFF_SECONDS
    cache_enabled: bool = CACHE_ENABLED
    cache_db_path: str = CACHE_DB_PATH
    default_cache_ttl_seconds: float = DEFAULT_CACHE_TTL_SECONDS
    poll_interval_seconds: int = POLL_INTERVAL_SECONDS
    heartbeat_interval_seconds: int = HEARTBEAT_INTERVAL_SECONDS
    suspicion_threshold: float = SUSPICION_THRESHOLD
    early_entry_window_seconds: int = EARLY_ENTRY_WINDOW_SECONDS


def load_config() -> AppConfig:
    """Loads a fresh AppConfig instance from current environment variables."""
    gmgn_key = os.getenv("GMGN_API_KEY", "").strip() or None
    solscan_key = os.getenv("SOLSCAN_API_KEY", "").strip() or None
    mode = os.getenv("CRYPTO_DATA_MODE", os.getenv("DATA_MODE", "auto")).lower()

    return AppConfig(
        gmgn_api_key=gmgn_key,
        solscan_api_key=solscan_key,
        crypto_data_mode=mode,
        gmgn_rate_limit_rps=float(os.getenv("GMGN_RATE_LIMIT_RPS", "1.0")),
        solscan_rate_limit_rps=float(os.getenv("SOLSCAN_RATE_LIMIT_RPS", "10.0")),
        max_retries=int(os.getenv("MAX_RETRIES", "5")),
        base_backoff_seconds=float(os.getenv("BASE_BACKOFF_SECONDS", "1.0")),
        max_backoff_seconds=float(os.getenv("MAX_BACKOFF_SECONDS", "30.0")),
        cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() in ("1", "true", "yes"),
        cache_db_path=os.getenv("CACHE_DB_PATH", ".cache/api_cache.db"),
        default_cache_ttl_seconds=float(os.getenv("CACHE_TTL_SECONDS", "300.0")),
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "300")),
        heartbeat_interval_seconds=int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "60")),
        suspicion_threshold=float(os.getenv("SUSPICION_THRESHOLD", "50.0")),
        early_entry_window_seconds=int(os.getenv("EARLY_ENTRY_WINDOW_SECONDS", "120")),
    )
