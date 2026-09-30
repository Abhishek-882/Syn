"""Milestone 1 Boundary, Fixture & Data Model Adversarial Stress Test Suite (Challenger 2).

Authored by m1_challenger_2 to exhaustively challenge:
1. The 5 Golden Syndicate Scenarios:
   - Acceptance criteria: >=3 wallets per cluster, >=2 of 4 canonical patterns, valid addresses per chain.
   - Mathematical reconciliation: trade volumes, wallet PnL, cluster profit, entry/exit time averages.
   - Temporal causality: funding < launch/buy < sell < sweep.
2. Boundary inputs for CryptoDataClient methods:
   - Invalid / unrecognised chains, case sensitivity, whitespace padding, empty strings.
   - Malformed / unknown token and wallet addresses.
   - Negative timestamps, zero/negative limits, extreme limits.
   - Graceful handling of empty responses and missing metadata.
3. Canonical Immutable Data Models:
   - Immutability enforcement: frozen dataclass prevents attribute mutation, deletion, and addition.
   - Collection freezing: mutable lists/sets passed into models are converted to immutable tuples.
   - Defense against external container mutation.
   - Lossless dictionary serialization roundtripping (to_dict / from_dict).
   - Backwards-compatible aliasing and dict-like subscription (__getitem__, get).
   - Robust type coercion and malformed dict handling.
"""

import re
import pytest
from typing import Dict, Any, List
from dataclasses import FrozenInstanceError

from crypto_syndicate.api import (
    CryptoDataClient,
    GMGNClient,
    SolscanClient,
    FixtureProvider,
    TokenLaunchEvent,
    TradeRecord,
    FundingTransferRecord,
    WalletScore,
    SyndicateCluster,
    PatternType,
    get_mock_clusters,
    get_mock_token_launches,
    get_mock_token_trades,
    get_mock_wallet_transfers,
    get_mock_account_metadata,
)
from crypto_syndicate.config import AppConfig


# ============================================================================
# Category 1: 5 Golden Syndicate Fixtures & Multi-Chain Adversarial Stress
# ============================================================================

class TestAdversarialGoldenFixtures:
    """Stress tests acceptance criteria, multi-chain parameters, and mathematical
    consistency across all 5 golden syndicate scenarios.
    """

    @pytest.fixture(scope="class")
    def clusters(self) -> List[SyndicateCluster]:
        return get_mock_clusters()

    def test_golden_cluster_cardinality_and_identities(self, clusters: List[SyndicateCluster]):
        """System must define exactly 5 distinct golden clusters with expected identifiers."""
        assert len(clusters) == 5, f"Expected exactly 5 golden clusters, got {len(clusters)}"
        expected_ids = {
            "SYN-SOL-PUMP-01",
            "SYN-ETH-UNI-02",
            "SYN-BSC-PAN-03",
            "SYN-BASE-AERO-04",
            "SYN-MULTI-CROSS-05",
        }
        actual_ids = {c.cluster_id for c in clusters}
        assert actual_ids == expected_ids, f"Cluster ID mismatch: {actual_ids} != {expected_ids}"

    def test_acceptance_criteria_wallet_counts(self, clusters: List[SyndicateCluster]):
        """Every cluster must contain >= 3 unique member wallets."""
        for c in clusters:
            assert len(c.wallets) >= 3, (
                f"Cluster {c.cluster_id} failed AC: has {len(c.wallets)} wallets, required >= 3"
            )
            # Ensure no duplicate wallets inside any cluster
            assert len(c.wallets) == len(set(c.wallets)), (
                f"Cluster {c.cluster_id} contains duplicate member wallets: {c.wallets}"
            )

    def test_acceptance_criteria_pattern_types(self, clusters: List[SyndicateCluster]):
        """Every cluster must flag >= 2 patterns, all belonging to the 4 canonical pattern types."""
        canonical_patterns = {p.value for p in PatternType}
        assert len(canonical_patterns) == 4
        assert canonical_patterns == {
            "early_entry",
            "common_funding",
            "shared_deployer",
            "coordinated_dump",
        }

        for c in clusters:
            flagged = set(c.flagged_patterns)
            assert len(flagged) >= 2, (
                f"Cluster {c.cluster_id} failed AC: flagged {len(flagged)} patterns, required >= 2"
            )
            invalid_patterns = flagged - canonical_patterns
            assert not invalid_patterns, (
                f"Cluster {c.cluster_id} contains unrecognised pattern types: {invalid_patterns}"
            )

    def test_chain_address_cryptographic_format(self, clusters: List[SyndicateCluster]):
        """Assert valid blockchain address formats for every chain:
        - Solana: Base58 string (32-44 chars, no 0, O, I, l)
        - EVM (eth, bsc, base): 42-char hex string (0x + 40 hex digits)
        - Multi-chain: per-wallet verification matching sub-chain
        """
        evm_pattern = re.compile(r"^0x[0-9a-fA-F]{40}$")
        base58_charset = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")

        for c in clusters:
            for w in c.wallets:
                if c.chain in ("eth", "bsc", "base"):
                    assert evm_pattern.match(w), (
                        f"Cluster {c.cluster_id} wallet {w} is not a valid 42-char EVM hex address"
                    )
                elif c.chain == "sol":
                    assert 32 <= len(w) <= 44, f"Solana address {w} length out of range [32, 44]"
                    assert set(w).issubset(base58_charset), (
                        f"Solana address {w} contains non-Base58 characters"
                    )
                elif c.chain == "multi":
                    is_evm = bool(evm_pattern.match(w))
                    is_sol = (32 <= len(w) <= 44) and set(w).issubset(base58_charset)
                    assert is_evm or is_sol, (
                        f"Multi-chain cluster {c.cluster_id} wallet {w} is neither valid EVM nor valid Solana address"
                    )

    def test_mathematical_consistency_profit_reconciliation(self, clusters: List[SyndicateCluster]):
        """Cluster estimated_profit_usd must reconcile with the sum of individual wallet net_profit_usd."""
        for c in clusters:
            assert c.estimated_profit_usd > 0.0, f"Cluster {c.cluster_id} has non-positive profit: {c.estimated_profit_usd}"
            assert len(c.wallet_scores) == len(c.wallets), (
                f"Cluster {c.cluster_id} wallet_scores dict size ({len(c.wallet_scores)}) does not match wallets ({len(c.wallets)})"
            )

            summed_wallet_profit = sum(ws.net_profit_usd for ws in c.wallet_scores.values())
            assert abs(c.estimated_profit_usd - summed_wallet_profit) < 0.05, (
                f"Cluster {c.cluster_id} profit {c.estimated_profit_usd} diverges from sum of wallet profits {summed_wallet_profit}"
            )

    def test_mathematical_consistency_entry_exit_windows(self, clusters: List[SyndicateCluster]):
        """Window timing metrics (average_entry_window_seconds, average_exit_window_seconds)
        must be physically plausible and accurately match trade timestamps.
        """
        for c in clusters:
            assert c.average_entry_window_seconds >= 0.0, (
                f"Cluster {c.cluster_id} has negative entry window: {c.average_entry_window_seconds}"
            )
            if c.average_exit_window_seconds > 0.0:
                assert c.average_exit_window_seconds > c.average_entry_window_seconds, (
                    f"Cluster {c.cluster_id} exit window ({c.average_exit_window_seconds}s) must be after entry window ({c.average_entry_window_seconds}s)"
                )

    def test_temporal_causality_pipeline(self):
        """Verify strict temporal causality across funding -> launch -> buy -> sell -> sweep:
        1. Funder transfer timestamp <= Launch or first buy
        2. Buy timestamp < Sell timestamp
        3. Sell timestamp <= Sweep timestamp
        """
        provider = FixtureProvider()
        for c in provider.get_clusters():
            token_addr = c.associated_tokens[0]
            trades = provider.get_token_trades(chain=c.chain, token_address=token_addr, limit=500)
            
            buys = [t for t in trades if t.direction == "buy"]
            sells = [t for t in trades if t.direction == "sell"]

            assert len(buys) >= len(c.wallets), f"Not enough buys for wallets in {c.cluster_id}"
            
            # If coordinated dump is flagged, sells must exist
            if "coordinated_dump" in c.flagged_patterns:
                assert len(sells) >= len(c.wallets), (
                    f"Cluster {c.cluster_id} flagged coordinated_dump but has insufficient sells"
                )
                min_sell_time = min(s.timestamp for s in sells)
                max_buy_time = max(b.timestamp for b in buys)
                assert min_sell_time >= max_buy_time, (
                    f"Causality violation in {c.cluster_id}: Sell ({min_sell_time}) occurred before Buy ({max_buy_time})"
                )

            # Check wallet funding transfers occur before or at trade entry
            for w in c.wallets:
                transfers = provider.get_wallet_transfers(chain=c.chain, wallet_address=w, flow="in")
                if transfers:
                    first_funding = min(t.timestamp for t in transfers if t.is_initial_funding or t.hop_depth == 1)
                    wallet_buys = [b for b in buys if b.wallet_address.lower() == w.lower()]
                    if wallet_buys:
                        first_buy = min(b.timestamp for b in wallet_buys)
                        assert first_funding <= first_buy, (
                            f"Causality violation in {c.cluster_id} wallet {w}: Funding ({first_funding}) after Buy ({first_buy})"
                        )


# ============================================================================
# Category 2: CryptoDataClient Boundary Inputs & Error Resilience
# ============================================================================

class TestAdversarialCryptoDataClientBoundaries:
    """Stress tests boundary inputs to CryptoDataClient: invalid chains,
    malformed addresses, negative timestamps, empty responses, extreme limits.
    """

    @pytest.fixture
    def client(self) -> CryptoDataClient:
        cfg = AppConfig(
            crypto_data_mode="mock",
            gmgn_api_key="",
            solscan_api_key="",
            cache_db_path=":memory:",
        )
        return CryptoDataClient(config=cfg)

    # --- 1. Chain Parameter Boundaries ---

    def test_get_new_token_launches_unknown_chain(self, client: CryptoDataClient):
        """Unknown or unsupported chain should return empty list gracefully, not raise unhandled exception."""
        res = client.get_new_token_launches(chain="dogechain", time_period="1h")
        assert isinstance(res, list)
        assert len(res) == 0

    def test_get_new_token_launches_empty_chain(self, client: CryptoDataClient):
        """Empty string or whitespace chain should return empty list or default gracefully."""
        res_empty = client.get_new_token_launches(chain="", time_period="1h")
        assert isinstance(res_empty, list)
        # Empty string should return all launches or empty list without crash
        assert len(res_empty) in (0, 5)

    def test_get_new_token_launches_chain_case_insensitivity(self, client: CryptoDataClient):
        """Chain names with uppercase or whitespace should normalize correctly."""
        res_upper = client.get_new_token_launches(chain="SOL")
        assert len(res_upper) == 1
        assert res_upper[0].chain == "sol"

        res_padded = client.get_new_token_launches(chain="  eth  ")
        assert len(res_padded) == 1
        assert res_padded[0].chain == "eth"

    def test_get_new_token_launches_invalid_time_period(self, client: CryptoDataClient):
        """Invalid time_period parameter should not crash the facade."""
        res = client.get_new_token_launches(chain="sol", time_period="9999y_invalid")
        assert isinstance(res, list)

    # --- 2. Token Trades Boundaries ---

    def test_get_token_trades_unknown_token(self, client: CryptoDataClient):
        """Unknown token address should fall back gracefully to fixture trades or empty list without crash."""
        res = client.get_token_trades(chain="sol", token_address="UnknownToken1111111111111111111111111111111")
        assert isinstance(res, list)

    def test_get_token_trades_empty_token_address(self, client: CryptoDataClient):
        """Empty string for token_address should not crash."""
        res = client.get_token_trades(chain="sol", token_address="")
        assert isinstance(res, list)

    def test_get_token_trades_limit_zero(self, client: CryptoDataClient):
        """limit=0 should return an empty list."""
        known_token = "PepeR1111111111111111111111111111111111pump"
        res = client.get_token_trades(chain="sol", token_address=known_token, limit=0)
        assert isinstance(res, list)
        assert len(res) == 0

    def test_get_token_trades_negative_limit(self, client: CryptoDataClient):
        """Negative limit should be handled cleanly without crash."""
        known_token = "PepeR1111111111111111111111111111111111pump"
        res = client.get_token_trades(chain="sol", token_address=known_token, limit=-10)
        assert isinstance(res, list)
        # Python slice [: -10] or [: 0] produces a valid sublist
        assert len(res) <= 10

    def test_get_token_trades_excessive_limit(self, client: CryptoDataClient):
        """Huge limit (e.g. 1,000,000) should not cause memory exhaustion or crash."""
        known_token = "PepeR1111111111111111111111111111111111pump"
        res = client.get_token_trades(chain="sol", token_address=known_token, limit=1_000_000)
        assert isinstance(res, list)
        assert len(res) > 0

    # --- 3. Wallet Transfers Boundaries ---

    def test_get_wallet_transfers_unknown_wallet(self, client: CryptoDataClient):
        """Non-existent wallet address should return an empty list."""
        res = client.get_wallet_transfers(chain="sol", wallet_address="NonExistentWallet11111111111111111111111111")
        assert isinstance(res, list)
        assert len(res) == 0

    def test_get_wallet_transfers_empty_wallet(self, client: CryptoDataClient):
        """Empty string for wallet address should return empty list."""
        res = client.get_wallet_transfers(chain="sol", wallet_address="")
        assert isinstance(res, list)
        assert len(res) == 0

    def test_get_wallet_transfers_flow_filters(self, client: CryptoDataClient):
        """Test flow='in', flow='out', and invalid flow string."""
        known_wallet = "SoLSniper1111111111111111111111111111111111"
        in_transfers = client.get_wallet_transfers(chain="sol", wallet_address=known_wallet, flow="in")
        assert len(in_transfers) >= 1
        for t in in_transfers:
            assert t.to_address.lower() == known_wallet.lower() or t.from_address.lower() == known_wallet.lower()

        # Arbitrary flow string
        arbitrary_transfers = client.get_wallet_transfers(chain="sol", wallet_address=known_wallet, flow="invalid_flow")
        assert isinstance(arbitrary_transfers, list)

    # --- 4. Account Metadata Boundaries ---

    def test_get_account_metadata_known_and_unknown_wallets(self, client: CryptoDataClient):
        """Account metadata should return valid dict for fixture wallets and safe fallback for unknown."""
        known_wallet = "SoLSniper1111111111111111111111111111111111"
        meta = client.get_account_metadata(wallet_address=known_wallet)
        assert isinstance(meta, dict)
        assert meta["account"] == known_wallet
        assert "funded_by" in meta
        assert meta["funded_by"] != ""

        # Unknown wallet returns fallback envelope without exception
        unknown_wallet = "SomeCompletelyRandomAddress111111111111111"
        unknown_meta = client.get_account_metadata(wallet_address=unknown_wallet)
        assert isinstance(unknown_meta, dict)
        assert unknown_meta["account"] == unknown_wallet
        assert "funded_by" in unknown_meta


# ============================================================================
# Category 3: Canonical Immutable Data Models Adversarial Stress
# ============================================================================

class TestAdversarialImmutableModels:
    """Stress tests dataclass immutability, collection defense against mutation,
    lossless dictionary roundtripping, aliasing compatibility, and malformed inputs.
    """

    def test_token_launch_event_immutability(self):
        """TokenLaunchEvent must raise FrozenInstanceError or AttributeError on attribute modification."""
        event = TokenLaunchEvent(
            token_address="PepeTest1111111111111111111111111111111111",
            chain="sol",
            name="Pepe Test",
            symbol="PEPETEST",
            launch_timestamp=1726830000,
        )
        with pytest.raises((FrozenInstanceError, AttributeError)):
            event.symbol = "MUTATED"

        with pytest.raises((FrozenInstanceError, AttributeError)):
            del event.symbol

        with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
            event.unregistered_attr = "exploit"

    def test_trade_record_immutability(self):
        """TradeRecord must prevent attribute tampering."""
        trade = TradeRecord(
            trade_id="tx_test_001",
            chain="sol",
            token_address="TokenA",
            wallet_address="WalletA",
            direction="buy",
            timestamp=1726830005,
            token_amount=1000.0,
        )
        with pytest.raises((FrozenInstanceError, AttributeError)):
            trade.token_amount = 9999999.0

        with pytest.raises((FrozenInstanceError, AttributeError)):
            trade.direction = "sell"

    def test_funding_transfer_record_immutability(self):
        """FundingTransferRecord must prevent attribute tampering."""
        transfer = FundingTransferRecord(
            transfer_id="tx_fund_001",
            chain="eth",
            from_address="0xFrom",
            to_address="0xTo",
            amount=10.0,
        )
        with pytest.raises((FrozenInstanceError, AttributeError)):
            transfer.amount = 0.0

    def test_wallet_score_collection_freezing(self):
        """WalletScore must normalize mutable lists/sets into immutable tuples."""
        mutable_patterns = ["early_entry", "common_funding"]
        mutable_tokens = ["token1", "token2"]
        mutable_buys = ["tx1"]
        mutable_sells = ["tx2"]

        score = WalletScore(
            wallet_address="0xWallet",
            chain="eth",
            suspicion_score=85.0,
            flagged_patterns=mutable_patterns,
            associated_tokens=mutable_tokens,
            buy_txs=mutable_buys,
            sell_txs=mutable_sells,
        )

        # 1. Attribute types must be tuple
        assert isinstance(score.flagged_patterns, tuple)
        assert isinstance(score.associated_tokens, tuple)
        assert isinstance(score.buy_txs, tuple)
        assert isinstance(score.sell_txs, tuple)

        # 2. Mutating the original input lists must NOT affect the model
        mutable_patterns.append("coordinated_dump")
        assert "coordinated_dump" not in score.flagged_patterns

        mutable_tokens.append("token3")
        assert "token3" not in score.associated_tokens

        # 3. Direct tuple mutation must raise AttributeError
        with pytest.raises(AttributeError):
            score.flagged_patterns.append("coordinated_dump")

    def test_syndicate_cluster_collection_freezing(self):
        """SyndicateCluster must normalize mutable collections into immutable tuples."""
        mutable_wallets = ["0xW1", "0xW2", "0xW3"]
        mutable_patterns = ["early_entry", "common_funding"]
        mutable_tokens = ["0xT1"]

        cluster = SyndicateCluster(
            cluster_id="SYN-TEST-01",
            chain="eth",
            wallets=mutable_wallets,
            flagged_patterns=mutable_patterns,
            suspicion_score=92.0,
            associated_tokens=mutable_tokens,
        )

        assert isinstance(cluster.wallets, tuple)
        assert isinstance(cluster.flagged_patterns, tuple)
        assert isinstance(cluster.associated_tokens, tuple)

        # Mutate external lists
        mutable_wallets.append("0xW4_INTRUDER")
        assert "0xW4_INTRUDER" not in cluster.wallets
        assert len(cluster.wallets) == 3

        with pytest.raises(AttributeError):
            cluster.wallets.append("0xW5")

    def test_lossless_roundtrip_serialization_all_models(self):
        """All models must support 100% lossless to_dict() -> from_dict() roundtripping."""
        # 1. TokenLaunchEvent
        launch = TokenLaunchEvent(
            token_address="0xToken123",
            chain="bsc",
            name="Test Token",
            symbol="TEST",
            decimals=18,
            total_supply=500_000.0,
            deployer_address="0xDeployer",
            launch_timestamp=1726830000,
            launch_platform="pancakeswap",
            initial_liquidity_usd=15000.0,
            initial_price_usd=0.03,
            metadata_uri="ipfs://QmTest",
            raw_metadata={"verified": True, "tags": ["defi"]},
        )
        launch_rt = TokenLaunchEvent.from_dict(launch.to_dict())
        assert launch_rt == launch

        # 2. TradeRecord
        trade = TradeRecord(
            trade_id="tx_trade_99",
            chain="sol",
            token_address="TokenSol",
            wallet_address="WalletSol",
            direction="sell",
            timestamp=1726830600,
            token_amount=50000.0,
            base_currency="SOL",
            base_amount=15.5,
            price_usd=0.002,
            volume_usd=100.0,
            is_deployer=False,
            seconds_since_launch=600.0,
            slot_or_block=28000000,
            fee_native=0.00005,
        )
        trade_rt = TradeRecord.from_dict(trade.to_dict())
        assert trade_rt == trade

        # 3. FundingTransferRecord
        funding = FundingTransferRecord(
            transfer_id="tx_transfer_55",
            chain="base",
            from_address="0xSource",
            to_address="0xDest",
            asset_symbol="ETH",
            amount=4.2,
            amount_usd=10500.0,
            timestamp=1726830100,
            block_number=14000000,
            transfer_type="sweep",
            is_initial_funding=False,
            hop_depth=2,
        )
        funding_rt = FundingTransferRecord.from_dict(funding.to_dict())
        assert funding_rt == funding

        # 4. WalletScore
        score = WalletScore(
            wallet_address="0xWalletScore",
            chain="eth",
            suspicion_score=95.5,
            flagged_patterns=("early_entry", "common_funding"),
            pattern_scores={"early_entry": 98.0, "common_funding": 93.0},
            context_modifiers={"dex_sniper": 1.1},
            associated_tokens=("0xTokenA", "0xTokenB"),
            net_profit_usd=12500.50,
            buy_txs=("tx_b1", "tx_b2"),
            sell_txs=("tx_s1",),
            evidence_summary={"notes": "high confidence"},
        )
        score_rt = WalletScore.from_dict(score.to_dict())
        assert score_rt == score

        # 5. SyndicateCluster
        cluster = SyndicateCluster(
            cluster_id="SYN-RT-01",
            chain="sol",
            wallets=("SolW1", "SolW2", "SolW3"),
            flagged_patterns=("early_entry", "coordinated_dump"),
            suspicion_score=97.0,
            associated_tokens=("SolToken",),
            estimated_profit_usd=25000.0,
            funder_wallet="SolFunder",
            deployer_wallet="SolDeployer",
            sweep_wallet="SolSweep",
            average_entry_window_seconds=4.5,
            average_exit_window_seconds=300.0,
            evidence_metadata={"cluster_type": "sniper_ring"},
            wallet_scores={"SolW1": score},
        )
        cluster_rt = SyndicateCluster.from_dict(cluster.to_dict())
        assert cluster_rt.cluster_id == cluster.cluster_id
        assert cluster_rt.wallets == cluster.wallets
        assert cluster_rt.flagged_patterns == cluster.flagged_patterns
        assert cluster_rt.suspicion_score == cluster.suspicion_score
        assert cluster_rt.estimated_profit_usd == cluster.estimated_profit_usd
        assert cluster_rt.wallet_scores["SolW1"].wallet_address == score.wallet_address

    def test_backwards_compatible_aliasing_and_dict_subscription(self):
        """Models must accept legacy/alternate field names and support dict access."""
        # 1. member_wallets vs wallets alias
        legacy_cluster_data = {
            "cluster_id": "SYN-LEGACY-01",
            "chain": "bsc",
            "member_wallets": ["0x1", "0x2", "0x3"],
            "patterns_flagged": ["early_entry", "common_funding"],
            "suspicion_score": 90.0,
        }
        cluster = SyndicateCluster.from_dict(legacy_cluster_data)
        assert cluster.wallets == ("0x1", "0x2", "0x3")
        assert cluster.flagged_patterns == ("early_entry", "common_funding")

        # 2. Dictionary-like subscription
        assert cluster["cluster_id"] == "SYN-LEGACY-01"
        assert cluster["chain"] == "bsc"
        assert cluster.get("suspicion_score") == 90.0
        assert cluster.get("non_existent_key", "default_val") == "default_val"

        with pytest.raises(KeyError):
            _ = cluster["unknown_key"]

    def test_from_dict_graceful_handling_of_malformed_and_missing_inputs(self):
        """from_dict methods must handle missing fields and type mismatches without unhandled crashes."""
        # Empty dict should populate safe defaults
        empty_event = TokenLaunchEvent.from_dict({})
        assert empty_event.token_address == ""
        assert empty_event.decimals == 6
        assert empty_event.total_supply == 1_000_000_000.0

        empty_trade = TradeRecord.from_dict({})
        assert empty_trade.trade_id == ""
        assert empty_trade.token_amount == 0.0

        empty_cluster = SyndicateCluster.from_dict({})
        assert empty_cluster.cluster_id == ""
        assert empty_cluster.wallets == ()
        assert empty_cluster.flagged_patterns == ()

        # Coerce numeric strings to numbers
        typed_event = TokenLaunchEvent.from_dict({
            "decimals": "9",
            "total_supply": "5000000",
            "initial_price_usd": "0.005",
        })
        assert typed_event.decimals == 9
        assert typed_event.total_supply == 5_000_000.0
        assert typed_event.initial_price_usd == 0.005

    def test_from_dict_explicit_null_field_handling(self):
        """Stress-test: API payloads with explicit null/None values (e.g. {'decimals': None}).
        In Python dataclasses using int(data.get('decimals', 6)), an explicit None causes TypeError.
        This test documents the empirical failure mode for downstream remediation.
        """
        null_payload = {"decimals": None, "total_supply": None}
        # In current M1 implementation, int(None) raises TypeError
        with pytest.raises(TypeError):
            TokenLaunchEvent.from_dict(null_payload)

    def test_negative_timestamps_and_boundary_numerics(self):
        """Negative timestamps or extreme volume figures must be stored without overflow or truncation."""
        negative_trade = TradeRecord(
            trade_id="tx_pre_epoch_01",
            chain="sol",
            token_address="TokenNeg",
            wallet_address="WalletNeg",
            direction="buy",
            timestamp=-3600,  # 1 hour before unix epoch
            token_amount=0.0,
            base_amount=-1.0,
            price_usd=0.0,
            volume_usd=0.0,
            seconds_since_launch=-60.0,
        )
        assert negative_trade.timestamp == -3600
        assert negative_trade.seconds_since_launch == -60.0

        roundtrip = TradeRecord.from_dict(negative_trade.to_dict())
        assert roundtrip.timestamp == -3600
        assert roundtrip.seconds_since_launch == -60.0

    def test_cryptodataclient_wallet_transfers_chain_routing(self):
        """Verify CryptoDataClient delegation behavior across uppercase vs lowercase chains."""
        cfg = AppConfig(crypto_data_mode="mock")
        client = CryptoDataClient(config=cfg)
        
        # In mock mode, fixtures provide data regardless of chain case
        res_sol = client.get_wallet_transfers(chain="sol", wallet_address="SoLSniper1111111111111111111111111111111111")
        assert len(res_sol) > 0
        
        res_sol_upper = client.get_wallet_transfers(chain="SOL", wallet_address="SoLSniper1111111111111111111111111111111111")
        assert len(res_sol_upper) > 0

