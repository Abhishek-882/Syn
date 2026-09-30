"""Unit tests for report generation (M5).

Tests CSV, JSON, HTML outputs, D3 script embedding, and schema compliance.
"""

import csv
import json
import os
import pytest

from crypto_syndicate.report import generate_report
from crypto_syndicate.api.models import SyndicateCluster


@pytest.fixture
def sample_wallets():
    return [
        {
            "wallet_address": "wallet_111",
            "chain": "sol",
            "suspicion_score": 85.5,
            "patterns_flagged": ["early_entry", "common_funding"],
            "tokens_traded": ["tok_a", "tok_b"],
            "estimated_profit_usd": 12500.0,
        },
        {
            "wallet_address": "wallet_222",
            "chain": "sol",
            "suspicion_score": 60.0,
            "patterns_flagged": ["early_entry"],
            "tokens_traded": ["tok_a"],
            "estimated_profit_usd": 3200.0,
        },
        {
            "wallet_address": "wallet_333",
            "chain": "sol",
            "suspicion_score": 70.0,
            "patterns_flagged": ["coordinated_dump"],
            "tokens_traded": ["tok_b"],
            "estimated_profit_usd": 5000.0,
        },
    ]


@pytest.fixture
def sample_clusters():
    return [
        SyndicateCluster(
            cluster_id="cluster_001",
            chain="sol",
            wallets=("wallet_111", "wallet_222", "wallet_333"),
            flagged_patterns=("early_entry", "common_funding", "coordinated_dump"),
            suspicion_score=71.8,
            associated_tokens=("tok_a", "tok_b"),
            estimated_profit_usd=20700.0,
        )
    ]


def test_generate_report_creates_csv(tmp_path, sample_wallets, sample_clusters):
    """Test that wallets.csv is created in output_dir."""
    paths = generate_report(sample_wallets, sample_clusters, output_dir=str(tmp_path))
    assert os.path.exists(paths["csv"])
    assert paths["csv"] == str(tmp_path / "wallets.csv")


def test_generate_report_creates_json(tmp_path, sample_wallets, sample_clusters):
    """Test that clusters.json is created and contains valid JSON list."""
    paths = generate_report(sample_wallets, sample_clusters, output_dir=str(tmp_path))
    assert os.path.exists(paths["json"])
    assert paths["json"] == str(tmp_path / "clusters.json")

    with open(paths["json"], "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["cluster_id"] == "cluster_001"


def test_generate_report_creates_html(tmp_path, sample_wallets, sample_clusters):
    """Test that report.html is created in output_dir."""
    paths = generate_report(sample_wallets, sample_clusters, output_dir=str(tmp_path))
    assert os.path.exists(paths["html"])
    assert paths["html"] == str(tmp_path / "report.html")


def test_csv_has_correct_columns(tmp_path, sample_wallets, sample_clusters):
    """Test CSV headers match specification exactly."""
    expected_headers = [
        "wallet_address",
        "chain",
        "suspicion_score",
        "patterns_flagged",
        "associated_tokens",
        "estimated_profit_usd",
    ]
    paths = generate_report(sample_wallets, sample_clusters, output_dir=str(tmp_path))
    with open(paths["csv"], "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)

    assert headers == expected_headers
    assert len(rows) == len(sample_wallets)
    # Check sorting descending by score
    scores = [float(r[2]) for r in rows]
    assert scores == sorted(scores, reverse=True)


def test_html_contains_d3_script(tmp_path, sample_wallets, sample_clusters):
    """Test that report.html contains inline script and zero external CDN references."""
    paths = generate_report(sample_wallets, sample_clusters, output_dir=str(tmp_path))
    with open(paths["html"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "<script>" in content
    assert "</script>" in content
    assert "d3js.org" not in content
    assert "cdnjs.cloudflare" not in content


def test_html_contains_graph_data(tmp_path, sample_wallets, sample_clusters):
    """Test that report.html contains the graphData JSON object."""
    paths = generate_report(sample_wallets, sample_clusters, output_dir=str(tmp_path))
    with open(paths["html"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "const graphData =" in content
    assert "wallet_111" in content


def test_report_empty_inputs(tmp_path):
    """Test that generate_report handles empty wallet and cluster lists without crashing."""
    out_dir = tmp_path / "empty_report"
    paths = generate_report([], [], output_dir=str(out_dir))

    assert os.path.exists(paths["csv"])
    assert os.path.exists(paths["json"])
    assert os.path.exists(paths["html"])

    with open(paths["csv"], "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)
    assert len(rows) == 0

    with open(paths["json"], "r", encoding="utf-8") as f:
        clusters_data = json.load(f)
    assert clusters_data == []


def test_generate_report_output_file_argument(tmp_path, sample_wallets, sample_clusters):
    """Test compatibility with output_file parameter."""
    custom_html = tmp_path / "custom_dir" / "my_report.html"
    paths = generate_report(sample_wallets, sample_clusters, output_file=str(custom_html))

    assert os.path.exists(str(custom_html))
    assert paths["html"] == str(custom_html)
    assert os.path.exists(tmp_path / "custom_dir" / "wallets.csv")
    assert os.path.exists(tmp_path / "custom_dir" / "clusters.json")
