"""M12 — Jito Bundle Detector for Crypto Syndicate Research System.

Detects Jito MEV bundles and coordinated on-chain transaction atomic groupings
on Solana mainnet. Implements multi-signal correlation:
1. Canonical tip accounts (8 verified mainnet tip recipients)
2. Inner instruction CPI transfers to tip accounts
3. Explicit bundle_id / jito metadata flags
4. Co-slot timing correlation within a 400ms ingress window
5. Bundler rate threshold integration

Pure-library architecture: zero external network calls.
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

logger = logging.getLogger("crypto_syndicate.jito_detector")

# 8 Verified Canonical Jito Tip Accounts on Solana Mainnet
CANONICAL_JITO_TIP_ACCOUNTS: Tuple[str, ...] = (
    "96gYZGLnJeTa9AGEefvjNArMBUwEpzDQRNSCGVFmhEEq",
    "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
    "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
    "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1sMaC9jnwRv",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
    "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyflaDeKd1qRv",
    "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6dW",
)

CANONICAL_TIP_ACCOUNTS_SET: frozenset = frozenset(CANONICAL_JITO_TIP_ACCOUNTS)

# Signal Names
SIGNAL_CANONICAL_TIP = "CANONICAL_TIP_ACCOUNT"
SIGNAL_INNER_CPI_TIP = "INNER_CPI_TIP_TRANSFER"
SIGNAL_BUNDLE_ID_METADATA = "BUNDLE_ID_METADATA"
SIGNAL_EXPLICIT_JITO_FLAG = "EXPLICIT_JITO_FLAG"
SIGNAL_HIGH_BUNDLER_RATE = "HIGH_BUNDLER_RATE"
SIGNAL_CO_SLOT_INGRESS = "CO_SLOT_INGRESS"

# Heuristic Confidence Weights
WEIGHT_CANONICAL_TIP = 0.50
WEIGHT_BUNDLE_ID_METADATA = 0.50
WEIGHT_INNER_CPI_TIP = 0.45
WEIGHT_EXPLICIT_JITO_FLAG = 0.30
WEIGHT_HIGH_BUNDLER_RATE = 0.20
WEIGHT_CO_SLOT_INGRESS = 0.25

# Detection Threshold: confidence >= 0.45 triggers is_jito_bundle
DETECTION_THRESHOLD = 0.45


def _safe_int(val: Any, default: int = 0) -> int:
    """Safely cast value to integer."""
    if val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely cast value to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


@dataclass
class JitoDetectionResult:
    """Detection result for a single transaction or trade event."""

    is_jito_bundle: bool = False
    confidence: float = 0.0
    signals: List[str] = field(default_factory=list)
    tip_account_matched: Optional[str] = None
    bundle_id: Optional[str] = None
    tip_lamports: int = 0
    slot: Optional[int] = None
    timestamp: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert detection result to serializable dictionary."""
        return {
            "is_jito_bundle": bool(self.is_jito_bundle),
            "confidence": round(float(self.confidence), 4),
            "signals": list(self.signals),
            "tip_account_matched": self.tip_account_matched,
            "bundle_id": self.bundle_id,
            "tip_lamports": int(self.tip_lamports),
            "slot": self.slot,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


class JitoDetector:
    """Standalone pure-library detector for Jito MEV bundles on Solana."""

    def __init__(
        self,
        canonical_tip_accounts: Optional[Iterable[str]] = None,
        detection_threshold: float = DETECTION_THRESHOLD,
        co_slot_window_ms: float = 400.0,
    ) -> None:
        self.canonical_tip_accounts: frozenset = (
            frozenset(canonical_tip_accounts)
            if canonical_tip_accounts is not None
            else CANONICAL_TIP_ACCOUNTS_SET
        )
        self.detection_threshold = detection_threshold
        self.co_slot_window_ms = co_slot_window_ms

    def detect(self, trade_or_tx: Any) -> JitoDetectionResult:
        """Evaluate a single trade, transaction record, or raw dictionary."""
        if trade_or_tx is None or not isinstance(trade_or_tx, (dict, object)):
            return JitoDetectionResult()

        tx_dict = self._normalize_to_dict(trade_or_tx)
        if not tx_dict:
            return JitoDetectionResult()

        # Chain check: canonical tips only apply to Solana
        chain = str(tx_dict.get("chain", "sol")).lower()
        if chain not in ("sol", "solana"):
            return JitoDetectionResult(
                is_jito_bundle=False,
                confidence=0.0,
                signals=[],
                metadata={"rejected_reason": f"unsupported_chain_{chain}"},
            )

        signals: List[str] = []
        confidence: float = 0.0
        matched_tip_account: Optional[str] = None
        bundle_id: Optional[str] = None
        tip_lamports: int = 0

        slot = tx_dict.get("slot")
        if slot is not None:
            slot = _safe_int(slot)

        timestamp = tx_dict.get("timestamp") or tx_dict.get("block_time") or tx_dict.get("time")
        if timestamp is not None:
            timestamp = _safe_float(timestamp)

        # Signal 1: Canonical Tip Account match
        tip_info = self._extract_tip_transfer(tx_dict)
        if tip_info:
            account, lamports, is_cpi = tip_info
            matched_tip_account = account
            tip_lamports = lamports
            if is_cpi:
                signals.append(SIGNAL_INNER_CPI_TIP)
                confidence += WEIGHT_INNER_CPI_TIP
            else:
                signals.append(SIGNAL_CANONICAL_TIP)
                confidence += WEIGHT_CANONICAL_TIP

        # Signal 2: Bundle ID metadata
        extracted_bundle_id = self._extract_bundle_id(tx_dict)
        if extracted_bundle_id:
            bundle_id = extracted_bundle_id
            signals.append(SIGNAL_BUNDLE_ID_METADATA)
            confidence += WEIGHT_BUNDLE_ID_METADATA

        # Signal 3: Explicit Jito flag in trade/cluster
        if self._check_explicit_flag(tx_dict):
            signals.append(SIGNAL_EXPLICIT_JITO_FLAG)
            confidence += WEIGHT_EXPLICIT_JITO_FLAG

        # Signal 4: High Bundler Rate (>= 40%)
        bundler_rate = _safe_float(tx_dict.get("bundler_rate", 0.0))
        if bundler_rate >= 0.40:
            signals.append(SIGNAL_HIGH_BUNDLER_RATE)
            confidence += WEIGHT_HIGH_BUNDLER_RATE

        # Clamp confidence to [0.0, 1.0]
        confidence = min(1.0, max(0.0, confidence))

        # Bundle determination:
        # 1. Any canonical tip account or bundle_id is an instant high-confidence bundle
        # 2. Or cumulative heuristic score >= threshold
        is_bundle = (
            confidence >= self.detection_threshold
            or matched_tip_account is not None
            or bundle_id is not None
        )

        return JitoDetectionResult(
            is_jito_bundle=is_bundle,
            confidence=confidence,
            signals=signals,
            tip_account_matched=matched_tip_account,
            bundle_id=bundle_id,
            tip_lamports=tip_lamports,
            slot=slot,
            timestamp=timestamp,
            metadata={
                "chain": chain,
                "bundler_rate": bundler_rate,
            },
        )

    def detect_batch(self, items: List[Any]) -> List[JitoDetectionResult]:
        """Detect Jito bundle characteristics across a list of trades or transactions."""
        if not items:
            return []
        return [self.detect(item) for item in items]

    def detect_co_slot_bundles(
        self,
        items: List[Any],
        window_ms: Optional[float] = None,
    ) -> List[JitoDetectionResult]:
        """Perform co-slot temporal correlation across a batch of transactions.

        Transactions landing in the same slot within window_ms (default: 400ms)
        receive the CO_SLOT_INGRESS signal (+0.25 confidence boost).
        """
        if not items:
            return []

        win_ms = window_ms if window_ms is not None else self.co_slot_window_ms
        win_seconds = win_ms / 1000.0

        results = self.detect_batch(items)

        # Group by slot
        slot_groups: Dict[int, List[int]] = {}
        for idx, res in enumerate(results):
            if res.slot is not None and res.slot > 0:
                slot_groups.setdefault(res.slot, []).append(idx)

        # Correlate timestamps within each slot
        for slot, indices in slot_groups.items():
            if len(indices) >= 2:
                # Multiple transactions in the same slot
                # Check timestamp delta
                timestamps = [results[i].timestamp for i in indices]
                valid_ts = [t for t in timestamps if t is not None and t > 0]
                is_co_slot_burst = False

                if len(valid_ts) >= 2:
                    min_t = min(valid_ts)
                    max_t = max(valid_ts)
                    if (max_t - min_t) <= win_seconds:
                        is_co_slot_burst = True
                else:
                    # If timestamps not available or identical, slot identity with >=2 txs qualifies
                    is_co_slot_burst = True

                if is_co_slot_burst:
                    for i in indices:
                        res = results[i]
                        if SIGNAL_CO_SLOT_INGRESS not in res.signals:
                            res.signals.append(SIGNAL_CO_SLOT_INGRESS)
                            res.confidence = min(1.0, res.confidence + WEIGHT_CO_SLOT_INGRESS)
                            if res.confidence >= self.detection_threshold:
                                res.is_jito_bundle = True

        return results

    def _normalize_to_dict(self, item: Any) -> Dict[str, Any]:
        """Normalize various trade/transaction object representations to a dict."""
        if isinstance(item, dict):
            return dict(item)

        d: Dict[str, Any] = {}
        for attr in (
            "tx_hash", "signature", "slot", "slot_or_block", "timestamp", "block_time", "time",
            "maker", "wallet", "wallet_address", "amount", "token_amount", "price_usd",
            "volume_usd", "is_buy", "direction", "chain", "bundler_rate", "is_jito_bundle",
            "is_jito", "bundle_id", "tip_account", "tip_lamports", "transfers",
            "instructions", "inner_instructions", "logs", "metadata",
        ):
            if hasattr(item, attr):
                val = getattr(item, attr)
                if attr == "slot_or_block" and "slot" not in d:
                    d["slot"] = val
                d[attr] = val
        return d

    def _extract_tip_transfer(self, tx: Dict[str, Any]) -> Optional[Tuple[str, int, bool]]:
        """Find transfers directed to canonical Jito tip accounts.

        Returns (matched_account, lamports, is_cpi) or None.
        """
        # 1. Direct explicit tip account field
        direct_account = tx.get("tip_account") or tx.get("tip_recipient")
        if direct_account and str(direct_account) in self.canonical_tip_accounts:
            lamports = _safe_int(tx.get("tip_lamports") or tx.get("tip_amount") or 0)
            return (str(direct_account), lamports, False)

        # 2. Check inner instructions / CPI transfers
        inner_instructions = tx.get("inner_instructions") or tx.get("inner_transfers") or []
        if isinstance(inner_instructions, list):
            for inner in inner_instructions:
                if isinstance(inner, dict):
                    recipient = inner.get("to") or inner.get("destination") or inner.get("recipient")
                    if recipient and str(recipient) in self.canonical_tip_accounts:
                        lamports = _safe_int(inner.get("lamports") or inner.get("amount") or 0)
                        return (str(recipient), lamports, True)

        # 3. Check general transfers / instructions array
        transfers = tx.get("transfers") or tx.get("instructions") or []
        if isinstance(transfers, list):
            for t in transfers:
                if isinstance(t, dict):
                    recipient = t.get("to") or t.get("destination") or t.get("recipient")
                    if recipient and str(recipient) in self.canonical_tip_accounts:
                        lamports = _safe_int(t.get("lamports") or t.get("amount") or 0)
                        is_cpi = bool(t.get("is_cpi") or t.get("is_inner"))
                        return (str(recipient), lamports, is_cpi)

        # 4. Check program / log messages
        logs = tx.get("logs") or []
        if isinstance(logs, list):
            for line in logs:
                line_str = str(line)
                for tip_acc in self.canonical_tip_accounts:
                    if tip_acc in line_str:
                        return (tip_acc, 0, True)

        return None

    def _extract_bundle_id(self, tx: Dict[str, Any]) -> Optional[str]:
        """Extract explicit Jito bundle ID from transaction dictionary."""
        for key in ("bundle_id", "jito_bundle_id", "bundleId", "bundle"):
            val = tx.get(key)
            if val and isinstance(val, (str, int)) and str(val).strip():
                return str(val).strip()

        meta = tx.get("metadata")
        if isinstance(meta, dict):
            for key in ("bundle_id", "jito_bundle_id", "bundleId", "bundle"):
                val = meta.get(key)
                if val and isinstance(val, (str, int)) and str(val).strip():
                    return str(val).strip()

        return None

    def _check_explicit_flag(self, tx: Dict[str, Any]) -> bool:
        """Check for explicit boolean flags indicating Jito bundle."""
        for key in ("is_jito", "is_jito_bundle", "is_bundle", "jito"):
            val = tx.get(key)
            if val is True or val == "true" or val == 1:
                return True

        meta = tx.get("metadata")
        if isinstance(meta, dict):
            for key in ("is_jito", "is_jito_bundle", "is_bundle", "jito"):
                val = meta.get(key)
                if val is True or val == "true" or val == 1:
                    return True

        return False
