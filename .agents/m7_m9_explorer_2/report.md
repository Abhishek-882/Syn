# Technical Investigation Report: Behavioral Fingerprinting & Syndicate Identity Engine (M7-M9)

**Author**: Explorer 2 (`m7_m9_explorer_2`)  
**Target Modules**: `src/crypto_syndicate/fingerprint.py` & `src/crypto_syndicate/identity.py`  
**Related Models**: `src/crypto_syndicate/api/models.py`, `src/crypto_syndicate/discovery.py`  
**Date**: 2026-09-20  

---

## 1. Executive Summary

In Milestones 1 through 6, the Crypto Syndicate Research System successfully established on-chain data ingestion, heuristic pattern discovery, graph-based clustering (WCC + Louvain), continuous alerting, and interactive visual reporting. However, M1-M6 cluster IDs (e.g. `cluster_0001_a9f8b1c2`) are fundamentally **ephemeral and token-scoped**: each execution clusters wallets that co-bought or transferred funds for a *single* run or token.

Real-world on-chain syndicates (such as the verified BELUGA token ring discovered on Solana) constantly rotate wallet addresses. They fund disposable burner wallets via 4-5 intermediate hops, snipe tokens within seconds, dump within 30 seconds to 10 minutes, and sweep profits to fresh destinations. **Address matching alone is blind to recurring syndicates across different tokens and chains.**

To solve this, Milestones 7 through 9 introduce two fundamental capabilities:
1. **Behavioral Fingerprinting (`src/crypto_syndicate/fingerprint.py`)**: Distills the temporal, volume, bot, bundler, and exit characteristics of an on-chain cluster into a deterministic, structured profile (`SyndicateBehavior`). This profile produces a canonical semantic string (`to_text()`) suitable for both human readability and dense vector embedding (e.g., `all-MiniLM-L6-v2` via Qdrant).
2. **Persistent Syndicate Identity (`src/crypto_syndicate/identity.py`)**: Entity resolution engine (`SyndicateIdentityEngine`) that maintains persistent identities (`SYND-0001`, `SYND-0002`, etc.) across multiple token launches, runs, and chains. It links new clusters to known syndicates using hybrid matching: graph wallet/funder overlap AND behavioral vector similarity.

---

## 2. Ingestion & Existing Model Analysis

### 2.1 `src/crypto_syndicate/api/models.py` Inspection

The canonical models in `src/crypto_syndicate/api/models.py` (and re-exported by `src/crypto_syndicate/models.py`) are frozen, slotted dataclasses designed for high throughput and immutability:

| Model | Key Attributes | Relevant Roles for Fingerprint & Identity |
|---|---|---|
| `TokenLaunchEvent` | `token_address`, `chain`, `name`, `symbol`, `decimals`, `total_supply`, `deployer_address`, `launch_timestamp`, `raw_metadata` | Serves as ground truth for pool creation time (`launch_timestamp`). `raw_metadata` stores GMGN/Solscan metrics like `bundler_rate`, `bot_degen_rate`, and platform tags. |
| `TradeRecord` | `trade_id`, `chain`, `token_address`, `wallet_address`, `direction`, `timestamp`, `token_amount`, `volume_usd`, `is_deployer`, `seconds_since_launch` | Granular swap data used by `from_cluster_and_token` to compute actual sniper buy delays (`timestamp - launch_timestamp` or `seconds_since_launch`), hold times (buy-to-sell duration), and deployer buy activity. |
| `FundingTransferRecord` | `transfer_id`, `from_address`, `to_address`, `amount`, `amount_usd`, `timestamp`, `hop_depth` | Captures upstream fund transfers. Used by `SyndicateIdentity` to track `known_funders` across operations. |
| `WalletScore` | `wallet_address`, `chain`, `suspicion_score`, `flagged_patterns`, `pattern_scores`, `net_profit_usd`, `buy_txs`, `sell_txs` | Individual wallet metrics embedded within clusters. |
| `SyndicateCluster` | `cluster_id`, `chain`, `wallets` (tuple), `flagged_patterns` (tuple), `suspicion_score`, `associated_tokens` (tuple), `estimated_profit_usd`, `funder_wallet`, `deployer_wallet`, `average_entry_window_seconds`, `average_exit_window_seconds`, `evidence_metadata`, `wallet_scores` | The primary input to fingerprinting and identity registration. Contains the clustered member wallets, aggregated pattern flags, total profit, and average timing windows. |
| `PatternType` (Enum) | `EARLY_ENTRY = "early_entry"`, `COMMON_FUNDING = "common_funding"`, `SHARED_DEPLOYER = "shared_deployer"`, `COORDINATED_DUMP = "coordinated_dump"` | Standardized manipulation pattern vocabulary. |

### 2.2 `src/crypto_syndicate/discovery.py` Heuristics & Constants

Investigation of `discovery.py` reveals the real-world pattern detection parameters derived from verified live on-chain data (BELUGA token launch, 2026-09-20):
- `SNIPER_WINDOW_S = 30`: Real early buyers enter within 16–30 seconds of launch.
- `EARLY_BUY_WINDOW = 300`: Broad boundary for early entry detection.
- `FLASH_HOLD_MAX_S = 60`: Mode A (micro-cap flash dump) positions are held for only 3–12 seconds, not minutes.
- `SUSTAINED_HOLD_MAX_S = 3600`: Mode B (sustained pump-and-dump) positions are held for up to 1 hour.
- `DUMP_WINDOW_FLASH_S = 30`: Mode A coordinated sell window.
- `DUMP_WINDOW_S = 600`: Mode B 10-minute coordinated sell window.
- `BUNDLER_THRESHOLD = 0.40`: Tokens with > 40% bundler volume strongly correlate with coordinated syndicates.
- `BOT_RATE_THRESHOLD = 0.60`: Bot degen rate > 60% indicates automated sniper networks.
- `MAX_HOPS = 5`: BFS fund tracer depth.

---

## 3. Specification of `src/crypto_syndicate/fingerprint.py`

### 3.1 `SyndicateBehavior` Dataclass Architecture

The dataclass must capture all behavioral dimensions, support dual naming conventions (so existing scripts referencing either `buy_delay_s` or `avg_buy_delay_s` never fail), provide deterministic semantic serialization, and handle robust extraction from varied inputs.

```python
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Union
import time
from collections import defaultdict
```

#### Dataclass Fields & Property Aliases
```python
@dataclass
class SyndicateBehavior:
    """Behavioral fingerprint capturing the operational signature of a syndicate."""
    cluster_id: str = ""
    token_address: str = ""
    chain: str = "sol"
    mode: str = "flash"                     # "flash" (<120s hold) or "sustained" (>=120s)
    avg_buy_delay_s: float = 30.0           # avg delay after launch when snipers bought
    avg_hold_duration_s: float = 7.0        # avg position hold time before dump
    dump_speed_s: float = 30.0              # duration of coordinated exit window (30s flash, 600s sustained)
    bundler_rate: float = 0.0               # 0.0 - 1.0 fraction of bundler volume / supply
    bot_rate: float = 0.0                   # 0.0 - 1.0 fraction of bot volume
    suspicion_score: float = 0.0            # 0.0 - 100.0 cluster suspicion score
    patterns_flagged: List[str] = field(default_factory=list) # e.g. ["early_entry", "common_funding"]
    wallet_count: int = 0                   # number of wallets in syndicate
    estimated_profit_usd: float = 0.0       # extracted profit in USD
    is_deployer_buying: bool = False        # whether deployer participated in early buy
    fresh_wallet_ratio: float = 0.0         # fraction of wallets with 0 prior transactions
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Property aliases for universal compatibility
    @property
    def buy_delay_s(self) -> float:
        return self.avg_buy_delay_s

    @buy_delay_s.setter
    def buy_delay_s(self, val: float) -> None:
        self.avg_buy_delay_s = float(val)

    @property
    def hold_time_s(self) -> float:
        return self.avg_hold_duration_s

    @hold_time_s.setter
    def hold_time_s(self, val: float) -> None:
        self.avg_hold_duration_s = float(val)

    @property
    def dump_window_s(self) -> float:
        return self.dump_speed_s

    @dump_window_s.setter
    def dump_window_s(self, val: float) -> None:
        self.dump_speed_s = float(val)

    @property
    def bot_degen_rate(self) -> float:
        return self.bot_rate

    @bot_degen_rate.setter
    def bot_degen_rate(self, val: float) -> None:
        self.bot_rate = float(val)

    @property
    def patterns(self) -> List[str]:
        return self.patterns_flagged

    @patterns.setter
    def patterns(self, val: List[str]) -> None:
        self.patterns_flagged = list(val)
```

### 3.2 Semantic Vectorization: `to_text()` Method

The semantic text representation is critical: it will be ingested by SentenceTransformer (`all-MiniLM-L6-v2`) to generate 384-dimensional dense vectors stored in Qdrant. It must be deterministic, compact, and descriptive:

```python
    def to_text(self) -> str:
        """Convert behavioral signature to canonical semantic text for vector embedding."""
        pats = "|".join(sorted(self.patterns_flagged)) if self.patterns_flagged else "none"
        return (
            f"chain:{self.chain} mode:{self.mode} "
            f"buy_delay:{self.avg_buy_delay_s:.0f}s hold:{self.avg_hold_duration_s:.0f}s "
            f"bundler:{self.bundler_rate:.2f} bots:{self.bot_rate:.2f} "
            f"wallets:{self.wallet_count} dump_window:{self.dump_speed_s:.0f}s "
            f"deployer_buys:{self.is_deployer_buying} fresh:{self.fresh_wallet_ratio:.2f} "
            f"patterns:{pats}"
        )
```

### 3.3 Factory: `from_cluster_and_token` Classmethod

The factory method must handle heterogeneous inputs:
1. `cluster`: `SyndicateCluster` dataclass instance OR plain dictionary.
2. `token`: `TokenLaunchEvent` dataclass instance OR dictionary OR string token address OR `None`.
3. `trades`: optional list of `TradeRecord` instances OR list of GMGN-CLI trader dictionaries (with `start_holding_at`, `end_holding_at`, `maker_token_tags`, `is_new`) OR `None`.

```python
    @classmethod
    def from_cluster_and_token(
        cls,
        cluster: Any,
        token: Any = None,
        trades: Any = None,
    ) -> "SyndicateBehavior":
        """Extract behavioral fingerprint from cluster, token launch event, and trades data."""
        # 1. Unpack Cluster fields
        c_dict = cluster.to_dict() if hasattr(cluster, "to_dict") else dict(cluster)
        cluster_id = str(c_dict.get("cluster_id", ""))
        chain = str(c_dict.get("chain", "sol"))
        wallets = list(c_dict.get("wallets") or c_dict.get("members") or [])
        patterns = list(c_dict.get("flagged_patterns") or c_dict.get("patterns_flagged") or [])
        score = float(c_dict.get("suspicion_score", 0.0))
        profit = float(c_dict.get("estimated_profit_usd", 0.0))
        entry_win = float(c_dict.get("average_entry_window_seconds", 0.0))
        exit_win = float(c_dict.get("average_exit_window_seconds", 0.0))
        evidence = dict(c_dict.get("evidence_metadata", {}))
        deployer_cluster = c_dict.get("deployer_wallet")

        # 2. Unpack Token fields
        token_address = ""
        launch_ts = 0
        token_deployer = deployer_cluster or ""
        bundler_rate = float(evidence.get("bundler_rate", 0.0))
        bot_rate = float(evidence.get("bot_rate") or evidence.get("bot_degen_rate", 0.0))

        if token is not None:
            if hasattr(token, "to_dict"):
                t_dict = token.to_dict()
            elif isinstance(token, dict):
                t_dict = token
            elif isinstance(token, str):
                t_dict = {"token_address": token}
            else:
                t_dict = {}

            token_address = str(t_dict.get("token_address") or t_dict.get("address", ""))
            launch_ts = int(t_dict.get("launch_timestamp") or t_dict.get("creation_timestamp") or t_dict.get("open_timestamp", 0))
            if not token_deployer:
                token_deployer = str(t_dict.get("deployer_address") or t_dict.get("creator", ""))
            if "bundler_rate" in t_dict:
                bundler_rate = float(t_dict.get("bundler_rate", 0.0))
            if "bot_degen_rate" in t_dict or "bot_rate" in t_dict:
                bot_rate = float(t_dict.get("bot_degen_rate") or t_dict.get("bot_rate", 0.0))
            raw_meta = t_dict.get("raw_metadata", {})
            if isinstance(raw_meta, dict):
                bundler_rate = float(raw_meta.get("bundler_rate", bundler_rate))
                bot_rate = float(raw_meta.get("bot_degen_rate") or raw_meta.get("bot_rate", bot_rate))

        if not token_address:
            assoc = c_dict.get("associated_tokens", [])
            token_address = assoc[0] if assoc else ""

        # 3. Process Trades (GMGN-CLI format vs TradeRecord format)
        delays: List[float] = []
        holds: List[float] = []
        fresh_count = 0
        deployer_buying = False
        trade_list = trades if isinstance(trades, list) else []

        if trade_list:
            is_gmgn_trader_format = any(
                isinstance(t, dict) and ("start_holding_at" in t or "maker_token_tags" in t)
                for t in trade_list
            )

            if is_gmgn_trader_format:
                for t in trade_list:
                    if not isinstance(t, dict):
                        continue
                    s = int(t.get("start_holding_at", 0))
                    e = int(t.get("end_holding_at", 0))
                    tags = t.get("maker_token_tags") or t.get("tags") or []
                    if s > launch_ts > 0:
                        delays.append(float(s - launch_ts))
                    if e > s > 0:
                        holds.append(float(e - s))
                    if t.get("is_new"):
                        fresh_count += 1
                    if "creator" in tags and "bundler" in tags:
                        deployer_buying = True
                    addr = t.get("address") or t.get("wallet", "")
                    if token_deployer and addr and addr.lower() == token_deployer.lower():
                        deployer_buying = True
            else:
                # Standard TradeRecord or trade dicts
                wallet_buys = defaultdict(list)
                wallet_sells = defaultdict(list)
                for item in trade_list:
                    tr = item.to_dict() if hasattr(item, "to_dict") else dict(item)
                    w = tr.get("wallet_address", "")
                    direction = str(tr.get("direction", "")).lower()
                    ts = int(tr.get("timestamp", 0))
                    sec_since = tr.get("seconds_since_launch")
                    is_dep = bool(tr.get("is_deployer", False))

                    if is_dep and direction == "buy":
                        deployer_buying = True
                    if token_deployer and w and w.lower() == token_deployer.lower() and direction == "buy":
                        deployer_buying = True

                    if direction == "buy":
                        wallet_buys[w].append(ts)
                        if sec_since is not None and float(sec_since) >= 0:
                            delays.append(float(sec_since))
                        elif launch_ts > 0 and ts >= launch_ts:
                            delays.append(float(ts - launch_ts))
                    elif direction == "sell":
                        wallet_sells[w].append(ts)

                for w, b_times in wallet_buys.items():
                    if w in wallet_sells:
                        first_b = min(b_times)
                        first_s = min(wallet_sells[w])
                        if first_s >= first_b:
                            holds.append(float(first_s - first_b))

        # 4. Synthesize Averages & Modes
        avg_delay = (sum(delays) / len(delays)) if delays else (entry_win if entry_win > 0 else 16.0)
        avg_hold = (sum(holds) / len(holds)) if holds else (exit_win if exit_win > 0 else 7.0)
        mode = "flash" if avg_hold < 120.0 else "sustained"
        dump_speed = 30.0 if mode == "flash" else 600.0
        fresh_ratio = (fresh_count / max(len(trade_list), 1)) if fresh_count > 0 else float(evidence.get("fresh_wallet_ratio", 0.0))
        wallet_cnt = len(wallets) if wallets else max(len(trade_list), 1)

        return cls(
            cluster_id=cluster_id,
            token_address=token_address,
            chain=chain,
            mode=mode,
            avg_buy_delay_s=avg_delay,
            avg_hold_duration_s=avg_hold,
            dump_speed_s=dump_speed,
            bundler_rate=bundler_rate,
            bot_rate=bot_rate,
            suspicion_score=score,
            patterns_flagged=patterns,
            wallet_count=wallet_cnt,
            estimated_profit_usd=profit,
            is_deployer_buying=deployer_buying,
            fresh_wallet_ratio=fresh_ratio,
            metadata=evidence,
        )
```

---

## 4. Specification of `src/crypto_syndicate/identity.py`

### 4.1 `SyndicateIdentity` Dataclass Architecture

```python
@dataclass
class SyndicateIdentity:
    """Persistent entity representing a discovered syndicate across time and chains."""
    identity_id: str                                # e.g. "SYND-0001"
    alias: str = ""                                 # human-readable label e.g. "Beluga Sniper Ring #1"
    primary_wallets: List[str] = field(default_factory=list) # member wallets
    historical_tokens: List[str] = field(default_factory=list) # manipulated tokens
    behavior_profile: Optional[SyndicateBehavior] = None       # latest behavioral signature
    confidence_score: float = 0.6                   # 0.0 - 1.0 confidence score
    first_seen: float = 0.0                         # Unix timestamp first observed
    last_seen: float = 0.0                          # Unix timestamp last observed
    operation_count: int = 1                        # number of operations detected
    total_profit_usd: float = 0.0                   # aggregate extracted profit in USD
    known_funders: List[str] = field(default_factory=list) # root funder wallets
    known_chains: List[str] = field(default_factory=list)  # chains operated on
    behavior_texts: List[str] = field(default_factory=list) # semantic descriptions history
    metadata: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    # Aliases
    @property
    def syndicate_id(self) -> str:
        return self.identity_id

    @syndicate_id.setter
    def syndicate_id(self, val: str) -> None:
        self.identity_id = str(val)

    @property
    def known_wallets(self) -> List[str]:
        return self.primary_wallets

    @known_wallets.setter
    def known_wallets(self, val: List[str]) -> None:
        self.primary_wallets = list(val)

    @property
    def confidence(self) -> float:
        return self.confidence_score

    @confidence.setter
    def confidence(self, val: float) -> None:
        self.confidence_score = float(val)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "syndicate_id": self.identity_id,
            "alias": self.alias,
            "primary_wallets": list(self.primary_wallets),
            "known_wallets": list(self.primary_wallets),
            "historical_tokens": list(self.historical_tokens),
            "behavior_profile": self.behavior_profile.to_dict() if self.behavior_profile else None,
            "confidence_score": self.confidence_score,
            "confidence": self.confidence_score,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "operation_count": self.operation_count,
            "total_profit_usd": self.total_profit_usd,
            "known_funders": list(self.known_funders),
            "known_chains": list(self.known_chains),
            "behavior_texts": list(self.behavior_texts),
            "metadata": dict(self.metadata),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyndicateIdentity":
        profile_data = data.get("behavior_profile")
        profile = SyndicateBehavior.from_dict(profile_data) if profile_data else None
        wallets = data.get("primary_wallets") or data.get("known_wallets") or []
        iid = str(data.get("identity_id") or data.get("syndicate_id") or "")
        return cls(
            identity_id=iid,
            alias=str(data.get("alias", "")),
            primary_wallets=list(wallets),
            historical_tokens=list(data.get("historical_tokens", [])),
            behavior_profile=profile,
            confidence_score=float(data.get("confidence_score") or data.get("confidence", 0.6)),
            first_seen=float(data.get("first_seen", 0.0)),
            last_seen=float(data.get("last_seen", 0.0)),
            operation_count=int(data.get("operation_count", 1)),
            total_profit_usd=float(data.get("total_profit_usd", 0.0)),
            known_funders=list(data.get("known_funders", [])),
            known_chains=list(data.get("known_chains", [])),
            behavior_texts=list(data.get("behavior_texts", [])),
            metadata=dict(data.get("metadata", {})),
            notes=str(data.get("notes", "")),
        )
```

### 4.2 `SyndicateIdentityEngine` Class Specification

```python
class SyndicateIdentityEngine:
    """Manages persistent syndicate identities with hybrid entity resolution."""

    SIMILARITY_THRESHOLD = 0.82
    WALLET_OVERLAP_THRESHOLD = 0.30
    IDENTITY_FILE = "syndicate_identities.json"

    def __init__(self, output_dir: str = "results", vector_store: Any = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.identity_file = self.output_dir / self.IDENTITY_FILE
        self.vector_store = vector_store
        self.identities: Dict[str, SyndicateIdentity] = self._load()

    def match_syndicate(
        self,
        cluster: Any,
        behavior: Optional[SyndicateBehavior] = None,
    ) -> Optional[Tuple[SyndicateIdentity, float]]:
        """Find matching known syndicate using graph overlap and vector similarity.
        
        Returns tuple of (matched_identity, match_score) or None.
        """
        c_dict = cluster.to_dict() if hasattr(cluster, "to_dict") else dict(cluster)
        c_wallets = set(c_dict.get("wallets") or c_dict.get("members") or [])
        funder = c_dict.get("funder_wallet")

        best_match: Optional[SyndicateIdentity] = None
        best_score = 0.0

        # Stage 1: Wallet graph overlap & Shared Funder matching
        for ident in self.identities.values():
            known = set(ident.primary_wallets)
            intersection = c_wallets & known
            jaccard = len(intersection) / max(len(c_wallets | known), 1)

            # High confidence if >= 2 shared wallets or high Jaccard
            if len(intersection) >= 2 or jaccard >= self.WALLET_OVERLAP_THRESHOLD:
                score = 0.85 + (0.15 * jaccard)
                if funder and funder in ident.known_funders:
                    score = max(score, 0.98)
                if score > best_score:
                    best_score = score
                    best_match = ident
            elif funder and funder in ident.known_funders:
                score = 0.90
                if score > best_score:
                    best_score = score
                    best_match = ident

        if best_match and best_score >= self.SIMILARITY_THRESHOLD:
            return best_match, best_score

        # Stage 2: Behavioral Vector Similarity via Qdrant (if vector_store present)
        if self.vector_store and behavior:
            b_text = behavior.to_text()
            try:
                matches = self.vector_store.find_similar(b_text, top_k=3)
                for m in matches:
                    sim = float(m.get("similarity", 0.0))
                    sid = m.get("syndicate_id") or m.get("address")
                    if sim >= self.SIMILARITY_THRESHOLD and sid in self.identities:
                        if sim > best_score:
                            best_score = sim
                            best_match = self.identities[sid]
            except Exception as exc:
                logger.warning("Vector store matching failed: %s", exc)

        if best_match and best_score >= self.SIMILARITY_THRESHOLD:
            return best_match, best_score

        return None

    def register_cluster(
        self,
        cluster: Any,
        token: Any = None,
        trades: Any = None,
        behavior: Optional[SyndicateBehavior] = None,
    ) -> SyndicateIdentity:
        """Register an on-chain cluster, resolving to existing identity or minting a new one."""
        c_dict = cluster.to_dict() if hasattr(cluster, "to_dict") else dict(cluster)
        c_wallets = list(c_dict.get("wallets") or c_dict.get("members") or [])
        c_tokens = list(c_dict.get("associated_tokens") or c_dict.get("tokens") or [])
        c_profit = float(c_dict.get("estimated_profit_usd", 0.0))
        c_chain = str(c_dict.get("chain", "sol"))
        funder = c_dict.get("funder_wallet")

        if behavior is None:
            behavior = SyndicateBehavior.from_cluster_and_token(cluster, token, trades)

        b_text = behavior.to_text()
        match_result = self.match_syndicate(cluster, behavior)

        now = time.time()
        if match_result:
            identity, score = match_result
            identity.operation_count += 1
            identity.last_seen = now
            identity.primary_wallets = sorted(list(set(identity.primary_wallets + c_wallets)))
            identity.historical_tokens = sorted(list(set(identity.historical_tokens + c_tokens)))
            identity.total_profit_usd += c_profit
            identity.confidence_score = min(1.0, identity.confidence_score + 0.05)
            identity.behavior_profile = behavior
            identity.behavior_texts.append(b_text)
            if funder and funder not in identity.known_funders:
                identity.known_funders.append(funder)
            if c_chain not in identity.known_chains:
                identity.known_chains.append(c_chain)
            logger.warning("RETURNING SYNDICATE: %s (op #%d, score=%.2f)", identity.identity_id, identity.operation_count, score)
        else:
            sid = f"SYND-{len(self.identities) + 1:04d}"
            alias = f"Syndicate {sid} ({behavior.mode.capitalize()})"
            funders = [funder] if funder else []
            identity = SyndicateIdentity(
                identity_id=sid,
                alias=alias,
                primary_wallets=sorted(c_wallets),
                historical_tokens=sorted(c_tokens),
                behavior_profile=behavior,
                confidence_score=0.60,
                first_seen=now,
                last_seen=now,
                operation_count=1,
                total_profit_usd=c_profit,
                known_funders=funders,
                known_chains=[c_chain],
                behavior_texts=[b_text],
            )
            self.identities[sid] = identity
            logger.info("NEW SYNDICATE: %s", sid)

        # Upsert into vector store if enabled
        if self.vector_store:
            try:
                self.vector_store.upsert_syndicate(identity, b_text)
            except Exception as exc:
                logger.warning("Vector store upsert failed: %s", exc)

        self._save()
        return identity

    def process(self, cluster: Any, behavior_text: str = "") -> SyndicateIdentity:
        """Compatibility wrapper accepting cluster and precomputed behavior_text."""
        c_dict = cluster.to_dict() if hasattr(cluster, "to_dict") else dict(cluster)
        behavior = None
        if behavior_text:
            # Reconstruct basic behavior from cluster dict
            behavior = SyndicateBehavior(
                cluster_id=c_dict.get("cluster_id", ""),
                chain=c_dict.get("chain", "sol"),
                wallet_count=len(c_dict.get("wallets", [])),
                estimated_profit_usd=c_dict.get("estimated_profit_usd", 0.0),
                patterns_flagged=list(c_dict.get("flagged_patterns", [])),
            )
        return self.register_cluster(cluster=cluster, behavior=behavior)

    def get_all_identities(self) -> List[SyndicateIdentity]:
        """Return all registered syndicate identities."""
        return list(self.identities.values())

    def get_identity(self, identity_id: str) -> Optional[SyndicateIdentity]:
        """Retrieve identity by ID."""
        return self.identities.get(identity_id)

    def get_watchlist(self) -> List[Dict[str, Any]]:
        """Return watchlist of syndicate funders and high-priority targets."""
        watchlist = []
        for ident in self.identities.values():
            for funder in ident.known_funders:
                watchlist.append({
                    "syndicate_id": ident.identity_id,
                    "alias": ident.alias,
                    "funder": funder,
                    "ops": ident.operation_count,
                    "wallets": len(ident.primary_wallets),
                    "profit": ident.total_profit_usd,
                    "confidence": ident.confidence_score,
                })
        return watchlist

    def _load(self) -> Dict[str, SyndicateIdentity]:
        """Load identities from persistent JSON store."""
        if not self.identity_file.exists():
            return {}
        try:
            data = json.loads(self.identity_file.read_text(encoding="utf-8"))
            return {k: SyndicateIdentity.from_dict(v) for k, v in data.items()}
        except Exception as exc:
            logger.error("Failed to load %s: %s", self.identity_file, exc)
            return {}

    def _save(self) -> None:
        """Persist identities atomically using temporary file swap."""
        tmp = self.identity_file.with_suffix(".tmp")
        try:
            payload = {k: v.to_dict() for k, v in self.identities.items()}
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            os.replace(tmp, self.identity_file)
        except Exception as exc:
            logger.error("Failed to save %s: %s", self.identity_file, exc)
            if tmp.exists():
                try:
                    tmp.unlink()
                except Exception:
                    pass
```

---

## 5. System Integration & Workflow

```
[Token Launches + Swaps + Transfers]
                 │
                 ▼
       DiscoveryPipeline (M2)
   (Flagged Patterns, Scores)
                 │
                 ▼
       SyndicateGraph (M3)
   (WCC + Louvain Clustering)
                 │
                 ▼
       SyndicateCluster (Tuple of Wallets, Tokens, Scores)
                 │
    ┌────────────┴───────────────────────────┐
    ▼                                        ▼
SyndicateBehavior                      HopTracer (M8)
.from_cluster_and_token(...)          (BFS Multi-Hop Root Funder)
    │                                        │
    ▼                                        ▼
Behavior Profile                       Root Funders List
& to_text() string                           │
    │                                        │
    └───────────────────┬────────────────────┘
                        ▼
             SyndicateIdentityEngine (M9)
                        │
      ┌─────────────────┴─────────────────┐
      ▼                                   ▼
 Graph & Funder Match            Vector Similarity Match
 (Overlap >= 0.30)              (Qdrant Cosine >= 0.82)
      │                                   │
      └─────────────────┬─────────────────┘
                        ▼
              Match Found (>= 0.82)?
              ├── YES ──► Update SYND-XXXX (ops+1, merge wallets/tokens/funders)
              └── NO  ──► Mint new SYND-XXXX (save to syndicate_identities.json)
                        │
                        ▼
            Persisted Syndicate Memory &
           D3 Interactive Graph Overlay
```

---

## 6. Defensive Architecture & Edge Cases

1. **Missing or None Trades**: When granular trade logs are unavailable (e.g. historical RPC gaps or mock fallback), `from_cluster_and_token` gracefully falls back to `average_entry_window_seconds`, `average_exit_window_seconds`, and `evidence_metadata`.
2. **Missing Token Launch Timestamps**: If `launch_timestamp` is 0 or unavailable, relative `seconds_since_launch` on `TradeRecord` is used; if neither is available, delays default to the verified 16s baseline.
3. **Empty Clusters or Singletons**: Guard clauses return early with zero values, preventing `ZeroDivisionError`.
4. **Serialization Safety**: `SyndicateCluster` uses frozen tuples for `wallets` and `flagged_patterns`; `SyndicateBehavior.to_dict()` and `SyndicateIdentity.to_dict()` explicitly cast tuples and sets to lists for JSON compliance.
5. **Atomic File Persistence**: Storage in `_save()` writes to `.tmp` and executes `os.replace` to prevent corrupted state on sudden termination or power interruption.
6. **Dual Property Accessors**: Universal access via both property names (e.g. `buy_delay_s` and `avg_buy_delay_s`, `syndicate_id` and `identity_id`) ensures seamless interop across existing code and test suites.

---

## 7. Verification Plan for Implementer Agent

To verify the implementation once written to `src/crypto_syndicate/fingerprint.py` and `src/crypto_syndicate/identity.py`:
1. **Import check**:
   ```bash
   python -c "import sys; sys.path.insert(0,'src'); from crypto_syndicate.fingerprint import SyndicateBehavior; from crypto_syndicate.identity import SyndicateIdentity, SyndicateIdentityEngine; print('Imports OK')"
   ```
2. **Behavior extraction test**:
   Verify that passing a `SyndicateCluster` and mock `TokenLaunchEvent` to `SyndicateBehavior.from_cluster_and_token` extracts:
   - `mode == 'flash'` when hold time < 120s
   - `to_text()` formats without error and includes `chain:`, `mode:`, `buy_delay:`, `hold:`, etc.
3. **Identity engine registration test**:
   - Register cluster A -> returns `SYND-0001` (ops=1).
   - Register cluster B with 80% overlapping wallets -> returns `SYND-0001` (ops=2, confidence increased).
   - Register cluster C with completely disjoint wallets -> returns `SYND-0002` (ops=1).
   - Verify `results/syndicate_identities.json` exists and parses cleanly as valid JSON.
4. **Regression test suite**:
   ```bash
   python -m pytest tests/unit/ -q
   ```
