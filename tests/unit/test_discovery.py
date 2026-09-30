"""Unit tests for DiscoveryPipeline (M2).

All tests use mock_mode=True with offline fixtures.
"""

import pytest
from unittest.mock import MagicMock

from crypto_syndicate.discovery import (
    DiscoveryPipeline,
    EARLY_BUY_WINDOW_SECONDS,
    DUMP_WINDOW_SECONDS,
    PatternType,
)
from crypto_syndicate.api.models import (
    TokenLaunchEvent,
    TradeRecord,
    FundingTransferRecord,
)


@pytest.fixture
def mock_pipeline():
    """Create a DiscoveryPipeline instance in mock mode."""
    return DiscoveryPipeline(mock_mode=True)


def test_fetch_recent_launches_returns_list(mock_pipeline):
    """Test that fetch_recent_launches returns a list of TokenLaunchEvent instances."""
    launches = mock_pipeline.fetch_recent_launches(chain="sol")
    assert isinstance(launches, list)
    assert len(launches) > 0
    for launch in launches:
        assert isinstance(launch, TokenLaunchEvent)
        assert launch.token_address
        assert launch.chain == "sol"


def test_get_early_buyers_filters_by_window(mock_pipeline):
    """Test that only buyers within the 300s window are captured."""
    launch_time = 1_700_000_000
    mock_trades = [
        TradeRecord(
            trade_id="tx1",
            slot_or_block=1,
            timestamp=launch_time + 100,  # inside 300s window
            wallet_address="wallet_early",
            token_address="token_1",
            chain="sol",
            direction="buy",
            token_amount=1000.0,
            volume_usd=500.0,
        ),
        TradeRecord(
            trade_id="tx2",
            slot_or_block=2,
            timestamp=launch_time + 500,  # outside 300s window
            wallet_address="wallet_late",
            token_address="token_1",
            chain="sol",
            direction="buy",
            token_amount=1000.0,
            volume_usd=500.0,
        ),
        TradeRecord(
            trade_id="tx3",
            slot_or_block=3,
            timestamp=launch_time + 50,  # inside 300s window, but a sell
            wallet_address="wallet_seller",
            token_address="token_1",
            chain="sol",
            direction="sell",
            token_amount=500.0,
            volume_usd=250.0,
        ),
    ]
    mock_pipeline.gmgn.get_token_trades = MagicMock(return_value=mock_trades)

    buyers = mock_pipeline.get_early_buyers(token="token_1", chain="sol", launch_time=launch_time)
    buyer_wallets = [b["wallet"] for b in buyers]

    assert "wallet_early" in buyer_wallets
    assert "wallet_late" not in buyer_wallets
    assert "wallet_seller" not in buyer_wallets


def test_get_early_buyers_deduplicates_wallets(mock_pipeline):
    """Test that multiple early buys by the same wallet are deduplicated."""
    launch_time = 1_700_000_000
    mock_trades = [
        TradeRecord(
            trade_id="tx1",
            slot_or_block=1,
            timestamp=launch_time + 50,
            wallet_address="repeat_buyer",
            token_address="token_1",
            chain="sol",
            direction="buy",
            token_amount=1000.0,
            volume_usd=500.0,
        ),
        TradeRecord(
            trade_id="tx2",
            slot_or_block=2,
            timestamp=launch_time + 120,
            wallet_address="repeat_buyer",
            token_address="token_1",
            chain="sol",
            direction="buy",
            token_amount=2000.0,
            volume_usd=1000.0,
        ),
    ]
    mock_pipeline.gmgn.get_token_trades = MagicMock(return_value=mock_trades)

    buyers = mock_pipeline.get_early_buyers(token="token_1", chain="sol", launch_time=launch_time)
    assert len(buyers) == 1
    assert buyers[0]["wallet"] == "repeat_buyer"
    assert buyers[0]["buy_time"] == launch_time + 50


def test_detect_coordinated_dumps_sliding_window(mock_pipeline):
    """Test that detect_coordinated_dumps detects overlapping 10-minute sell windows."""
    base_time = 1_700_001_000
    mock_trades = [
        TradeRecord(
            trade_id="tx1",
            slot_or_block=10,
            timestamp=base_time + 50,
            wallet_address="dump_wallet_1",
            token_address="token_dump",
            chain="sol",
            direction="sell",
            token_amount=500.0,
            volume_usd=2500.0,
        ),
        TradeRecord(
            trade_id="tx2",
            slot_or_block=11,
            timestamp=base_time + 200,  # within 600s
            wallet_address="dump_wallet_2",
            token_address="token_dump",
            chain="sol",
            direction="sell",
            token_amount=600.0,
            volume_usd=3000.0,
        ),
        TradeRecord(
            trade_id="tx3",
            slot_or_block=12,
            timestamp=base_time + 2000,  # isolated sell > 600s later
            wallet_address="isolated_seller",
            token_address="token_dump",
            chain="sol",
            direction="sell",
            token_amount=100.0,
            volume_usd=500.0,
        ),
    ]
    mock_pipeline.gmgn.get_token_trades = MagicMock(return_value=mock_trades)

    dumps = mock_pipeline.detect_coordinated_dumps(
        token="token_dump",
        wallets=["dump_wallet_1", "dump_wallet_2", "isolated_seller"],
        chain="sol",
    )
    assert len(dumps) >= 1
    involved = dumps[0]["wallets_involved"]
    assert "dump_wallet_1" in involved
    assert "dump_wallet_2" in involved
    assert "isolated_seller" not in involved


def test_score_wallet_single_pattern(mock_pipeline):
    """Test that a wallet flagged with a single pattern receives score 20."""
    score = mock_pipeline.score_wallet(
        wallet_data={"cluster_size": 1},
        patterns=[PatternType.EARLY_ENTRY.value],
    )
    assert score == 20.0


def test_score_wallet_all_four_patterns(mock_pipeline):
    """Test that all 4 patterns earn 80 points + 10 bonus = 90 points."""
    all_patterns = [p.value for p in PatternType]
    score = mock_pipeline.score_wallet(
        wallet_data={"cluster_size": 1},
        patterns=all_patterns,
    )
    assert score == 90.0


def test_score_wallet_capped_at_100(mock_pipeline):
    """Test that score never exceeds 100 even with all bonuses applied."""
    all_patterns = [p.value for p in PatternType]
    score = mock_pipeline.score_wallet(
        wallet_data={"cluster_size": 25},  # size 10+ bonus (+10) + 4 patterns (80+10) = 100
        patterns=all_patterns,
    )
    assert score == 100.0

    # Ensure even arbitrary higher size doesn't breach 100
    score_large = mock_pipeline.score_wallet(
        wallet_data={"cluster_size": 100},
        patterns=all_patterns,
    )
    assert score_large == 100.0


def test_run_pipeline_mock_returns_wallets(mock_pipeline):
    """Test that full pipeline execution in mock mode returns candidate wallets (>0)."""
    wallets = mock_pipeline.run_pipeline(chains=["sol"])
    assert isinstance(wallets, list)
    assert len(wallets) > 0
    for w in wallets:
        assert "wallet_address" in w
        assert "chain" in w
        assert "patterns_flagged" in w


def test_run_pipeline_populates_funding_relationships(mock_pipeline):
    """Test that run_pipeline populates the funding_relationships attribute."""
    mock_pipeline.run_pipeline(chains=["sol"])
    rels = mock_pipeline.funding_relationships
    assert isinstance(rels, list)
    assert len(rels) > 0
    for rel in rels:
        assert "funder" in rel
        assert "funded" in rel
        assert rel["funder"] != rel["funded"]


def test_run_pipeline_all_wallets_have_suspicion_score(mock_pipeline):
    """Test that every discovered wallet has a valid suspicion_score >= 0 and <= 100."""
    wallets = mock_pipeline.run_pipeline(chains=["sol"])
    for w in wallets:
        assert "suspicion_score" in w
        assert isinstance(w["suspicion_score"], (int, float))
        assert 0.0 <= w["suspicion_score"] <= 100.0


def test_get_deployer_fallback(mock_pipeline):
    """Test that get_deployer resolves deployer via security info or fallback."""
    deployer = mock_pipeline.get_deployer(token="test_token", chain="sol")
    assert isinstance(deployer, str)


def test_score_cluster_method(mock_pipeline):
    """Test that score_cluster returns a bounded score for clusters."""
    score = mock_pipeline.score_cluster(
        cluster_wallets=["w1", "w2", "w3", "w4", "w5"],
        patterns=["early_entry", "common_funding"],
    )
    assert isinstance(score, float)
    assert 0.0 <= score <= 100.0
