"""Crypto Syndicate Research & Continuous Monitoring System.

Package initialization and public API re-exports.
"""

from crypto_syndicate.api import (
    CryptoDataClient,
    APIClient,
    GMGNClient,
    SolscanClient,
    TokenBucketRateLimiter,
    SQLiteCache,
    TokenLaunchEvent,
    TradeRecord,
    FundingTransferRecord,
    WalletScore,
    SyndicateCluster,
    PatternType,
    FixtureProvider,
)
from crypto_syndicate import config

__version__ = "0.1.0"

__all__ = [
    "config",
    "CryptoDataClient",
    "APIClient",
    "GMGNClient",
    "SolscanClient",
    "TokenBucketRateLimiter",
    "SQLiteCache",
    "TokenLaunchEvent",
    "TradeRecord",
    "FundingTransferRecord",
    "WalletScore",
    "SyndicateCluster",
    "PatternType",
    "FixtureProvider",
]
