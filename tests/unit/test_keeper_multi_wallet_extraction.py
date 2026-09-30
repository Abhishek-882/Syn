"""Unit & Integration Tests for Autonomous Keeper Multi-Wallet Extraction & Live Scanning."""

import json
import os
import tempfile
from pathlib import Path
import pytest

from crypto_syndicate.keeper import SyndicateKeeper, TimeSync


@pytest.fixture
def temp_keeper_env(tmp_path):
    identities_file = tmp_path / "syndicate_identities.json"
    live_tokens_file = tmp_path / "live_tokens.json"
    wallets_csv_file = tmp_path / "wallets.csv"

    # Seed initial identities
    identities_file.write_text(json.dumps({
        "SYND-0001": {
            "identity_id": "SYND-0001",
            "syndicate_id": "SYND-0001",
            "alias": "Syndicate SYND-0001",
            "primary_wallets": ["Deployer111111111111111111111111111111111111"],
            "known_wallets": ["Deployer111111111111111111111111111111111111"],
            "historical_tokens": ["Token1111111111111111111111111111111111111"],
            "behavior_profile": {
                "cluster_id": "cluster_1",
                "token_address": "Token1111111111111111111111111111111111111",
                "deployer_wallet": "Deployer111111111111111111111111111111111111",
                "wallet_count": 1,
            },
            "total_profit_usd": 10000.0,
        }
    }), encoding="utf-8")

    keeper = SyndicateKeeper(
        identities_file=identities_file,
        live_tokens_file=live_tokens_file,
        wallets_csv_file=wallets_csv_file,
        mock_mode=True,
    )
    return keeper, identities_file, live_tokens_file, wallets_csv_file


def test_multi_wallet_auto_extraction(temp_keeper_env):
    keeper, identities_file, live_tokens_file, wallets_csv_file = temp_keeper_env

    mock_token_info = {
        "token": "4xjvmiKa5vzkQtaNrTV17v8PFU5mP69Hf1Kq5A9wpump",
        "symbol": "ZLONG",
        "name": "ZLONG Token",
        "deployers": ["69aiAKU3uJMxMLRkUEGFNt6nQ43PiVimE4ZbErJ7VSM1"],
        "fund_from": "Binance",
        "ath_market_cap_usd": 68900.0,
        "current_market_cap_usd": 3000.0,
        "raw_data": {
            "dev": {
                "creator_address": "69aiAKU3uJMxMLRkUEGFNt6nQ43PiVimE4ZbErJ7VSM1",
                "fund_from": "Binance",
                "twitter_name_change_history": [
                    {"address": "NBYi7bDyC13d7sCRK9BoaB43cLL32iL5uyVUHmcUe2m"}
                ]
            }
        }
    }

    wallets = keeper.extract_syndicate_wallets_for_token(mock_token_info, "SYND-0001")
    assert len(wallets) >= 6, f"Expected at least 6 extracted syndicate wallets, got {len(wallets)}"

    roles = {w["role"] for w in wallets}
    assert "DEPLOYER" in roles, "Expected DEPLOYER role"
    assert "FUNDER" in roles, "Expected FUNDER role"
    assert "BUNDLER" in roles, "Expected BUNDLER role"
    assert "SNIPER" in roles, "Expected SNIPER role"
    assert "SYNDICATE_CONTRACT" in roles, "Expected SYNDICATE_CONTRACT role"

    # Ingest token
    ingested = keeper.ingest_token(mock_token_info, syndicate_id="SYND-0001")
    assert ingested["token"] == "4xjvmiKa5vzkQtaNrTV17v8PFU5mP69Hf1Kq5A9wpump"

    # Verify identities file updated with multi-wallet network
    with open(identities_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    synd = data["SYND-0001"]
    assert len(synd["known_wallets"]) >= 6
    assert synd["behavior_profile"]["wallet_count"] >= 6


def test_time_sync_calibration():
    sync = TimeSync.get_instance()
    drift = sync.calibrate()
    assert isinstance(drift, float)
    now_ts = sync.now()
    assert now_ts > 1700000000


def test_scan_watched_deployers(temp_keeper_env):
    keeper, _, _, _ = temp_keeper_env
    deltas = keeper.scan_watched_deployers()
    assert isinstance(deltas, list)


def test_scan_live_launches(temp_keeper_env):
    keeper, _, _, _ = temp_keeper_env
    deltas = keeper.scan_live_launches()
    assert isinstance(deltas, list)
