"""Unit tests for LiveSyndicateScanner and 4D Temporal State Engine."""

import json
from pathlib import Path
import tempfile
import pytest

from crypto_syndicate.scanner import LiveSyndicateScanner


class TestLiveSyndicateScanner:
    """Test suite verifying the live scanner and 4D temporal state generation."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    def test_scanner_initialization(self, temp_dir):
        scanner = LiveSyndicateScanner(output_dir=str(temp_dir), mock_mode=True)
        assert scanner.output_dir == temp_dir
        assert scanner.mock_mode is True
        assert scanner.state_3d_file == temp_dir / "syndicate_3d_state.json"
        assert scanner.alerts_file == temp_dir / "live_alerts.json"

    def test_fetch_trending_tokens_mock(self, temp_dir):
        scanner = LiveSyndicateScanner(output_dir=str(temp_dir), mock_mode=True)
        tokens = scanner.fetch_trending_tokens(chain="sol", limit=5)
        assert len(tokens) >= 3
        for t in tokens:
            assert "address" in t
            assert "symbol" in t
            assert "bundler_rate" in t
            assert "bot_degen_rate" in t

    def test_scan_token_lifecycle(self, temp_dir):
        scanner = LiveSyndicateScanner(output_dir=str(temp_dir), mock_mode=True)
        token_info = {
            "address": "4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX",
            "symbol": "BELUGA",
            "creator": "8p7Z2M9tq4F1kL5n6uR8vX7yT9wQ2pM3kL4n5uR6vX7y",
            "creation_timestamp": 1726830000,
            "bundler_rate": 0.5153,
            "bot_degen_rate": 0.6669,
            "liquidity": 18500.0,
        }
        res = scanner.scan_token(token_info)
        assert res is not None
        assert res["identity_id"].startswith("SYND-")
        assert res["token_symbol"] == "BELUGA"
        assert len(res["wallets"]) >= 2
        assert res["behavior_mode"] in ("flash", "sustained")
        assert res["bundler_rate"] == 0.5153
        assert res["confidence_score"] >= 0.60

        # Verify alert appended
        assert scanner.alerts_file.exists()
        lines = scanner.alerts_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) >= 1
        last_alert = json.loads(lines[-1])
        assert last_alert["identity_id"] == res["identity_id"]

    def test_generate_4d_temporal_state_schema(self, temp_dir):
        scanner = LiveSyndicateScanner(output_dir=str(temp_dir), mock_mode=True)
        token_info = {
            "address": "4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX",
            "symbol": "BELUGA",
            "bundler_rate": 0.5153,
            "bot_degen_rate": 0.6669,
        }
        cluster_rec = scanner.scan_token(token_info)
        state_4d = scanner.generate_4d_temporal_state([cluster_rec])

        # Validate top-level keys
        assert "generated_at" in state_4d
        assert "stats" in state_4d
        assert "nodes" in state_4d
        assert "links" in state_4d
        assert "clusters" in state_4d
        assert "timeline" in state_4d
        assert "entities" in state_4d

        # Validate nodes schema (3D coordinates + role + color)
        for n in state_4d["nodes"]:
            assert "id" in n
            assert "x" in n and "y" in n and "z" in n
            assert "role" in n
            assert "color" in n
            assert "size" in n
            assert isinstance(n["x"], (int, float))

        # Validate links schema
        for link in state_4d["links"]:
            assert "source" in link
            assert "target" in link
            assert "type" in link
            assert "speed" in link

        # Validate timeline events (OpenMontage format)
        for ev in state_4d["timeline"]:
            assert "t_s" in ev
            assert "type" in ev
            assert "desc" in ev

        # Validate entities index (COG second brain format)
        assert "syndicates" in state_4d["entities"]
        assert "wallets" in state_4d["entities"]
        assert "tokens" in state_4d["entities"]
        assert cluster_rec["identity_id"] in state_4d["entities"]["syndicates"]

    def test_run_scan_cycle_exports_file(self, temp_dir):
        scanner = LiveSyndicateScanner(output_dir=str(temp_dir), mock_mode=True)
        state = scanner.run_scan_cycle()
        assert scanner.state_3d_file.exists()
        disk_data = json.loads(scanner.state_3d_file.read_text(encoding="utf-8"))
        assert len(disk_data["nodes"]) == len(state["nodes"])
        assert len(disk_data["clusters"]) >= 1
