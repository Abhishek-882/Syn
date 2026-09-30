"""M3 — Graph Construction and Syndicate Clustering.

Builds a NetworkX DiGraph from wallet relationships and applies
WCC + Louvain community detection to surface syndicate clusters.
"""

import logging
import hashlib
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

try:
    import community as community_louvain
    HAS_LOUVAIN = True
except ImportError:
    HAS_LOUVAIN = False

from crypto_syndicate.api.models import PatternType, SyndicateCluster, WalletScore

# Ensure SyndicateCluster supports dict(c) and "key in c" operations
if not hasattr(SyndicateCluster, "keys"):
    SyndicateCluster.keys = lambda self: self.to_dict().keys()
if not hasattr(SyndicateCluster, "__iter__"):
    SyndicateCluster.__iter__ = lambda self: iter(self.to_dict())
if not hasattr(SyndicateCluster, "__contains__"):
    SyndicateCluster.__contains__ = lambda self, key: key in self.to_dict()

logger = logging.getLogger("crypto_syndicate.graph")

MIN_CLUSTER_SIZE = 3


class SyndicateGraph:
    """Builds wallet relationship graphs and detects syndicate clusters."""

    def __init__(self):
        self.graph: nx.DiGraph = nx.DiGraph()
        self._wallet_meta: Dict[str, Dict[str, Any]] = {}

    # ── Graph construction ────────────────────────────────────────────────────

    def build_graph(
        self,
        wallets: List[Dict[str, Any]],
        funding_relationships: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Build directed graph. Co-buy edges weight=1, funding edges weight=2."""
        self.graph.clear()
        self._wallet_meta.clear()

        # Add wallet nodes with aliases
        for w in (wallets or []):
            addr = w.get("wallet_address") or w.get("address", "")
            if not addr:
                continue
            self._wallet_meta[addr] = w
            patterns = list(w.get("patterns_flagged") or w.get("flagged_patterns") or w.get("patterns") or [])
            tokens = list(w.get("tokens_traded") or w.get("associated_tokens") or w.get("tokens") or [])
            profit = float(w.get("estimated_profit_usd") or w.get("net_profit_usd") or 0.0)
            score = float(w.get("suspicion_score", 0.0))
            self.graph.add_node(
                addr,
                suspicion_score=score,
                patterns=patterns,
                tokens=tokens,
                chain=w.get("chain", "sol"),
                estimated_profit_usd=profit,
            )

        # Co-buy edges: wallets that both bought the same token
        token_to_buyers: Dict[str, List[str]] = defaultdict(list)
        for w in (wallets or []):
            addr = w.get("wallet_address") or w.get("address", "")
            if not addr:
                continue
            tokens = list(w.get("tokens_traded") or w.get("associated_tokens") or w.get("tokens") or [])
            for token in tokens:
                token_to_buyers[token].append(addr)

        for token, buyers in token_to_buyers.items():
            for i in range(len(buyers)):
                for j in range(i + 1, len(buyers)):
                    a, b = buyers[i], buyers[j]
                    if a == b:
                        continue
                    if self.graph.has_edge(a, b):
                        self.graph[a][b]["weight"] += 1
                        if token not in self.graph[a][b]["shared_tokens"]:
                            self.graph[a][b]["shared_tokens"].append(token)
                    else:
                        self.graph.add_edge(a, b, weight=1, type="co_buy", shared_tokens=[token])

                    if self.graph.has_edge(b, a):
                        self.graph[b][a]["weight"] += 1
                        if token not in self.graph[b][a]["shared_tokens"]:
                            self.graph[b][a]["shared_tokens"].append(token)
                    else:
                        self.graph.add_edge(b, a, weight=1, type="co_buy", shared_tokens=[token])

        # Funding edges (weight=2, directed funder→funded)
        for rel in (funding_relationships or []):
            funder = rel.get("funder", "")
            funded = rel.get("funded", "")
            if not funder or not funded or funder == funded:
                continue
            # Ensure both nodes exist
            for addr in (funder, funded):
                if not self.graph.has_node(addr):
                    self.graph.add_node(
                        addr,
                        suspicion_score=0.0,
                        patterns=[],
                        tokens=[],
                        chain=rel.get("chain", "sol"),
                        estimated_profit_usd=0.0,
                    )
            if self.graph.has_edge(funder, funded):
                self.graph[funder][funded]["weight"] = max(self.graph[funder][funded].get("weight", 1), 2)
                self.graph[funder][funded]["type"] = "funding"
            else:
                self.graph.add_edge(
                    funder,
                    funded,
                    weight=2,
                    type="funding",
                    amount=rel.get("amount", 0.0),
                    amount_usd=rel.get("amount_usd", 0.0),
                )

        logger.info("Graph built: %d nodes, %d edges", self.graph.number_of_nodes(), self.graph.number_of_edges())

    # ── Clustering ────────────────────────────────────────────────────────────

    def detect_clusters(self) -> List[SyndicateCluster]:
        """Apply WCC then Louvain. Return clusters with >= MIN_CLUSTER_SIZE members."""
        if self.graph.number_of_nodes() == 0:
            return []

        undirected = self.graph.to_undirected()
        components = list(nx.connected_components(undirected))
        clusters: List[SyndicateCluster] = []
        cluster_idx = 0

        for component in components:
            if len(component) < MIN_CLUSTER_SIZE:
                continue

            subgraph = undirected.subgraph(component)
            comp_nodes = list(component)

            if len(comp_nodes) < 6 or not HAS_LOUVAIN or subgraph.number_of_edges() == 0:
                communities = [comp_nodes]
            else:
                partition = community_louvain.best_partition(subgraph, random_state=42)
                comm_map: Dict[int, List[str]] = defaultdict(list)
                for node, comm_id in partition.items():
                    comm_map[comm_id].append(node)

                valid_comms = [m for m in comm_map.values() if len(m) >= MIN_CLUSTER_SIZE]
                orphan_comms = [m for m in comm_map.values() if len(m) < MIN_CLUSTER_SIZE]

                if not valid_comms:
                    communities = [comp_nodes]
                else:
                    for orphan_group in orphan_comms:
                        for node in orphan_group:
                            best_idx = 0
                            max_wt = -1.0
                            for c_idx, v_members in enumerate(valid_comms):
                                wt = sum(
                                    subgraph[node][nbr].get("weight", 1.0)
                                    for nbr in v_members
                                    if subgraph.has_edge(node, nbr)
                                )
                                if wt > max_wt:
                                    max_wt = wt
                                    best_idx = c_idx
                            valid_comms[best_idx].append(node)
                    communities = valid_comms

            for members in communities:
                if len(members) < MIN_CLUSTER_SIZE:
                    continue
                cluster = self._build_cluster(members, cluster_idx)
                if cluster:
                    clusters.append(cluster)
                    cluster_idx += 1

        clusters.sort(key=lambda c: c.suspicion_score, reverse=True)
        logger.info("Detected %d syndicate clusters", len(clusters))
        return clusters

    def _build_cluster(self, members: List[str], idx: int) -> Optional[SyndicateCluster]:
        scores, patterns, tokens = [], set(), set()
        profits = 0.0
        wallet_scores: Dict[str, WalletScore] = {}

        for addr in members:
            meta = self._wallet_meta.get(addr) or {}
            node_data = self.graph.nodes.get(addr, {})
            score = node_data.get("suspicion_score", meta.get("suspicion_score", 0.0))
            pats = node_data.get("patterns", meta.get("patterns_flagged", []))
            tkns = node_data.get("tokens", meta.get("tokens_traded", []))
            profit = node_data.get("estimated_profit_usd", meta.get("estimated_profit_usd", 0.0))

            scores.append(score)
            patterns.update(pats)
            tokens.update(tkns)
            profits += profit

            wallet_scores[addr] = WalletScore(
                wallet_address=addr,
                chain=node_data.get("chain", "sol"),
                suspicion_score=score,
                flagged_patterns=tuple(pats),
                associated_tokens=tuple(tkns),
                net_profit_usd=profit,
            )

        avg_score = sum(scores) / len(scores) if scores else 0.0
        cluster_id = f"cluster_{idx:04d}_{hashlib.md5(','.join(sorted(members)).encode()).hexdigest()[:8]}"

        return SyndicateCluster(
            cluster_id=cluster_id,
            chain=wallet_scores[members[0]].chain if wallet_scores else "sol",
            wallets=tuple(members),
            flagged_patterns=tuple(patterns),
            suspicion_score=avg_score,
            associated_tokens=tuple(tokens),
            estimated_profit_usd=profits,
            wallet_scores=wallet_scores,
            evidence_metadata={"size": len(members), "louvain_used": HAS_LOUVAIN},
        )

    # ── D3 export ─────────────────────────────────────────────────────────────

    def export_graph_json(self, clusters: Optional[List[SyndicateCluster]] = None) -> Dict[str, Any]:
        """Export D3-compatible JSON for force-directed graph rendering."""
        wallet_to_cluster: Dict[str, str] = {}
        if clusters:
            for c in clusters:
                c_wallets = getattr(c, "wallets", None) or (c.get("wallets") if isinstance(c, dict) else [])
                cid = getattr(c, "cluster_id", None) or (c.get("cluster_id") if isinstance(c, dict) else "unclustered")
                for w in c_wallets:
                    wallet_to_cluster[w] = cid

        nodes = []
        for node, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node,
                "suspicion_score": data.get("suspicion_score", 0.0),
                "patterns": data.get("patterns", []),
                "tokens": data.get("tokens", []),
                "chain": data.get("chain", "sol"),
                "estimated_profit_usd": data.get("estimated_profit_usd", 0.0),
                "cluster_id": wallet_to_cluster.get(node, "unclustered"),
            })

        links = []
        seen_edges: Set[Tuple[str, str]] = set()
        for u, v, data in self.graph.edges(data=True):
            key = tuple(sorted([u, v]))
            if key in seen_edges:
                continue
            seen_edges.add(key)
            links.append({
                "source": u,
                "target": v,
                "type": data.get("type", "co_buy"),
                "weight": data.get("weight", 1),
            })

        return {"nodes": nodes, "links": links}
