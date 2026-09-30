"""M9 — Persistent Syndicate Identity Engine (SyndicateIdentityEngine).

Manages persistent entity resolution for suspicious wallet clusters across
tokens, runs, and chains. Assigns canonical syndicate IDs (e.g. SYND-0001),
tracks operational history, updates confidence scores, and maintains an
atomic JSON repository (syndicate_identities.json).
"""

from dataclasses import dataclass, field
import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid

from crypto_syndicate.fingerprint import SyndicateBehavior

logger = logging.getLogger(__name__)


def _norm_addr(addr: Any) -> str:
    """Normalize address: lowercase EVM (0x...) addresses for case-insensitive comparison."""
    s = str(addr or "").strip()
    return s.lower() if s.startswith("0x") else s




@dataclass
class SyndicateIdentity:
    """Persistent entity representing a discovered syndicate across time and chains."""

    identity_id: str
    alias: str = ""
    primary_wallets: List[str] = field(default_factory=list)
    historical_tokens: List[str] = field(default_factory=list)
    behavior_profile: Optional[SyndicateBehavior] = None
    confidence_score: float = 0.60
    first_seen: float = 0.0
    last_seen: float = 0.0
    operation_count: int = 1
    total_profit_usd: float = 0.0
    known_funders: List[str] = field(default_factory=list)
    chains: List[str] = field(default_factory=lambda: ["sol"])
    behavior_texts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def __init__(
        self,
        identity_id: str = "",
        alias: str = "",
        primary_wallets: Optional[List[str]] = None,
        historical_tokens: Optional[List[str]] = None,
        behavior_profile: Optional[SyndicateBehavior] = None,
        confidence_score: Optional[float] = None,
        first_seen: Optional[float] = None,
        last_seen: Optional[float] = None,
        operation_count: int = 1,
        total_profit_usd: float = 0.0,
        known_funders: Optional[List[str]] = None,
        chains: Optional[List[str]] = None,
        behavior_texts: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        notes: str = "",
        # Backward compatibility aliases
        syndicate_id: Optional[str] = None,
        known_wallets: Optional[List[str]] = None,
        known_chains: Optional[List[str]] = None,
        confidence: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        self.identity_id = str(identity_id or syndicate_id or "")
        self.alias = str(alias)
        raw_wallets = primary_wallets if primary_wallets is not None else known_wallets
        self.primary_wallets = list(raw_wallets) if raw_wallets is not None else []
        self.historical_tokens = list(historical_tokens) if historical_tokens is not None else []
        self.behavior_profile = behavior_profile

        raw_conf = confidence_score if confidence_score is not None else confidence
        self.confidence_score = float(raw_conf) if raw_conf is not None else 0.60

        now = time.time()
        self.first_seen = float(first_seen) if first_seen is not None and first_seen > 0 else now
        self.last_seen = float(last_seen) if last_seen is not None and last_seen > 0 else now
        self.operation_count = int(operation_count)
        self.total_profit_usd = float(total_profit_usd)
        self.known_funders = list(known_funders) if known_funders is not None else []

        raw_chains = chains if chains is not None else known_chains
        self.chains = list(raw_chains) if raw_chains is not None else ["sol"]
        self.behavior_texts = list(behavior_texts) if behavior_texts is not None else []
        self.metadata = dict(metadata) if metadata is not None else {}
        self.notes = str(notes)

    # Dual property accessors for cross-compatibility
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
    def known_chains(self) -> List[str]:
        return self.chains

    @known_chains.setter
    def known_chains(self, val: List[str]) -> None:
        self.chains = list(val)

    @property
    def confidence(self) -> float:
        return self.confidence_score

    @confidence.setter
    def confidence(self, val: float) -> None:
        self.confidence_score = float(val)

    def to_dict(self) -> Dict[str, Any]:
        """Convert identity to JSON-compatible dictionary."""
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
            "chains": list(self.chains),
            "known_chains": list(self.chains),
            "behavior_texts": list(self.behavior_texts),
            "metadata": dict(self.metadata),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyndicateIdentity":
        """Instantiate SyndicateIdentity from dictionary."""
        b_data = data.get("behavior_profile")
        profile = SyndicateBehavior.from_dict(b_data) if isinstance(b_data, dict) else None
        return cls(
            identity_id=str(data.get("identity_id") or data.get("syndicate_id") or ""),
            alias=str(data.get("alias", "")),
            primary_wallets=list(data.get("primary_wallets") or data.get("known_wallets") or []),
            historical_tokens=list(data.get("historical_tokens", [])),
            behavior_profile=profile,
            confidence_score=float(data.get("confidence_score") or data.get("confidence", 0.60)),
            first_seen=float(data.get("first_seen", 0.0)),
            last_seen=float(data.get("last_seen", 0.0)),
            operation_count=int(data.get("operation_count", 1)),
            total_profit_usd=float(data.get("total_profit_usd", 0.0)),
            known_funders=list(data.get("known_funders", [])),
            chains=list(data.get("chains") or data.get("known_chains") or ["sol"]),
            behavior_texts=list(data.get("behavior_texts", [])),
            metadata=dict(data.get("metadata", {})),
            notes=str(data.get("notes", "")),
        )


class SyndicateIdentityEngine:
    """Manages persistent syndicate identities with hybrid entity resolution."""

    SIMILARITY_THRESHOLD = 0.82
    WALLET_OVERLAP_THRESHOLD = 0.30
    IDENTITY_FILE = "syndicate_identities.json"

    def __init__(
        self,
        output_dir: str = "results",
        vector_store: Any = None,
        similarity_threshold: float = 0.82,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.identity_file = self.output_dir / self.IDENTITY_FILE
        self.vector_store = vector_store
        self.similarity_threshold = float(similarity_threshold)
        self._lock = threading.Lock()
        self.identities: Dict[str, SyndicateIdentity] = self._load()

    def match_syndicate(
        self,
        cluster: Any,
        behavior: Optional[SyndicateBehavior] = None,
        shared_funder: Optional[str] = None,
    ) -> Optional[SyndicateIdentity]:
        """Find matching known syndicate using graph overlap and vector similarity.

        Returns matching SyndicateIdentity instance or None if no match meets threshold.
        """
        c_dict = cluster.to_dict() if hasattr(cluster, "to_dict") else (dict(cluster) if isinstance(cluster, dict) else {})
        c_wallets = set(_norm_addr(w) for w in (c_dict.get("wallets") or c_dict.get("members") or []) if w)
        raw_funder = shared_funder or c_dict.get("funder_wallet")
        funder = _norm_addr(raw_funder) if raw_funder else None

        best_match: Optional[SyndicateIdentity] = None
        best_score = 0.0

        # Stage 1: Wallet overlap & Shared Funder matching
        for ident in self.identities.values():
            known = set(_norm_addr(w) for w in ident.primary_wallets if w)
            intersection = c_wallets & known
            jaccard = len(intersection) / max(len(c_wallets | known), 1)

            score = 0.0
            # Normalize known_funders for comparison too
            known_funders_norm = set(_norm_addr(f) for f in ident.known_funders if f)
            if funder and funder in known_funders_norm:
                # Direct common funder match
                score = 0.95
                if len(intersection) >= 1:
                    score = 0.99
            elif len(intersection) >= 2 or jaccard >= self.WALLET_OVERLAP_THRESHOLD:
                # Substantial wallet overlap
                score = 0.85 + (0.15 * jaccard)

            if score > best_score:
                best_score = score
                best_match = ident

        if best_match and best_score >= self.similarity_threshold:
            return best_match

        # Stage 2: Behavioral Vector Similarity via Qdrant / vector_store
        if self.vector_store and behavior:
            b_text = behavior.to_text()
            try:
                matches = self.vector_store.find_similar(b_text, top_k=3)
                for m in (matches or []):
                    sim = float(m.get("similarity", 0.0))
                    sid = m.get("syndicate_id") or m.get("address")
                    if sim >= self.similarity_threshold and sid in self.identities:
                        if sim > best_score:
                            best_score = sim
                            best_match = self.identities[sid]
            except Exception as exc:
                logger.warning("Vector store matching failed: %s", exc)

        if best_match and best_score >= self.similarity_threshold:
            return best_match

        return None

    def register_cluster(
        self,
        cluster: Any,
        token: Any = None,
        trades: Any = None,
        shared_funder: Optional[str] = None,
        behavior: Optional[SyndicateBehavior] = None,
        behavior_text: str = "",
    ) -> SyndicateIdentity:
        """Register an on-chain cluster, resolving to existing identity or minting a new one."""
        c_dict = cluster.to_dict() if hasattr(cluster, "to_dict") else (dict(cluster) if isinstance(cluster, dict) else {})
        # Filter None values to prevent sorted() TypeError and normalize EVM addresses
        c_wallets = [_norm_addr(w) for w in (c_dict.get("wallets") or c_dict.get("members") or []) if w]
        c_tokens = [str(t) for t in (c_dict.get("associated_tokens") or c_dict.get("tokens") or []) if t]
        c_profit = float(c_dict.get("estimated_profit_usd") or 0.0)
        c_chain = str(c_dict.get("chain", "sol"))
        funder = shared_funder or c_dict.get("funder_wallet")

        if behavior is None:
            if behavior_text:
                behavior = SyndicateBehavior(
                    cluster_id=c_dict.get("cluster_id", ""),
                    chain=c_chain,
                    wallet_count=len(c_wallets),
                    estimated_profit_usd=c_profit,
                    patterns_flagged=list(c_dict.get("flagged_patterns", [])),
                    funder_wallet=funder,
                )
            else:
                behavior = SyndicateBehavior.from_cluster_and_token(cluster, token, trades)

        b_text = behavior.to_text() if not behavior_text else behavior_text
        match = self.match_syndicate(cluster, behavior=behavior, shared_funder=funder)

        now = time.time()
        if match:
            identity = match
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
            if c_chain not in identity.chains:
                identity.chains.append(c_chain)
            logger.warning(
                "RETURNING SYNDICATE: %s (op #%d)",
                identity.identity_id,
                identity.operation_count,
            )
        else:
            # Safe ID minting: use max existing numeric suffix to avoid collisions
            existing_nums = [
                int(k.split("-")[1])
                for k in self.identities
                if k.startswith("SYND-") and len(k) > 5 and k.split("-")[1].isdigit()
            ]
            next_idx = (max(existing_nums) + 1) if existing_nums else 1
            sid = f"SYND-{next_idx:04d}"
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
                chains=[c_chain],
                behavior_texts=[b_text],
            )
            self.identities[sid] = identity
            logger.info("NEW SYNDICATE: %s", sid)

        # Upsert into vector store if enabled
        if self.vector_store:
            try:
                if hasattr(self.vector_store, "upsert_syndicate"):
                    self.vector_store.upsert_syndicate(identity, b_text)
            except Exception as exc:
                logger.warning("Vector store upsert failed: %s", exc)

        self._save()
        return identity

    def process(
        self,
        clusters: Any,
        tokens: Optional[Any] = None,
        trades: Optional[Any] = None,
    ) -> Union[SyndicateIdentity, List[SyndicateIdentity]]:
        """Process either a single cluster (with optional behavior_text) or a list of clusters."""
        if isinstance(clusters, list):
            results: List[SyndicateIdentity] = []
            tokens_map = tokens if isinstance(tokens, dict) else {}
            trades_map = trades if isinstance(trades, dict) else {}
            for c in clusters:
                c_dict = c.to_dict() if hasattr(c, "to_dict") else (dict(c) if isinstance(c, dict) else {})
                assoc = c_dict.get("associated_tokens", [])
                tok_key = assoc[0] if assoc else ""
                t_obj = tokens_map.get(tok_key)
                tr_obj = trades_map.get(tok_key)
                results.append(self.register_cluster(c, token=t_obj, trades=tr_obj))
            return results
        else:
            # Single cluster mode
            b_text = str(tokens) if isinstance(tokens, str) else ""
            return self.register_cluster(cluster=clusters, behavior_text=b_text)

    def get_all_identities(self) -> List[SyndicateIdentity]:
        """Return all registered syndicate identities."""
        return list(self.identities.values())

    def get_identity(self, identity_id: str) -> Optional[SyndicateIdentity]:
        """Retrieve a syndicate identity by ID."""
        return self.identities.get(identity_id)

    def get_watchlist(self, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """Return watchlist of syndicate funders and operations."""
        watchlist = []
        for ident in self.identities.values():
            if ident.confidence_score >= min_confidence:
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
        """Persist identities atomically using a lock and unique temporary file swap."""
        with self._lock:
            tmp = self.identity_file.parent / f"{self.identity_file.stem}_{uuid.uuid4().hex}.tmp"
            try:
                payload = {k: v.to_dict() for k, v in list(self.identities.items())}
                tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                os.replace(tmp, self.identity_file)
            except Exception as exc:
                logger.error("Failed to save %s: %s", self.identity_file, exc)
            finally:
                try:
                    if tmp.exists():
                        tmp.unlink()
                except Exception:
                    pass
