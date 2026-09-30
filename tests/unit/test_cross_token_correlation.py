"""Unit and adversarial test suite for Milestone 14: Cross-Token Campaign Correlation.

Verifies:
1. Mathematical Jaccard wallet overlap calculations.
2. Shared root funder correlation and lineage clustering.
3. Multi-token campaign classification (SERIAL_PUMP_AND_DUMP, DEPLOYER_CLONE_FACTORY, PARALLEL_LAUNCH_RING).
4. Profit and token aggregation across participating clusters.
5. 3D campaign bridge generation.
6. Concurrent multi-token scanning via LiveSyndicateScanner.
7. Resilience against malformed cluster payloads and edge cases.
"""

import unittest
from typing import Any, Dict, List

from crypto_syndicate.correlator import CrossTokenCorrelator, SyndicateCampaign
from crypto_syndicate.scanner import LiveSyndicateScanner


class TestCrossTokenCorrelator(unittest.TestCase):
    """Unit tests for CrossTokenCorrelator algorithms and data models."""

    def setUp(self):
        self.correlator = CrossTokenCorrelator(min_wallet_overlap=0.20, min_semantic_sim=0.75)

    def test_jaccard_wallet_overlap_exact_match(self):
        wallets = ["WalletA111", "WalletB222", "WalletC333"]
        jaccard = CrossTokenCorrelator.compute_jaccard(wallets, wallets)
        self.assertAlmostEqual(jaccard, 1.0, places=4)

    def test_jaccard_wallet_overlap_disjoint(self):
        w_a = ["WalletA111", "WalletB222"]
        w_b = ["WalletC333", "WalletD444"]
        jaccard = CrossTokenCorrelator.compute_jaccard(w_a, w_b)
        self.assertEqual(jaccard, 0.0)

    def test_jaccard_wallet_overlap_partial(self):
        # 2 in intersection, 4 in union -> 2 / 4 = 0.50
        w_a = ["W1", "W2", "W3"]
        w_b = ["W2", "W3", "W4"]
        jaccard = CrossTokenCorrelator.compute_jaccard(w_a, w_b)
        self.assertAlmostEqual(jaccard, 0.50, places=4)

    def test_jaccard_case_insensitivity_and_empty(self):
        w_a = ["wallet1", "WALLET2"]
        w_b = ["WALLET1", "wallet2"]
        self.assertAlmostEqual(CrossTokenCorrelator.compute_jaccard(w_a, w_b), 1.0)
        self.assertEqual(CrossTokenCorrelator.compute_jaccard([], ["W1"]), 0.0)
        self.assertEqual(CrossTokenCorrelator.compute_jaccard([], []), 0.0)

    def test_shared_root_funder_correlation(self):
        clusters = [
            {
                "cluster_id": "CLUST-1",
                "identity_id": "SYND-0001",
                "token_address": "TokenA1111",
                "token_symbol": "TOKA",
                "wallets": ["W1", "W2", "W3"],
                "root_funder": "MasterFunder1111",
                "estimated_profit_usd": 150000.0,
            },
            {
                "cluster_id": "CLUST-2",
                "identity_id": "SYND-0002",
                "token_address": "TokenB2222",
                "token_symbol": "TOKB",
                "wallets": ["W4", "W5", "W6"],
                "root_funder": "MasterFunder1111",
                "estimated_profit_usd": 200000.0,
            },
        ]
        campaigns = self.correlator.correlate_clusters(clusters)
        self.assertEqual(len(campaigns), 1)
        c = campaigns[0]
        self.assertEqual(c.shared_root_funder, "MasterFunder1111")
        self.assertEqual(c.campaign_type, "DEPLOYER_CLONE_FACTORY")
        self.assertIn("TOKA", c.token_symbols)
        self.assertIn("TOKB", c.token_symbols)
        self.assertAlmostEqual(c.total_profit_usd, 350000.0)

    def test_campaign_clustering_serial_pump(self):
        # Both shared funder AND overlapping wallets -> SERIAL_PUMP_AND_DUMP
        clusters = [
            {
                "cluster_id": "CLUST-1",
                "identity_id": "SYND-0001",
                "token_address": "TokenA1111",
                "token_symbol": "BELUGA",
                "wallets": ["SniperA", "SniperB", "SniperC"],
                "root_funder": "MasterFunder1111",
                "estimated_profit_usd": 300000.0,
            },
            {
                "cluster_id": "CLUST-2",
                "identity_id": "SYND-0002",
                "token_address": "TokenB2222",
                "token_symbol": "SNIPEX",
                "wallets": ["SniperB", "SniperC", "SniperD"],
                "root_funder": "MasterFunder1111",
                "estimated_profit_usd": 450000.0,
            },
        ]
        campaigns = self.correlator.correlate_clusters(clusters)
        self.assertEqual(len(campaigns), 1)
        c = campaigns[0]
        self.assertEqual(c.campaign_type, "SERIAL_PUMP_AND_DUMP")
        self.assertIn("SniperB", c.reused_wallets)
        self.assertIn("SniperC", c.reused_wallets)
        self.assertAlmostEqual(c.total_profit_usd, 750000.0)
        self.assertGreaterEqual(c.confidence_score, 0.90)

    def test_shared_root_funder_ignored_if_empty_or_placeholder(self):
        clusters = [
            {
                "cluster_id": "CLUST-1",
                "identity_id": "SYND-0001",
                "token_address": "TokenA1111",
                "token_symbol": "TOKA",
                "wallets": ["W1", "W2"],
                "root_funder": "--",
            },
            {
                "cluster_id": "CLUST-2",
                "identity_id": "SYND-0002",
                "token_address": "TokenB2222",
                "token_symbol": "TOKB",
                "wallets": ["W3", "W4"],
                "root_funder": "--",
            },
        ]
        campaigns = self.correlator.correlate_clusters(clusters)
        self.assertEqual(len(campaigns), 0)

    def test_correlate_clusters_single_or_empty(self):
        self.assertEqual(self.correlator.correlate_clusters([]), [])
        self.assertEqual(self.correlator.correlate_clusters([{"wallets": ["W1"]}]), [])

    def test_campaign_bridges_generation(self):
        camp = SyndicateCampaign(
            campaign_id="CAMP-0001",
            name="Test Campaign",
            token_addresses=["TokA", "TokB"],
            token_symbols=["TOKA", "TOKB"],
            syndicate_ids=["SYND-0001", "SYND-0002"],
            reused_wallets=["W1"],
            confidence_score=0.95,
        )
        clusters = [
            {"id": "SYND-0001", "center": [0, 0, 0]},
            {"id": "SYND-0002", "center": [100, 0, 100]},
        ]
        bridges = CrossTokenCorrelator.generate_campaign_bridges([camp], clusters)
        self.assertEqual(len(bridges), 1)
        b = bridges[0]
        self.assertEqual(b["source_cluster"], "SYND-0001")
        self.assertEqual(b["target_cluster"], "SYND-0002")
        self.assertEqual(b["type"], "campaign_bridge")
        self.assertEqual(b["color"], "#f59e0b")

    def test_min_overlap_threshold_filtering(self):
        # 1 overlapping wallet out of 10 -> 1/9 = 0.111 (< 0.20 threshold)
        w_a = [f"W{i}" for i in range(5)]
        w_b = ["W4"] + [f"WB{i}" for i in range(4)]
        clusters = [
            {"cluster_id": "C1", "token_address": "T1", "wallets": w_a, "root_funder": None},
            {"cluster_id": "C2", "token_address": "T2", "wallets": w_b, "root_funder": None},
        ]
        campaigns = self.correlator.correlate_clusters(clusters)
        self.assertEqual(len(campaigns), 0)

    def test_campaign_to_dict_serialization(self):
        camp = SyndicateCampaign(
            campaign_id="CAMP-0001",
            name="Test Serial Ring",
            token_addresses=["TokA", "TokB"],
            token_symbols=["TOKA", "TOKB"],
            syndicate_ids=["SYND-0001", "SYND-0002"],
            reused_wallets=["W1", "W2"],
            shared_root_funder="Fund1",
            jaccard_overlap=0.3333,
            semantic_similarity=0.8888,
            total_profit_usd=500000.0,
            campaign_type="SERIAL_PUMP_AND_DUMP",
            confidence_score=0.95,
        )
        d = camp.to_dict()
        self.assertEqual(d["campaign_id"], "CAMP-0001")
        self.assertEqual(d["reused_wallets_count"], 2)
        self.assertEqual(d["campaign_type"], "SERIAL_PUMP_AND_DUMP")
        self.assertEqual(d["shared_root_funder"], "Fund1")


class TestLiveScannerConcurrencyAndCampaigns(unittest.TestCase):
    """Tests concurrent token ingestion and campaign integration in LiveSyndicateScanner."""

    def setUp(self):
        self.scanner = LiveSyndicateScanner(mock_mode=True, enable_vector_store=False)

    def test_concurrent_multi_token_scanning(self):
        tokens = self.scanner.fetch_trending_tokens(limit=3)
        self.assertGreaterEqual(len(tokens), 2)
        results = self.scanner.scan_tokens_concurrently(tokens, max_workers=2)
        self.assertEqual(len(results), len(tokens))
        for r in results:
            self.assertIn("cluster_id", r)
            self.assertIn("wallets", r)
            self.assertIn("token_symbol", r)

    def test_scanner_correlate_cross_token_campaigns(self):
        tokens = self.scanner.fetch_trending_tokens(limit=3)
        clusters = self.scanner.scan_tokens_concurrently(tokens, max_workers=2)
        camps = self.scanner.correlate_cross_token_campaigns(clusters)
        self.assertIsInstance(camps, list)
        self.assertEqual(camps, self.scanner.discovered_campaigns)

    def test_4d_temporal_state_includes_campaigns(self):
        tokens = self.scanner.fetch_trending_tokens(limit=2)
        clusters = self.scanner.scan_tokens_concurrently(tokens, max_workers=2)
        state_4d = self.scanner.generate_4d_temporal_state(clusters)
        self.assertIn("campaigns", state_4d)
        self.assertIn("campaigns_count", state_4d["stats"])
        self.assertIsInstance(state_4d["campaigns"], list)

    def test_adversarial_malformed_clusters_resilience(self):
        correlator = CrossTokenCorrelator()
        malformed_clusters = [
            {"invalid_key": None},
            {"cluster_id": None, "wallets": None, "root_funder": None},
            {"token_address": "T1", "wallets": ["W1", None, 123]},  # non-string or None wallet
            {},
        ]
        # Should execute safely without uncaught exceptions
        campaigns = correlator.correlate_clusters(malformed_clusters)
        self.assertEqual(campaigns, [])


if __name__ == "__main__":
    unittest.main()
