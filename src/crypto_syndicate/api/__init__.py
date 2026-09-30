"""API Ingestion & Caching Layer for Crypto Syndicate Research System.

Exports:
- SolscanClient: Client for Solscan Pro API v2
- GMGNClient: Client for GMGN Quotation and Multi-Chain Service
- TokenBucketRateLimiter: High-precision rate limiter
- SQLiteCache: Local SQLite disk cache with SHA-256 keying and tiered TTL
- CryptoDataClient: Unified multi-chain on-chain data facade
- APIClient: Compatibility client adapter
"""

import os
from typing import Optional, Dict, Any, List

from crypto_syndicate.api.models import (
    TokenLaunchEvent,
    TradeRecord,
    FundingTransferRecord,
    WalletScore,
    SyndicateCluster,
    PatternType,
)
from crypto_syndicate.api.rate_limiter import (
    TokenBucketRateLimiter,
    RateLimitError,
    RateLimitTimeoutError,
    get_rate_limiter,
)
from crypto_syndicate.api.cache import (
    SQLiteCache,
    TTL_IMMUTABLE,
    TTL_SEMI_STATIC,
    TTL_DYNAMIC,
    TTL_DEFAULT,
)
from crypto_syndicate.api.base_client import (
    BaseAPIClient,
    APIClientError,
    APIRequestError,
    APIAuthenticationError,
    APIForbiddenError,
    APINotFoundError,
    MaxRetriesExceededError,
)
from crypto_syndicate.api.gmgn_client import GMGNClient
from crypto_syndicate.api.solscan_client import SolscanClient
from crypto_syndicate.api.fixtures import (
    FixtureProvider,
    get_mock_clusters,
    get_mock_token_launches,
    get_mock_token_trades,
    get_mock_wallet_transfers,
    get_mock_account_metadata,
)
from crypto_syndicate.config import (
    AppConfig,
    load_config,
    get_effective_data_mode,
)


class CryptoDataClient:
    """Unified multi-chain on-chain data facade for downstream discovery engine."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.cache = SQLiteCache(db_path=self.config.cache_db_path)
        self.gmgn = GMGNClient(api_key=self.config.gmgn_api_key, cache=self.cache)
        self.solscan = SolscanClient(api_key=self.config.solscan_api_key, cache=self.cache)
        self.fixtures = FixtureProvider()

    def _should_use_fixtures(self) -> bool:
        mode = self.config.crypto_data_mode
        if mode == "mock":
            return True
        if mode == "auto":
            return not (self.config.gmgn_api_key and self.config.solscan_api_key)
        return False

    def get_new_token_launches(self, chain: str = "sol", time_period: str = "1h") -> List[TokenLaunchEvent]:
        if self._should_use_fixtures():
            return self.fixtures.get_new_token_launches(chain=chain, time_period=time_period)
        return self.gmgn.get_new_token_launches(chain=chain, time_period=time_period)

    def get_token_trades(self, chain: str, token_address: str, limit: int = 500) -> List[TradeRecord]:
        if self._should_use_fixtures():
            return self.fixtures.get_token_trades(chain=chain, token_address=token_address, limit=limit)
        return self.gmgn.get_token_trades(chain=chain, token_address=token_address, limit=limit)

    def get_wallet_transfers(self, chain: str, wallet_address: str, flow: str = "in") -> List[FundingTransferRecord]:
        if self._should_use_fixtures():
            return self.fixtures.get_wallet_transfers(chain=chain, wallet_address=wallet_address, flow=flow)
        if chain in ("sol", "solana"):
            return self.solscan.get_account_transfers(address=wallet_address, flow=flow)
        return self.fixtures.get_wallet_transfers(chain=chain, wallet_address=wallet_address, flow=flow)

    def get_account_metadata(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        if self._should_use_fixtures():
            return self.fixtures.get_account_metadata(wallet_address=wallet_address)
        return self.solscan.get_account_metadata(address=wallet_address)


class APIClient:
    """Compatibility adapter matching prototype APIClient interface."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.cache = SQLiteCache(db_path=self.config.cache_db_path)
        self.gmgn = GMGNClient(api_key=self.config.gmgn_api_key, cache=self.cache)
        self.solscan = SolscanClient(api_key=self.config.solscan_api_key, cache=self.cache)

        self.gmgn_url = self.gmgn.BASE_URL
        self.solscan_url = self.solscan.BASE_URL
        self.gmgn_headers = self.gmgn.gmgn_headers
        self.solscan_headers = self.solscan.solscan_headers

    def get_recent_launches(self, chain: str = "sol", limit: int = 50) -> List[Any]:
        return self.gmgn.get_recent_launches(chain=chain, limit=limit)

    def get_token_traders(self, token: str, chain: str = "sol") -> List[Dict[str, Any]]:
        return self.gmgn.get_token_buyers(token_address=token, chain=chain)

    def get_token_buyers(self, token: str, chain: str = "sol") -> List[Dict[str, Any]]:
        return self.gmgn.get_token_buyers(token_address=token, chain=chain)

    def get_wallet_funding(self, wallet: str, chain: str = "sol") -> List[Any]:
        return self.solscan.get_wallet_funding(address=wallet)

    def get_wallet_transfers(self, wallet: str, chain: str = "sol") -> List[Any]:
        return self.solscan.get_wallet_funding(address=wallet)

    def _request_with_retry(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        method: str = "GET",
    ) -> Optional[Any]:
        client = self.gmgn if "gmgn.ai" in url else self.solscan
        return client._request_with_retry(url=url, params=params, headers=headers, method=method)


__all__ = [
    "TokenLaunchEvent",
    "TradeRecord",
    "FundingTransferRecord",
    "WalletScore",
    "SyndicateCluster",
    "PatternType",
    "TokenBucketRateLimiter",
    "RateLimitError",
    "RateLimitTimeoutError",
    "get_rate_limiter",
    "SQLiteCache",
    "TTL_IMMUTABLE",
    "TTL_SEMI_STATIC",
    "TTL_DYNAMIC",
    "TTL_DEFAULT",
    "BaseAPIClient",
    "APIClientError",
    "APIRequestError",
    "APIAuthenticationError",
    "APIForbiddenError",
    "APINotFoundError",
    "MaxRetriesExceededError",
    "GMGNClient",
    "SolscanClient",
    "CryptoDataClient",
    "APIClient",
    "FixtureProvider",
    "get_mock_clusters",
    "get_mock_token_launches",
    "get_mock_token_trades",
    "get_mock_wallet_transfers",
    "get_mock_account_metadata",
]
