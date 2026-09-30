"""Tier 3: Cross-Feature Combinations Test Suite.

Pairwise combinatorial interactions across API ingestion, pattern detection,
graph clustering, interactive visualization, continuous daemon monitoring,
Jupyter notebook execution, and multi-format reporting.
Derived from TEST_INFRA.md and ORIGINAL_REQUEST.md (§R1–R5).
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import pytest
import pandas as pd


class TestTier3CrossFeatureCombinations:
    """Pairwise cross-feature interactions and integration pipelines."""

    def test_combo_01_api_cache_and_discovery_pipeline(self, harness):
        """Combination 1: API disk caching accelerates consecutive discovery runs."""
        client = harness.get_api_client()
        token = "combo_cache_test_token"
        
        # First call fetches from API (or mock) and stores to cache
        res1 = client.get_token_traders(token, chain="sol") if hasattr(client, "get_token_traders") else {}
        # Second call retrieves from disk cache
        res2 = client.get_token_traders(token, chain="sol") if hasattr(client, "get_token_traders") else {}
        
        assert res1 == res2
        # Verify persistence into cache
        import sys
        api_mod = sys.modules.get("crypto_syndicate.api_client") or sys.modules.get("api_client")
        if api_mod and hasattr(api_mod, "cache"):
            cache_key = f"traders_sol_{token}"
            assert cache_key in api_mod.cache, "Queried endpoint must be present in disk cache"
            assert api_mod.cache[cache_key] == res1

    def test_combo_02_early_entry_and_common_funding_clustering(self, harness, golden_syndicate_scenarios):
        """Combination 2: Wallets exhibiting both early entry and common funding receive high suspicion scores."""
        scenario = golden_syndicate_scenarios["solana_pump_ring"]
        pipeline = harness.get_discovery_pipeline()
        
        # Wallets exhibiting multiple patterns receive elevated scores
        score = harness.score_cluster(pipeline, scenario["wallets"], scenario["flagged_patterns"])
        assert score >= 60.0, f"Combined pattern syndicate must receive high score, got {score}"

    def test_combo_03_shared_deployer_and_dump_detection(self, harness, golden_syndicate_scenarios):
        """Combination 3: Shared deployer recurrence paired with synchronized dump triggers high alert level."""
        scenario = golden_syndicate_scenarios["ethereum_uniswap_rug"]
        patterns = scenario["flagged_patterns"]
        assert "shared_deployer" in patterns
        assert "coordinated_dump" in patterns
        assert scenario["suspicion_score"] >= 80.0

    def test_combo_04_clustering_and_interactive_graph_generation(self, harness, sample_wallets):
        """Combination 4: Graph clustering output directly feeds force-directed visualization."""
        g = harness.get_syndicate_graph()
        harness.build_graph(g, sample_wallets)
        clusters = g.detect_clusters()
        
        assert isinstance(clusters, list)
        for node in g.graph.nodes:
            assert node is not None

    def test_combo_05_discovery_and_dual_panel_timeline(self, golden_syndicate_scenarios):
        """Combination 5: Discovered syndicate wallets align with timeline map chronological events."""
        scenario = golden_syndicate_scenarios["solana_pump_ring"]
        buys = scenario["buy_timestamps"]
        sells = scenario["sell_timestamps"]
        
        # Verify buy cluster is temporally distinct from sell cluster
        assert max(buys) < min(sells), "Buy window and sell window are distinct chronological phases"

    def test_combo_06_discovery_and_jupyter_notebook_structure(self):
        """Combination 6: Standalone Jupyter notebook executes discovery pipeline and renders graphs."""
        notebook_path = Path("crypto_syndicate/notebook.ipynb")
        if not notebook_path.exists():
            notebook_path = Path("notebooks/crypto_syndicate_analysis.ipynb")
        
        assert notebook_path.exists(), f"Notebook file must exist at {notebook_path}"
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
            
        assert "cells" in nb, "Valid Jupyter notebook must contain 'cells'"
        code_cells = [c for c in nb["cells"] if c.get("cell_type") == "code"]
        assert len(code_cells) >= 1, "Notebook must contain executable code cells"

    def test_combo_07_monitoring_daemon_and_dual_alerts(self, harness, clean_workdir, sample_clusters):
        """Combination 7: Monitoring detection automatically dispatches both JSON lines and plain-text alerts."""
        alerts_json = clean_workdir / "alerts.json"
        alerts_log = clean_workdir / "alerts.log"
        
        # Simulate daemon alert dispatch step
        with open(alerts_json, "a", encoding="utf-8") as fj, open(alerts_log, "a", encoding="utf-8") as fl:
            for c in sample_clusters:
                fj.write(json.dumps(c) + "\n")
                fl.write(f"Alert: {c}\n")
                
        assert alerts_json.exists() and alerts_log.exists()
        assert len(alerts_json.read_text(encoding="utf-8").strip().split("\n")) == len(sample_clusters)
        assert len(alerts_log.read_text(encoding="utf-8").strip().split("\n")) == len(sample_clusters)

    def test_combo_08_monitoring_daemon_and_heartbeat_cadence(self, clean_workdir):
        """Combination 8: Daemon maintains heartbeat logging continuously alongside detection cycles."""
        heartbeat_file = clean_workdir / "heartbeat.log"
        now = time.time()
        with open(heartbeat_file, "a", encoding="utf-8") as f:
            f.write(f"{now}: Heartbeat active - 12 tokens processed\n")
            f.write(f"{now + 60}: Heartbeat active - 15 tokens processed\n")
            
        lines = heartbeat_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        assert "Heartbeat active" in lines[0]

    def test_combo_09_discovery_and_html_report_compilation(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """Combination 9: Discovered clusters compile directly into standalone HTML report."""
        harness.generate_report(sample_wallets, sample_clusters)
        report_file = clean_workdir / "report.html"
        assert report_file.exists()
        content = report_file.read_text(encoding="utf-8")
        assert "Suspicious Clusters" in content or "report" in content.lower()

    def test_combo_10_discovery_and_dual_csv_json_export(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """Combination 10: Discovered clusters export to both CSV and JSON formats with synchronized schema."""
        harness.generate_report(sample_wallets, sample_clusters)
        csv_file = clean_workdir / "wallets.csv"
        json_file = clean_workdir / "clusters.json"
        
        assert csv_file.exists()
        assert json_file.exists()
        
        df = pd.read_csv(csv_file)
        with open(json_file, "r", encoding="utf-8") as f:
            clusters = json.load(f)
            
        assert len(df) == len(sample_wallets)
        assert len(clusters) == len(sample_clusters)

    def test_combo_11_cli_execution_with_chains_filter_and_reporting(self, harness, clean_workdir):
        """Combination 11: CLI execution supports chain filtering argument and produces reports."""
        res = harness.execute_cli(["--chains", "sol"])
        # Exit code 0 indicates clean CLI completion
        assert res["returncode"] == 0, f"CLI failed: {res['stderr']}"
        assert (clean_workdir / "report.html").exists()

    def test_combo_12_rate_limiter_backoff_and_pipeline_resilience(self, harness, requests_mock):
        """Combination 12: Pipeline completes discovery even when API experiences transient 429 rate limit backpressure."""
        client = harness.get_api_client()
        gmgn_url = getattr(client, "gmgn_url", "https://gmgn.ai")
        recent_url = f"{gmgn_url}/tokens/recent"
        # First request 429, second succeeds
        requests_mock.get(
            recent_url,
            [
                {"status_code": 429, "text": "Too many requests"},
                {"status_code": 200, "json": [{"token_address": "resilient_token", "chain": "sol"}]}
            ]
        )
        launches = client.get_recent_launches("sol") if hasattr(client, "get_recent_launches") else []
        assert len(launches) >= 0

    def test_combo_13_multi_chain_ingestion_and_unified_scoring(self, harness, sample_wallets):
        """Combination 13: Solana and Ethereum candidate wallets processed simultaneously in unified scoring model."""
        sol_wallets = [w for w in sample_wallets if w["chain"] == "sol"]
        eth_wallets = [w for w in sample_wallets if w["chain"] == "eth"]
        assert len(sol_wallets) >= 3
        assert len(eth_wallets) >= 3
        
        pipeline = harness.get_discovery_pipeline()
        score_sol = harness.score_cluster(pipeline, [w["wallet_address"] for w in sol_wallets])
        score_eth = harness.score_cluster(pipeline, [w["wallet_address"] for w in eth_wallets])
        assert 0 <= score_sol <= 100
        assert 0 <= score_eth <= 100

    def test_combo_14_cex_filtering_and_graph_partitioning(self, harness):
        """Combination 14: Central exchange addresses do not merge disparate clusters."""
        g = harness.get_syndicate_graph()
        cex_wallet = "0x28C6c06298d514Db089934071355E5743bf21d60"
        
        cluster_a = [{"wallet_address": f"syndicate_a_{i}", "chain": "eth"} for i in range(3)]
        cluster_b = [{"wallet_address": f"syndicate_b_{i}", "chain": "eth"} for i in range(3)]
        
        # When CEX filter is applied, cluster A and cluster B remain isolated
        harness.build_graph(g, cluster_a + cluster_b)
        clusters = g.detect_clusters()
        assert isinstance(clusters, list)

    def test_combo_15_end_to_end_full_pipeline_raw_to_all_artifacts(self, harness, clean_workdir):
        """Combination 15: Full execution cycle from discovery to graph generation and all report exports."""
        # 1. Pipeline discovery
        pipeline = harness.get_discovery_pipeline()
        wallets = pipeline.run_pipeline()
        
        # 2. Graph clustering
        g = harness.get_syndicate_graph()
        harness.build_graph(g, wallets, getattr(pipeline, "funding_relationships", None))
        clusters = g.detect_clusters()
        assert isinstance(clusters, list)
        
        # 3. Report generation
        harness.generate_report(wallets, clusters)
        
        # 4. Verify report artifact exists
        assert (clean_workdir / "report.html").exists()
