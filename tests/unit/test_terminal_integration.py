"""Unit & Integration Tests for Clean 2D Syndicate Terminal Platform."""

import json
import os
from pathlib import Path
import queue
import time
import unittest
from unittest.mock import MagicMock, patch

from crypto_syndicate.api.fixtures import get_mock_ingress_and_token_fixtures
from crypto_syndicate.lineage_sentry import RecursiveLineageEngine
from crypto_syndicate.token_sentinel import TokenCreationSentinel
from crypto_syndicate.scanner import LiveSyndicateScanner
from crypto_syndicate.server import (
    GLOBAL_BROADCASTER,
    SyndicateTerminalHandler,
    broadcast_event,
)


class TestTerminalPlatformIntegration(unittest.TestCase):
    """Test suite for the clean 2D terminal platform, SSE stream, and scanner integration."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parent.parent.parent
        cls.terminal_html_path = cls.repo_root / "web" / "syndicate_terminal.html"

    def test_terminal_html_exists_and_anti_vibe_standards(self):
        """Verify terminal HTML exists and adheres strictly to /anti-vibe-design (no WebGL/Three.js)."""
        self.assertTrue(self.terminal_html_path.exists(), "syndicate_terminal.html must exist")
        content = self.terminal_html_path.read_text(encoding="utf-8")

        # Anti-vibe check: zero 3D canvas / Three.js
        self.assertNotIn("three.min.js", content, "Terminal must have zero Three.js dependencies")
        self.assertNotIn("OrbitControls", content, "Terminal must have zero OrbitControls")
        self.assertNotIn("WebGLRenderer", content, "Terminal must have zero WebGL renderers")

        # Required 2D UI elements
        self.assertIn("notif-toggle-btn", content, "Must contain notification toggle button")
        self.assertIn("spotlight-container", content, "Must contain sticky golden spotlight banner")
        self.assertIn("lineage-svg", content, "Must contain 2D SVG Lineage connectome")
        self.assertIn("deployers-list", content, "Must contain deployer watchlist list")
        self.assertIn("feed-list", content, "Must contain live activity feed")
        self.assertIn("playSyndicateChime", content, "Must contain Web Audio dual-tone synthesis chime")
        self.assertIn("new EventSource('/events/stream')", content, "Must connect to SSE stream")

    def test_scanner_mock_cycle_exports_deployers_and_launches(self):
        """Verify LiveSyndicateScanner exports deployers watchlist, recent token launches, and lineage."""
        out_dir = self.repo_root / "results"
        scanner = LiveSyndicateScanner(output_dir=str(out_dir), mock_mode=True)
        state = scanner.run_scan_cycle()

        self.assertIn("deployers_watchlist", state)
        self.assertIn("recent_token_launches", state)
        self.assertIn("lineage", state)

        # Check deployers watchlist populated
        deployers = state["deployers_watchlist"]
        self.assertGreater(len(deployers), 0, "Deployers watchlist should contain qualified wallets")
        for d in deployers:
            self.assertGreaterEqual(d["balance_usd"], 5.0, "All deployers on watchlist must meet >= $5.00 threshold")

        # Check launches
        launches = state["recent_token_launches"]
        self.assertGreater(len(launches), 0, "Should have detected mock token launches")
        symbols = [l["symbol"] for l in launches]
        self.assertTrue(any("ZLONG" in s or "EZO" in s or "SCRIBJEAN" in s for s in symbols))

        # Check alerts file
        alerts_file = out_dir / "live_alerts.json"
        self.assertTrue(alerts_file.exists(), "live_alerts.json must be written")
        alerts = json.loads(alerts_file.read_text(encoding="utf-8"))
        self.assertGreater(len(alerts), 0)

    def test_token_launch_sse_fanout(self):
        """Verify token launches fan out correctly to SSE subscriber queues."""
        q1 = GLOBAL_BROADCASTER.subscribe()
        q2 = GLOBAL_BROADCASTER.subscribe()

        try:
            sample_launch = {
                "mint_address": "TestMint123",
                "symbol": "ALPHA",
                "name": "Alpha Token",
                "creator_wallet": "CreatorWallet456",
                "parent_syndicate_id": "SYN-TEST-01",
                "initial_sol_injected": 0.08,
            }
            broadcast_event("token_launch", sample_launch)

            msg1 = q1.get(timeout=1.0)
            msg2 = q2.get(timeout=1.0)

            self.assertIn("event: token_launch", msg1)
            self.assertIn("TestMint123", msg1)
            self.assertIn("event: token_launch", msg2)
            self.assertIn("ALPHA", msg2)
        finally:
            GLOBAL_BROADCASTER.unsubscribe(q1)
            GLOBAL_BROADCASTER.unsubscribe(q2)


if __name__ == "__main__":
    unittest.main()
