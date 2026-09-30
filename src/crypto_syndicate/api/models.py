"""Canonical immutable data models for Crypto Syndicate Research System.

Provides high-performance, memory-efficient, frozen dataclasses with slots
for token launches, trades, funding transfers, wallet scores, and syndicate clusters.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List, Union


class PatternType(str, Enum):
    """The four canonical manipulation patterns defined in ORIGINAL_REQUEST.md."""
    EARLY_ENTRY = "early_entry"
    COMMON_FUNDING = "common_funding"
    SHARED_DEPLOYER = "shared_deployer"
    COORDINATED_DUMP = "coordinated_dump"


@dataclass(frozen=True, slots=True)
class TokenLaunchEvent:
    """Immutable record representing a token launch / pool initialization."""
    token_address: str
    chain: str
    name: str
    symbol: str
    decimals: int = 6
    total_supply: float = 1_000_000_000.0
    deployer_address: str = ""
    launch_timestamp: int = 0
    launch_platform: str = ""
    initial_liquidity_usd: float = 0.0
    initial_price_usd: float = 0.0
    metadata_uri: str = ""
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_address": self.token_address,
            "chain": self.chain,
            "name": self.name,
            "symbol": self.symbol,
            "decimals": self.decimals,
            "total_supply": self.total_supply,
            "deployer_address": self.deployer_address,
            "launch_timestamp": self.launch_timestamp,
            "launch_platform": self.launch_platform,
            "initial_liquidity_usd": self.initial_liquidity_usd,
            "initial_price_usd": self.initial_price_usd,
            "metadata_uri": self.metadata_uri,
            "raw_metadata": dict(self.raw_metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenLaunchEvent":
        return cls(
            token_address=str(data.get("token_address", "")),
            chain=str(data.get("chain", "sol")),
            name=str(data.get("name", "")),
            symbol=str(data.get("symbol", "")),
            decimals=int(data.get("decimals", 6)),
            total_supply=float(data.get("total_supply", 1_000_000_000.0)),
            deployer_address=str(data.get("deployer_address", "")),
            launch_timestamp=int(data.get("launch_timestamp", 0)),
            launch_platform=str(data.get("launch_platform", "")),
            initial_liquidity_usd=float(data.get("initial_liquidity_usd", 0.0)),
            initial_price_usd=float(data.get("initial_price_usd", 0.0)),
            metadata_uri=str(data.get("metadata_uri", "")),
            raw_metadata=dict(data.get("raw_metadata", {})),
        )

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)


@dataclass(frozen=True, slots=True)
class TradeRecord:
    """Immutable record representing a granular DEX swap (buy or sell)."""
    trade_id: str
    chain: str
    token_address: str
    wallet_address: str
    direction: str  # "buy" or "sell"
    timestamp: int
    token_amount: float
    base_currency: str = "SOL"
    base_amount: float = 0.0
    price_usd: float = 0.0
    volume_usd: float = 0.0
    is_deployer: bool = False
    seconds_since_launch: Optional[float] = None
    slot_or_block: Optional[int] = None
    fee_native: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "chain": self.chain,
            "token_address": self.token_address,
            "wallet_address": self.wallet_address,
            "direction": self.direction,
            "timestamp": self.timestamp,
            "token_amount": self.token_amount,
            "base_currency": self.base_currency,
            "base_amount": self.base_amount,
            "price_usd": self.price_usd,
            "volume_usd": self.volume_usd,
            "is_deployer": self.is_deployer,
            "seconds_since_launch": self.seconds_since_launch,
            "slot_or_block": self.slot_or_block,
            "fee_native": self.fee_native,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradeRecord":
        return cls(
            trade_id=str(data.get("trade_id", "")),
            chain=str(data.get("chain", "sol")),
            token_address=str(data.get("token_address", "")),
            wallet_address=str(data.get("wallet_address", "")),
            direction=str(data.get("direction", "buy")),
            timestamp=int(data.get("timestamp", 0)),
            token_amount=float(data.get("token_amount", 0.0)),
            base_currency=str(data.get("base_currency", "SOL")),
            base_amount=float(data.get("base_amount", 0.0)),
            price_usd=float(data.get("price_usd", 0.0)),
            volume_usd=float(data.get("volume_usd", 0.0)),
            is_deployer=bool(data.get("is_deployer", False)),
            seconds_since_launch=data.get("seconds_since_launch"),
            slot_or_block=data.get("slot_or_block"),
            fee_native=float(data.get("fee_native", 0.0)),
        )

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)


@dataclass(frozen=True, slots=True)
class FundingTransferRecord:
    """Immutable record representing native or token transfer between wallets."""
    transfer_id: str
    chain: str
    from_address: str
    to_address: str
    asset_symbol: str = "SOL"
    asset_address: str = ""
    amount: float = 0.0
    amount_usd: float = 0.0
    timestamp: int = 0
    block_number: Optional[int] = None
    transfer_type: str = "transfer"
    is_initial_funding: bool = False
    hop_depth: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transfer_id": self.transfer_id,
            "chain": self.chain,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "asset_symbol": self.asset_symbol,
            "asset_address": self.asset_address,
            "amount": self.amount,
            "amount_usd": self.amount_usd,
            "timestamp": self.timestamp,
            "block_number": self.block_number,
            "transfer_type": self.transfer_type,
            "is_initial_funding": self.is_initial_funding,
            "hop_depth": self.hop_depth,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FundingTransferRecord":
        return cls(
            transfer_id=str(data.get("transfer_id", "")),
            chain=str(data.get("chain", "sol")),
            from_address=str(data.get("from_address", "")),
            to_address=str(data.get("to_address", "")),
            asset_symbol=str(data.get("asset_symbol", "SOL")),
            asset_address=str(data.get("asset_address", "")),
            amount=float(data.get("amount", 0.0)),
            amount_usd=float(data.get("amount_usd", 0.0)),
            timestamp=int(data.get("timestamp", 0)),
            block_number=data.get("block_number"),
            transfer_type=str(data.get("transfer_type", "transfer")),
            is_initial_funding=bool(data.get("is_initial_funding", False)),
            hop_depth=int(data.get("hop_depth", 1)),
        )

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)


@dataclass(frozen=True, slots=True)
class WalletScore:
    """Immutable scoring and suspicious evidence container for a single wallet."""
    wallet_address: str
    chain: str
    suspicion_score: float
    flagged_patterns: Tuple[str, ...] = field(default_factory=tuple)
    pattern_scores: Dict[str, float] = field(default_factory=dict)
    context_modifiers: Dict[str, float] = field(default_factory=dict)
    associated_tokens: Tuple[str, ...] = field(default_factory=tuple)
    net_profit_usd: float = 0.0
    buy_txs: Tuple[str, ...] = field(default_factory=tuple)
    sell_txs: Tuple[str, ...] = field(default_factory=tuple)
    evidence_summary: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.flagged_patterns, (list, set)):
            object.__setattr__(self, "flagged_patterns", tuple(self.flagged_patterns))
        if isinstance(self.associated_tokens, (list, set)):
            object.__setattr__(self, "associated_tokens", tuple(self.associated_tokens))
        if isinstance(self.buy_txs, (list, set)):
            object.__setattr__(self, "buy_txs", tuple(self.buy_txs))
        if isinstance(self.sell_txs, (list, set)):
            object.__setattr__(self, "sell_txs", tuple(self.sell_txs))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wallet_address": self.wallet_address,
            "chain": self.chain,
            "suspicion_score": self.suspicion_score,
            "flagged_patterns": list(self.flagged_patterns),
            "patterns_flagged": list(self.flagged_patterns),
            "pattern_scores": dict(self.pattern_scores),
            "context_modifiers": dict(self.context_modifiers),
            "associated_tokens": list(self.associated_tokens),
            "net_profit_usd": self.net_profit_usd,
            "buy_txs": list(self.buy_txs),
            "sell_txs": list(self.sell_txs),
            "evidence_summary": dict(self.evidence_summary),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletScore":
        patterns = data.get("flagged_patterns") or data.get("patterns_flagged") or ()
        return cls(
            wallet_address=str(data.get("wallet_address", "")),
            chain=str(data.get("chain", "sol")),
            suspicion_score=float(data.get("suspicion_score", 0.0)),
            flagged_patterns=tuple(patterns),
            pattern_scores=dict(data.get("pattern_scores", {})),
            context_modifiers=dict(data.get("context_modifiers", {})),
            associated_tokens=tuple(data.get("associated_tokens", ())),
            net_profit_usd=float(data.get("net_profit_usd", 0.0)),
            buy_txs=tuple(data.get("buy_txs", ())),
            sell_txs=tuple(data.get("sell_txs", ())),
            evidence_summary=dict(data.get("evidence_summary", {})),
        )

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)


@dataclass(frozen=True, slots=True)
class SyndicateCluster:
    """Immutable cluster of coordinated manipulation wallets forming a suspected syndicate."""
    cluster_id: str
    chain: str
    wallets: Tuple[str, ...]
    flagged_patterns: Tuple[str, ...]
    suspicion_score: float
    associated_tokens: Tuple[str, ...] = field(default_factory=tuple)
    estimated_profit_usd: float = 0.0
    funder_wallet: Optional[str] = None
    deployer_wallet: Optional[str] = None
    sweep_wallet: Optional[str] = None
    average_entry_window_seconds: float = 0.0
    average_exit_window_seconds: float = 0.0
    evidence_metadata: Dict[str, Any] = field(default_factory=dict)
    wallet_scores: Dict[str, WalletScore] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.wallets, (list, set)):
            object.__setattr__(self, "wallets", tuple(self.wallets))
        if isinstance(self.flagged_patterns, (list, set)):
            object.__setattr__(self, "flagged_patterns", tuple(self.flagged_patterns))
        if isinstance(self.associated_tokens, (list, set)):
            object.__setattr__(self, "associated_tokens", tuple(self.associated_tokens))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "chain": self.chain,
            "wallets": list(self.wallets),
            "member_wallets": list(self.wallets),
            "members": list(self.wallets),
            "flagged_patterns": list(self.flagged_patterns),
            "patterns_flagged": list(self.flagged_patterns),
            "patterns": list(self.flagged_patterns),
            "suspicion_score": self.suspicion_score,
            "associated_tokens": list(self.associated_tokens),
            "tokens": list(self.associated_tokens),
            "tokens_traded": list(self.associated_tokens),
            "estimated_profit_usd": self.estimated_profit_usd,
            "net_profit_usd": self.estimated_profit_usd,
            "funder_wallet": self.funder_wallet,
            "deployer_wallet": self.deployer_wallet,
            "sweep_wallet": self.sweep_wallet,
            "average_entry_window_seconds": self.average_entry_window_seconds,
            "average_exit_window_seconds": self.average_exit_window_seconds,
            "evidence_metadata": dict(self.evidence_metadata),
            "wallet_scores": {
                k: (v.to_dict() if hasattr(v, "to_dict") else v)
                for k, v in self.wallet_scores.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyndicateCluster":
        wallets = data.get("wallets") or data.get("member_wallets") or ()
        patterns = data.get("flagged_patterns") or data.get("patterns_flagged") or ()
        scores_raw = data.get("wallet_scores", {})
        scores_parsed = {}
        for k, v in scores_raw.items():
            if isinstance(v, dict):
                scores_parsed[k] = WalletScore.from_dict(v)
            elif isinstance(v, WalletScore):
                scores_parsed[k] = v

        return cls(
            cluster_id=str(data.get("cluster_id", "")),
            chain=str(data.get("chain", "sol")),
            wallets=tuple(wallets),
            flagged_patterns=tuple(patterns),
            suspicion_score=float(data.get("suspicion_score", 0.0)),
            associated_tokens=tuple(data.get("associated_tokens", ())),
            estimated_profit_usd=float(data.get("estimated_profit_usd", 0.0)),
            funder_wallet=data.get("funder_wallet"),
            deployer_wallet=data.get("deployer_wallet"),
            sweep_wallet=data.get("sweep_wallet"),
            average_entry_window_seconds=float(data.get("average_entry_window_seconds", 0.0)),
            average_exit_window_seconds=float(data.get("average_exit_window_seconds", 0.0)),
            evidence_metadata=dict(data.get("evidence_metadata", {})),
            wallet_scores=scores_parsed,
        )

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)
