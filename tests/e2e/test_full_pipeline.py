"""E2E test suite for full pipeline and CLI execution (M2-M6).

Runs the entire discovery -> graph -> clustering -> report pipeline in mock mode
and verifies CLI subprocess execution.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from crypto_syndicate.discovery import DiscoveryPipeline
from crypto_syndicate.graph import SyndicateGraph
from crypto_syndicate.report import generate_report


def test_full_pipeline_mock_sol(tmp_path):
    """Run discovery -> graph -> clusters -> report for sol chain in mock mode."""
    out_dir = str(tmp_path / "sol_results")

    pipeline = DiscoveryPipeline(mock_mode=True)
    wallets = pipeline.run_pipeline(chains=["sol"])
    assert isinstance(wallets, list)
    assert len(wallets) > 0

    sg = SyndicateGraph()
    sg.build_graph(wallets, pipeline.funding_relationships)
    clusters = sg.detect_clusters()
    assert isinstance(clusters, list)
    assert len(clusters) > 0

    paths = generate_report(wallets, clusters, output_dir=out_dir)
    assert os.path.exists(paths["csv"])
    assert os.path.exists(paths["json"])
    assert os.path.exists(paths["html"])


def test_full_pipeline_reports_exist(tmp_path):
    """Verify CSV, JSON, and HTML files exist and contain non-trivial data."""
    out_dir = str(tmp_path / "reports_exist")

    pipeline = DiscoveryPipeline(mock_mode=True)
    wallets = pipeline.run_pipeline(chains=["sol"])
    sg = SyndicateGraph()
    sg.build_graph(wallets, pipeline.funding_relationships)
    clusters = sg.detect_clusters()

    paths = generate_report(wallets, clusters, output_dir=out_dir)

    # Check CSV
    assert os.path.getsize(paths["csv"]) > 50
    with open(paths["csv"], "r", encoding="utf-8") as f:
        csv_lines = [line.strip() for line in f if line.strip()]
    assert len(csv_lines) >= 2  # header + at least 1 wallet row

    # Check JSON
    assert os.path.getsize(paths["json"]) > 10
    with open(paths["json"], "r", encoding="utf-8") as f:
        json_data = json.load(f)
    assert isinstance(json_data, list)
    assert len(json_data) >= 1

    # Check HTML
    assert os.path.getsize(paths["html"]) > 1000
    with open(paths["html"], "r", encoding="utf-8") as f:
        html_text = f.read()
    assert "<!DOCTYPE html>" in html_text
    assert "graphData" in html_text
    assert "d3js.org" not in html_text


def test_full_pipeline_no_crash_empty_results(tmp_path):
    """Verify that a pipeline with no data completes without crash."""
    out_dir = str(tmp_path / "empty_results")

    pipeline = DiscoveryPipeline(mock_mode=True)
    pipeline.fetch_recent_launches = MagicMock(return_value=[])

    wallets = pipeline.run_pipeline(chains=["sol"])
    assert wallets == []

    sg = SyndicateGraph()
    sg.build_graph(wallets, pipeline.funding_relationships)
    clusters = sg.detect_clusters()
    assert clusters == []

    paths = generate_report(wallets, clusters, output_dir=out_dir)
    assert os.path.exists(paths["csv"])
    assert os.path.exists(paths["json"])
    assert os.path.exists(paths["html"])


def test_cli_mock_run(tmp_path):
    """Subprocess call to run_analysis.py --mock --chains sol returns exit code 0."""
    out_dir = str(tmp_path / "cli_test_out")
    repo_root = Path(__file__).resolve().parent.parent.parent
    cli_path = repo_root / "src" / "crypto_syndicate" / "run_analysis.py"

    cmd = [
        sys.executable,
        str(cli_path),
        "--mock",
        "--chains", "sol",
        "--output", out_dir,
    ]

    result = subprocess.run(
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, f"CLI exited with {result.returncode}: {result.stderr}"
    assert "Analysis Complete" in result.stdout
    assert "Syndicates found :" in result.stdout
    assert os.path.exists(os.path.join(out_dir, "wallets.csv"))
    assert os.path.exists(os.path.join(out_dir, "clusters.json"))
    assert os.path.exists(os.path.join(out_dir, "report.html"))


def test_full_pipeline_multichain(tmp_path):
    """Multi-chain discovery across sol, eth, and bsc in mock mode."""
    out_dir = str(tmp_path / "multichain_results")

    pipeline = DiscoveryPipeline(mock_mode=True)
    wallets = pipeline.run_pipeline(chains=["sol", "eth", "bsc"])
    assert len(wallets) >= 6

    sg = SyndicateGraph()
    sg.build_graph(wallets, pipeline.funding_relationships)
    clusters = sg.detect_clusters()
    assert len(clusters) >= 1

    paths = generate_report(wallets, clusters, output_dir=out_dir)
    assert os.path.exists(paths["csv"])
    assert os.path.exists(paths["json"])
    assert os.path.exists(paths["html"])
