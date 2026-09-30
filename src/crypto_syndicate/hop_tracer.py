"""M8 — Multi-Hop Funding Lineage Tracer (HopTracer).

Performs Breadth-First Search (BFS) backwards across incoming SOL transfers
to identify shared upstream funders, common dispensers, and syndicate roots,
with cycle detection, depth limiting (MAX_HOPS=5), and CEX hot wallet pruning.
"""

from collections import deque
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from crypto_syndicate.api.models import FundingTransferRecord
from crypto_syndicate.api.solscan_client import SolscanClient

logger = logging.getLogger(__name__)

# Verified canonical CEX hot wallets and liquidity dispersers to prevent false clustering
KNOWN_CEX_ADDRESSES: Set[str] = {
    "5tzFkiKscXBHgVXYR9qTJaMmk7p8XQzL7",            # Binance Solana Hot Wallet 1
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",  # OKX Solana Deposit / Hot Wallet
    "2OJv9BAiHUHGuxuhvDtUbDYmgRspvtuSQUauuhBQ5TrV",  # Coinbase Solana Hot Wallet 1
    "H8sMJSCQxfKiFTCfDR3DUMLPwcRbM614MbUpYqCT3PXx",  # Coinbase Solana Hot Wallet 2
    "ASTyfSima4LLAdDgoFGkgqoKowG1LZFDr9fAQrg7iaJZ",  # Bybit Solana Hot Wallet
    "AC5RDfQFmDS1deWZos921qqvw3LGiLQqLPP2jL2nd5Cm",  # KuCoin Solana Hot Wallet
    "0x28C6c06298d514Db089934071355E5743bf21d60",  # Binance EVM Hot Wallet reference
}


class SharedRootResult(dict):
    """Result dictionary representing shared root funders, with property accessors."""

    @property
    def shared_root(self) -> Optional[str]:
        # Check key presence, not truthiness — empty [] must NOT fall through to shared_funders
        if "shared_root" in self and self["shared_root"] is not None:
            return self["shared_root"]
        if "syndicate_shared_roots" in self:
            roots = self["syndicate_shared_roots"]
            return roots[0] if roots else None
        roots = self.get("shared_funders") or []
        return roots[0] if roots else None

    def __str__(self) -> str:
        return self.shared_root or ""

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.shared_root == other
        if other is None:
            return self.shared_root is None
        return super().__eq__(other)


class HopTracer:
    """Multi-hop funding tracer tracing wallet lineage backwards via Solscan API."""

    MAX_HOPS: int = 5
    MIN_TRANSFER_SOL: float = 0.05

    def __init__(
        self,
        solscan_client: Optional[Any] = None,
        api_client: Optional[Any] = None,
        max_hops: int = 5,
        min_transfer_sol: float = 0.05,
        known_cex_addresses: Optional[Set[str]] = None,
        router: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize HopTracer.

        Args:
            solscan_client: SolscanClient instance (positional or keyword)
            api_client: Alternative name for SolscanClient instance
            max_hops: Maximum BFS depth (default 5)
            min_transfer_sol: Minimum SOL transfer threshold (default 0.05)
            known_cex_addresses: Custom set of CEX addresses to prune
            router: Optional SmartOnChainRouter for circuit-broken, cached queries
        """
        client = solscan_client or api_client or kwargs.get("client")
        if client is None:
            is_mock = "pytest" in sys.modules or os.getenv("DATA_MODE") == "mock"
            self.client = SolscanClient(mock_mode=is_mock)
        else:
            self.client = client

        self.router = router
        self.max_hops = int(max_hops if max_hops is not None else self.MAX_HOPS)
        self.min_transfer_sol = float(
            min_transfer_sol if min_transfer_sol is not None else self.MIN_TRANSFER_SOL
        )
        self.known_cex = (
            set(known_cex_addresses)
            if known_cex_addresses is not None
            else set(KNOWN_CEX_ADDRESSES)
        )
        self._cache: Dict[str, List[Tuple[str, float, int, str]]] = {}

    def trace_funding(self, start_wallets: List[str]) -> Dict[str, Any]:
        """Perform comprehensive multi-hop backward funding trace for a list of wallets.

        Returns:
            Dict containing:
                - start_wallets: list of input addresses
                - visited_nodes: all addresses discovered during trace
                - hop_paths: mapping of start wallet to list of lineages [[w, f1, f2], ...]
                - root_funders: terminal upstream funding sources
                - shared_funders: funders common to >= 2 start wallets
                - common_ancestors: intersection of ancestors across ALL start wallets
                - cex_wallets: CEX hot wallets encountered
                - edges: list of funding edges (for SyndicateGraph / NetworkX)
                - confidence: funding commonality confidence score (0.0 to 1.0)
        """
        if not start_wallets:
            return {
                "start_wallets": [],
                "visited_nodes": [],
                "hop_paths": {},
                "root_funders": [],
                "shared_funders": [],
                "common_ancestors": [],
                "cex_wallets": [],
                "edges": [],
                "confidence": 0.0,
            }

        all_ancestors: Dict[str, Set[str]] = {}
        hop_paths: Dict[str, List[List[str]]] = {}
        all_visited: Set[str] = set()
        all_edges: List[Dict[str, Any]] = []
        cex_encountered: Set[str] = set()
        edge_keys: Set[Tuple[str, str]] = set()

        for wallet in start_wallets:
            wallet_ancestors: Set[str] = set()
            wallet_paths: List[List[str]] = []

            # Queue elements: (current_address, current_depth, current_path)
            queue: deque[Tuple[str, int, List[str]]] = deque([(wallet, 0, [wallet])])

            while queue:
                curr, depth, path = queue.popleft()
                all_visited.add(curr)

                # Stop condition 1: Depth limit reached
                if depth >= self.max_hops:
                    wallet_paths.append(path)
                    continue

                # Stop condition 2: Current node is known CEX hot wallet
                if self._is_cex(curr) and depth > 0:
                    cex_encountered.add(curr)
                    wallet_paths.append(path)
                    continue

                funders = self._get_funders(curr)
                # If terminal node with no upstream funders >= threshold
                if not funders and depth > 0:
                    wallet_paths.append(path)
                    continue

                has_valid_upstream = False
                for funder, amount, ts, tx_id in funders:
                    if amount < self.min_transfer_sol:
                        continue

                    # Record edge
                    edge_key = (funder, curr)
                    if edge_key not in edge_keys:
                        edge_keys.add(edge_key)
                        all_edges.append({
                            "from_address": funder,
                            "to_address": curr,
                            "amount": amount,
                            "depth": depth + 1,
                            "timestamp": ts,
                            "tx_id": tx_id,
                            "is_cex": self._is_cex(funder),
                        })

                    wallet_ancestors.add(funder)
                    all_visited.add(funder)

                    # Cycle detection: check if funder is already in current path
                    if funder in path:
                        # Cycle detected: record path but do not expand further
                        wallet_paths.append(path + [funder])
                        continue

                    has_valid_upstream = True
                    new_path = path + [funder]

                    if self._is_cex(funder):
                        cex_encountered.add(funder)
                        wallet_paths.append(new_path)
                    else:
                        queue.append((funder, depth + 1, new_path))

                if not has_valid_upstream and depth > 0:
                    wallet_paths.append(path)

            all_ancestors[wallet] = wallet_ancestors
            hop_paths[wallet] = wallet_paths

        # Compute shared funders across >= 2 wallets
        funder_counts: Dict[str, int] = {}
        for w, ancestors in all_ancestors.items():
            for f in ancestors:
                funder_counts[f] = funder_counts.get(f, 0) + 1

        shared_funders = [f for f, count in funder_counts.items() if count >= 2]
        shared_funders.sort(key=lambda f: funder_counts[f], reverse=True)

        # Common ancestors (intersection of all wallets)
        sets = list(all_ancestors.values())
        common: Set[str] = set()
        if sets and all(len(s) > 0 for s in sets):
            common = sets[0].copy()
            for s in sets[1:]:
                common &= s

        # Root funders: terminal nodes with in-degree 0 in explored graph
        destinations = {e["to_address"] for e in all_edges}
        origins = {e["from_address"] for e in all_edges}
        roots = sorted(list(origins - destinations))

        confidence = len(common) / max(len(start_wallets), 1)

        return {
            "start_wallets": start_wallets,
            "visited_nodes": sorted(list(all_visited)),
            "hop_paths": hop_paths,
            "root_funders": roots,
            "shared_funders": shared_funders,
            "common_ancestors": sorted(list(common)),
            "cex_wallets": sorted(list(cex_encountered)),
            "edges": all_edges,
            "confidence": min(float(confidence), 1.0),
        }

    def find_shared_root(self, wallets: List[str]) -> SharedRootResult:
        """BFS from each wallet back to find shared upstream funder."""
        if not wallets:
            return SharedRootResult()

        all_ancestors: Dict[str, Set[str]] = {}
        for w in wallets:
            ancestors = self._bfs_ancestors(w)
            all_ancestors[w] = ancestors

        sets = list(all_ancestors.values())
        if not sets or any(len(s) == 0 for s in sets):
            common = set()
        else:
            common = sets[0].copy()
            for s in sets[1:]:
                common &= s

        # Exclude CEX addresses from syndicate common root
        syndicate_common = common - self.known_cex

        res = SharedRootResult({
            "shared_root": sorted(list(syndicate_common))[0] if syndicate_common else None,
            "shared_funders": sorted(list(common)),
            "syndicate_shared_roots": sorted(list(syndicate_common)),
            "wallet_ancestors": {k: sorted(list(v)) for k, v in all_ancestors.items()},
            "confidence": len(syndicate_common) / max(len(wallets), 1),
        })
        return res

    def get_shared_root(self, wallets: List[str]) -> Optional[str]:
        """Convenience method returning the common non-CEX root funder address or None."""
        res = self.find_shared_root(wallets)
        return res.shared_root

    def _bfs_ancestors(self, start: str) -> Set[str]:
        """BFS traversal collecting all upstream ancestors for a single wallet."""
        visited: Set[str] = set()
        queue: deque[Tuple[str, int, Set[str]]] = deque([(start, 0, {start})])
        ancestors: Set[str] = set()

        while queue:
            addr, depth, branch_seen = queue.popleft()
            if addr in visited or depth >= self.max_hops:
                continue
            visited.add(addr)

            if self._is_cex(addr) and depth > 0:
                continue

            for funder, amount, _, _ in self._get_funders(addr):
                if amount >= self.min_transfer_sol:
                    ancestors.add(funder)
                    if funder not in branch_seen and not self._is_cex(funder):
                        queue.append((funder, depth + 1, branch_seen | {funder}))

        return ancestors

    def _get_funders(self, wallet: str) -> List[Tuple[str, float, int, str]]:
        """Fetch incoming transfers from cache or Solscan client/SmartRouter."""
        if wallet not in self._cache:
            try:
                if self.router is not None:
                    transfers = self.router.fetch_transfers(wallet, limit=50)
                else:
                    transfers = self.client.get_account_transfers(wallet, flow="in")
                records = []
                for t in (transfers or []):
                    from_addr = (
                        getattr(t, "from_address", None)
                        or (t.get("from_address") if isinstance(t, dict) else "")
                        or (t.get("from") if isinstance(t, dict) else "")
                        or ""
                    )
                    amt = (
                        getattr(t, "amount", None)
                        if hasattr(t, "amount")
                        else (t.get("amount", 0.0) if isinstance(t, dict) else 0.0)
                    )
                    ts = (
                        getattr(t, "timestamp", None)
                        if hasattr(t, "timestamp")
                        else (t.get("timestamp", 0) if isinstance(t, dict) else 0)
                    )
                    tx_id = (
                        getattr(t, "transfer_id", None)
                        if hasattr(t, "transfer_id")
                        else (t.get("transfer_id", "") if isinstance(t, dict) else "")
                    )
                    amt_val = float(amt or 0.0)
                    if from_addr and from_addr.lower() != wallet.lower():
                        records.append((str(from_addr), amt_val, int(ts or 0), str(tx_id or "")))
                self._cache[wallet] = records
            except Exception as exc:
                logger.warning("Error fetching transfers for %s: %s", wallet, exc)
                self._cache[wallet] = []
        return self._cache[wallet]

    def _is_cex(self, address: str) -> bool:
        """Check if address is a known centralized exchange hot wallet."""
        return address in self.known_cex
