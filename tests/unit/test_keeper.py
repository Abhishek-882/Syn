"""Unit tests for Autonomous Syndicate Keeper, TimeSync, and Historical Token Track Record."""

import json
from pathlib import Path
import time
import pytest
from unittest.mock import MagicMock, patch

from crypto_syndicate.keeper import SyndicateKeeper, TimeSync, get_syndicate_keeper
from crypto_syndicate.ground_truth_loader import GroundTruthLoader, format_usd, format_relative_time


def test_time_sync_calibration():
    """Verify TimeSync singleton calculates drift and now() returns calibrated time."""
    sync = TimeSync.get_instance()
    assert sync is not None
    ts = sync.now()
    assert isinstance(ts, int)
    assert ts > 1700000000  # Valid modern unix epoch
    # Drift should be a finite float
    assert isinstance(sync.drift_seconds, float)


def test_format_helpers():
    """Verify USD and relative time compact formatters."""
    assert format_usd(1454467.20) == "$1.45M"
    assert format_usd(49880.00) == "$49.9K"
    assert format_usd(12.50) == "$12.50"

    assert format_relative_time(30) == "just now"
    assert format_relative_time(300) == "5m ago"
    assert format_relative_time(7200) == "2h ago"
    assert format_relative_time(172800) == "2d ago"


def test_keeper_mock_token_info():
    """Verify fetch_gmgn_token_info extracts correct schema in mock mode."""
    keeper = SyndicateKeeper(mock_mode=True)
    info = keeper.fetch_gmgn_token_info("BM2k8mJUbMthHoioykyUm2NjMrXvLBYhoXruwYLpump")
    assert info is not None
    assert info["symbol"] == "LEVERAGE"
    assert info["ath_market_cap_usd"] == 1454467.20
    assert info["current_market_cap_usd"] == 12999.80
    assert "DFZ497f4YTS4RXjPeKPuECHXSmoVnvoFMpmErnZK61cc" in info["deployers"]
    assert "dexscreener.com/solana/" in info["dex_url"]
    assert "gmgn.ai/sol/token/" in info["gmgn_url"]


def test_keeper_ingest_token_and_next_syndicate_id(tmp_path):
    """Verify ingest_token persists to identities and live tokens file."""
    identities_file = tmp_path / "syndicate_identities.json"
    live_tokens_file = tmp_path / "live_tokens.json"
    wallets_csv = tmp_path / "wallets.csv"

    # Seed identities with SYND-0001
    identities_file.write_text(json.dumps({"SYND-0001": {"identity_id": "SYND-0001"}}), encoding="utf-8")
    live_tokens_file.write_text("[]", encoding="utf-8")

    keeper = SyndicateKeeper(
        identities_file=identities_file,
        live_tokens_file=live_tokens_file,
        wallets_csv_file=wallets_csv,
        mock_mode=True,
    )

    token_info = keeper.fetch_gmgn_token_info("BM2k8mJUbMthHoioykyUm2NjMrXvLBYhoXruwYLpump")
    ingested = keeper.ingest_token(token_info)

    assert ingested["syndicates"] == ["SYND-0002"]  # next after 0001
    assert live_tokens_file.exists()
    saved_tokens = json.loads(live_tokens_file.read_text(encoding="utf-8"))
    assert len(saved_tokens) == 1
    assert saved_tokens[0]["symbol"] == "LEVERAGE"
    assert saved_tokens[0]["ath_market_cap_usd"] == 1454467.20


def test_ground_truth_token_history_ranking():
    """Verify get_syndicate_token_history returns tokens strictly sorted by recency."""
    loader = GroundTruthLoader()
    history = loader.get_syndicate_token_history()

    assert len(history) >= 12
    # Verify strict descending monotonic order of launch_timestamp
    for i in range(len(history) - 1):
        assert history[i]["launch_timestamp"] >= history[i + 1]["launch_timestamp"]

    # Verify Rank 1 is the most recent
    assert history[0]["rank"] == 1
    assert "symbol" in history[0] and len(history[0]["symbol"]) > 0

    # Verify LEVERAGE exists in history with full ground truth metrics
    leverage = next((t for t in history if t.get("symbol") == "LEVERAGE"), None)
    assert leverage is not None
    assert leverage["ath_market_cap_usd"] == 1454467.20
    assert leverage["ath_market_cap_formatted"] == "$1.45M"
    assert "dex_url" in leverage and "gmgn_url" in leverage


def test_keeper_cycle_execution():
    """Verify run_keeper_cycle executes without errors."""
    keeper = get_syndicate_keeper()
    res = keeper.run_keeper_cycle()
    assert res["status"] == "success"
    assert "time_drift_seconds" in res
    assert res["refreshed_tokens_count"] >= 0
    assert "new_tokens_count" in res
