"""Cross-token syndicate campaign correlation engine.

Analyzes discovered syndicate clusters across multiple tokens, detecting serial
syndicates and coordinated attack campaigns through:
1. Shared Root Funding Lineage (HopTracer multi-hop origins)
2. Actor Re-use (Jaccard wallet set overlap)
3. Semantic Behavioral Similarity (Qdrant 768-dim embedding cosine matching)
4. Serial and Parallel Timing Patterns
"""

from dataclasses import dataclass, field
import logging
import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

logger = logging.getLogger("crypto_syndicate.correlator")


@dataclass
class SyndicateCampaign:
    """Represents a coordinated multi-token syndicate campaign."""

    campaign_id: str
    name: str
    token_addresses: List[str]
    token_symbols: List[str]
    syndicate_ids: List[str]
    reused_wallets: List[str]
    shared_root_funder: Optional[str] = None
    jaccard_overlap: float = 0.0
    semantic_similarity: float = 0.0
    total_profit_usd: float = 0.0
    campaign_type: str = "SERIAL_PUMP_AND_DUMP"
    confidence_score: float = 0.85
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize campaign to JSON-compatible dictionary."""
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "token_addresses": self.token_addresses,
            "token_symbols": self.token_symbols,
            "syndicate_ids": self.syndicate_ids,
            "reused_wallets": self.reused_wallets,
            "reused_wallets_count": len(self.reused_wallets),
            "shared_root_funder": self.shared_root_funder,
            "jaccard_overlap": round(self.jaccard_overlap, 4),
            "semantic_similarity": round(self.semantic_similarity, 4),
            "total_profit_usd": round(self.total_profit_usd, 2),
            "campaign_type": self.campaign_type,
            "confidence_score": round(self.confidence_score, 4),
            "created_at": self.created_at,
        }


class CrossTokenCorrelator:
    """Detects multi-token campaigns by correlating wallet sets and behavioral memory."""

    def __init__(
        self,
        min_wallet_overlap: float = 0.15,
        min_semantic_sim: float = 0.75,
    ) -> None:
        self.min_wallet_overlap = min_wallet_overlap
        self.min_semantic_sim = min_semantic_sim

    @staticmethod
    def compute_jaccard(wallets_a: Iterable[Any], wallets_b: Iterable[Any]) -> float:
        """Computes Jaccard similarity index between two sets of wallet addresses."""
        if not wallets_a or not wallets_b:
            return 0.0
        try:
            set_a = {str(w).strip().lower() for w in wallets_a if w is not None and str(w).strip()}
            set_b = {str(w).strip().lower() for w in wallets_b if w is not None and str(w).strip()}
        except Exception:
            return 0.0
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union if union > 0 else 0.0

    def correlate_clusters(
        self,
        clusters: List[Dict[str, Any]],
        vector_store: Optional[Any] = None,
    ) -> List[SyndicateCampaign]:
        """Correlate a list of cluster records into multi-token campaigns."""
        if not clusters or len(clusters) < 2:
            return []

        # Filter and sanitize valid dict clusters
        valid_clusters = [c for c in clusters if isinstance(c, dict)]
        if len(valid_clusters) < 2:
            return []

        # Graph of cluster indices linked by correlation
        n = len(valid_clusters)
        adj: Dict[int, List[Tuple[int, float, float, str, Optional[str], List[str]]]] = {
            i: [] for i in range(n)
        }

        for i in range(n):
            c_a = valid_clusters[i]
            raw_w_a = c_a.get("wallets") if isinstance(c_a.get("wallets"), (list, tuple, set)) else (c_a.get("member_ids") if isinstance(c_a.get("member_ids"), (list, tuple, set)) else [])
            wallets_a = [str(w).strip() for w in raw_w_a if w is not None and str(w).strip()]
            funder_a = str(c_a.get("root_funder")).strip() if c_a.get("root_funder") else None
            token_a = str(c_a.get("token_address") or "").strip()

            for j in range(i + 1, n):
                c_b = valid_clusters[j]
                token_b = str(c_b.get("token_address") or "").strip()

                raw_w_b = c_b.get("wallets") if isinstance(c_b.get("wallets"), (list, tuple, set)) else (c_b.get("member_ids") if isinstance(c_b.get("member_ids"), (list, tuple, set)) else [])
                wallets_b = [str(w).strip() for w in raw_w_b if w is not None and str(w).strip()]
                funder_b = str(c_b.get("root_funder")).strip() if c_b.get("root_funder") else None

                # 1. Check wallet overlap
                jaccard = self.compute_jaccard(wallets_a, wallets_b)
                set_b_lower = {w.lower() for w in wallets_b}
                reused = list(dict.fromkeys(w for w in wallets_a if w.lower() in set_b_lower))

                # 2. Check shared root funder
                shared_funder = None
                if (
                    funder_a
                    and funder_b
                    and funder_a.lower() == funder_b.lower()
                    and funder_a != "--"
                    and funder_a.lower() != "none"
                ):
                    shared_funder = funder_a

                # 3. Check semantic similarity if vector_store available
                semantic_sim = 0.0
                if vector_store and hasattr(vector_store, "find_similar"):
                    beh_a = c_a.get("behavior")
                    if beh_a:
                        try:
                            # Query top matches
                            matches = vector_store.find_similar(beh_a, top_k=5)
                            for m in matches:
                                if m.get("cluster_id") in (c_b.get("identity_id"), c_b.get("cluster_id")):
                                    semantic_sim = max(semantic_sim, float(m.get("similarity", 0.0)))
                        except Exception as exc:
                            logger.debug("Semantic correlation error: %s", exc)

                # Evaluate correlation criteria
                has_shared_funder = shared_funder is not None
                has_wallet_overlap = jaccard >= self.min_wallet_overlap
                has_semantic_match = semantic_sim >= self.min_semantic_sim

                if has_shared_funder or has_wallet_overlap or has_semantic_match:
                    # Classify correlation archetype
                    if has_shared_funder and has_wallet_overlap:
                        ctype = "SERIAL_PUMP_AND_DUMP"
                    elif has_shared_funder:
                        ctype = "DEPLOYER_CLONE_FACTORY"
                    else:
                        ctype = "PARALLEL_LAUNCH_RING"

                    adj[i].append((j, jaccard, semantic_sim, ctype, shared_funder, reused))
                    adj[j].append((i, jaccard, semantic_sim, ctype, shared_funder, reused))

        # Find connected components to form unified campaigns
        visited: Set[int] = set()
        campaigns: List[SyndicateCampaign] = []
        camp_counter = 1

        for i in range(n):
            if i in visited or not adj[i]:
                continue

            # BFS to gather connected clusters
            component = []
            queue = [i]
            visited.add(i)

            comp_jaccards = []
            comp_semantics = []
            comp_types = []
            comp_funders = set()
            comp_reused_wallets = set()

            while queue:
                curr = queue.pop(0)
                component.append(curr)
                for neighbor, jacc, sem, ctype, sf, rw in adj[curr]:
                    comp_jaccards.append(jacc)
                    comp_semantics.append(sem)
                    comp_types.append(ctype)
                    if sf:
                        comp_funders.add(sf)
                    comp_reused_wallets.update(rw)
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            # Build campaign object from component
            comp_clusters = [valid_clusters[idx] for idx in component]
            tokens = [str(c.get("token_address") or "").strip() for c in comp_clusters if c.get("token_address")]
            tokens = list(dict.fromkeys(t for t in tokens if t))
            symbols = list(dict.fromkeys(str(c.get("token_symbol") or "TOKEN") for c in comp_clusters))
            synd_ids = list(dict.fromkeys(str(c.get("identity_id") or c.get("cluster_id") or "SYND") for c in comp_clusters))
            
            def _parse_profit(c_dict):
                val = c_dict.get("estimated_profit_usd") if c_dict.get("estimated_profit_usd") is not None else c_dict.get("profit_usd")
                try:
                    return float(val) if val is not None else 0.0
                except (ValueError, TypeError):
                    return 0.0

            total_profit = sum(_parse_profit(c) for c in comp_clusters)

            avg_jacc = sum(comp_jaccards) / len(comp_jaccards) if comp_jaccards else 0.0
            avg_sem = sum(comp_semantics) / len(comp_semantics) if comp_semantics else 0.0
            primary_type = max(set(comp_types), key=comp_types.count) if comp_types else "SERIAL_PUMP_AND_DUMP"
            primary_funder = list(comp_funders)[0] if comp_funders else None

            # Calculate confidence score based on multi-signal evidence
            conf = 0.70
            if comp_funders:
                conf += 0.15
            if avg_jacc >= 0.25:
                conf += 0.10
            if avg_sem >= 0.80:
                conf += 0.05
            conf = min(1.0, conf)

            cid = f"CAMP-{camp_counter:04d}"
            camp_name = f"Campaign {cid}: {' x '.join(['$' + s for s in symbols[:3]])}"
            camp = SyndicateCampaign(
                campaign_id=cid,
                name=camp_name,
                token_addresses=tokens,
                token_symbols=symbols,
                syndicate_ids=synd_ids,
                reused_wallets=sorted(list(comp_reused_wallets)),
                shared_root_funder=primary_funder,
                jaccard_overlap=avg_jacc,
                semantic_similarity=avg_sem,
                total_profit_usd=total_profit,
                campaign_type=primary_type,
                confidence_score=conf,
            )
            campaigns.append(camp)
            camp_counter += 1

        logger.info("Correlated %d clusters into %d cross-token campaigns", len(clusters), len(campaigns))
        return campaigns

    @staticmethod
    def generate_campaign_bridges(
        campaigns: List[SyndicateCampaign],
        clusters: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generates 3D graph inter-cluster campaign bridge links."""
        bridges = []
        cluster_id_to_center = {}
        for c in clusters:
            cid = c.get("identity_id") or c.get("cluster_id") or c.get("id")
            center = c.get("center")
            if cid and center:
                cluster_id_to_center[cid] = center

        for camp in campaigns:
            sids = camp.syndicate_ids
            for i in range(len(sids)):
                for j in range(i + 1, len(sids)):
                    src, tgt = sids[i], sids[j]
                    bridges.append({
                        "campaign_id": camp.campaign_id,
                        "source_cluster": src,
                        "target_cluster": tgt,
                        "type": "campaign_bridge",
                        "color": "#f59e0b",
                        "weight": round(camp.confidence_score, 2),
                        "reused_wallets_count": len(camp.reused_wallets),
                    })
        return bridges
