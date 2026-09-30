"""Unit tests for GroundTruthLoader & Authoritative Syndicate Dataset."""

import csv
import os
from pathlib import Path
import unittest

from crypto_syndicate.ground_truth_loader import GroundTruthLoader, get_ground_truth_loader


class TestGroundTruthLoader(unittest.TestCase):
    """Test suite verifying ground-truth syndicate and meme token ingestion."""

    def setUp(self):
        self.loader = get_ground_truth_loader()
        self.loader.reload()

    def test_identities_loaded(self):
        """Verify 94 syndicate identities are loaded."""
        self.assertGreaterEqual(len(self.loader.identities), 90)
        self.assertIn("SYND-0001", self.loader.identities)
        self.assertIn("SYND-0006", self.loader.identities)

    def test_unique_wallets_count(self):
        """Verify 805 unique syndicate wallets are extracted and indexed."""
        wallets = self.loader.get_all_wallets()
        self.assertGreaterEqual(len(wallets), 800)

        # Check sample known wallets exist
        sample_w = "8p7Z2M9tq4F1kL5n6uR8vX7yT9wQ2pM3kL4n5uR6vX7y"
        self.assertIn(sample_w, self.loader.wallets_by_address)
        rec = self.loader.wallets_by_address[sample_w]
        self.assertGreater(rec["suspicion_score"], 50.0)
        self.assertIn("early_entry", rec["patterns_flagged"])

    def test_wallets_csv_generated(self):
        """Verify results/wallets.csv is generated with 800+ lines and correct columns."""
        csv_path = Path(self.loader.wallets_csv_path)
        self.assertTrue(csv_path.exists())

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertGreaterEqual(len(rows), 800)
        first = rows[0]
        self.assertIn("wallet_address", first)
        self.assertIn("suspicion_score", first)
        self.assertIn("patterns_flagged", first)
        self.assertIn("associated_tokens", first)
        self.assertIn("estimated_profit_usd", first)

        # Verify sorted by suspicion score descending
        scores = [float(r["suspicion_score"]) for r in rows]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_deployers_extracted(self):
        """Verify real deployers are cataloged with DEPLOYER_READY status."""
        deployers = self.loader.get_deployers()
        self.assertGreaterEqual(len(deployers), 50)
        for dep in deployers:
            self.assertIn("address", dep)
            self.assertIn("syndicate_id", dep)
            self.assertGreaterEqual(dep["balance_sol"], 0.033)  # >= $5 USD
            self.assertEqual(dep["status"], "DEPLOYER_READY")

    def test_verified_token_launches(self):
        """Verify confirmed pump.fun meme tokens are returned with verified DEX links."""
        launches = self.loader.get_verified_launches()
        self.assertGreaterEqual(len(launches), 5)

        mint_addresses = [l.mint_address for l in launches]
        # Must contain ZLONG, EZO, SCRIBJEAN
        self.assertIn("4xjvmiKa5vzkQtaNrTV17v8PFU5mP69Hf1Kq5A9wpump", mint_addresses)
        self.assertIn("2Ecj4UJjegEcjCEPFMuXJprFUD8HMVphqTg2Qtm5pump", mint_addresses)
        self.assertIn("GpUkmLHWPZkBFYjNiwrhuqoFXaoxB6cF2WYKgFbPpump", mint_addresses)

        # MUST NOT contain the fake/placeholder Raydium 2021 coin 7xKXtg...
        self.assertNotIn("7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU", mint_addresses)

        # Check launch attributes
        zlong = next(l for l in launches if l.mint_address == "4xjvmiKa5vzkQtaNrTV17v8PFU5mP69Hf1Kq5A9wpump")
        self.assertEqual(zlong.symbol, "ZLONG")
        self.assertEqual(zlong.creator_wallet, "69aiAKU3uJMxMLRkUEGFNt6nQ43PiVimE4ZbErJ7VSM1")
        self.assertIn("dexscreener.com/solana/", zlong.dex_screener_url)
        self.assertIn("pump.fun/", zlong.pump_fun_url)
        self.assertIn("photon-sol.tinyastro.io", zlong.photon_url)

    def test_ground_truth_transfers(self):
        """Verify realistic multi-hop transfers are created from real deployers."""
        transfers = self.loader.get_ground_truth_transfers()
        self.assertGreaterEqual(len(transfers), 10)
        for t in transfers:
            self.assertIn("from_address", t)
            self.assertIn("to_address", t)
            self.assertIn("amount_sol", t)
            self.assertIn("tx_hash", t)


if __name__ == "__main__":
    unittest.main()
