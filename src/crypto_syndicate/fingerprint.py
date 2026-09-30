"""M7 — Behavioral Fingerprinting for Crypto Syndicate Research System.

Distills the temporal, volume, bot, bundler, and exit characteristics of an
on-chain cluster into a deterministic, structured profile (SyndicateBehavior).
Produces a canonical semantic string (to_text()) suitable for human inspection
and dense vector embedding (Qdrant / SentenceTransformer).
"""

from collections import defaultdict
from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely coerce a value to float, returning default on None or error."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


@dataclass
class SyndicateBehavior:
    """Behavioral fingerprint capturing the operational signature of a syndicate."""

    cluster_id: str = ""
    token_address: str = ""
    chain: str = "sol"
    mode: str = "sustained"  # "flash" (<60s hold) or "sustained" (>=60s)
    avg_buy_delay_s: float = 0.0
    avg_hold_duration_s: float = 0.0
    dump_speed_s: float = 0.0
    bundler_rate: float = 0.0
    bot_rate: float = 0.0
    suspicion_score: float = 0.0
    wallet_count: int = 0
    estimated_profit_usd: float = 0.0
    patterns_flagged: List[str] = field(default_factory=list)
    is_deployer_buying: bool = False
    fresh_wallet_ratio: float = 0.0
    funder_wallet: Optional[str] = None
    deployer_wallet: Optional[str] = None
    is_jito_bundle: bool = False
    jito_confidence: float = 0.0
    jito_signals: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        cluster_id: str = "",
        token_address: str = "",
        chain: str = "sol",
        mode: str = "sustained",
        avg_buy_delay_s: Optional[float] = None,
        avg_hold_duration_s: Optional[float] = None,
        dump_speed_s: Optional[float] = None,
        bundler_rate: float = 0.0,
        bot_rate: Optional[float] = None,
        suspicion_score: float = 0.0,
        wallet_count: int = 0,
        estimated_profit_usd: float = 0.0,
        patterns_flagged: Optional[Union[List[str], Tuple[str, ...]]] = None,
        is_deployer_buying: bool = False,
        fresh_wallet_ratio: float = 0.0,
        funder_wallet: Optional[str] = None,
        deployer_wallet: Optional[str] = None,
        is_jito_bundle: bool = False,
        jito_confidence: float = 0.0,
        jito_signals: Optional[Union[List[str], Tuple[str, ...]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        buy_delay_s: Optional[float] = None,
        hold_time_s: Optional[float] = None,
        dump_window_s: Optional[float] = None,
        bot_degen_rate: Optional[float] = None,
        patterns: Optional[Union[List[str], Tuple[str, ...]]] = None,
        **kwargs: Any,
    ) -> None:
        self.cluster_id = str(cluster_id)
        self.token_address = str(token_address)
        self.chain = str(chain)
        self.mode = str(mode)

        # Resolve buy delay
        if avg_buy_delay_s is not None:
            self.avg_buy_delay_s = float(avg_buy_delay_s)
        elif buy_delay_s is not None:
            self.avg_buy_delay_s = float(buy_delay_s)
        else:
            self.avg_buy_delay_s = 0.0

        # Resolve hold duration
        if avg_hold_duration_s is not None:
            self.avg_hold_duration_s = float(avg_hold_duration_s)
        elif hold_time_s is not None:
            self.avg_hold_duration_s = float(hold_time_s)
        else:
            self.avg_hold_duration_s = 0.0

        # Resolve dump speed
        if dump_speed_s is not None:
            self.dump_speed_s = float(dump_speed_s)
        elif dump_window_s is not None:
            self.dump_speed_s = float(dump_window_s)
        else:
            self.dump_speed_s = 30.0 if self.mode == "flash" else 600.0

        self.bundler_rate = float(bundler_rate)

        # Resolve bot rate
        if bot_rate is not None:
            self.bot_rate = float(bot_rate)
        elif bot_degen_rate is not None:
            self.bot_rate = float(bot_degen_rate)
        else:
            self.bot_rate = 0.0

        self.suspicion_score = float(suspicion_score)
        self.wallet_count = int(wallet_count)
        self.estimated_profit_usd = float(estimated_profit_usd)

        # Resolve patterns
        raw_patterns = patterns_flagged if patterns_flagged is not None else patterns
        self.patterns_flagged = list(raw_patterns) if raw_patterns is not None else []

        self.is_deployer_buying = bool(is_deployer_buying)
        self.fresh_wallet_ratio = float(fresh_wallet_ratio)
        self.funder_wallet = funder_wallet
        self.deployer_wallet = deployer_wallet
        self.is_jito_bundle = bool(is_jito_bundle)
        self.jito_confidence = float(jito_confidence)
        self.jito_signals = list(jito_signals) if jito_signals is not None else []
        self.metadata = dict(metadata) if metadata is not None else {}

    # Property aliases for universal backward/cross compatibility
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
    def patterns(self, val: Union[List[str], Tuple[str, ...]]) -> None:
        self.patterns_flagged = list(val)

    def to_text(self, include_jito: bool = False) -> str:
        """Deterministic semantic text representation for embeddings and auditing."""
        pats = "|".join(sorted(self.patterns_flagged)) if self.patterns_flagged else "none"
        base = (
            f"chain:{self.chain} mode:{self.mode} "
            f"buy_delay:{self.avg_buy_delay_s:.0f}s hold:{self.avg_hold_duration_s:.0f}s "
            f"bundler:{self.bundler_rate:.2f} bots:{self.bot_rate:.2f} "
            f"wallets:{self.wallet_count} dump_window:{self.dump_speed_s:.0f}s "
            f"deployer_buys:{self.is_deployer_buying} fresh:{self.fresh_wallet_ratio:.2f} "
            f"patterns:{pats}"
        )
        if include_jito:
            return f"{base} jito:{'yes' if self.is_jito_bundle else 'no'}"
        return base

    def to_dict(self) -> Dict[str, Any]:
        """Convert fingerprint to clean dictionary."""
        return {
            "cluster_id": self.cluster_id,
            "token_address": self.token_address,
            "chain": self.chain,
            "mode": self.mode,
            "avg_buy_delay_s": self.avg_buy_delay_s,
            "buy_delay_s": self.avg_buy_delay_s,
            "avg_hold_duration_s": self.avg_hold_duration_s,
            "hold_time_s": self.avg_hold_duration_s,
            "dump_speed_s": self.dump_speed_s,
            "dump_window_s": self.dump_speed_s,
            "bundler_rate": self.bundler_rate,
            "bot_rate": self.bot_rate,
            "bot_degen_rate": self.bot_rate,
            "suspicion_score": self.suspicion_score,
            "wallet_count": self.wallet_count,
            "estimated_profit_usd": self.estimated_profit_usd,
            "patterns_flagged": list(self.patterns_flagged),
            "patterns": list(self.patterns_flagged),
            "is_deployer_buying": self.is_deployer_buying,
            "fresh_wallet_ratio": self.fresh_wallet_ratio,
            "funder_wallet": self.funder_wallet,
            "deployer_wallet": self.deployer_wallet,
            "is_jito_bundle": self.is_jito_bundle,
            "jito_confidence": self.jito_confidence,
            "jito_signals": list(self.jito_signals),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyndicateBehavior":
        """Recreate SyndicateBehavior instance from dict."""
        return cls(**data)

    @classmethod
    def from_cluster_and_token(
        cls,
        cluster: Any,
        token: Any = None,
        trades: Any = None,
    ) -> "SyndicateBehavior":
        """Extract behavior fingerprint from cluster, token event, and trades data."""
        # 1. Parse Cluster
        if hasattr(cluster, "to_dict"):
            c_dict = cluster.to_dict()
        elif isinstance(cluster, dict):
            c_dict = cluster
        else:
            c_dict = {}

        cluster_id = str(c_dict.get("cluster_id", ""))
        chain = str(c_dict.get("chain", "sol"))
        wallets = list(c_dict.get("wallets") or c_dict.get("members") or [])
        patterns = list(c_dict.get("flagged_patterns") or c_dict.get("patterns_flagged") or [])
        score = _safe_float(c_dict.get("suspicion_score"), 0.0)
        profit = _safe_float(c_dict.get("estimated_profit_usd"), 0.0)
        entry_win = _safe_float(c_dict.get("average_entry_window_seconds"), 0.0)
        exit_win = _safe_float(c_dict.get("average_exit_window_seconds"), 0.0)
        evidence = dict(c_dict.get("evidence_metadata") or {})
        funder_wallet = c_dict.get("funder_wallet")
        deployer_wallet = c_dict.get("deployer_wallet")

        # 2. Parse Token
        token_address = ""
        launch_ts = 0
        token_deployer = deployer_wallet or ""
        bundler_rate = _safe_float(evidence.get("bundler_rate"), 0.0)
        bot_rate = _safe_float(evidence.get("bot_rate") or evidence.get("bot_degen_rate"), 0.0)

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
            launch_ts = int(
                t_dict.get("launch_timestamp")
                or t_dict.get("creation_timestamp")
                or t_dict.get("open_timestamp", 0)
            )
            if not token_deployer:
                token_deployer = str(t_dict.get("deployer_address") or t_dict.get("creator", ""))
            if "bundler_rate" in t_dict:
                bundler_rate = _safe_float(t_dict.get("bundler_rate"), 0.0)
            if "bot_degen_rate" in t_dict or "bot_rate" in t_dict:
                bot_rate = _safe_float(t_dict.get("bot_degen_rate") or t_dict.get("bot_rate"), 0.0)
            raw_meta = t_dict.get("raw_metadata", {})
            if isinstance(raw_meta, dict):
                bundler_rate = _safe_float(raw_meta.get("bundler_rate", bundler_rate), bundler_rate)
                bot_rate = _safe_float(raw_meta.get("bot_degen_rate") or raw_meta.get("bot_rate", bot_rate), bot_rate)

        if not token_address:
            assoc = c_dict.get("associated_tokens", [])
            token_address = assoc[0] if assoc else ""

        # 3. Process Trades
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
                    s = int(t.get("start_holding_at", 0) or 0)
                    e = int(t.get("end_holding_at", 0) or 0)
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
                wallet_buys = defaultdict(list)
                wallet_sells = defaultdict(list)
                for item in trade_list:
                    if hasattr(item, "to_dict"):
                        tr = item.to_dict()
                    elif isinstance(item, dict):
                        tr = item
                    else:
                        continue  # skip non-dict scalars (None, str, int) safely
                    w = tr.get("wallet_address", "")
                    direction = str(tr.get("direction", "")).lower()
                    ts = int(tr.get("timestamp", 0) or 0)
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

        # 4. Fallback Averages & Mode Detection
        avg_delay = (sum(delays) / len(delays)) if delays else (entry_win if entry_win > 0 else 16.0)
        avg_hold = (sum(holds) / len(holds)) if holds else (exit_win if exit_win > 0 else 7.0)

        # Mode classification: flash if hold duration < 60s else sustained
        mode = "flash" if avg_hold < 60.0 else "sustained"
        dump_speed = 30.0 if mode == "flash" else 600.0
        fresh_ratio = (
            (fresh_count / max(len(trade_list), 1))
            if fresh_count > 0
            else float(evidence.get("fresh_wallet_ratio", 0.0))
        )
        wallet_cnt = len(wallets) if wallets else max(len(trade_list), 1)

        is_jito = bool(c_dict.get("is_jito_bundle") or evidence.get("is_jito_bundle", False))
        jito_conf = _safe_float(c_dict.get("jito_confidence") or evidence.get("jito_confidence", 0.0))
        jito_sigs = list(c_dict.get("jito_signals") or evidence.get("jito_signals", []))

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
            funder_wallet=funder_wallet,
            deployer_wallet=deployer_wallet or token_deployer,
            is_jito_bundle=is_jito,
            jito_confidence=jito_conf,
            jito_signals=jito_sigs,
            metadata=evidence,
        )
