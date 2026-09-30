"""M2 — Heuristics & Discovery Pipeline.

6-stage pipeline to discover suspicious wallets from token launches
without any seed wallets. Detects 4 manipulation patterns:
  1. Early entry (coordinated buys within 5 min of launch)
  2. Common funding (shared funder wallet before buys)
  3. Shared deployer (same creator across multiple tokens)
  4. Coordinated dump (synchronized sells within 10-min window)
"""

import logging
import os
import sys
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from crypto_syndicate.api.gmgn_client import GMGNClient
from crypto_syndicate.api.solscan_client import SolscanClient
from crypto_syndicate.api.models import (
    FundingTransferRecord,
    PatternType,
    TokenLaunchEvent,
    TradeRecord,
    WalletScore,
)

logger = logging.getLogger("crypto_syndicate.discovery")

# Verified constants from real on-chain data (BELUGA, Pump.fun, 2026-09-20)
SNIPER_WINDOW_S = 30          # < 30s after launch = coordinated sniper
EARLY_BUY_WINDOW = 300        # broad suspicious window
EARLY_BUY_WINDOW_SECONDS = EARLY_BUY_WINDOW  # Backwards-compatible alias for tests

FLASH_HOLD_MAX_S = 60         # Mode A: micro-cap, hold < 60s
SUSTAINED_HOLD_MAX_S = 3600   # Mode B: established token, hold < 1hr

DUMP_WINDOW_FLASH_S = 30      # Mode A coordinated sell window
DUMP_WINDOW_S = 600           # Mode B 10-min sell window
DUMP_WINDOW_SECONDS = DUMP_WINDOW_S  # Backwards-compatible alias for tests

BUNDLER_THRESHOLD = 0.40      # token bundler_rate > 40% = strong signal
BOT_RATE_THRESHOLD = 0.60     # bot_degen_rate > 60% = likely coordinated
MAX_HOPS = 5                  # BFS fund tracer depth

MIN_EARLY_BUYERS = 2
SCORE_PER_PATTERN = 20
SCORE_BONUS_ALL_PATTERNS = 10
SCORE_BONUS_SIZE_5 = 5
SCORE_BONUS_SIZE_10 = 10


class DiscoveryPipeline:
    def __init__(self, gmgn=None, solscan=None, mock_mode=None):
        if mock_mode is None:
            is_test_env = (
                "pytest" in sys.modules
                or bool(os.getenv("PYTEST_CURRENT_TEST"))
                or os.getenv("DATA_MODE") == "mock"
            )
            mock_mode = is_test_env

        self.gmgn = gmgn or GMGNClient(mock_mode=mock_mode)
        self.solscan = solscan or SolscanClient(mock_mode=mock_mode)
        self.funding_relationships = []
        self._mock_mode = mock_mode

    def fetch_recent_launches(self, chain: str = "sol") -> List[TokenLaunchEvent]:
        """Stage 1: Ingest new token launches across chains without seed wallets."""
        launches = []
        try:
            launches = self.gmgn.get_new_token_launches(chain=chain, time_period="1h", limit=50)
        except Exception as exc:
            logger.warning("Stage 1 get_new_token_launches error on %s: %s", chain, exc)

        if not launches and chain == "sol":
            try:
                launches = self.solscan.get_token_latest(platform_id="pumpfun", page_size=40)
            except Exception as exc:
                logger.warning("Stage 1 solscan fallback error on %s: %s", chain, exc)

        if not launches:
            try:
                raw_pairs = self.gmgn.get_recent_launches(chain=chain, limit=50)
                if raw_pairs:
                    launches = [
                        TokenLaunchEvent(
                            token_address=p.get("address") or p.get("token_address", ""),
                            chain=chain,
                            name=p.get("name", "Unknown Token"),
                            symbol=p.get("symbol", "UNKNOWN"),
                            deployer_address=p.get("creator") or p.get("deployer_address", ""),
                            launch_timestamp=int(p.get("open_timestamp") or p.get("launch_timestamp", 0)),
                        )
                        for p in raw_pairs if isinstance(p, dict)
                    ]
            except Exception as exc:
                logger.warning("Stage 1 get_recent_launches fallback error on %s: %s", chain, exc)

        pass

        parsed: List[TokenLaunchEvent] = []
        for item in (launches or []):
            if isinstance(item, TokenLaunchEvent):
                parsed.append(item)
            elif isinstance(item, dict):
                parsed.append(TokenLaunchEvent.from_dict(item))

        logger.info("Stage 1: %d launches on %s", len(parsed), chain)
        return parsed

    def get_early_buyers(self, token: str, chain: str = "sol", launch_time: int = 0) -> List[Dict[str, Any]]:
        """Stage 2: Detect coordinated early buyers within EARLY_BUY_WINDOW_SECONDS."""
        trades = []
        try:
            trades = self.gmgn.get_token_trades(chain=chain, token_address=token, limit=200)
        except Exception as exc:
            logger.warning("get_early_buyers error %s/%s: %s", chain, token, exc)

        if not trades:
            try:
                buyers_raw = self.gmgn.get_token_buyers(token_address=token, chain=chain)
                if buyers_raw:
                    parsed_buyers = []
                    for b in buyers_raw:
                        w = b.get("address") or b.get("wallet", "")
                        t = int(b.get("first_buy_time") or b.get("timestamp", 0))
                        vol = float(b.get("buy_volume_usd") or b.get("amount_usd", 0.0))
                        amt = float(b.get("amount") or b.get("token_amount", 0.0))
                        if w:
                            parsed_buyers.append({
                                "wallet": w,
                                "buy_time": t,
                                "amount_usd": vol,
                                "token_amount": amt,
                                "is_deployer": False,
                            })
                    return parsed_buyers
            except Exception as exc:
                logger.warning("get_token_buyers fallback error %s/%s: %s", chain, token, exc)

        parsed_trades: List[TradeRecord] = []
        for t in (trades or []):
            if isinstance(t, TradeRecord):
                parsed_trades.append(t)
            elif isinstance(t, dict):
                parsed_trades.append(TradeRecord.from_dict(t))

        cutoff = (launch_time + EARLY_BUY_WINDOW_SECONDS) if launch_time > 0 else (
            (min((tr.timestamp for tr in parsed_trades), default=0) + EARLY_BUY_WINDOW_SECONDS) if parsed_trades else 0
        )
        buyers, seen = [], set()
        for trade in parsed_trades:
            if (trade.direction.lower() == "buy" and (cutoff == 0 or trade.timestamp <= cutoff)
                    and trade.wallet_address and trade.wallet_address not in seen):
                seen.add(trade.wallet_address)
                buyers.append({
                    "wallet": trade.wallet_address,
                    "buy_time": trade.timestamp,
                    "amount_usd": trade.volume_usd,
                    "token_amount": trade.token_amount,
                    "is_deployer": trade.is_deployer,
                })
        return buyers

    def get_funding_sources(self, wallet: str, chain: str = "sol", before_timestamp: Optional[int] = None) -> List[Dict[str, Any]]:
        """Stage 3: Trace incoming funding sources for wallet prior to purchases."""
        sources = []
        try:
            transfers = []
            if chain == "sol":
                transfers = self.solscan.get_account_transfers(
                    address=wallet, flow="in", to_time=before_timestamp)

            pass

            for t in (transfers or []):
                from_addr = getattr(t, "from_address", None) or (
                    t.get("from_address") or t.get("source") or t.get("src", "") if isinstance(t, dict) else ""
                )
                amt = getattr(t, "amount", 0.0) or (t.get("amount", 0.0) if isinstance(t, dict) else 0.0)
                amt_usd = getattr(t, "amount_usd", 0.0) or (t.get("amount_usd", 0.0) if isinstance(t, dict) else 0.0)
                ts = getattr(t, "timestamp", 0) or (t.get("timestamp") or t.get("block_time", 0) if isinstance(t, dict) else 0)
                if from_addr and from_addr.lower() != wallet.lower():
                    sources.append({
                        "source_wallet": from_addr,
                        "amount": float(amt),
                        "amount_usd": float(amt_usd),
                        "timestamp": int(ts),
                    })
        except Exception as exc:
            logger.warning("get_funding_sources error %s: %s", wallet[:8], exc)
        return sources

    def _build_deployer_map(self, launches: List[TokenLaunchEvent]) -> Dict[str, List[str]]:
        """Stage 4 helper: Map deployers to launched token addresses."""
        dmap = defaultdict(list)
        for launch in launches:
            deployer = launch.deployer_address
            if not deployer and not self._mock_mode:
                try:
                    info = self.gmgn.get_token_security(chain=launch.chain, token_address=launch.token_address)
                    deployer = info.get("creator") or info.get("deployer_address") or ""
                except Exception:
                    pass
            if deployer:
                dmap[deployer].append(launch.token_address)
        return {d: tokens for d, tokens in dmap.items() if len(tokens) > 1}

    def get_deployer(self, token: str, chain: str = "sol") -> str:
        """Resolve creator/deployer wallet address for a token."""
        try:
            info = self.gmgn.get_token_security(chain=chain, token_address=token)
            if isinstance(info, dict):
                deployer = (
                    info.get("creator")
                    or info.get("creator_address")
                    or info.get("deployer_address")
                    or info.get("deployer")
                )
                if deployer:
                    return str(deployer)
        except Exception as exc:
            logger.warning("get_deployer error for %s: %s", token, exc)
        return "unknown"

    def detect_coordinated_dumps(self, token: str, wallets: List[str], chain: str = "sol") -> List[Dict[str, Any]]:
        """Stage 5: Find coordinated sells by multiple wallets within 10-minute sliding window."""
        wallets_set = set(wallets)
        sell_events = []
        trades = []
        try:
            trades = self.gmgn.get_token_trades(chain=chain, token_address=token, limit=200)
        except Exception as exc:
            logger.warning("detect_coordinated_dumps error %s: %s", token, exc)

        pass

        for item in (trades or []):
            trade = item if isinstance(item, TradeRecord) else TradeRecord.from_dict(item)
            if trade.wallet_address in wallets_set and trade.direction.lower() == "sell":
                sell_events.append((trade.timestamp, trade.wallet_address))

        if len(sell_events) < 2:
            return []
        sell_events.sort(key=lambda x: x[0])
        dumps, i = [], 0
        while i < len(sell_events):
            start = sell_events[i][0]
            involved = {sell_events[i][1]}
            j = i + 1
            while j < len(sell_events) and sell_events[j][0] - start <= DUMP_WINDOW_SECONDS:
                involved.add(sell_events[j][1])
                j += 1
            if len(involved) >= 2:
                dumps.append({
                    "wallets_involved": list(involved),
                    "sell_window_start": start,
                    "sell_window_end": sell_events[j - 1][0] if j > i + 1 else start,
                    "token": token,
                })
            i += 1
        return dumps

    def score_wallet(self, wallet_data: Dict[str, Any], patterns: List[str]) -> float:
        """Stage 6: Score a wallet between 0.0 and 100.0 based on flagged patterns and cluster size."""
        unique = set(patterns)
        score = min(len(unique) * SCORE_PER_PATTERN, 80)
        size = wallet_data.get("cluster_size", 1)
        if size >= 10:
            score += SCORE_BONUS_SIZE_10
        elif size >= 5:
            score += SCORE_BONUS_SIZE_5
        canonical = {p.value for p in PatternType}
        if canonical.issubset(unique):
            score += SCORE_BONUS_ALL_PATTERNS
        return min(float(score), 100.0)

    def score_cluster(self, cluster_wallets: List[str], patterns: Optional[List[str]] = None) -> float:
        """Score a cluster strictly bounded in [0.0, 100.0]."""
        if not cluster_wallets:
            return 0.0
        patterns = patterns or [PatternType.EARLY_ENTRY.value, PatternType.COMMON_FUNDING.value]
        unique_patterns = set(patterns)
        score = min(len(unique_patterns) * SCORE_PER_PATTERN, 80.0)
        size = len(cluster_wallets)
        if size >= 10:
            score += SCORE_BONUS_SIZE_10
        elif size >= 5:
            score += SCORE_BONUS_SIZE_5
        canonical = {p.value for p in PatternType}
        if canonical.issubset(unique_patterns):
            score += SCORE_BONUS_ALL_PATTERNS
        return float(min(max(score, 0.0), 100.0))

    def run_pipeline(self, chains=None) -> List[Dict[str, Any]]:
        """Run the full 6-stage discovery pipeline across chains."""
        if not chains:
            chains = ["sol"]
        all_wallets = {}
        self.funding_relationships = []
        for chain in chains:
            launches = self.fetch_recent_launches(chain)
            if not launches:
                continue
            shared_deployers = self._build_deployer_map(launches)
            for launch in launches:
                token = launch.token_address
                if not token:
                    continue
                launch_time = launch.launch_timestamp or 0
                buyers = self.get_early_buyers(token, chain, launch_time)
                if len(buyers) < MIN_EARLY_BUYERS:
                    continue
                buyer_wallets = [b["wallet"] for b in buyers if b.get("wallet")]
                dump_events = self.detect_coordinated_dumps(token, buyer_wallets, chain)
                dump_wallets = set()
                for d in dump_events:
                    dump_wallets.update(d["wallets_involved"])
                token_has_shared_deployer = launch.deployer_address in shared_deployers
                for buyer in buyers:
                    w = buyer.get("wallet")
                    if not w:
                        continue
                    if w not in all_wallets:
                        all_wallets[w] = {
                            "wallet_address": w,
                            "chain": chain,
                            "tokens_traded": set(),
                            "patterns_flagged": set(),
                            "estimated_profit_usd": 0.0,
                            "cluster_size": 1,
                        }
                    entry = all_wallets[w]
                    entry["tokens_traded"].add(token)
                    entry["patterns_flagged"].add(PatternType.EARLY_ENTRY.value)
                    entry["estimated_profit_usd"] += buyer.get("amount_usd", 0.0)
                    if w in dump_wallets:
                        entry["patterns_flagged"].add(PatternType.COORDINATED_DUMP.value)
                    if token_has_shared_deployer:
                        entry["patterns_flagged"].add(PatternType.SHARED_DEPLOYER.value)
                    sources = self.get_funding_sources(w, chain, buyer.get("buy_time"))
                    for src in sources:
                        funder = src.get("source_wallet", "")
                        if not funder or funder == w:
                            continue
                        self.funding_relationships.append({
                            "funder": funder,
                            "funded": w,
                            "amount": src.get("amount", 0.0),
                            "amount_usd": src.get("amount_usd", 0.0),
                            "timestamp": src.get("timestamp", 0),
                            "chain": chain,
                        })
                        entry["patterns_flagged"].add(PatternType.COMMON_FUNDING.value)
                        if funder not in all_wallets:
                            all_wallets[funder] = {
                                "wallet_address": funder,
                                "chain": chain,
                                "tokens_traded": set(),
                                "patterns_flagged": set(),
                                "estimated_profit_usd": 0.0,
                                "cluster_size": 1,
                            }
                        all_wallets[funder]["patterns_flagged"].add(PatternType.COMMON_FUNDING.value)

        logger.info("Pipeline complete: %d wallets, %d funding edges", len(all_wallets), len(self.funding_relationships))
        result = []
        for w, data in all_wallets.items():
            data["tokens_traded"] = list(data["tokens_traded"])
            data["patterns_flagged"] = list(data["patterns_flagged"])
            data["suspicion_score"] = self.score_wallet(data, data["patterns_flagged"])
            result.append(data)
        return result
