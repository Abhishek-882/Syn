"""Unit and adversarial test suite for WalletVectorStore (M13)."""

import os
import shutil
import tempfile
import unittest
from typing import Any, Dict

from crypto_syndicate.fingerprint import SyndicateBehavior
from crypto_syndicate.vector_store import WalletVectorStore


class TestVectorStoreInit(unittest.TestCase):
    """Test WalletVectorStore initialization and collection management."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="qdrant_test_")
        self.store = WalletVectorStore(path=self.tmp_dir, force_memory=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_init_creates_collection(self):
        self.assertEqual(self.store.COLLECTION_NAME, "wallet_fingerprints")
        self.assertEqual(self.store.vector_dim, 768)
        stats = self.store.get_collection_stats()
        self.assertEqual(stats["collection_name"], "wallet_fingerprints")
        self.assertEqual(stats["total_points"], 0)

    def test_deterministic_address_uuid(self):
        id1 = self.store._address_to_id("7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU")
        id2 = self.store._address_to_id("7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU")
        id3 = self.store._address_to_id("7xkxtg2cw87d97txjsdpbd5jbkhetqa83tzrujosgasu")  # Case insensitive
        self.assertEqual(id1, id2)
        self.assertEqual(id1, id3)


class TestVectorStoreUpsertAndQuery(unittest.TestCase):
    """Test upserting fingerprints and semantic similarity queries."""

    def setUp(self):
        self.store = WalletVectorStore(force_memory=True)

    def tearDown(self):
        self.store.clear_collection()

    def test_single_wallet_upsert(self):
        behavior = SyndicateBehavior(
            sniper_count=4,
            avg_buy_delay_s=14.2,
            avg_hold_duration_s=7.5,
            bundler_rate=0.68,
            is_jito_bundle=True,
            jito_confidence=0.92,
            jito_signals=["CANONICAL_TIP", "CPI_INNER"],
            patterns_flagged=["sniper", "bundler", "jito_bundle"],
        )
        point_id = self.store.upsert_wallet(
            wallet_address="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            behavior=behavior,
            cluster_id="SYND-0001",
            chain="sol",
        )
        self.assertTrue(len(point_id) > 10)
        stats = self.store.get_collection_stats()
        self.assertEqual(stats["total_points"], 1)

    def test_idempotent_reupsert(self):
        behavior = SyndicateBehavior(
            sniper_count=2,
            avg_buy_delay_s=15.0,
            avg_hold_duration_s=10.0,
            bundler_rate=0.50,
        )
        addr = "4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX"
        id1 = self.store.upsert_wallet(addr, behavior)
        id2 = self.store.upsert_wallet(addr, behavior)
        self.assertEqual(id1, id2)
        stats = self.store.get_collection_stats()
        self.assertEqual(stats["total_points"], 1)

    def test_batch_upsert(self):
        wallets = [
            {
                "address": f"SniperWallet_{i:02d}_Test11111111111111111111111111",
                "behavior": SyndicateBehavior(
                    sniper_count=3,
                    avg_buy_delay_s=12.0 + i,
                    avg_hold_duration_s=8.0,
                    bundler_rate=0.60,
                    is_jito_bundle=True,
                ),
                "cluster_id": "SYND-0001",
            }
            for i in range(5)
        ]
        count = self.store.upsert_batch(wallets)
        self.assertEqual(count, 5)
        stats = self.store.get_collection_stats()
        self.assertEqual(stats["total_points"], 5)

    def test_find_similar_semantic_clustering(self):
        # 1. Fast Jito Snipers
        sniper1 = SyndicateBehavior(
            sniper_count=5,
            avg_buy_delay_s=13.0,
            avg_hold_duration_s=7.0,
            bundler_rate=0.75,
            is_jito_bundle=True,
            jito_confidence=0.95,
            patterns_flagged=["sniper", "bundler", "jito_bundle"],
        )
        sniper2 = SyndicateBehavior(
            sniper_count=4,
            avg_buy_delay_s=14.0,
            avg_hold_duration_s=8.0,
            bundler_rate=0.70,
            is_jito_bundle=True,
            jito_confidence=0.90,
            patterns_flagged=["sniper", "bundler", "jito_bundle"],
        )
        # 2. Slow Organic Trader
        slow_trader = SyndicateBehavior(
            sniper_count=0,
            avg_buy_delay_s=1200.0,
            avg_hold_duration_s=86400.0,
            bundler_rate=0.0,
            is_jito_bundle=False,
            jito_confidence=0.0,
            patterns_flagged=[],
        )

        self.store.upsert_wallet("Sniper_Alpha_1111111111111111111111111111", sniper1, cluster_id="SYND-0001")
        self.store.upsert_wallet("Sniper_Beta_2222222222222222222222222222", sniper2, cluster_id="SYND-0001")
        self.store.upsert_wallet("Slow_Trader_999999999999999999999999999", slow_trader, cluster_id="ORGANIC")

        # Query with another sniper behavior
        query_sniper = SyndicateBehavior(
            sniper_count=4,
            avg_buy_delay_s=13.5,
            avg_hold_duration_s=7.5,
            bundler_rate=0.72,
            is_jito_bundle=True,
            jito_confidence=0.92,
            patterns_flagged=["sniper", "bundler"],
        )
        matches = self.store.find_similar(query_sniper, top_k=3)
        self.assertEqual(len(matches), 3)
        # The top two matches must be the snipers, not the slow trader
        top_addrs = [m["address"] for m in matches[:2]]
        self.assertIn("Sniper_Alpha_1111111111111111111111111111", top_addrs)
        self.assertIn("Sniper_Beta_2222222222222222222222222222", top_addrs)
        self.assertTrue(matches[0]["similarity"] > matches[2]["similarity"])

    def test_find_similar_by_address_excludes_self(self):
        behavior = SyndicateBehavior(
            sniper_count=3,
            avg_buy_delay_s=15.0,
            bundler_rate=0.55,
        )
        addr1 = "TargetWallet1111111111111111111111111111111"
        addr2 = "PeerWallet222222222222222222222222222222222"
        self.store.upsert_wallet(addr1, behavior)
        self.store.upsert_wallet(addr2, behavior)

        results = self.store.find_similar_by_address(addr1, top_k=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["address"], addr2)

    def test_delete_wallet(self):
        behavior = SyndicateBehavior(bundler_rate=0.5)
        addr = "ToDeleteWallet11111111111111111111111111111"
        self.store.upsert_wallet(addr, behavior)
        self.assertEqual(self.store.get_collection_stats()["total_points"], 1)

        ok = self.store.delete_wallet(addr)
        self.assertTrue(ok)
        self.assertEqual(self.store.get_collection_stats()["total_points"], 0)

    def test_empty_collection_query(self):
        behavior = SyndicateBehavior()
        results = self.store.find_similar(behavior, top_k=5)
        self.assertEqual(results, [])

    def test_dict_behavior_input(self):
        dict_behavior = {
            "chain": "sol",
            "bundler_rate": 0.55,
            "avg_buy_delay_s": 16.0,
            "avg_hold_duration_s": 9.0,
            "patterns_flagged": ["sniper", "bundler"],
            "is_jito_bundle": True,
            "jito_confidence": 0.85,
        }
        point_id = self.store.upsert_wallet("DictInputWallet111111111111111111111111", dict_behavior)
        self.assertTrue(len(point_id) > 10)
        matches = self.store.find_similar(dict_behavior, top_k=1)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["address"], "DictInputWallet111111111111111111111111")


if __name__ == "__main__":
    unittest.main()
