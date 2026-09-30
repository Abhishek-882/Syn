"""Syndicate Token Creation Sentinel.

Monitors transactions initiated or signed by syndicate-controlled wallets in the
DeployerWatchlist. Detects token minting and pool initialization across:
1. Pump.fun bonding curves (Program: 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P)
2. Raydium Liquidity Pool v4 / CPMM (Program: 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8)
3. SPL Token Program (Program: TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA)

Extracts complete launch metadata, builds direct inspection links, and dispatches
atomic SYNDICATE_TOKEN_CREATED event notifications.
"""

from dataclasses import asdict, dataclass, field
import logging
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Known Canonical Program IDs on Solana
PUMP_FUN_PROGRAM_ID = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
RAYDIUM_POOL_V4_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
SPL_TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"


@dataclass
class SyndicateTokenLaunch:
    """Detailed record of a meme token created by a watched syndicate deployer."""

    mint_address: str
    symbol: str
    name: str
    creator_wallet: str
    parent_syndicate_id: str
    tx_signature: str
    timestamp: float
    launch_type: str  # "PUMP_FUN" | "RAYDIUM" | "SPL_MINT" | "GENERIC"
    initial_sol_injected: float
    lineage_path: List[str] = field(default_factory=list)
    bonding_curve_address: Optional[str] = None
    dex_screener_url: str = ""
    photon_url: str = ""
    pump_fun_url: str = ""
    gmgn_url: str = ""

    def __post_init__(self):
        if not self.dex_screener_url and self.mint_address:
            self.dex_screener_url = f"https://dexscreener.com/solana/{self.mint_address}"
        if not self.photon_url and self.mint_address:
            self.photon_url = f"https://photon-sol.tinyastro.io/en/lp/{self.mint_address}"
        if not self.pump_fun_url and self.mint_address:
            self.pump_fun_url = f"https://pump.fun/{self.mint_address}"
        if not self.gmgn_url and self.mint_address:
            self.gmgn_url = f"https://gmgn.ai/sol/token/{self.mint_address}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TokenCreationSentinel:
    """Sentinel intercepting meme token launches created by syndicate wallets."""

    def __init__(self, lineage_engine: Optional[Any] = None):
        self.lineage_engine = lineage_engine
        self.recent_launches: List[SyndicateTokenLaunch] = []
        self.listeners: List[Callable[[SyndicateTokenLaunch], None]] = []

    @property
    def detected_launches(self) -> Dict[str, SyndicateTokenLaunch]:
        """Dictionary of detected launches keyed by mint address."""
        return {l.mint_address: l for l in self.recent_launches}

    def add_listener(self, callback: Callable[[SyndicateTokenLaunch], None]) -> None:
        """Register a callback for live event dispatch."""
        if callback not in self.listeners:
            self.listeners.append(callback)

    # Alias for consistency
    add_launch_listener = add_listener

    def is_watched_deployer(self, address: str) -> bool:
        """Check if an address is actively monitored under a syndicate."""
        if not address:
            return False
        if self.lineage_engine:
            return (
                address in self.lineage_engine.deployer_watchlist
                or address in self.lineage_engine.syndicate_wallets
            )
        return False

    def get_parent_syndicate(self, address: str) -> str:
        """Retrieve syndicate ID for an address."""
        if self.lineage_engine and address in self.lineage_engine.syndicate_wallets:
            return self.lineage_engine.syndicate_wallets[address]
        return "SYND-UNKNOWN"

    def inspect_transaction(self, tx: Dict[str, Any]) -> Optional[SyndicateTokenLaunch]:
        """Inspect a raw transaction payload for token creation from a watched deployer."""
        if not isinstance(tx, dict):
            return None

        # 1. Identify signer / fee payer / creator
        creator = str(
            tx.get("creator_wallet")
            or tx.get("fee_payer")
            or tx.get("signer")
            or tx.get("from_address")
            or ""
        )

        if not self.is_watched_deployer(creator):
            return None

        parent_synd_id = self.get_parent_syndicate(creator)
        sig = str(tx.get("tx_signature") or tx.get("signature") or tx.get("tx_hash") or f"sig_{time.time()}")
        try:
            ts = float(tx.get("timestamp") or time.time())
        except (ValueError, TypeError):
            ts = time.time()

        # Determine lineage path if available
        lineage_path: List[str] = []
        if self.lineage_engine and creator in self.lineage_engine.lineage_nodes:
            node = self.lineage_engine.lineage_nodes[creator]
            curr: Optional[str] = creator
            visited = set()
            while curr and curr != "GENESIS" and curr not in visited:
                lineage_path.insert(0, curr)
                visited.add(curr)
                parent_node = self.lineage_engine.lineage_nodes.get(curr)
                curr = parent_node.funded_by if parent_node else None

        # 2. Check for Pump.fun Launch
        pump_launch = self._check_pump_fun(tx, creator, parent_synd_id, sig, ts, lineage_path)
        if pump_launch:
            self.record_launch(pump_launch)
            return pump_launch

        # 3. Check for Raydium Liquidity Pool Launch
        raydium_launch = self._check_raydium(tx, creator, parent_synd_id, sig, ts, lineage_path)
        if raydium_launch:
            self.record_launch(raydium_launch)
            return raydium_launch

        # 4. Check for SPL Token Mint Initialization
        spl_launch = self._check_spl_mint(tx, creator, parent_synd_id, sig, ts, lineage_path)
        if spl_launch:
            self.record_launch(spl_launch)
            return spl_launch

        # 5. Generic token creation signal in payload
        if tx.get("is_token_creation") or tx.get("type") in ("TOKEN_CREATE", "MINT_INITIALIZED"):
            mint = str(tx.get("mint_address") or tx.get("token_address") or f"Mint_{creator[:8]}")
            sym = str(tx.get("symbol") or "MEME")
            name = str(tx.get("name") or f"Syndicate {sym}")
            try:
                init_sol = float(tx.get("initial_sol_injected") or tx.get("amount_sol") or 0.5)
            except (ValueError, TypeError):
                init_sol = 0.5

            launch = SyndicateTokenLaunch(
                mint_address=mint,
                symbol=sym,
                name=name,
                creator_wallet=creator,
                parent_syndicate_id=parent_synd_id,
                tx_signature=sig,
                timestamp=ts,
                launch_type="GENERIC",
                initial_sol_injected=init_sol,
                lineage_path=lineage_path,
            )
            self.record_launch(launch)
            return launch

        return None

    # Alias for transaction processing
    process_transaction = inspect_transaction

    def get_pinned_launches(self, max_age_seconds: float = 3600.0) -> List[SyndicateTokenLaunch]:
        """Return all active launches within pinning window."""
        now = time.time()
        return [l for l in self.recent_launches if (now - l.timestamp) <= max_age_seconds]

    def _check_pump_fun(
        self,
        tx: Dict[str, Any],
        creator: str,
        synd_id: str,
        sig: str,
        ts: float,
        lineage_path: List[str],
    ) -> Optional[SyndicateTokenLaunch]:
        """Parse Pump.fun bonding curve creation instructions."""
        programs = tx.get("programs") or []
        prog_id = str(tx.get("program_id") or "")
        instruction = str(tx.get("instruction") or tx.get("type") or "").lower()

        is_pump = (
            PUMP_FUN_PROGRAM_ID in programs
            or prog_id == PUMP_FUN_PROGRAM_ID
            or "pump" in instruction
            or tx.get("launch_type") == "PUMP_FUN"
        )
        if not is_pump:
            return None

        mint = str(tx.get("mint_address") or tx.get("token_address") or f"PumpMint_{creator[:6]}")
        symbol = str(tx.get("symbol") or tx.get("token_symbol") or "PUMP")
        name = str(tx.get("name") or tx.get("token_name") or f"{symbol} Token")
        curve_addr = str(tx.get("bonding_curve_address") or f"Curve_{mint[:8]}")

        try:
            sol_amount = float(tx.get("initial_sol_injected") or tx.get("amount_sol") or 0.05)
        except (ValueError, TypeError):
            sol_amount = 0.05

        return SyndicateTokenLaunch(
            mint_address=mint,
            symbol=symbol.upper(),
            name=name,
            creator_wallet=creator,
            parent_syndicate_id=synd_id,
            tx_signature=sig,
            timestamp=ts,
            launch_type="PUMP_FUN",
            initial_sol_injected=sol_amount,
            lineage_path=lineage_path,
            bonding_curve_address=curve_addr,
        )

    def _check_raydium(
        self,
        tx: Dict[str, Any],
        creator: str,
        synd_id: str,
        sig: str,
        ts: float,
        lineage_path: List[str],
    ) -> Optional[SyndicateTokenLaunch]:
        """Parse Raydium liquidity pool initialization."""
        programs = tx.get("programs") or []
        prog_id = str(tx.get("program_id") or "")
        instruction = str(tx.get("instruction") or tx.get("type") or "").lower()

        is_raydium = (
            RAYDIUM_POOL_V4_PROGRAM_ID in programs
            or prog_id == RAYDIUM_POOL_V4_PROGRAM_ID
            or "raydium" in instruction
            or "initializepool" in instruction
            or tx.get("launch_type") == "RAYDIUM"
        )
        if not is_raydium:
            return None

        mint = str(tx.get("mint_address") or tx.get("token_address") or f"RayMint_{creator[:6]}")
        symbol = str(tx.get("symbol") or tx.get("token_symbol") or "RAYD")
        name = str(tx.get("name") or tx.get("token_name") or f"{symbol} Raydium Pool")

        try:
            sol_amount = float(tx.get("initial_sol_injected") or tx.get("amount_sol") or 5.0)
        except (ValueError, TypeError):
            sol_amount = 5.0

        return SyndicateTokenLaunch(
            mint_address=mint,
            symbol=symbol.upper(),
            name=name,
            creator_wallet=creator,
            parent_syndicate_id=synd_id,
            tx_signature=sig,
            timestamp=ts,
            launch_type="RAYDIUM",
            initial_sol_injected=sol_amount,
            lineage_path=lineage_path,
        )

    def _check_spl_mint(
        self,
        tx: Dict[str, Any],
        creator: str,
        synd_id: str,
        sig: str,
        ts: float,
        lineage_path: List[str],
    ) -> Optional[SyndicateTokenLaunch]:
        """Parse standard SPL Token InitializeMint instructions."""
        instruction = str(tx.get("instruction") or tx.get("type") or "").lower()
        prog_id = str(tx.get("program_id") or "")

        is_spl = (
            "initializemint" in instruction
            or (prog_id == SPL_TOKEN_PROGRAM_ID and "mint" in instruction)
            or tx.get("launch_type") == "SPL_MINT"
        )
        if not is_spl:
            return None

        mint = str(tx.get("mint_address") or tx.get("token_address") or f"SPL_{creator[:6]}")
        symbol = str(tx.get("symbol") or tx.get("token_symbol") or "SPLM")
        name = str(tx.get("name") or tx.get("token_name") or f"{symbol} SPL Token")

        try:
            sol_amount = float(tx.get("initial_sol_injected") or tx.get("amount_sol") or 0.0)
        except (ValueError, TypeError):
            sol_amount = 0.0

        return SyndicateTokenLaunch(
            mint_address=mint,
            symbol=symbol.upper(),
            name=name,
            creator_wallet=creator,
            parent_syndicate_id=synd_id,
            tx_signature=sig,
            timestamp=ts,
            launch_type="SPL_MINT",
            initial_sol_injected=sol_amount,
            lineage_path=lineage_path,
        )

    def record_launch(self, launch: SyndicateTokenLaunch) -> None:
        """Store verified launch, notify listeners, and update lineage engine."""
        # Prevent duplicate entries for the same mint address
        for existing in self.recent_launches:
            if existing.mint_address == launch.mint_address:
                return

        self.recent_launches.insert(0, launch)
        # Cap list to 100 recent launches
        if len(self.recent_launches) > 100:
            self.recent_launches = self.recent_launches[:100]

        # Annotate wallet in lineage engine
        if self.lineage_engine:
            self.lineage_engine.record_token_creation_for_wallet(
                launch.creator_wallet, launch.mint_address
            )

        # Dispatch event to active listeners
        for cb in self.listeners:
            try:
                cb(launch)
            except Exception as exc:
                logger.error("Token creation listener error: %s", exc)

    def get_recent_launches(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return serialized list of recent syndicate token launches."""
        return [l.to_dict() for l in self.recent_launches[:limit]]

    def get_active_pinned_launch(self, max_age_seconds: float = 3600.0) -> Optional[Dict[str, Any]]:
        """Return the most recent launch within the pinning window to display on top banner."""
        if not self.recent_launches:
            return None
        latest = self.recent_launches[0]
        age = time.time() - latest.timestamp
        if age <= max_age_seconds:
            return latest.to_dict()
        return None
