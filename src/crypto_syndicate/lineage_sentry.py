"""Recursive Multi-Hop Lineage Engine & Capital Sentry.

Tracks outgoing fund transfers from known syndicate controllers and members,
recursively adopting child wallets up to 5 hops deep.
Implements the Dynamic High-Value Treasury Anchor rule: whenever a syndicate
wallet holds >= 20 SOL, it is promoted to a primary treasury anchor and spawns
a fresh dedicated 5-hop descent tree.
Gates wallets holding >= $5.00 USD into the active DeployerWatchlist.
"""

from dataclasses import asdict, dataclass, field
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Canonical CEX hot wallets to exclude from syndicate adoption
EXCLUDED_CEX_ADDRESSES: Set[str] = {
    "5tzFkiKscXBHgVXYR9qTJaMmk7p8XQzL7",
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    "2OJv9BAiHUHGuxuhvDtUbDYmgRspvtuSQUauuhBQ5TrV",
    "H8sMJSCQxfKiFTCfDR3DUMLPwcRbM614MbUpYqCT3PXx",
    "ASTyfSima4LLAdDgoFGkgqoKowG1LZFDr9fAQrg7iaJZ",
    "AC5RDfQFmDS1deWZos921qqvw3LGiLQqLPP2jL2nd5Cm",
}


@dataclass
class LineageTransfer:
    """Record of a verified capital transfer within or extending a syndicate tree."""

    tx_hash: str
    from_address: str
    to_address: str
    amount_sol: float
    amount_usd: float
    timestamp: float
    hop_level: int
    parent_syndicate_id: str
    is_treasury_anchor: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LineageWalletNode:
    """Tracked wallet node within a syndicate's multi-hop lineage graph."""

    address: str
    parent_syndicate_id: str
    funded_by: str
    hop_level: int
    balance_sol: float
    balance_usd: float
    is_deployer_ready: bool
    is_treasury_anchor: bool
    tree_anchor_address: str
    created_at: float
    status: str  # "DEPLOYER_READY", "DUST_MONITOR", "TREASURY_ANCHOR", "ROOT_FUNDER"
    tokens_created: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeployerWatchlistEntry:
    """Wallet qualified to deploy/create a meme token (holding >= $5.00 USD)."""

    address: str
    parent_syndicate_id: str
    balance_sol: float
    balance_usd: float
    funded_by: str
    first_funded_at: float
    hop_distance_from_anchor: int
    anchor_address: str
    tokens_created: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RecursiveLineageEngine:
    """Recursive fund lineage tracker with dynamic high-value treasury anchor re-centering."""

    def __init__(
        self,
        max_hops_per_anchor: int = 5,
        min_capital_usd: float = 5.0,
        treasury_threshold_sol: float = 20.0,
        sol_price_usd: float = 150.0,
    ):
        self.max_hops_per_anchor = max_hops_per_anchor
        self.min_capital_usd = min_capital_usd
        self.treasury_threshold_sol = treasury_threshold_sol
        self.sol_price_usd = sol_price_usd

        # wallet_address -> parent_syndicate_id
        self.syndicate_wallets: Dict[str, str] = {}
        # wallet_address -> LineageWalletNode
        self.lineage_nodes: Dict[str, LineageWalletNode] = {}
        # wallet_address -> DeployerWatchlistEntry
        self.deployer_watchlist: Dict[str, DeployerWatchlistEntry] = {}
        # History of all observed transfers
        self.transfers: List[LineageTransfer] = []
        # Set of treasury anchor wallet addresses
        self.treasury_anchors: Set[str] = set()

    def register_syndicate_members(
        self,
        syndicate_id: str,
        wallets: List[str],
        root_funder: Optional[str] = None,
        initial_balances: Optional[Dict[str, float]] = None,
    ) -> None:
        """Register known syndicate members and optional root funder as initial anchors."""
        initial_balances = initial_balances or {}
        now = time.time()

        if root_funder and root_funder not in EXCLUDED_CEX_ADDRESSES:
            funder_bal = float(initial_balances.get(root_funder, 50.0))
            is_treasury = funder_bal >= self.treasury_threshold_sol
            if is_treasury:
                self.treasury_anchors.add(root_funder)

            self.syndicate_wallets[root_funder] = syndicate_id
            self.lineage_nodes[root_funder] = LineageWalletNode(
                address=root_funder,
                parent_syndicate_id=syndicate_id,
                funded_by="GENESIS",
                hop_level=0,
                balance_sol=funder_bal,
                balance_usd=round(funder_bal * self.sol_price_usd, 2),
                is_deployer_ready=(funder_bal * self.sol_price_usd) >= self.min_capital_usd,
                is_treasury_anchor=is_treasury,
                tree_anchor_address=root_funder,
                created_at=now,
                status="TREASURY_ANCHOR" if is_treasury else "ROOT_FUNDER",
            )
            anchor_ref = root_funder
        else:
            anchor_ref = wallets[0] if wallets else "UNKNOWN_ANCHOR"

        for w in wallets:
            if not w or w in EXCLUDED_CEX_ADDRESSES:
                continue
            bal = float(initial_balances.get(w, 2.5))
            bal_usd = round(bal * self.sol_price_usd, 2)
            is_deployer = bal_usd >= self.min_capital_usd
            is_treasury = bal >= self.treasury_threshold_sol

            if is_treasury:
                self.treasury_anchors.add(w)

            self.syndicate_wallets[w] = syndicate_id
            node = LineageWalletNode(
                address=w,
                parent_syndicate_id=syndicate_id,
                funded_by=root_funder or "MEMBER",
                hop_level=1 if root_funder else 0,
                balance_sol=bal,
                balance_usd=bal_usd,
                is_deployer_ready=is_deployer,
                is_treasury_anchor=is_treasury,
                tree_anchor_address=anchor_ref,
                created_at=now,
                status="TREASURY_ANCHOR" if is_treasury else ("DEPLOYER_READY" if is_deployer else "DUST_MONITOR"),
            )
            self.lineage_nodes[w] = node

            if is_deployer:
                self.deployer_watchlist[w] = DeployerWatchlistEntry(
                    address=w,
                    parent_syndicate_id=syndicate_id,
                    balance_sol=bal,
                    balance_usd=bal_usd,
                    funded_by=root_funder or "MEMBER",
                    first_funded_at=now,
                    hop_distance_from_anchor=node.hop_level,
                    anchor_address=anchor_ref,
                )

    def register_syndicate_member(
        self,
        wallet: str,
        syndicate_id: str = "SYN-UNKNOWN",
        depth: int = 0,
        balance_sol: float = 1.0,
    ) -> None:
        """Register a single syndicate member."""
        self.register_syndicate_members(
            syndicate_id=syndicate_id,
            wallets=[wallet],
            initial_balances={wallet: balance_sol},
        )

    def process_transfer(self, tx: Union[Dict[str, Any], LineageTransfer]) -> Optional[LineageTransfer]:
        """Evaluate an outgoing transfer and recursively adopt child wallets under the syndicate."""
        if hasattr(tx, "__dict__") and hasattr(tx, "from_address"):
            tx_data = asdict(tx)
        elif isinstance(tx, dict):
            tx_data = tx
        else:
            return None

        sender = str(tx_data.get("from_address") or tx_data.get("source") or "")
        recipient = str(tx_data.get("to_address") or tx_data.get("destination") or "")
        tx_hash = str(tx_data.get("tx_hash") or tx_data.get("signature") or f"tx_{time.time()}")
        try:
            ts = float(tx_data.get("timestamp") or time.time())
        except (ValueError, TypeError):
            ts = time.time()

        try:
            amount_sol = float(tx_data.get("amount_sol") or tx_data.get("amount") or 0.0)
        except (ValueError, TypeError):
            amount_sol = 0.0

        amount_usd = round(amount_sol * self.sol_price_usd, 2)

        # 1. Ignore if sender is not an indexed syndicate wallet or recipient is a known CEX
        if sender not in self.syndicate_wallets or recipient in EXCLUDED_CEX_ADDRESSES or not recipient:
            return None

        synd_id = self.syndicate_wallets[sender]
        parent_node = self.lineage_nodes.get(sender)

        # 2. Determine anchor reference and hop level
        if parent_node:
            active_anchor = parent_node.tree_anchor_address
            # If the sender itself is a high-value treasury anchor, it resets descent depth to hop 1
            if parent_node.is_treasury_anchor:
                current_hop = 1
                active_anchor = sender
            else:
                current_hop = parent_node.hop_level + 1
        else:
            active_anchor = sender
            current_hop = 1

        # 3. Check if recipient hop exceeds max allowed hops from active anchor
        if current_hop > self.max_hops_per_anchor:
            logger.debug(
                "Transfer from %s to %s rejected: exceeds max hops (%d > %d) from anchor %s",
                sender[:8], recipient[:8], current_hop, self.max_hops_per_anchor, active_anchor[:8]
            )
            return None

        # 4. Check recipient balance & Dynamic Treasury Rule
        recipient_bal_sol = float(tx_data.get("recipient_balance_sol", amount_sol))
        recipient_bal_usd = round(recipient_bal_sol * self.sol_price_usd, 2)
        is_treasury = recipient_bal_sol >= self.treasury_threshold_sol
        is_deployer = recipient_bal_usd >= self.min_capital_usd

        # If recipient has high capital, it becomes a NEW dedicated anchor
        if is_treasury:
            self.treasury_anchors.add(recipient)
            active_anchor = recipient
            current_hop = 0
            node_status = "TREASURY_ANCHOR"
        elif is_deployer:
            node_status = "DEPLOYER_READY"
        else:
            node_status = "DUST_MONITOR"

        # 5. Adopt recipient into syndicate connectome
        self.syndicate_wallets[recipient] = synd_id
        node = LineageWalletNode(
            address=recipient,
            parent_syndicate_id=synd_id,
            funded_by=sender,
            hop_level=current_hop,
            balance_sol=recipient_bal_sol,
            balance_usd=recipient_bal_usd,
            is_deployer_ready=is_deployer,
            is_treasury_anchor=is_treasury,
            tree_anchor_address=active_anchor,
            created_at=ts,
            status=node_status,
        )
        self.lineage_nodes[recipient] = node

        # 6. If balance >= $5, register on Deployer Watchlist
        if is_deployer:
            self.deployer_watchlist[recipient] = DeployerWatchlistEntry(
                address=recipient,
                parent_syndicate_id=synd_id,
                balance_sol=recipient_bal_sol,
                balance_usd=recipient_bal_usd,
                funded_by=sender,
                first_funded_at=ts,
                hop_distance_from_anchor=current_hop,
                anchor_address=active_anchor,
            )

        # 7. Record verified transfer
        record = LineageTransfer(
            tx_hash=tx_hash,
            from_address=sender,
            to_address=recipient,
            amount_sol=amount_sol,
            amount_usd=amount_usd,
            timestamp=ts,
            hop_level=current_hop,
            parent_syndicate_id=synd_id,
            is_treasury_anchor=is_treasury,
        )
        self.transfers.append(record)
        return record

    def update_wallet_balance(self, address: str, balance_sol: float) -> Optional[LineageWalletNode]:
        """Update balance of a monitored wallet and dynamically update deployer qualification."""
        if address not in self.lineage_nodes:
            return None

        node = self.lineage_nodes[address]
        node.balance_sol = balance_sol
        node.balance_usd = round(balance_sol * self.sol_price_usd, 2)
        node.is_deployer_ready = node.balance_usd >= self.min_capital_usd
        is_treasury = balance_sol >= self.treasury_threshold_sol

        if is_treasury and not node.is_treasury_anchor:
            node.is_treasury_anchor = True
            node.status = "TREASURY_ANCHOR"
            node.tree_anchor_address = address
            node.hop_level = 0
            self.treasury_anchors.add(address)
        elif node.is_deployer_ready:
            node.status = "DEPLOYER_READY"
        else:
            node.status = "DUST_MONITOR"

        if node.is_deployer_ready:
            self.deployer_watchlist[address] = DeployerWatchlistEntry(
                address=address,
                parent_syndicate_id=node.parent_syndicate_id,
                balance_sol=node.balance_sol,
                balance_usd=node.balance_usd,
                funded_by=node.funded_by,
                first_funded_at=node.created_at,
                hop_distance_from_anchor=node.hop_level,
                anchor_address=node.tree_anchor_address,
                tokens_created=node.tokens_created,
            )
        elif address in self.deployer_watchlist:
            # Demote from active watch if balance dropped below threshold
            del self.deployer_watchlist[address]

        return node

    def record_token_creation_for_wallet(self, deployer_address: str, token_mint: str) -> None:
        """Record that a watched wallet deployed a token."""
        if deployer_address in self.lineage_nodes:
            if token_mint not in self.lineage_nodes[deployer_address].tokens_created:
                self.lineage_nodes[deployer_address].tokens_created.append(token_mint)

        if deployer_address in self.deployer_watchlist:
            if token_mint not in self.deployer_watchlist[deployer_address].tokens_created:
                self.deployer_watchlist[deployer_address].tokens_created.append(token_mint)

    def get_deployer_watchlist(self, syndicate_id: Optional[str] = None) -> List[DeployerWatchlistEntry]:
        """Retrieve all active deployer-ready wallets, optionally filtered by syndicate."""
        items = list(self.deployer_watchlist.values())
        if syndicate_id:
            items = [w for w in items if w.parent_syndicate_id == syndicate_id]
        return sorted(items, key=lambda w: w.balance_usd, reverse=True)

    def export_lineage_graph(self, syndicate_id: Optional[str] = None) -> Dict[str, Any]:
        """Export nodes and edges structured for a 2D SVG Directed Acyclic Graph (DAG)."""
        nodes_out: List[Dict[str, Any]] = []
        edges_out: List[Dict[str, Any]] = []

        target_nodes = self.lineage_nodes.values()
        if syndicate_id:
            target_nodes = [n for n in target_nodes if n.parent_syndicate_id == syndicate_id]

        for n in target_nodes:
            nodes_out.append(n.to_dict())

        target_addrs = {n["address"] for n in nodes_out}
        for t in self.transfers:
            if t.from_address in target_addrs and t.to_address in target_addrs:
                edges_out.append(t.to_dict())

        return {
            "nodes": nodes_out,
            "edges": edges_out,
            "total_nodes": len(nodes_out),
            "total_transfers": len(edges_out),
            "deployers_count": len([n for n in nodes_out if n["is_deployer_ready"]]),
            "treasury_anchors_count": len([n for n in nodes_out if n["is_treasury_anchor"]]),
        }
