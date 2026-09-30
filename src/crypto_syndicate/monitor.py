"""M4 — Continuous Monitoring Loop with Alerts."""

import json
import logging
import time
import os
from typing import List, Optional, Set

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

from crypto_syndicate.discovery import DiscoveryPipeline
from crypto_syndicate.graph import SyndicateGraph
from crypto_syndicate.api.models import SyndicateCluster
from crypto_syndicate.identity import SyndicateIdentityEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("crypto_syndicate.monitor")

DEFAULT_POLL_INTERVAL = 300  # 5 minutes
HEARTBEAT_INTERVAL = 60      # 1 minute


class MonitoringLoop:
    def __init__(
        self,
        chains: Optional[List[str]] = None,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        output_dir: str = ".",
        mock_mode: bool = False,
    ):
        self.chains = chains or ["sol"]
        self.poll_interval = poll_interval
        self.output_dir = output_dir
        self.mock_mode = mock_mode
        os.makedirs(output_dir, exist_ok=True)
        self.identity_engine = SyndicateIdentityEngine(output_dir=output_dir)
        self.seen_clusters_file = os.path.join(output_dir, "seen_clusters.json")
        self.alerts_json_file = os.path.join(output_dir, "alerts.json")
        self.alerts_log_file = os.path.join(output_dir, "alerts.log")
        self.heartbeat_log_file = os.path.join(output_dir, "heartbeat.log")
        self.seen_clusters: Set[str] = set()
        self._load_seen_clusters()

    def _load_seen_clusters(self) -> None:
        if os.path.exists(self.seen_clusters_file):
            try:
                with open(self.seen_clusters_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        if isinstance(data, list):
                            self.seen_clusters = set(data)
                        elif isinstance(data, dict):
                            self.seen_clusters = set(data.keys())
                logger.info("Loaded %d previously seen clusters", len(self.seen_clusters))
            except Exception as exc:
                logger.error("Error loading seen clusters: %s", exc)
                self.seen_clusters = set()

    def _save_seen_clusters(self) -> None:
        tmp_path = self.seen_clusters_file + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(list(self.seen_clusters), f)
            os.replace(tmp_path, self.seen_clusters_file)
        except Exception as exc:
            logger.error("Error saving seen clusters: %s", exc)
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def _write_alert(self, cluster: Any) -> None:
        data = cluster.to_dict() if hasattr(cluster, "to_dict") else dict(cluster)
        data["alert_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        cluster_id = getattr(cluster, "cluster_id", None) or data.get("cluster_id", "unknown")
        score = float(getattr(cluster, "suspicion_score", None) or data.get("suspicion_score", 0.0))
        wallets = getattr(cluster, "wallets", None) or data.get("wallets", []) or data.get("members", [])
        patterns = getattr(cluster, "flagged_patterns", None) or data.get("patterns_flagged", []) or data.get("flagged_patterns", [])
        profit = float(getattr(cluster, "estimated_profit_usd", None) or data.get("estimated_profit_usd", 0.0))

        # NDJSON append
        try:
            with open(self.alerts_json_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, default=str) + "\n")
        except Exception as exc:
            logger.error("Error writing alerts.json: %s", exc)

        # Human-readable log append
        try:
            with open(self.alerts_log_file, "a", encoding="utf-8") as f:
                f.write(
                    f"[{data['alert_timestamp']}] ALERT: Syndicate {cluster_id} | "
                    f"Score: {score:.1f} | Size: {len(wallets)} wallets | "
                    f"Patterns: {', '.join(patterns)} | "
                    f"Profit est: ${profit:,.2f}\n"
                )
        except Exception as exc:
            logger.error("Error writing alerts.log: %s", exc)

    def _log_heartbeat(self) -> None:
        msg = f"Heartbeat: monitoring active, {len(self.seen_clusters)} clusters seen so far"
        logger.info(msg)
        try:
            with open(self.heartbeat_log_file, "a", encoding="utf-8") as f:
                ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                f.write(f"[{ts}] {msg}\n")
        except Exception as exc:
            logger.error("Error writing heartbeat.log: %s", exc)

    def _run_cycle(self) -> int:
        """Run one discovery+cluster cycle. Returns count of new alerts."""
        pipeline = DiscoveryPipeline(mock_mode=self.mock_mode)
        wallets = pipeline.run_pipeline(chains=self.chains)
        sg = SyndicateGraph()
        sg.build_graph(wallets, pipeline.funding_relationships)
        clusters = sg.detect_clusters()

        new_count = 0
        for cluster in clusters:
            c_wallets = getattr(cluster, "wallets", None) or (cluster.get("wallets", []) if isinstance(cluster, dict) else [])
            c_chain = getattr(cluster, "chain", None) or (cluster.get("chain", "sol") if isinstance(cluster, dict) else "sol")
            sig = f"{c_chain}:{','.join(sorted(c_wallets))}"
            if sig not in self.seen_clusters:
                self.seen_clusters.add(sig)
                self._write_alert(cluster)
                cid = getattr(cluster, "cluster_id", None) or (cluster.get("cluster_id") if isinstance(cluster, dict) else "")
                score = getattr(cluster, "suspicion_score", 0.0) or (cluster.get("suspicion_score", 0.0) if isinstance(cluster, dict) else 0.0)
                pats = getattr(cluster, "flagged_patterns", []) or (cluster.get("flagged_patterns", []) if isinstance(cluster, dict) else [])
                logger.warning(
                    "NEW SYNDICATE: %s | score=%.1f | wallets=%d | patterns=%s",
                    cid, score, len(c_wallets), list(pats),
                )
                new_count += 1

        if new_count:
            self._save_seen_clusters()
        return new_count

    def run(self, max_iterations: Optional[int] = None) -> None:
        logger.info("Monitoring started | chains=%s | poll_interval=%ds", self.chains, self.poll_interval)
        last_heartbeat = time.time()
        self._log_heartbeat()

        iterations = 0
        while True:
            now = time.time()
            if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                self._log_heartbeat()
                last_heartbeat = now

            try:
                new_alerts = self._run_cycle()
                logger.info("Cycle complete: %d new syndicate alerts", new_alerts)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user.")
                break
            except Exception as exc:
                logger.error("Unhandled error in monitoring cycle (continuing): %s", exc, exc_info=True)

            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                logger.info("Reached maximum iterations (%d), exiting run.", max_iterations)
                break

            time.sleep(min(self.poll_interval, 1))
