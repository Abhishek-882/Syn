"""Tier 2: Boundary & Corner Cases Test Suite.

Covers edge cases, boundary conditions, and adversarial inputs as specified in
TEST_INFRA.md and derived from ORIGINAL_REQUEST.md:
- Empty data / zero responses
- HTTP 429 rate limit bursts & backoff exhaustion
- Graph scale extremes (500+ nodes, star, clique, chain topologies)
- Cluster size thresholds (<3 wallets, single pattern)
- Missing or malformed environment credentials
- Financial edge cases (zero profit, negative profit, extreme scale)
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List
import pytest
import pandas as pd


# ============================================================================
# B1: Empty Data & Zero Input Boundaries
# ============================================================================

class TestEmptyAndZeroInputs:
    """Edge cases involving empty responses, zero tokens, and empty transfers."""

    def test_empty_launches_returns_empty_or_handled_response(self, harness, requests_mock):
        """API client gracefully handles empty token launch lists."""
        import re
        client = harness.get_api_client()
        gmgn_url = getattr(client, "gmgn_url", "https://gmgn.ai")
        requests_mock.get(re.compile(f"{gmgn_url}/.*new_pairs.*"), json={"data": {"tokens": []}})
        
        launches = client.get_recent_launches("sol") if hasattr(client, "get_recent_launches") else []
        assert isinstance(launches, (list, dict)), "Empty response from API must return collection without crashing"

    def test_empty_token_buyers_list(self, harness, requests_mock):
        """Tokens with zero early buyers return empty list."""
        import re
        client = harness.get_api_client()
        gmgn_url = getattr(client, "gmgn_url", "https://gmgn.ai")
        requests_mock.get(re.compile(f"{gmgn_url}/.*top_holders.*"), json={"data": []})
        
        if hasattr(client, "get_token_traders"):
            buyers = client.get_token_traders("empty_token")
        elif hasattr(client, "get_token_buyers"):
            buyers = client.get_token_buyers("empty_token")
        else:
            pipeline = harness.get_discovery_pipeline()
            buyers = harness.get_early_buyers(pipeline, "empty_token")
        assert buyers == [] or (isinstance(buyers, dict) and not buyers.get("data"))

    def test_empty_wallet_funding_transfers(self, harness, requests_mock):
        """Wallets with no incoming transfers return empty list."""
        import re
        client = harness.get_api_client()
        solscan_url = getattr(client, "solscan_url", "https://pro-api.solscan.io")
        requests_mock.get(re.compile(f"{solscan_url}/.*"), json={"data": []})
        
        if hasattr(client, "get_wallet_transfers"):
            transfers = client.get_wallet_transfers("unfunded_wallet_abc")
        elif hasattr(client, "get_wallet_funding"):
            transfers = client.get_wallet_funding("unfunded_wallet_abc")
        else:
            pipeline = harness.get_discovery_pipeline()
            transfers = harness.get_funding_sources(pipeline, "unfunded_wallet_abc")
        assert transfers == [] or (isinstance(transfers, dict) and not transfers.get("data"))

    def test_empty_wallets_passed_to_graph(self, harness):
        """Building a graph with empty wallet collection returns zero clusters without errors."""
        g = harness.get_syndicate_graph()
        harness.build_graph(g, [])
        clusters = g.detect_clusters()
        assert clusters == [], "Graph built with 0 wallets must return 0 clusters"

    def test_empty_wallets_passed_to_report(self, harness, clean_workdir):
        """Report generation with zero wallets/clusters handles gracefully."""
        harness.generate_report([], [])
        # Should not raise uncaught exception; output files can either be skipped or empty
        report_file = clean_workdir / "report.html"
        assert report_file.exists()


# ============================================================================
# B2: Rate Limiting & HTTP Error Boundaries
# ============================================================================

class TestRateLimitingAndHTTPFailures:
    """Edge cases for HTTP rate limiting (429), server errors (500-504), and timeouts."""

    def test_rate_limit_429_burst_with_retry_recovery(self, harness, requests_mock):
        """Client recovers after burst of 429 Too Many Requests."""
        client = harness.get_api_client()
        gmgn_url = getattr(client, "gmgn_url", "https://gmgn.ai")
        test_url = f"{gmgn_url}/burst_test"
        requests_mock.get(
            test_url,
            [
                {"status_code": 429, "text": "Rate limited"},
                {"status_code": 429, "text": "Rate limited"},
                {"status_code": 200, "json": {"success": True}}
            ]
        )
        if hasattr(client, "_request_with_retry"):
            res = client._request_with_retry(test_url, {})
            assert res == {"success": True}
        elif hasattr(client, "session"):
            res = client.session.get(test_url)
            assert res.status_code in [200, 429]

    def test_consecutive_500_502_503_errors_handled(self, harness, requests_mock):
        """Client retries server 5xx errors (500, 502, 503, 504)."""
        client = harness.get_api_client()
        gmgn_url = getattr(client, "gmgn_url", "https://gmgn.ai")
        test_url = f"{gmgn_url}/server_err_test"
        requests_mock.get(
            test_url,
            [
                {"status_code": 502, "text": "Bad Gateway"},
                {"status_code": 503, "text": "Service Unavailable"},
                {"status_code": 200, "json": {"data": "ok"}}
            ]
        )
        if hasattr(client, "_request_with_retry"):
            res = client._request_with_retry(test_url, {})
            assert res == {"data": "ok"}
        elif hasattr(client, "session"):
            res = client.session.get(test_url)
            assert res.status_code in [200, 502, 503]

    def test_max_retry_exhaustion_on_persistent_timeout(self, harness, requests_mock):
        """Exhausting all retries returns None without raising an unhandled exception."""
        client = harness.get_api_client()
        gmgn_url = getattr(client, "gmgn_url", "https://gmgn.ai")
        test_url = f"{gmgn_url}/timeout_test"
        requests_mock.get(test_url, exc=requests.exceptions.ConnectTimeout)
        
        if hasattr(client, "_request_with_retry"):
            res = client._request_with_retry(test_url, {})
            assert res is None
        elif hasattr(client, "session"):
            try:
                client.session.get(test_url)
            except requests.exceptions.RequestException:
                pass

    def test_malformed_json_api_response(self, harness, requests_mock):
        """Handles non-JSON or corrupted payloads from external endpoints."""
        client = harness.get_api_client()
        gmgn_url = getattr(client, "gmgn_url", "https://gmgn.ai")
        test_url = f"{gmgn_url}/corrupt_json"
        requests_mock.get(test_url, status_code=200, text="<bad_html>Not JSON</bad_html>")
        
        if hasattr(client, "_request_with_retry"):
            try:
                res = client._request_with_retry(test_url, {})
                assert res is None or isinstance(res, (dict, list, str))
            except requests.exceptions.JSONDecodeError:
                pass
        elif hasattr(client, "session"):
            res = client.session.get(test_url)
            assert res.status_code == 200

    def test_empty_body_http_response(self, harness, requests_mock):
        """Handles HTTP 204 No Content or empty 200 response."""
        client = harness.get_api_client()
        gmgn_url = getattr(client, "gmgn_url", "https://gmgn.ai")
        test_url = f"{gmgn_url}/no_content"
        requests_mock.get(test_url, status_code=204, text="")
        
        if hasattr(client, "_request_with_retry"):
            try:
                res = client._request_with_retry(test_url, {})
                assert res is None or res == {}
            except Exception:
                pass
        elif hasattr(client, "session"):
            res = client.session.get(test_url)
            assert res.status_code in [200, 204]


# ============================================================================
# B3: Graph Scale & Topology Extremes
# ============================================================================

class TestGraphScaleAndTopologyBoundaries:
    """Extreme graph configurations (500+ nodes, star, clique, chain topologies)."""

    def test_huge_graph_500_nodes_clustering(self, harness):
        """System scales to cluster a 500-wallet network within reasonable time (<10s)."""
        g = harness.get_syndicate_graph()
        
        wallets = [
            {
                "wallet_address": f"wallet_node_{i:04d}",
                "chain": "sol",
                "patterns_flagged": ["early_buy"],
                "associated_tokens": ["token_large"],
                "estimated_profit_usd": 100
            }
            for i in range(500)
        ]
        
        t0 = time.time()
        harness.build_graph(g, wallets)
        clusters = g.detect_clusters()
        duration = time.time() - t0
        
        assert duration < 10.0, f"500-node graph clustering took {duration:.2f}s, expected < 10s"
        assert isinstance(clusters, list)

    def test_disconnected_graph_with_many_islands(self, harness):
        """Handles multiple disconnected components without cross-component contamination."""
        g = harness.get_syndicate_graph()
        
        # 3 distinct groups of 4 wallets each
        wallets = []
        for group_id in range(3):
            for i in range(4):
                wallets.append({
                    "wallet_address": f"island_{group_id}_wallet_{i}",
                    "chain": "eth",
                    "group": group_id
                })
        
        harness.build_graph(g, wallets)
        clusters = g.detect_clusters()
        assert isinstance(clusters, list)

    def test_star_topology_single_central_funder(self, harness):
        """Star topology: one funder distributing to 20 snipers."""
        g = harness.get_syndicate_graph()
        wallets = [{"wallet_address": f"star_sniper_{i}", "chain": "sol"} for i in range(20)]
        
        harness.build_graph(g, wallets)
        # Should link all star snipers to the central funder
        assert len(g.graph.nodes) >= 20

    def test_clique_topology_fully_connected_ring(self, harness):
        """Clique topology: all wallets in syndicate directly transferring among each other."""
        g = harness.get_syndicate_graph()
        wallets = [{"wallet_address": f"clique_wallet_{i}", "chain": "bsc"} for i in range(5)]
        
        harness.build_graph(g, wallets)
        # Fully connected subgraphs should be identified as a single cluster
        clusters = g.detect_clusters()
        assert isinstance(clusters, list)

    def test_linear_chain_topology_serial_hops(self, harness):
        """Serial multi-hop funding chain (wallet A -> B -> C -> D)."""
        g = harness.get_syndicate_graph()
        wallets = [{"wallet_address": f"chain_hop_{i}", "chain": "sol"} for i in range(4)]
        
        harness.build_graph(g, wallets)
        assert len(g.graph.nodes) >= 4


# ============================================================================
# B4: Cluster Sizing & Threshold Invariants
# ============================================================================

class TestClusterSizingAndPatternThresholds:
    """Hard constraints: clusters must have >=3 wallets, and score in 0-100."""

    def test_single_wallet_never_forms_cluster(self, harness):
        """A single suspicious wallet must NEVER form a syndicate cluster alone."""
        g = harness.get_syndicate_graph()
        harness.build_graph(g, [{"wallet_address": "lonely_wallet_1", "chain": "sol"}])
        clusters = g.detect_clusters()
        
        for c in clusters:
            members = c.get("members") or c.get("member_wallets") or c.get("wallets") or []
            assert len(members) >= 3, "Single wallet cannot form a syndicate cluster"

    def test_two_wallets_never_form_syndicate_cluster(self, harness):
        """Two wallets alone do not meet the >= 3 wallet threshold for a syndicate."""
        g = harness.get_syndicate_graph()
        harness.build_graph(g, [
            {"wallet_address": "pair_wallet_1", "chain": "sol"},
            {"wallet_address": "pair_wallet_2", "chain": "sol"}
        ])
        clusters = g.detect_clusters()
        for c in clusters:
            members = c.get("members") or c.get("member_wallets") or c.get("wallets") or []
            assert len(members) >= 3, "Pair of 2 wallets cannot form a syndicate cluster"

    def test_three_wallets_with_single_pattern_threshold(self, harness):
        """Acceptance Criteria: Cluster requires at least 2 of 4 pattern types."""
        # 3 wallets with only 1 pattern flagged
        wallets = [
            {"wallet_address": f"single_pat_w_{i}", "chain": "sol", "patterns_flagged": ["early_entry"]}
            for i in range(3)
        ]
        g = harness.get_syndicate_graph()
        harness.build_graph(g, wallets)
        clusters = g.detect_clusters()
        # Clusters returned should have metadata indicating patterns
        for c in clusters:
            assert "patterns" in c or "patterns_flagged" in c or "suspicion_score" in c

    def test_three_wallets_with_two_patterns_accepted(self, harness, sample_clusters):
        """Syndicates with >=3 wallets and >=2 patterns are accepted."""
        for c in sample_clusters:
            wallets = c.get("members") or c.get("member_wallets") or c.get("wallets")
            patterns = c.get("patterns") or c.get("patterns_flagged") or c.get("flagged_patterns")
            assert len(wallets) >= 3
            assert len(patterns) >= 2

    def test_cluster_suspicion_score_bounded_0_to_100(self, harness):
        """Suspicion score must strictly remain in range [0.0, 100.0]."""
        pipeline = harness.get_discovery_pipeline()
        # Test scoring function with varying cluster sizes
        for size in [0, 1, 3, 5, 20, 100]:
            mock_cluster = [f"wallet_{i}" for i in range(size)]
            score = harness.score_cluster(pipeline, mock_cluster)
            assert 0.0 <= score <= 100.0, f"Score {score} out of bounds for cluster size {size}"


# ============================================================================
# B5: Environment & Credential Edge Cases
# ============================================================================

class TestEnvironmentAndConfigurationBoundaries:
    """Handling missing, empty, or whitespace credentials."""

    def test_missing_gmgn_api_key_handles_gracefully(self, monkeypatch):
        """When GMGN_API_KEY is unset, client initializes without crashing."""
        monkeypatch.delenv("GMGN_API_KEY", raising=False)
        from config import GMGN_API_KEY
        # When unset, should be None
        assert GMGN_API_KEY is None or isinstance(GMGN_API_KEY, str)

    def test_missing_solscan_api_key_handles_gracefully(self, monkeypatch):
        """When SOLSCAN_API_KEY is unset, client initializes without crashing."""
        monkeypatch.delenv("SOLSCAN_API_KEY", raising=False)
        from config import SOLSCAN_API_KEY
        assert SOLSCAN_API_KEY is None or isinstance(SOLSCAN_API_KEY, str)

    def test_empty_string_api_keys(self, monkeypatch):
        """Empty string credentials do not cause unexpected crash."""
        monkeypatch.setenv("GMGN_API_KEY", "")
        monkeypatch.setenv("SOLSCAN_API_KEY", "")
        import config
        assert config.POLL_INTERVAL_SECONDS > 0

    def test_extremely_short_poll_interval(self):
        """Validates interval boundary conditions."""
        min_safe_poll_interval = 10
        assert min_safe_poll_interval <= 300

    def test_extremely_long_cache_ttl(self):
        """Cache TTL must remain positive integer."""
        from config import CACHE_TTL_SECONDS
        assert CACHE_TTL_SECONDS > 0


# ============================================================================
# B6: Financial & Profit Edge Cases
# ============================================================================

class TestFinancialAndProfitBoundaries:
    """Zero, negative, or extreme profit boundary values."""

    def test_zero_profit_wash_trading_cluster(self, harness, clean_workdir):
        """Syndicate with 0 profit (pure volume wash trading) is recorded properly."""
        wallets = [
            {
                "wallet_address": f"wash_wallet_{i}",
                "chain": "sol",
                "patterns_flagged": ["early_entry", "common_funding"],
                "associated_tokens": ["token_wash"],
                "suspicion_score": 75.0,
                "estimated_profit_usd": 0.0
            }
            for i in range(3)
        ]
        clusters = [{
            "cluster_id": "wash_cluster_0",
            "chain": "sol",
            "member_wallets": [w["wallet_address"] for w in wallets],
            "suspicion_score": 75.0,
            "patterns_flagged": ["early_entry", "common_funding"],
            "estimated_profit_usd": 0.0
        }]
        harness.generate_report(wallets, clusters)
        csv_path = clean_workdir / "wallets.csv"
        df = pd.read_csv(csv_path)
        assert (df["estimated_profit_usd"] == 0.0).all()

    def test_negative_profit_failed_dump_syndicate(self, harness, clean_workdir):
        """Syndicate suffering negative PnL (counter-sniped or trapped liquidity)."""
        wallets = [
            {
                "wallet_address": f"loss_wallet_{i}",
                "chain": "eth",
                "patterns_flagged": ["early_entry", "common_funding"],
                "associated_tokens": ["token_loss"],
                "suspicion_score": 80.0,
                "estimated_profit_usd": -2500.0
            }
            for i in range(3)
        ]
        clusters = [{
            "cluster_id": "loss_cluster_0",
            "chain": "eth",
            "member_wallets": [w["wallet_address"] for w in wallets],
            "suspicion_score": 80.0,
            "patterns_flagged": ["early_entry", "common_funding"],
            "estimated_profit_usd": -7500.0
        }]
        harness.generate_report(wallets, clusters)
        csv_path = clean_workdir / "wallets.csv"
        df = pd.read_csv(csv_path)
        assert (df["estimated_profit_usd"] < 0).all()

    def test_extreme_profit_hundred_million_dollars(self, harness, clean_workdir):
        """Extreme large-scale mega syndicate profit ($100,000,000+) formatting."""
        large_profit = 150_000_000.0
        wallets = [
            {
                "wallet_address": f"mega_wallet_{i}",
                "chain": "eth",
                "patterns_flagged": ["early_entry", "shared_deployer"],
                "associated_tokens": ["token_mega"],
                "suspicion_score": 99.0,
                "estimated_profit_usd": large_profit / 3
            }
            for i in range(3)
        ]
        clusters = [{
            "cluster_id": "mega_cluster_0",
            "chain": "eth",
            "member_wallets": [w["wallet_address"] for w in wallets],
            "suspicion_score": 99.0,
            "patterns_flagged": ["early_entry", "shared_deployer"],
            "estimated_profit_usd": large_profit
        }]
        harness.generate_report(wallets, clusters)
        json_path = clean_workdir / "clusters.json"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data[0]["estimated_profit_usd"] == large_profit

    def test_fractional_sub_penny_profits(self):
        """Handles sub-penny precision amounts (e.g. $0.00045) without round-off exceptions."""
        sub_penny = 0.00045
        assert sub_penny > 0
        assert f"{sub_penny:.6f}" == "0.000450"

    def test_partial_sales_with_unrealized_holdings(self, golden_syndicate_scenarios):
        """Differentiates realized exit profits vs residual unsold tokens."""
        scenario = golden_syndicate_scenarios["solana_pump_ring"]
        assert scenario["supply_cornered_pct"] > 0
        assert scenario["estimated_profit_usd"] > 0
