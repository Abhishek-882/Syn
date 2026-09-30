"""Unit tests for SSE Broadcaster and Server Components."""

import json
import unittest
from crypto_syndicate.server import SSEBroadcaster, broadcast_event


class TestSSEBroadcaster(unittest.TestCase):
    """Test suite for SSE event delivery and queue handling."""

    def test_subscribe_and_broadcast(self):
        """Verify subscriber receives formatted SSE events."""
        broadcaster = SSEBroadcaster()
        q = broadcaster.subscribe()

        event_data = {"mint": "Token123", "symbol": "TEST"}
        broadcaster.broadcast("TOKEN_CREATED", event_data)

        self.assertFalse(q.empty())
        raw_msg = q.get_nowait()
        self.assertIn("event: TOKEN_CREATED\n", raw_msg)
        self.assertIn('data: {"mint": "Token123", "symbol": "TEST"}\n\n', raw_msg)

        broadcaster.unsubscribe(q)

    def test_multiple_subscribers(self):
        """Verify broadcast fans out to all active subscribers."""
        broadcaster = SSEBroadcaster()
        q1 = broadcaster.subscribe()
        q2 = broadcaster.subscribe()

        broadcaster.broadcast("WALLET_FUNDED", {"amount": 5.0})

        self.assertFalse(q1.empty())
        self.assertFalse(q2.empty())

        broadcaster.unsubscribe(q1)
        broadcaster.unsubscribe(q2)

    def test_global_broadcast_event_helper(self):
        """Verify global broadcast_event helper dispatches without errors."""
        # Should execute safely even without active subscribers
        broadcast_event("HEARTBEAT", {"status": "OK"})

    def test_server_initialization_and_healthz(self):
        """Verify server starts on custom port and responds to healthz probe."""
        import urllib.request
        from crypto_syndicate.server import start_terminal_server
        server = start_terminal_server(port=8899)
        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            # Test standard /healthz
            with urllib.request.urlopen("http://127.0.0.1:8899/healthz") as resp:
                self.assertEqual(resp.status, 200)
                body = json.loads(resp.read().decode())
                self.assertEqual(body["status"], "healthy")

            # Test typo /heathz
            with urllib.request.urlopen("http://127.0.0.1:8899/heathz") as resp:
                self.assertEqual(resp.status, 200)
                body = json.loads(resp.read().decode())
                self.assertEqual(body["status"], "healthy")

            # Test HEAD probe
            req = urllib.request.Request("http://127.0.0.1:8899/heathz", method="HEAD")
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
