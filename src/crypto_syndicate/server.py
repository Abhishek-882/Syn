"""Lightweight SSE Streaming & Static Web Terminal Server.

Provides:
- Static file serving for the clean 2D terminal (`web/syndicate_terminal.html`).
- REST endpoint `/api/syndicates` returning full snapshot of active syndicates,
  deployer watchlist, and recent launches.
- Server-Sent Events (SSE) endpoint `/events/stream` pushing real-time JSON
  deltas to connected terminals with automatic client queue management.
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import logging
import os
from pathlib import Path
import queue
import socketserver
import sys
import threading
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs

# Ensure src directory is in sys.path so crypto_syndicate package can be imported
SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

logger = logging.getLogger(__name__)


class SSEBroadcaster:
    """Thread-safe event broadcaster for Server-Sent Events (SSE)."""

    def __init__(self):
        self._subscribers: List[queue.Queue] = []
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue:
        """Register a new SSE client queue."""
        q = queue.Queue(maxsize=100)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        """Remove a disconnected SSE client queue."""
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast an event to all connected SSE clients."""
        payload = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        with self._lock:
            dead_queues = []
            for q in self._subscribers:
                try:
                    q.put_nowait(payload)
                except queue.Full:
                    dead_queues.append(q)
            for dq in dead_queues:
                self._subscribers.remove(dq)


# Global broadcaster instance
GLOBAL_BROADCASTER = SSEBroadcaster()


def broadcast_event(event_type: str, data: Dict[str, Any]) -> None:
    """Global helper to broadcast events to all active terminals."""
    GLOBAL_BROADCASTER.broadcast(event_type, data)


HEALTH_PATHS = {
    "/healthz", "/heathz", "/health", "/heath", "/api/health", "/api/healthz",
    "/ping", "/status", "/live", "/ready", "/health-check"
}


class SyndicateTerminalHandler(SimpleHTTPRequestHandler):
    """HTTP request handler supporting static files, REST snapshot, and SSE streaming."""

    def __init__(self, *args, **kwargs):
        # Default working directory to repo root
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        super().__init__(*args, directory=str(self.repo_root), **kwargs)

    def do_HEAD(self):
        parsed = urlparse(self.path)
        if parsed.path in HEALTH_PATHS:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        elif parsed.path in ("/", "/terminal"):
            self.path = "/web/syndicate_terminal.html"
            super().do_HEAD()
        else:
            super().do_HEAD()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path in HEALTH_PATHS:
            self.handle_health_check()
        elif parsed.path == "/events/stream":
            self.handle_sse_stream()
        elif parsed.path == "/api/syndicates":
            self.handle_api_syndicates()
        elif parsed.path == "/api/token-history":
            self.handle_api_token_history()
        elif parsed.path in ("/api/keeper/run", "/api/keeper/sync"):
            self.handle_api_keeper_run()
        elif parsed.path == "/api/keeper/status":
            self.handle_api_keeper_status()
        elif parsed.path == "/api/token-lineage":
            self.handle_api_token_lineage(parsed)
        elif parsed.path == "/" or parsed.path == "/terminal":
            self.path = "/web/syndicate_terminal.html"
            super().do_GET()
        else:
            super().do_GET()

    def handle_health_check(self):
        """Health check probe endpoint for cloud runtimes (Render, K8s, Docker)."""
        data = {
            "status": "healthy",
            "service": "crypto-syndicate-sentinel",
            "version": "1.0.0",
            "timestamp": time.time(),
            "uptime_seconds": time.time() - SERVER_START_TIME,
        }
        resp = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(resp)

    def handle_sse_stream(self):
        """Handle real-time Server-Sent Events connection."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        client_queue = GLOBAL_BROADCASTER.subscribe()
        logger.info("SSE client connected from %s", self.client_address)

        # Send initial connected greeting
        init_msg = f"event: CONNECTED\ndata: {json.dumps({'status': 'ONLINE', 'timestamp': time.time()})}\n\n"
        try:
            self.wfile.write(init_msg.encode("utf-8"))
            self.wfile.flush()
        except Exception:
            GLOBAL_BROADCASTER.unsubscribe(client_queue)
            return

        try:
            while True:
                try:
                    msg = client_queue.get(timeout=15.0)
                    self.wfile.write(msg.encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    # Send periodic keep-alive heartbeat comment
                    heartbeat = f": heartbeat {time.time()}\n\n"
                    self.wfile.write(heartbeat.encode("utf-8"))
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            logger.info("SSE client disconnected: %s", self.client_address)
        finally:
            GLOBAL_BROADCASTER.unsubscribe(client_queue)

    def handle_api_syndicates(self):
        """Return snapshot of current syndicates, deployers, and launches."""
        state_file = self.repo_root / "results" / "syndicate_3d_state.json"
        data: Dict[str, Any] = {"status": "ok", "syndicates": [], "deployers": [], "launches": []}

        if state_file.exists():
            try:
                state_data = json.loads(state_file.read_text(encoding="utf-8"))
                data["syndicates"] = state_data.get("clusters", [])
                data["stats"] = state_data.get("stats", {})
                data["timeline"] = state_data.get("timeline", [])
                data["campaigns"] = state_data.get("campaigns", [])
                data["lineage"] = state_data.get("lineage", {})
                data["deployers"] = state_data.get("deployers_watchlist", [])
                data["launches"] = state_data.get("recent_token_launches", [])
            except Exception as e:
                logger.error("Error reading syndicate state: %s", e)

        # Fallback for launches from live_alerts.json if empty
        if not data["launches"]:
            alerts_file = self.repo_root / "results" / "live_alerts.json"
            if alerts_file.exists():
                try:
                    data["launches"] = json.loads(alerts_file.read_text(encoding="utf-8"))
                except Exception as e:
                    logger.debug("Failed reading live_alerts.json: %s", e)

        # Always merge live deployers and verified launches from GroundTruthLoader
        try:
            from crypto_syndicate.ground_truth_loader import get_ground_truth_loader
            loader = get_ground_truth_loader()
            loader.reload_if_needed()
            
            existing_deps = {d.get("address"): d for d in data.get("deployers", []) if d.get("address")}
            for d in loader.get_deployers():
                if d.get("address") not in existing_deps:
                    data["deployers"].append(d)

            existing_launches = {l.get("mint_address"): l for l in data.get("launches", []) if l.get("mint_address")}
            for l in loader.get_verified_launches():
                l_dict = l.to_dict()
                if l_dict.get("mint_address") not in existing_launches:
                    data["launches"].append(l_dict)
        except Exception as e:
            logger.debug("GroundTruthLoader live merge error: %s", e)

        # Filter out 0-pair tokens (BELUGA) so spotlight only showcases active trading pairs (LEVERAGE, ZLONG, EZO, etc.)
        data["launches"] = [
            l for l in data.get("launches", [])
            if l.get("mint_address") != "4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX"
            and l.get("symbol") != "BELUGA"
        ]

        # Include rich historical token track record ranked by recency
        try:
            from crypto_syndicate.ground_truth_loader import get_ground_truth_loader
            loader = get_ground_truth_loader()
            data["token_history"] = loader.get_syndicate_token_history()
        except Exception as e:
            logger.debug("Failed adding token_history to syndicates snapshot: %s", e)
            data["token_history"] = []

        resp_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(resp_bytes)

    def handle_api_token_history(self):
        """Return historical tokens ranked chronologically by release date (most recent first)."""
        try:
            from crypto_syndicate.ground_truth_loader import get_ground_truth_loader
            loader = get_ground_truth_loader()
            loader.reload_if_needed()
            tokens = loader.get_syndicate_token_history()
        except Exception as e:
            logger.error("Error retrieving token history: %s", e)
            tokens = []

        data = {
            "status": "ok",
            "total_tokens": len(tokens),
            "timestamp": time.time(),
            "token_history": tokens,
        }
        resp = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(resp)

    def handle_api_keeper_run(self):
        """Trigger an on-demand Keeper sync cycle."""
        try:
            from crypto_syndicate.keeper import get_syndicate_keeper
            keeper = get_syndicate_keeper()
            res = keeper.run_keeper_cycle()
        except Exception as e:
            res = {"status": "error", "error": str(e)}

        resp = json.dumps(res, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(resp)

    def handle_api_keeper_status(self):
        """Return Turbo Keeper scanner status: batch index, cycle count, discoveries."""
        try:
            from crypto_syndicate.keeper import get_syndicate_keeper
            keeper = get_syndicate_keeper()
            res = keeper.get_keeper_status()
        except Exception as e:
            res = {"status": "error", "error": str(e)}

        resp = json.dumps(res, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(resp)

    def handle_api_token_lineage(self, parsed):
        """Return 5-stage on-chain chained-link proof graph for a specific token mint or symbol."""
        query_params = parse_qs(parsed.query)
        mint = query_params.get("mint", [None])[0] or query_params.get("token", [None])[0] or query_params.get("symbol", [None])[0]
        try:
            from crypto_syndicate.ground_truth_loader import get_ground_truth_loader
            loader = get_ground_truth_loader()
            loader.reload_if_needed()
            lineage = loader.get_token_lineage(mint)
            if not lineage:
                res = {"status": "not_found", "message": f"Token lineage for '{mint}' not found"}
            else:
                res = lineage
        except Exception as e:
            res = {"status": "error", "error": str(e)}

        resp = json.dumps(res, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(resp)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Threaded HTTP server to handle concurrent SSE client connections without blocking."""

    daemon_threads = True
    allow_reuse_address = True


SERVER_START_TIME = time.time()


def start_terminal_server(port: Optional[int] = None, host: str = "0.0.0.0", auto_start_keeper: bool = True) -> ThreadedHTTPServer:
    """Start threaded HTTP server serving terminal and SSE stream with autonomous background keeper."""
    if port is None:
        port = int(os.environ.get("PORT", 8000))
    server = ThreadedHTTPServer((host, port), SyndicateTerminalHandler)
    logger.info("Syndicate Terminal & SSE Server started on http://%s:%d", host, port)

    if auto_start_keeper:
        try:
            from crypto_syndicate.keeper import get_syndicate_keeper
            from crypto_syndicate.config import KEEPER_SCAN_INTERVAL, SOLSCAN_JWT_TOKEN
            keeper = get_syndicate_keeper()
            if SOLSCAN_JWT_TOKEN and not keeper.solscan_jwt:
                keeper.solscan_jwt = SOLSCAN_JWT_TOKEN
            keeper.start_background_loop(interval_seconds=KEEPER_SCAN_INTERVAL)
            logger.info(
                "Turbo Keeper daemon active (interval=%ds, solscan=%s)",
                KEEPER_SCAN_INTERVAL, "YES" if keeper.solscan_jwt else "NO",
            )
        except Exception as e:
            logger.warning("Could not auto-start keeper background loop: %s", e)

    return server


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Crypto Syndicate Live Terminal Server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)), help="Port to bind (default: $PORT or 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    parser.add_argument("--no-keeper", action="store_true", help="Disable autonomous keeper daemon loop")
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    server = start_terminal_server(port=args.port, host=args.host, auto_start_keeper=not args.no_keeper)
    print(f"[READY] Syndicate Sentinel Server running on http://{args.host}:{args.port}")
    print(f"[STREAM] Real-time SSE Stream: http://{args.host}:{args.port}/events/stream")
    print(f"[HEALTH] Health Check Probe: http://{args.host}:{args.port}/healthz")
    print(f"[KEEPER] Turbo Scanner: {'ENABLED (15s turbo loop)' if not args.no_keeper else 'DISABLED'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        try:
            from crypto_syndicate.keeper import get_syndicate_keeper
            get_syndicate_keeper().stop_background_loop()
        except Exception:
            pass
        server.server_close()


if __name__ == "__main__":
    main()
