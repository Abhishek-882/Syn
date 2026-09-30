"""Smart On-Chain Multi-Provider Router with Autonomous Cascade & Resilience.

Orchestrates API calls across GMGN CLI, Solscan, RPC endpoints, and local cache.
Features:
- Circuit-breaker fast failover (0ms penalty when an API is down)
- Client-side token bucket rate limiting (avoids 429 penalties)
- Multi-tier immutable caching (serves confirmed on-chain history at 0ms)
- Comprehensive live telemetry exported directly to the visualizer HUD
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

from crypto_syndicate.resilience.circuit_breaker import CircuitBreaker
from crypto_syndicate.resilience.rate_limiter import AdaptiveTokenBucket, DecorrelatedJitter
from crypto_syndicate.resilience.cache import ImmutableOnChainCache
from crypto_syndicate.api.gmgn_cli_bridge import (
    gmgn_cli_call,
    get_token_traders,
    get_wallet_activity,
    get_token_holders,
)
from crypto_syndicate.api.solscan_client import SolscanClient

logger = logging.getLogger("crypto_syndicate.resilience.smart_router")


class SmartOnChainRouter:
    """Enterprise-grade multi-provider router with adaptive failover."""

    def __init__(self, cache_db_path: str = "results/onchain_cache.db") -> None:
        self.cache = ImmutableOnChainCache(db_path=cache_db_path)

        # 1. Circuit Breakers per provider
        self.breakers = {
            "GMGN_CLI": CircuitBreaker(name="GMGN_CLI", failure_threshold=3, recovery_timeout=30.0),
            "SOLSCAN_REST": CircuitBreaker(name="SOLSCAN_REST", failure_threshold=3, recovery_timeout=60.0),
            "SOLANA_RPC": CircuitBreaker(name="SOLANA_RPC", failure_threshold=4, recovery_timeout=20.0),
        }

        # 2. Token Bucket Rate Limiters per provider
        self.rate_limiters = {
            "GMGN_CLI": AdaptiveTokenBucket(rate_per_second=3.0, capacity=6.0),
            "SOLSCAN_REST": AdaptiveTokenBucket(rate_per_second=2.0, capacity=4.0),
            "SOLANA_RPC": AdaptiveTokenBucket(rate_per_second=5.0, capacity=10.0),
        }

        # 3. Provider Latency Telemetry
        self.latencies: Dict[str, float] = {
            "GMGN_CLI": 0.0,
            "SOLSCAN_REST": 0.0,
            "SOLANA_RPC": 0.0,
        }

        self.solscan_client = SolscanClient()

    def fetch_trending_tokens(self, chain: str = "sol", limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch trending tokens with cache bypass check and circuit evaluation."""
        cache_key = f"trending:{chain}:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Try GMGN CLI
        breaker = self.breakers["GMGN_CLI"]
        if breaker.can_execute():
            if self.rate_limiters["GMGN_CLI"].acquire(timeout=2.0):
                t0 = time.time()
                try:
                    res = gmgn_cli_call(["market", "trending", f"--chain={chain}", "--interval=1h", f"--limit={limit}", "--raw"])
                    latency = (time.time() - t0) * 1000.0
                    self.latencies["GMGN_CLI"] = round(latency, 1)

                    data = res.get("data")
                    ranks = []
                    if isinstance(data, dict):
                        ranks = data.get("rank") or data.get("list") or []
                    elif isinstance(data, list):
                        ranks = data

                    if ranks:
                        breaker.record_success()
                        self.cache.set(cache_key, ranks, ttl_seconds=30.0)  # 30s cache for trending
                        return ranks
                    else:
                        breaker.record_failure(Exception("Empty ranks returned"))
                except Exception as exc:
                    breaker.record_failure(exc)

        # Fallback to empty list (caller can supply fixture)
        return []

    def fetch_token_traders(self, chain: str = "sol", address: str = "", limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch early/top traders with circuit breaker protection, caching, and rate limiting."""
        cache_key = f"traders:{chain}:{address}:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        breaker = self.breakers["GMGN_CLI"]
        if breaker.can_execute():
            if self.rate_limiters["GMGN_CLI"].acquire(timeout=2.0):
                t0 = time.time()
                try:
                    res = get_token_traders(chain=chain, address=address, limit=limit)
                    self.latencies["GMGN_CLI"] = round((time.time() - t0) * 1000.0, 1)
                    traders = res.get("data", []) or res.get("list", [])
                    if traders:
                        breaker.record_success()
                        self.cache.set(cache_key, traders, ttl_seconds=60.0)
                        return traders
                    else:
                        breaker.record_failure(Exception("Empty traders"))
                except Exception as exc:
                    breaker.record_failure(exc)
        return []

    def fetch_transfers(self, address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch historical on-chain transfers with immutable caching and circuit failover."""
        cache_key = f"transfers:{address}:{limit}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # 1. Try Solscan REST
        solscan_breaker = self.breakers["SOLSCAN_REST"]
        if solscan_breaker.can_execute():
            if self.rate_limiters["SOLSCAN_REST"].acquire(timeout=1.5):
                t0 = time.time()
                try:
                    transfers = self.solscan_client.get_account_transfers(address, page_size=limit)
                    self.latencies["SOLSCAN_REST"] = round((time.time() - t0) * 1000.0, 1)
                    solscan_breaker.record_success()
                    # Confirmed historical transfers are immutable -> cache forever (0 ttl)
                    self.cache.set(cache_key, transfers, ttl_seconds=None)
                    return transfers
                except Exception as exc:
                    solscan_breaker.record_failure(exc)

        # 2. Try GMGN CLI Wallet Activity Fallback
        gmgn_breaker = self.breakers["GMGN_CLI"]
        if gmgn_breaker.can_execute():
            if self.rate_limiters["GMGN_CLI"].acquire(timeout=1.5):
                t0 = time.time()
                try:
                    res = get_wallet_activity(chain="sol", wallet_address=address, limit=limit)
                    self.latencies["GMGN_CLI"] = round((time.time() - t0) * 1000.0, 1)
                    activities = res.get("data", []) or res.get("list", [])
                    if activities:
                        gmgn_breaker.record_success()
                        self.cache.set(cache_key, activities, ttl_seconds=300.0)
                        return activities
                    else:
                        gmgn_breaker.record_failure(Exception("Empty activity"))
                except Exception as exc:
                    gmgn_breaker.record_failure(exc)

        return []

    def get_health_telemetry(self) -> Dict[str, Any]:
        """Aggregate health metrics across all circuit breakers, rate limiters, and cache."""
        providers = {}
        for name, breaker in self.breakers.items():
            providers[name] = {
                "state": breaker.state,
                "latency_ms": self.latencies.get(name, 0.0),
                "is_available": breaker.can_execute(),
                "failures": breaker.failure_count,
                "trips": breaker.total_trips,
            }

        return {
            "timestamp": time.time(),
            "providers": providers,
            "cache": self.cache.stats(),
        }
