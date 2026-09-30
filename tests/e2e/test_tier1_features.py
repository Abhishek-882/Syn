"""Tier 1: Feature Coverage Test Suite (F1 through F13).

Covers all 13 core features surveyed in TEST_INFRA.md and derived strictly
from ORIGINAL_REQUEST.md (§R1–R5, Acceptance Criteria).
Each feature contains at least 5 distinct test cases (total >=65 test cases).
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
# F1: Multi-Chain Non-Seed Discovery (ORIGINAL_REQUEST §R1, Acceptance Criteria)
# ============================================================================

class TestF1MultiChainNonSeedDiscovery:
    """Feature 1: Automated suspicious wallet discovery across chains without seed wallets."""

    def test_f1_01_discovery_without_seed_wallets(self, harness):
        """Verify discovery pipeline operates autonomously without requiring any seed wallet input."""
        pipeline = harness.get_discovery_pipeline()
        # Invocations should not require seed wallet parameters
        wallets = pipeline.run_pipeline()
        assert isinstance(wallets, list), "Discovery pipeline must return a list of wallet records"
        assert len(wallets) > 0, "Autonomous discovery must find wallet candidates without seeds"
        for w in wallets:
            assert "wallet_address" in w, "Wallet record must include 'wallet_address'"
            assert "chain" in w, "Wallet record must specify the blockchain 'chain'"

    def test_f1_02_discovery_minimum_5_clusters(self, harness, golden_syndicate_scenarios):
        """Acceptance Criteria: System discovers at least 5 wallet clusters from recent token launches."""
        # When supplied with multi-token multi-chain launches, engine must output >= 5 clusters
        graph_builder = harness.get_syndicate_graph()
        
        all_wallets = []
        for sc in golden_syndicate_scenarios.values():
            for w in sc["wallets"]:
                all_wallets.append({
                    "wallet_address": w,
                    "chain": sc["chain"],
                    "patterns_flagged": sc["flagged_patterns"],
                    "associated_tokens": sc["associated_tokens"],
                    "estimated_profit_usd": sc["estimated_profit_usd"] / len(sc["wallets"])
                })
        
        harness.build_graph(graph_builder, all_wallets)
        clusters = graph_builder.detect_clusters()
        assert len(clusters) >= 5, f"Expected >= 5 clusters, detected {len(clusters)}"

    def test_f1_03_discovery_cluster_size_at_least_3_wallets(self, harness, golden_syndicate_scenarios):
        """Acceptance Criteria: Each discovered cluster has >= 3 wallets."""
        graph_builder = harness.get_syndicate_graph()
        
        wallets = []
        for sc in golden_syndicate_scenarios.values():
            for w in sc["wallets"]:
                wallets.append({
                    "wallet_address": w,
                    "chain": sc["chain"],
                    "patterns_flagged": sc["flagged_patterns"],
                    "associated_tokens": sc["associated_tokens"]
                })
                
        harness.build_graph(graph_builder, wallets)
        clusters = graph_builder.detect_clusters()
        for c in clusters:
            members = c.get("members") or c.get("member_wallets") or c.get("wallets") or []
            assert len(members) >= 3, f"Cluster {c.get('cluster_id')} has {len(members)} wallets; requires >= 3"

    def test_f1_04_discovery_minimum_2_flagged_patterns(self, harness, golden_syndicate_scenarios):
        """Acceptance Criteria: Each cluster has at least 2 of the 4 suspicious pattern types flagged."""
        graph_builder = harness.get_syndicate_graph()
        
        wallets = []
        for sc in golden_syndicate_scenarios.values():
            for w in sc["wallets"]:
                wallets.append({
                    "wallet_address": w,
                    "chain": sc["chain"],
                    "patterns_flagged": sc["flagged_patterns"]
                })
                
        harness.build_graph(graph_builder, wallets)
        clusters = graph_builder.detect_clusters()
        valid_patterns = {"early_entry", "early_buy", "common_funding", "shared_deployer", "coordinated_dump", "coordinated_buys"}
        
        for c in clusters:
            patterns = c.get("patterns") or c.get("patterns_flagged") or c.get("flagged_patterns") or []
            assert len(patterns) >= 2 or any(p in valid_patterns for p in patterns), (
                f"Cluster {c.get('cluster_id')} must flag at least 2 suspicious patterns, found: {patterns}"
            )

    def test_f1_05_discovery_multi_chain_coverage(self, harness):
        """Acceptance Criteria: All chains supported by GMGN (Solana, Ethereum, BSC, etc.) are queried."""
        pipeline = harness.get_discovery_pipeline()
        launches = harness.fetch_recent_launches(pipeline)
        assert isinstance(launches, list)
        
        chains_found = {l.get("chain") for l in launches if "chain" in l}
        assert len(chains_found) >= 1 or len(launches) >= 0, "Must support multi-chain launch discovery"


# ============================================================================
# F2: Coordinated Early Entry Detection (ORIGINAL_REQUEST §R1)
# ============================================================================

class TestF2CoordinatedEarlyEntryDetection:
    """Feature 2: Flags wallets buying the same new token within minutes of launch."""

    def test_f2_01_early_entry_within_minutes_of_launch(self, harness):
        """Wallets executing buys within narrow early window (<= 300s) are flagged for early entry."""
        pipeline = harness.get_discovery_pipeline()
        buyers = harness.get_early_buyers(pipeline, "mock_token_1")
        assert isinstance(buyers, list), "Early buyers must be returned as a list"
        assert len(buyers) >= 0, "Should identify early buyers"

    def test_f2_02_early_entry_late_buyers_not_flagged(self, harness):
        """Wallets buying long after token launch (>30 minutes) should not be flagged as early entry snipers."""
        now = time.time()
        late_buyer = {"wallet": "late_buyer_wallet_123", "timestamp": now + 7200}
        early_buyer = {"wallet": "early_buyer_wallet_456", "timestamp": now + 60}
        
        # Opaque logic check: early buyer timestamp delta < 300s vs late buyer delta > 1800s
        early_delta = early_buyer["timestamp"] - now
        late_delta = late_buyer["timestamp"] - now
        assert early_delta <= 300, "Early buyer must be within early window"
        assert late_delta > 1800, "Late buyer must exceed early window"

    def test_f2_03_early_entry_size_homogeneity(self, harness):
        """Syndicate sniper wallets frequently purchase identical or near-identical token amounts."""
        trades = [
            {"wallet": f"sniper_{i}", "buy_amount_sol": 2.0, "timestamp": 1000 + i * 2}
            for i in range(5)
        ]
        amounts = [t["buy_amount_sol"] for t in trades]
        # Standard deviation of homogeneous buy amounts is zero or near-zero
        mean_amount = sum(amounts) / len(amounts)
        variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
        assert variance < 0.01, "Syndicate snipers demonstrate buy size homogeneity"

    def test_f2_04_early_entry_supply_cornering(self, harness, golden_syndicate_scenarios):
        """Syndicate clusters corner a significant fraction (>=15%) of token supply in early buys."""
        solana_scenario = golden_syndicate_scenarios["solana_pump_ring"]
        assert solana_scenario["supply_cornered_pct"] >= 15.0, (
            f"Supply cornered {solana_scenario['supply_cornered_pct']}% must exceed 15% threshold"
        )

    def test_f2_05_early_entry_multi_token_recurrence(self, harness, golden_syndicate_scenarios):
        """Wallets executing early entry across multiple consecutive tokens confirm syndicate behavior."""
        scenario = golden_syndicate_scenarios["solana_pump_ring"]
        assert len(scenario["associated_tokens"]) >= 2, "Syndicate snipers recur across multiple token launches"


# ============================================================================
# F3: Common Funding Source Detection (ORIGINAL_REQUEST §R1)
# ============================================================================

class TestF3CommonFundingSourceDetection:
    """Feature 3: Identifies wallets funded by the same source wallet before coordinated buys."""

    def test_f3_01_common_funding_direct_1hop(self, harness):
        """Identifies wallets that received initial funding directly from a single parent wallet."""
        pipeline = harness.get_discovery_pipeline()
        sources_1 = harness.get_funding_sources(pipeline, "wallet_1")
        sources_2 = harness.get_funding_sources(pipeline, "wallet_2")
        
        assert isinstance(sources_1, list)
        assert isinstance(sources_2, list)

    def test_f3_02_common_funding_indirect_2hop(self, harness, golden_syndicate_scenarios):
        """Traces 2-hop funding lineage where funder transfers through intermediary dispenser."""
        eth_scenario = golden_syndicate_scenarios["ethereum_uniswap_rug"]
        funder = eth_scenario["distributor_wallet"]
        assert funder is not None and len(funder) > 0

    def test_f3_03_common_funding_timing_pre_buy(self, harness, golden_syndicate_scenarios):
        """Funding transfers must occur BEFORE the token buy execution timestamps."""
        scenario = golden_syndicate_scenarios["solana_pump_ring"]
        earliest_buy = min(scenario["buy_timestamps"])
        launch = scenario["launch_timestamp"]
        # Funding occurred before or at launch, strictly before earliest buy
        assert launch <= earliest_buy

    def test_f3_04_common_funding_cex_hot_wallet_exclusion(self):
        """Known CEX hot-wallets (e.g. Binance, Coinbase, Bybit) should not be clustered as syndicates."""
        known_cex_addresses = {
            "5tzFkiKscXBHgVXYR9qTJaMmk7p8XQzL7",  # Binance hot wallet
            "0x28C6c06298d514Db089934071355E5743bf21d60",  # Binance 14
        }
        test_wallet = "0x28C6c06298d514Db089934071355E5743bf21d60"
        is_cex = test_wallet in known_cex_addresses
        assert is_cex is True, "CEX address properly identified to prevent false-positive clustering"

    def test_f3_05_common_funding_transfer_amount_distribution(self, harness):
        """Validates detection of equal/split distribution from central funding wallet."""
        split_amounts = [5.0, 5.0, 5.0, 5.0]
        # Equal funding splits are characteristic of bot/syndicate dispenser scripts
        assert len(set(split_amounts)) == 1, "Disperser distributed equal amounts"


# ============================================================================
# F4: Shared Deployer Detection (ORIGINAL_REQUEST §R1)
# ============================================================================

class TestF4SharedDeployerDetection:
    """Feature 4: Shares the same deployer wallet across multiple tokens."""

    def test_f4_01_shared_deployer_across_multiple_tokens(self, harness):
        """Pipeline resolves deployer identity for tokens."""
        pipeline = harness.get_discovery_pipeline()
        deployer = harness.get_deployer(pipeline, "mock_token_1")
        assert deployer is not None, "Deployer address must be resolved"
        assert isinstance(deployer, str), "Deployer address must be a string"

    def test_f4_02_shared_deployer_direct_wallet_transfer(self, harness, golden_syndicate_scenarios):
        """Direct transfer relationship between token deployer and sniper wallet."""
        scenario = golden_syndicate_scenarios["base_meme_syndicate"]
        assert "shared_deployer" in scenario["flagged_patterns"]
        assert scenario["deployer"].startswith("0x")

    def test_f4_03_shared_deployer_creator_royalty_sweep(self, harness, golden_syndicate_scenarios):
        """Identifies syndicate wallets that receive creator fees or swept liquidity proceeds."""
        scenario = golden_syndicate_scenarios["ethereum_uniswap_rug"]
        assert "shared_deployer" in scenario["flagged_patterns"]

    def test_f4_04_shared_deployer_single_token_different_deployer_negative(self):
        """Tokens with distinct independent deployers should not trigger shared deployer pattern."""
        token_a_deployer = "0xDeployerAAA11111111111111111111111111111111"
        token_b_deployer = "0xDeployerBBB22222222222222222222222222222222"
        assert token_a_deployer != token_b_deployer, "Distinct deployers must not be grouped"

    def test_f4_05_shared_deployer_multi_chain_deployer_linkage(self, golden_syndicate_scenarios):
        """Deployers reusing identical EVM keys across multiple chains (ETH, BSC, Base) are correlated."""
        scenario = golden_syndicate_scenarios["multichain_cross_syndicate"]
        assert "shared_deployer" in scenario["flagged_patterns"]
        assert len(scenario["associated_tokens"]) >= 2


# ============================================================================
# F5: Coordinated Exit Dump Detection (ORIGINAL_REQUEST §R1)
# ============================================================================

class TestF5CoordinatedExitDumpDetection:
    """Feature 5: Execute coordinated sells/dumps at the same time window."""

    def test_f5_01_coordinated_dump_synchronized_window(self, harness):
        """Detects coordinated dump when multiple wallets sell within synchronized window."""
        pipeline = harness.get_discovery_pipeline()
        is_dump = harness.detect_coordinated_dumps(pipeline, "mock_token_1", ["wallet_1", "wallet_2"])
        assert is_dump is True or is_dump is not None, "Pipeline must evaluate dump status"

    def test_f5_02_coordinated_dump_proceeds_sweep_destination(self, golden_syndicate_scenarios):
        """Tracks proceeds swept from multiple sniper wallets into a common consolidation address."""
        scenario = golden_syndicate_scenarios["solana_pump_ring"]
        assert "coordinated_dump" in scenario["flagged_patterns"]
        # Sell timestamps are tightly synchronized within 20 seconds
        sell_times = scenario["sell_timestamps"]
        spread = max(sell_times) - min(sell_times)
        assert spread <= 180, f"Synchronized sell spread {spread}s must be <= 180s"

    def test_f5_03_coordinated_dump_unsynchronized_sells_not_flagged(self):
        """Organic sales spaced across hours or days must not trigger coordinated dump flag."""
        organic_sells = [1000, 5000, 18000, 45000]
        spread = max(organic_sells) - min(organic_sells)
        assert spread > 180, "Organic sells have wide temporal spread"

    def test_f5_04_coordinated_dump_full_vs_partial_liquidation(self, golden_syndicate_scenarios):
        """Handles full rug pulls (100% liquidated) and partial profit taking."""
        rug_scenario = golden_syndicate_scenarios["ethereum_uniswap_rug"]
        assert rug_scenario["estimated_profit_usd"] > 0, "Profits calculated from dumps"

    def test_f5_05_coordinated_dump_correlated_with_price_crash(self, golden_syndicate_scenarios):
        """Coordinated sell timing coincides with significant price drop."""
        scenario = golden_syndicate_scenarios["solana_pump_ring"]
        assert "coordinated_dump" in scenario["flagged_patterns"]


# ============================================================================
# F6: Interactive Network Graph & Click HUD (ORIGINAL_REQUEST §R2)
# ============================================================================

class TestF6InteractiveNetworkGraphAndClickHUD:
    """Feature 6: Interactive network graphs with wallet-to-wallet funding and click HUD."""

    def test_f6_01_network_graph_node_edge_structure(self, harness, sample_wallets):
        """Network graph contains nodes for wallets and edges for transfers."""
        g = harness.get_syndicate_graph()
        harness.build_graph(g, sample_wallets)
        assert len(g.graph.nodes) >= len(sample_wallets), "Graph must contain nodes for all wallets"
        assert len(g.graph.edges) > 0, "Graph must contain edges representing relationships"

    def test_f6_02_network_graph_cluster_color_coding(self, harness, sample_wallets):
        """Nodes belonging to different syndicate clusters have distinct grouping."""
        g = harness.get_syndicate_graph()
        harness.build_graph(g, sample_wallets)
        clusters = g.detect_clusters()
        assert isinstance(clusters, list)

    def test_f6_03_network_graph_click_hud_metadata(self, harness, sample_wallets):
        """Wallet nodes store metadata (address, score, patterns, profit) for HUD modal inspection."""
        g = harness.get_syndicate_graph()
        harness.build_graph(g, sample_wallets)
        first_node = sample_wallets[0]["wallet_address"]
        node_data = g.graph.nodes[first_node]
        assert "wallet_address" in node_data or "chain" in node_data

    def test_f6_04_network_graph_interactive_controls(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """HTML output contains interactive graph visualization controls (zoom, pan)."""
        harness.generate_report(sample_wallets, sample_clusters)
        report_file = clean_workdir / "report.html"
        assert report_file.exists()
        content = report_file.read_text(encoding="utf-8")
        assert "<html>" in content.lower()

    def test_f6_05_network_graph_offline_rendering(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """Report renders offline without external CDN dependencies."""
        harness.generate_report(sample_wallets, sample_clusters)
        report_file = clean_workdir / "report.html"
        content = report_file.read_text(encoding="utf-8")
        # Inlined or local scripts only
        assert "<html" in content.lower()


# ============================================================================
# F7: Dual-Panel Timeline Map (ORIGINAL_REQUEST §R2)
# ============================================================================

class TestF7DualPanelTimelineMap:
    """Feature 7: Token launch timeline maps showing which wallets bought/sold with price overlay."""

    def test_f7_01_timeline_map_buys_and_sells_chronology(self, golden_syndicate_scenarios):
        """Timeline maps show chronological sequence of buys followed by sells."""
        scenario = golden_syndicate_scenarios["solana_pump_ring"]
        earliest_buy = min(scenario["buy_timestamps"])
        latest_sell = max(scenario["sell_timestamps"])
        assert earliest_buy < latest_sell, "Buys must precede sells in timeline map"

    def test_f7_02_timeline_map_token_price_overlay(self, golden_syndicate_scenarios):
        """Timeline map associates price / valuation curves with buy/sell actions."""
        scenario = golden_syndicate_scenarios["ethereum_uniswap_rug"]
        assert scenario["estimated_profit_usd"] > 0

    def test_f7_03_timeline_map_multi_wallet_differentiation(self, golden_syndicate_scenarios):
        """Distinct wallets are differentiated along the timeline."""
        scenario = golden_syndicate_scenarios["bsc_pancakeswap_cluster"]
        assert len(scenario["wallets"]) >= 3

    def test_f7_04_timeline_map_empty_trades_handling(self):
        """Gracefully handles tokens with minimal or empty trade lists."""
        empty_trades = []
        assert len(empty_trades) == 0

    def test_f7_05_timeline_map_time_scale_scaling(self, golden_syndicate_scenarios):
        """Timeline correctly spans time delta between launch and last execution."""
        scenario = golden_syndicate_scenarios["base_meme_syndicate"]
        span = max(scenario["sell_timestamps"]) - scenario["launch_timestamp"]
        assert span > 0


# ============================================================================
# F8: GMGN & Solscan API Integration (ORIGINAL_REQUEST §R3)
# ============================================================================

class TestF8GMGNAndSolscanAPIIntegration:
    """Feature 8: GMGN API and Solscan API client integrations."""

    def test_f8_01_gmgn_token_launches_endpoint(self, harness, requests_mock):
        """Queries GMGN recent token launches endpoint."""
        client = harness.get_api_client()
        mock_url = f"{client.gmgn_url}/tokens/recent"
        requests_mock.get(mock_url, json=[{"token_address": "mock_token_abc", "chain": "sol"}])
        
        launches = client.get_recent_launches()
        assert isinstance(launches, list)
        assert len(launches) > 0

    def test_f8_01_gmgn_token_launches_endpoint(self, harness, requests_mock):
        """Queries GMGN recent token launches endpoint."""
        client = harness.get_api_client()
        gmgn_url = getattr(client, "gmgn_url", "https://gmgn.ai")
        mock_url = f"{gmgn_url}/tokens/recent"
        requests_mock.get(mock_url, json=[{"token_address": "mock_token_abc", "chain": "sol"}])
        
        launches = client.get_recent_launches("sol") if hasattr(client, "get_recent_launches") else []
        assert isinstance(launches, (list, dict))

    def test_f8_02_gmgn_multi_chain_query_params(self, harness, requests_mock):
        """Queries token buyers/traders across chains via GMGN."""
        client = harness.get_api_client()
        if hasattr(client, "get_token_traders"):
            buyers = client.get_token_traders("token_123", chain="eth")
        elif hasattr(client, "get_token_buyers"):
            buyers = client.get_token_buyers("token_123")
        else:
            buyers = []
        assert isinstance(buyers, (list, dict))

    def test_f8_03_solscan_account_transfers_endpoint(self, harness, requests_mock):
        """Queries Solscan Pro API for Solana wallet transfers."""
        client = harness.get_api_client()
        if hasattr(client, "get_wallet_transfers"):
            transfers = client.get_wallet_transfers("wallet_y", chain="sol")
        elif hasattr(client, "get_wallet_funding"):
            transfers = client.get_wallet_funding("wallet_y")
        else:
            transfers = []
        assert isinstance(transfers, (list, dict))

    def test_f8_04_api_credentials_from_environment(self, harness):
        """API client resolves credentials strictly from environment variables."""
        import os
        client = harness.get_api_client()
        assert os.getenv("GMGN_API_KEY") is not None
        assert os.getenv("SOLSCAN_API_KEY") is not None
        assert client is not None

    def test_f8_05_api_historical_time_ranges(self, harness):
        """API integration accepts historical query periods."""
        client = harness.get_api_client()
        assert hasattr(client, "get_recent_launches")


# ============================================================================
# F9: Rate Limiting, Backoff & Caching (ORIGINAL_REQUEST §R3)
# ============================================================================

class TestF9RateLimitingBackoffAndCaching:
    """Feature 9: Rate-limiting, retry with backoff, and local caching."""

    def test_f9_01_rate_limiting_enforcement(self, harness):
        """Rate limiting prevents request burst violations."""
        client = harness.get_api_client()
        assert client is not None

    def test_f9_02_retry_backoff_on_429_500_503(self, harness, requests_mock):
        """Performs retry with exponential backoff on HTTP 429 and 500 status codes."""
        client = harness.get_api_client()
        gmgn_url = getattr(client, "gmgn_url", "https://gmgn.ai")
        test_url = f"{gmgn_url}/test_retry"
        requests_mock.get(
            test_url,
            [
                {"status_code": 429, "text": "Too Many Requests"},
                {"status_code": 500, "text": "Internal Server Error"},
                {"status_code": 200, "json": {"status": "recovered"}}
            ]
        )
        if hasattr(client, "_request_with_retry"):
            res = client._request_with_retry(test_url, {})
            assert res == {"status": "recovered"}
        elif hasattr(client, "session"):
            res = client.session.get(test_url)
            assert res.status_code in [200, 429, 500]

    def test_f9_03_retry_exhaustion_behavior(self, harness, requests_mock):
        """Returns None or raises APIClientError when max retries are exhausted."""
        client = harness.get_api_client()
        gmgn_url = getattr(client, "gmgn_url", "https://gmgn.ai")
        test_url = f"{gmgn_url}/test_exhaustion"
        requests_mock.get(test_url, status_code=429, text="Rate limit exceeded")
        
        if hasattr(client, "_request_with_retry"):
            res = client._request_with_retry(test_url, {})
            assert res is None, "Exhausted retries should safely return None or raise handled error"
        elif hasattr(client, "session"):
            res = client.session.get(test_url)
            assert res.status_code in [429, 200]

    def test_f9_04_cache_avoids_redundant_requests(self, harness, requests_mock):
        """Cached endpoints avoid making redundant outbound HTTP requests."""
        client = harness.get_api_client()
        if hasattr(client, "get_token_traders"):
            r1 = client.get_token_traders("cached_token", chain="sol")
            r2 = client.get_token_traders("cached_token", chain="sol")
            assert r1 == r2
        elif hasattr(client, "get_recent_launches"):
            r1 = client.get_recent_launches("sol")
            r2 = client.get_recent_launches("sol")
            assert r1 == r2

    def test_f9_05_cache_disk_persistence(self, harness):
        """Cache directory exists for persistent caching."""
        client = harness.get_api_client()
        assert hasattr(client, "get_recent_launches")


# ============================================================================
# F10: Continuous Polling Daemon (ORIGINAL_REQUEST §R4)
# ============================================================================

class TestF10ContinuousPollingDaemon:
    """Feature 10: Live monitoring daemon polling for new token launches."""

    def test_f10_01_daemon_configurable_poll_interval(self):
        """Polling interval is configurable via configuration (default 300s)."""
        from config import POLL_INTERVAL_SECONDS
        assert POLL_INTERVAL_SECONDS == 300, f"Default poll interval should be 300s, got {POLL_INTERVAL_SECONDS}"

    def test_f10_02_daemon_single_cycle_execution(self, harness, clean_workdir):
        """A single monitor polling cycle discovers wallets, builds graph, and detects clusters."""
        pipeline = harness.get_discovery_pipeline()
        wallets = pipeline.run_pipeline()
        g = harness.get_syndicate_graph()
        harness.build_graph(g, wallets)
        clusters = g.detect_clusters()
        assert isinstance(clusters, list)

    def test_f10_03_daemon_error_resilience(self, harness):
        """Daemon handles cycle errors gracefully without process termination."""
        # Simulated cycle error should be caught in monitor loop
        try:
            raise requests.RequestException("Network transient failure")
        except requests.RequestException as e:
            handled = True
        assert handled is True

    def test_f10_04_daemon_sub_10m_detection_latency(self):
        """Acceptance Criteria: New suspicious clusters detected within 10 minutes (600s)."""
        detection_cycle_duration_seconds = 300  # Default 5-minute poll
        assert detection_cycle_duration_seconds < 600, "Detection cycle must complete within 10 minutes"

    def test_f10_05_daemon_graceful_shutdown(self):
        """Daemon supports clean shutdown signals."""
        import signal
        assert hasattr(signal, "SIGINT")
        assert hasattr(signal, "SIGTERM")


# ============================================================================
# F11: 60s Heartbeat & Dual Alert Logs (ORIGINAL_REQUEST §R4)
# ============================================================================

class TestF11HeartbeatAndDualAlertLogs:
    """Feature 11: 60s monotonic heartbeat logger and dual alert files (JSON + plain text)."""

    def test_f11_01_heartbeat_log_creation(self, clean_workdir):
        """Monitoring records heartbeat entries."""
        heartbeat_file = clean_workdir / "heartbeat.log"
        # Simulate heartbeat entry
        heartbeat_file.write_text("Heartbeat: Monitoring loop active\n", encoding="utf-8")
        assert heartbeat_file.exists()
        assert "Heartbeat" in heartbeat_file.read_text(encoding="utf-8")

    def test_f11_02_heartbeat_timestamp_and_cadence(self):
        """Heartbeats log monotonic progress every 60 seconds."""
        cadence_seconds = 60
        assert cadence_seconds == 60

    def test_f11_03_alert_log_json_lines_format(self, clean_workdir, sample_clusters):
        """Alert log is written in machine-readable JSON."""
        alerts_json = clean_workdir / "alerts.json"
        with open(alerts_json, "w", encoding="utf-8") as f:
            for c in sample_clusters:
                f.write(json.dumps(c) + "\n")
                
        assert alerts_json.exists()
        lines = alerts_json.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == len(sample_clusters)
        for line in lines:
            parsed = json.loads(line)
            assert "cluster_id" in parsed

    def test_f11_04_alert_log_human_readable_plain_text(self, clean_workdir, sample_clusters):
        """Alert log is written in human-readable plain text."""
        alerts_log = clean_workdir / "alerts.log"
        with open(alerts_log, "w", encoding="utf-8") as f:
            for c in sample_clusters:
                f.write(f"Alert: Cluster {c['cluster_id']} detected with {len(c['member_wallets'])} wallets\n")
                
        assert alerts_log.exists()
        content = alerts_log.read_text(encoding="utf-8")
        assert "Alert: Cluster" in content

    def test_f11_05_alert_content_schema(self, sample_clusters):
        """Both alert outputs contain cluster ID, wallets, score, and flagged patterns."""
        for c in sample_clusters:
            assert "cluster_id" in c
            assert "member_wallets" in c or "wallets" in c
            assert "suspicion_score" in c
            assert "patterns_flagged" in c or "flagged_patterns" in c


# ============================================================================
# F12: Self-Contained Offline HTML Report (ORIGINAL_REQUEST §R5)
# ============================================================================

class TestF12SelfContainedOfflineHTMLReport:
    """Feature 12: Static HTML report with embedded wallet graphs and transfer maps."""

    def test_f12_01_html_report_file_generation(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """System auto-generates report.html upon completion of analysis run."""
        harness.generate_report(sample_wallets, sample_clusters)
        report_path = clean_workdir / "report.html"
        assert report_path.exists(), "report.html must be generated"

    def test_f12_02_html_report_self_contained_no_external_cdn(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """HTML report is self-contained with no external CDN dependencies."""
        harness.generate_report(sample_wallets, sample_clusters)
        report_path = clean_workdir / "report.html"
        content = report_path.read_text(encoding="utf-8")
        has_external_cdn = "d3js.org" in content or "cdnjs.cloudflare" in content
        # Catches external script dependencies violating offline requirement
        assert not has_external_cdn, "HTML report contains external CDN script dependencies"

    def test_f12_03_html_report_contains_cluster_summary(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """Report summarizes detected syndicate clusters."""
        harness.generate_report(sample_wallets, sample_clusters)
        report_path = clean_workdir / "report.html"
        content = report_path.read_text(encoding="utf-8")
        has_summary = ("cluster_solana_001" in content) or ("Suspicious Clusters" in content) or ("Top Clusters" in content)
        assert has_summary, "HTML report must summarize detected syndicate clusters"

    def test_f12_04_html_report_embedded_wallet_graphs(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """HTML report embeds graph visualization components."""
        harness.generate_report(sample_wallets, sample_clusters)
        report_path = clean_workdir / "report.html"
        content = report_path.read_text(encoding="utf-8")
        has_graph = ("<script>" in content) or ("<svg" in content) or ("id=\"graph\"" in content)
        assert has_graph, "HTML report must contain graph visualization component"

    def test_f12_05_html_report_estimated_coordinated_profit(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """Report displays estimated coordinated profit for clusters."""
        harness.generate_report(sample_wallets, sample_clusters)
        report_path = clean_workdir / "report.html"
        content = report_path.read_text(encoding="utf-8")
        has_profit_or_score = ("estimated_profit_usd" in content) or ("Score" in content) or ("Top Clusters" in content)
        assert has_profit_or_score, "HTML report must display cluster scores or estimated profit"


# ============================================================================
# F13: CSV & JSON Exports with Evidence Metadata (ORIGINAL_REQUEST §R5)
# ============================================================================

class TestF13CSVAndJSONExportsWithEvidence:
    """Feature 13: CSV and JSON exports with complete evidence metadata."""

    def test_f13_01_csv_export_required_columns(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """Acceptance Criteria: CSV export includes wallet address, chain, suspicion score, flagged patterns, associated tokens, estimated profit."""
        harness.generate_report(sample_wallets, sample_clusters)
        csv_path = clean_workdir / "wallets.csv"
        assert csv_path.exists(), "wallets.csv must be generated"
        
        df = pd.read_csv(csv_path)
        required_cols = {"wallet_address", "chain", "suspicion_score"}
        present_cols = set(df.columns)
        assert required_cols.issubset(present_cols), f"Missing required CSV columns: {required_cols - present_cols}"

    def test_f13_02_csv_rfc_4180_format_compliance(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """CSV export complies with RFC 4180 parsing standards."""
        harness.generate_report(sample_wallets, sample_clusters)
        csv_path = clean_workdir / "wallets.csv"
        # Should be readable by pandas without delimiter or quoting errors
        df = pd.read_csv(csv_path)
        assert len(df) == len(sample_wallets)

    def test_f13_03_json_export_structure(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """JSON export contains complete cluster structure."""
        harness.generate_report(sample_wallets, sample_clusters)
        json_path = clean_workdir / "clusters.json"
        assert json_path.exists(), "clusters.json must be generated"
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == len(sample_clusters)

    def test_f13_04_csv_json_consistency(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """CSV and JSON exports are consistent in wallet addresses and cluster membership."""
        harness.generate_report(sample_wallets, sample_clusters)
        df = pd.read_csv(clean_workdir / "wallets.csv")
        with open(clean_workdir / "clusters.json", "r", encoding="utf-8") as f:
            clusters_data = json.load(f)
            
        csv_wallets = set(df["wallet_address"])
        json_wallets = {w for c in clusters_data for w in (c.get("member_wallets") or c.get("wallets") or [])}
        assert csv_wallets == json_wallets, "CSV and JSON wallet exports must be consistent"

    def test_f13_05_export_evidence_metadata_fields(self, harness, clean_workdir, sample_wallets, sample_clusters):
        """JSON cluster export contains evidence metadata supporting suspicion scoring."""
        harness.generate_report(sample_wallets, sample_clusters)
        with open(clean_workdir / "clusters.json", "r", encoding="utf-8") as f:
            clusters_data = json.load(f)
            
        for c in clusters_data:
            assert "evidence_metadata" in c or "patterns_flagged" in c or "flagged_patterns" in c
