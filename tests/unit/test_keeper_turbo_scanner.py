"""Unit tests for Milestone 23 Turbo Multi-Source Scanner & Forward-Tracing Wallet Expansion.

Validates:
1. Deployer qualification filtering (>= $5 USD profit).
2. Round-Robin batch rotation across 5 batches.
3. Solscan-based Pump.fun token discovery and GMGN enrichment.
4. Forward-tracing wallet expansion from known deployers.
5. Keeper status reporting.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from crypto_syndicate.keeper import SyndicateKeeper


@pytest.fixture
def temp_turbo_env():
    """Create isolated temporary files for identities, live tokens, and wallets."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        identities_file = tmp_path / "syndicate_identities.json"
        live_tokens_file = tmp_path / "live_tokens.json"
        wallets_csv_file = tmp_path / "wallets.csv"

        # Seed identities with mock deployers with varying profit
        identities = {
            "SYND-0001": {
                "syndicate_id": "SYND-0001",
                "known_wallets": ["DEP_ACTIVE_1_ABCDEFGHIJKLMN1234567890", "DEP_LOW_PROFIT_ABCDEFGHIJKLMN1234567890"],
                "primary_wallets": ["DEP_ACTIVE_1_ABCDEFGHIJKLMN1234567890"],
                "total_profit_usd": 15000.0,
                "created_tokens": [
                    {
                        "mint": "TokenMint111111111111111111111111111111111",
                        "symbol": "TOKEN1",
                        "creator": "DEP_ACTIVE_1_ABCDEFGHIJKLMN1234567890",
                        "deployer": "DEP_ACTIVE_1_ABCDEFGHIJKLMN1234567890",
                        "ath_market_cap_usd": 50000.0,
                        "launch_timestamp": 1727700000,
                    }
                ],
            }
        }
        with open(identities_file, "w", encoding="utf-8") as f:
            json.dump(identities, f, indent=2)

        with open(live_tokens_file, "w", encoding="utf-8") as f:
            json.dump([], f)

        keeper = SyndicateKeeper(
            api_key="test_gmgn_key",
            solscan_jwt="test_solscan_jwt",
            identities_file=identities_file,
            live_tokens_file=live_tokens_file,
            wallets_csv_file=wallets_csv_file,
            mock_mode=True,
            batch_count=5,
            min_profit_usd=5.0,
        )

        yield keeper, identities_file, live_tokens_file, wallets_csv_file


def test_eligible_deployer_filtering(temp_turbo_env):
    """Test that deployers with < $5 profit are excluded from the active sweep list."""
    keeper, _, _, _ = temp_turbo_env
    eligible = keeper._get_eligible_deployers()
    assert isinstance(eligible, list)
    for dep in eligible:
        assert float(dep.get("profit_usd", 0.0)) >= 5.0
        assert not dep.get("address", "").startswith("Whale")


def test_round_robin_batch_rotation(temp_turbo_env):
    """Test that batch_index rotates cyclically 0 -> 1 -> 2 -> 3 -> 4 -> 0."""
    keeper, _, _, _ = temp_turbo_env
    assert keeper._batch_index == 0

    with patch.object(keeper, "_get_eligible_deployers") as mock_eligible:
        mock_eligible.return_value = [
            {"address": f"DEP_{i}_111111111111111111111111111111", "profit_usd": 50.0}
            for i in range(15)
        ]
        with patch("urllib.request.urlopen"):
            # Call batch 0
            keeper.scan_deployer_batch()
            assert keeper._batch_index == 1

            # Call batch 1
            keeper.scan_deployer_batch()
            assert keeper._batch_index == 2

            # Advance through remaining batches
            keeper.scan_deployer_batch()
            assert keeper._batch_index == 3
            keeper.scan_deployer_batch()
            assert keeper._batch_index == 4
            keeper.scan_deployer_batch()
            assert keeper._batch_index == 0  # Wrapped around


def test_solscan_new_tokens_discovery(temp_turbo_env):
    """Test discovering fresh Pump.fun tokens via Solscan latest endpoint."""
    keeper, _, live_tokens_file, _ = temp_turbo_env

    mock_solscan_payload = {
        "data": [
            {
                "address": "FreshSolscanMint11111111111111111111111111",
                "name": "Solscan Fresh Meme",
                "symbol": "FRESH",
                "created_time": 1727750000,
            }
        ]
    }

    mock_gmgn_info = {
        "token": "FreshSolscanMint11111111111111111111111111",
        "address": "FreshSolscanMint11111111111111111111111111",
        "symbol": "FRESH",
        "name": "Solscan Fresh Meme",
        "ath_market_cap_usd": 25000.0,
        "fund_from": "Binance",
        "holder_count": 80,
        "deployers": ["DEP_SOLSCAN_DISCOVERY_111111111111111111"],
    }

    def fake_solscan_urlopen(req, timeout=6):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        resp = MagicMock()
        if "solscan.io" in url:
            resp.read.return_value = json.dumps(mock_solscan_payload).encode("utf-8")
        else:
            resp.read.return_value = json.dumps({"result": []}).encode("utf-8")
        resp.__enter__.return_value = resp
        return resp

    with patch("urllib.request.urlopen", side_effect=fake_solscan_urlopen):
        with patch.object(keeper, "fetch_gmgn_token_info", return_value=mock_gmgn_info):
            newly_ingested = keeper.scan_solscan_new_tokens()
            assert len(newly_ingested) == 1
            assert newly_ingested[0]["symbol"] == "FRESH"
            assert keeper._session_discovered_tokens == 1


def test_forward_tracing_wallet_expansion(temp_turbo_env):
    """Test forward-tracing: deployer funds a new wallet which has DEX pairs."""
    keeper, _, _, _ = temp_turbo_env

    mock_transfers_payload = {
        "data": [
            {
                "to_address": "NEW_FUNDED_WALLET_1111111111111111111111111111",
                "amount": 2_000_000_000,  # 2.0 SOL
            }
        ]
    }

    mock_pairs_payload = {
        "pairs": [
            {
                "baseToken": {
                    "address": "ForwardTracedMint1111111111111111111111111111",
                    "symbol": "FWDTRACED",
                }
            }
        ]
    }

    with patch.object(keeper, "_get_eligible_deployers") as mock_eligible:
        mock_eligible.return_value = [
            {"address": "DEP_SOURCE_111111111111111111111111111111", "syndicate_id": "SYND-0001", "profit_usd": 500.0}
        ]

        def fake_urlopen(req, timeout=5):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            resp = MagicMock()
            if "solscan.io" in url:
                resp.read.return_value = json.dumps(mock_transfers_payload).encode("utf-8")
            else:
                resp.read.return_value = json.dumps(mock_pairs_payload).encode("utf-8")
            resp.__enter__.return_value = resp
            return resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            with patch.object(keeper, "fetch_gmgn_token_info") as mock_gmgn:
                mock_gmgn.return_value = {
                    "address": "ForwardTracedMint1111111111111111111111111111",
                    "symbol": "FWDTRACED",
                    "name": "Forward Traced Token",
                    "ath_market_cap_usd": 15000.0,
                }
                res = keeper.expand_syndicate_network()
                assert res["new_wallets"] >= 1
                assert res["new_deployers"] >= 1


def test_keeper_status_output(temp_turbo_env):
    """Test get_keeper_status returns expected telemetry fields."""
    keeper, _, _, _ = temp_turbo_env
    status = keeper.get_keeper_status()
    assert "status" in status
    assert "batch_index" in status
    assert "batch_count" in status
    assert "cycle_count" in status
    assert "session_discovered_tokens" in status
    assert "session_discovered_wallets" in status
    assert "min_profit_filter_usd" in status
    assert status["batch_count"] == 5
    assert status["min_profit_filter_usd"] == 5.0
