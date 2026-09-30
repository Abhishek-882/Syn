"""Unit tests for MonitoringLoop (M4).

Tests alert logging (NDJSON and plain text), seen-cluster persistence, and directory creation.
"""

import json
import os
import pytest

from crypto_syndicate.monitor import MonitoringLoop
from crypto_syndicate.api.models import SyndicateCluster


def test_init_creates_output_dir(tmp_path):
    """Test that MonitoringLoop creates the specified output directory on init."""
    out_dir = tmp_path / "sub_monitor_dir"
    assert not out_dir.exists()

    loop = MonitoringLoop(output_dir=str(out_dir), mock_mode=True)
    assert out_dir.exists()
    assert loop.output_dir == str(out_dir)


def test_load_seen_clusters_empty_file(tmp_path):
    """Test that missing or empty seen_clusters.json is handled gracefully."""
    out_dir = tmp_path / "monitor_empty"
    loop = MonitoringLoop(output_dir=str(out_dir), mock_mode=True)
    assert loop.seen_clusters == set()

    # Empty file
    seen_file = out_dir / "seen_clusters.json"
    seen_file.write_text("", encoding="utf-8")
    loop2 = MonitoringLoop(output_dir=str(out_dir), mock_mode=True)
    assert loop2.seen_clusters == set()

    # Corrupt JSON file
    seen_file.write_text("{corrupt-json", encoding="utf-8")
    loop3 = MonitoringLoop(output_dir=str(out_dir), mock_mode=True)
    assert loop3.seen_clusters == set()


def test_write_alert_appends_to_json(tmp_path):
    """Test that alerts are written to alerts.json as valid NDJSON lines."""
    out_dir = tmp_path / "monitor_alerts"
    loop = MonitoringLoop(output_dir=str(out_dir), mock_mode=True)

    cluster = SyndicateCluster(
        cluster_id="cluster_alpha_01",
        chain="sol",
        wallets=("w1", "w2", "w3"),
        flagged_patterns=("early_entry", "common_funding"),
        suspicion_score=82.5,
        estimated_profit_usd=4500.0,
    )
    loop._write_alert(cluster)

    assert os.path.exists(loop.alerts_json_file)
    with open(loop.alerts_json_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["cluster_id"] == "cluster_alpha_01"
    assert record["suspicion_score"] == 82.5
    assert "alert_timestamp" in record
    assert record["chain"] == "sol"
    assert record["wallets"] == ["w1", "w2", "w3"]


def test_write_alert_appends_to_log(tmp_path):
    """Test that alerts are appended to alerts.log as human-readable lines."""
    out_dir = tmp_path / "monitor_logs"
    loop = MonitoringLoop(output_dir=str(out_dir), mock_mode=True)

    cluster = SyndicateCluster(
        cluster_id="cluster_beta_02",
        chain="sol",
        wallets=("wallet_a", "wallet_b", "wallet_c"),
        flagged_patterns=("early_entry", "coordinated_dump"),
        suspicion_score=90.0,
        estimated_profit_usd=12345.67,
    )
    loop._write_alert(cluster)

    assert os.path.exists(loop.alerts_log_file)
    with open(loop.alerts_log_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "ALERT: Syndicate cluster_beta_02" in content
    assert "Score: 90.0" in content
    assert "Size: 3 wallets" in content
    assert "early_entry" in content
    assert "Profit est: $12,345.67" in content


def test_save_and_reload_seen_clusters(tmp_path):
    """Test that seen_clusters persists to disk and is reloaded by new instances."""
    out_dir = tmp_path / "monitor_persist"
    loop1 = MonitoringLoop(output_dir=str(out_dir), mock_mode=True)
    loop1.seen_clusters.add("sol:w1,w2,w3")
    loop1.seen_clusters.add("sol:w4,w5,w6")
    loop1._save_seen_clusters()

    assert os.path.exists(loop1.seen_clusters_file)

    # Initialize a new loop instance pointing to the same folder
    loop2 = MonitoringLoop(output_dir=str(out_dir), mock_mode=True)
    assert "sol:w1,w2,w3" in loop2.seen_clusters
    assert "sol:w4,w5,w6" in loop2.seen_clusters
    assert len(loop2.seen_clusters) == 2


def test_run_cycle_mock_and_deduplication(tmp_path):
    """Test that running a cycle in mock mode detects clusters and subsequent cycle deduplicates."""
    out_dir = tmp_path / "monitor_cycle"
    loop = MonitoringLoop(chains=["sol"], output_dir=str(out_dir), mock_mode=True)

    first_cycle_count = loop._run_cycle()
    assert first_cycle_count > 0
    assert len(loop.seen_clusters) == first_cycle_count

    # Second cycle on same data should suppress duplicates
    second_cycle_count = loop._run_cycle()
    assert second_cycle_count == 0


def test_heartbeat_logging(tmp_path):
    """Test that heartbeat writes to heartbeat.log."""
    out_dir = tmp_path / "monitor_heartbeat"
    loop = MonitoringLoop(output_dir=str(out_dir), mock_mode=True)
    loop._log_heartbeat()

    assert os.path.exists(loop.heartbeat_log_file)
    with open(loop.heartbeat_log_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Heartbeat: monitoring active" in content
