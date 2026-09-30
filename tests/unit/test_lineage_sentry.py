"""Unit tests for Recursive Lineage Engine & Capital Sentry (M16/Platform Core)."""

import unittest
from crypto_syndicate.lineage_sentry import (
    DeployerWatchlistEntry,
    LineageTransfer,
    LineageWalletNode,
    RecursiveLineageEngine,
)


class TestRecursiveLineageEngine(unittest.TestCase):
    """Test suite verifying multi-hop lineage, treasury re-centering, and $5 gating."""

    def setUp(self):
        self.engine = RecursiveLineageEngine(
            max_hops_per_anchor=5,
            min_capital_usd=5.0,
            treasury_threshold_sol=20.0,
            sol_price_usd=150.0,
        )
        self.root_funder = "RootFunder_8p7Z2M9tq4F1kL5n6uR8vX7yT9wQ2pM3kL4n5uR6vX7y"
        self.member1 = "Member1_Snip1_4dNj3yuR8vX7yT9wQ2pM3kL4n5"
        self.member2 = "Member2_Snip2_7xKXtg2CW87d97TXJSDpbD5j"
        self.synd_id = "SYND-0001"

    def test_register_syndicate_members(self):
        """Verify initial syndicate registration creates anchors and nodes."""
        self.engine.register_syndicate_members(
            syndicate_id=self.synd_id,
            wallets=[self.member1, self.member2],
            root_funder=self.root_funder,
            initial_balances={self.root_funder: 50.0, self.member1: 2.0, self.member2: 0.01},
        )
        # Root funder with 50 SOL (>= 20) is a treasury anchor
        self.assertIn(self.root_funder, self.engine.treasury_anchors)
        self.assertIn(self.root_funder, self.engine.lineage_nodes)
        self.assertEqual(self.engine.lineage_nodes[self.root_funder].status, "TREASURY_ANCHOR")

        # Member 1 has 2.0 SOL ($300 >= $5) -> DEPLOYER_READY
        self.assertIn(self.member1, self.engine.deployer_watchlist)
        self.assertEqual(self.engine.lineage_nodes[self.member1].status, "DEPLOYER_READY")

        # Member 2 has 0.01 SOL ($1.50 < $5) -> DUST_MONITOR
        self.assertNotIn(self.member2, self.engine.deployer_watchlist)
        self.assertEqual(self.engine.lineage_nodes[self.member2].status, "DUST_MONITOR")

    def test_multi_hop_recursive_descent(self):
        """Verify funds trace recursively from member to child up to 5 hops."""
        self.engine.register_syndicate_members(
            syndicate_id=self.synd_id,
            wallets=[self.member1],
            root_funder=self.root_funder,
            initial_balances={self.root_funder: 50.0, self.member1: 2.0},
        )

        w1 = self.member1  # hop 1
        w2 = "Child_Hop2_Wallet"
        w3 = "Child_Hop3_Wallet"
        w4 = "Child_Hop4_Wallet"
        w5 = "Child_Hop5_Wallet"
        w6 = "Child_Hop6_Wallet"

        # Hop 1 -> Hop 2 (transfers 0.5 SOL = $75)
        tx1 = self.engine.process_transfer({
            "from_address": w1,
            "to_address": w2,
            "amount_sol": 0.5,
            "recipient_balance_sol": 0.5,
            "tx_hash": "tx_hop2",
        })
        self.assertIsNotNone(tx1)
        self.assertEqual(tx1.hop_level, 2)
        self.assertIn(w2, self.engine.syndicate_wallets)
        self.assertEqual(self.engine.lineage_nodes[w2].hop_level, 2)

        # Hop 2 -> Hop 3
        tx2 = self.engine.process_transfer({
            "from_address": w2,
            "to_address": w3,
            "amount_sol": 0.4,
            "recipient_balance_sol": 0.4,
            "tx_hash": "tx_hop3",
        })
        self.assertIsNotNone(tx2)
        self.assertEqual(tx2.hop_level, 3)

        # Hop 3 -> Hop 4
        tx3 = self.engine.process_transfer({
            "from_address": w3,
            "to_address": w4,
            "amount_sol": 0.3,
            "recipient_balance_sol": 0.3,
            "tx_hash": "tx_hop4",
        })
        self.assertIsNotNone(tx3)
        self.assertEqual(tx3.hop_level, 4)

        # Hop 4 -> Hop 5
        tx4 = self.engine.process_transfer({
            "from_address": w4,
            "to_address": w5,
            "amount_sol": 0.2,
            "recipient_balance_sol": 0.2,
            "tx_hash": "tx_hop5",
        })
        self.assertIsNotNone(tx4)
        self.assertEqual(tx4.hop_level, 5)

        # Hop 5 -> Hop 6 (exceeds max 5 hops from active anchor -> must reject)
        tx5 = self.engine.process_transfer({
            "from_address": w5,
            "to_address": w6,
            "amount_sol": 0.1,
            "recipient_balance_sol": 0.1,
            "tx_hash": "tx_hop6",
        })
        self.assertIsNone(tx5)
        self.assertNotIn(w6, self.engine.syndicate_wallets)

    def test_dynamic_high_value_treasury_anchor_re_centering(self):
        """Verify that when a descendant receives >= 20 SOL, it promotes to a Treasury Anchor and resets depth."""
        self.engine.register_syndicate_members(
            syndicate_id=self.synd_id,
            wallets=[self.member1],
            root_funder=self.root_funder,
            initial_balances={self.root_funder: 10.0, self.member1: 2.0},  # Root < 20 SOL
        )

        w1 = self.member1  # hop 1
        w2 = "Child_Hop2_Wallet"
        w3 = "Child_Hop3_Wallet"
        treasury_whale = "SubTreasury_Whale_Wallet"
        sub_child1 = "SubChild_After_Whale_1"
        sub_child5 = "SubChild_After_Whale_5"

        # 1. Normal descent to Hop 3
        self.engine.process_transfer({"from_address": w1, "to_address": w2, "amount_sol": 1.0, "recipient_balance_sol": 1.0})
        self.engine.process_transfer({"from_address": w2, "to_address": w3, "amount_sol": 0.8, "recipient_balance_sol": 0.8})

        # 2. Hop 3 transfers to a wallet with a high total balance (25.0 SOL >= 20 SOL)
        tx_whale = self.engine.process_transfer({
            "from_address": w3,
            "to_address": treasury_whale,
            "amount_sol": 5.0,
            "recipient_balance_sol": 25.0,  # Whale balance!
            "tx_hash": "tx_whale",
        })
        self.assertIsNotNone(tx_whale)
        self.assertTrue(tx_whale.is_treasury_anchor)
        self.assertIn(treasury_whale, self.engine.treasury_anchors)
        self.assertEqual(self.engine.lineage_nodes[treasury_whale].status, "TREASURY_ANCHOR")
        self.assertEqual(self.engine.lineage_nodes[treasury_whale].hop_level, 0)  # Re-centered to 0!

        # 3. Descendants from treasury_whale can now have a fresh dedicated 5 hops!
        tx_sub1 = self.engine.process_transfer({
            "from_address": treasury_whale,
            "to_address": sub_child1,
            "amount_sol": 1.0,
            "recipient_balance_sol": 1.0,
        })
        self.assertIsNotNone(tx_sub1)
        self.assertEqual(tx_sub1.hop_level, 1)  # 1 hop from the whale anchor!
        self.assertEqual(self.engine.lineage_nodes[sub_child1].tree_anchor_address, treasury_whale)

    def test_capital_threshold_gating_5_usd(self):
        """Verify >= $5 USD qualifies as DEPLOYER_READY and < $5 USD is DUST_MONITOR."""
        self.engine.register_syndicate_members(
            syndicate_id=self.synd_id,
            wallets=[self.member1],
            root_funder=self.root_funder,
            initial_balances={self.root_funder: 50.0, self.member1: 2.0},
        )

        # $150/SOL -> $5.00 USD = 0.0333 SOL
        qualified_child = "Deployer_Qualified_Wallet"
        dust_child = "Dust_Unqualified_Wallet"

        # Transfer 0.04 SOL ($6.00 >= $5.00)
        self.engine.process_transfer({
            "from_address": self.member1,
            "to_address": qualified_child,
            "amount_sol": 0.04,
            "recipient_balance_sol": 0.04,
        })
        self.assertIn(qualified_child, self.engine.deployer_watchlist)
        self.assertEqual(self.engine.lineage_nodes[qualified_child].status, "DEPLOYER_READY")
        self.assertTrue(self.engine.lineage_nodes[qualified_child].is_deployer_ready)

        # Transfer 0.02 SOL ($3.00 < $5.00)
        self.engine.process_transfer({
            "from_address": self.member1,
            "to_address": dust_child,
            "amount_sol": 0.02,
            "recipient_balance_sol": 0.02,
        })
        self.assertNotIn(dust_child, self.engine.deployer_watchlist)
        self.assertEqual(self.engine.lineage_nodes[dust_child].status, "DUST_MONITOR")
        self.assertFalse(self.engine.lineage_nodes[dust_child].is_deployer_ready)

    def test_wallet_balance_update_promotion_and_demotion(self):
        """Verify updating wallet balance dynamically promotes dust to deployer and demotes when depleted."""
        self.engine.register_syndicate_members(
            syndicate_id=self.synd_id,
            wallets=[self.member1],
            root_funder=self.root_funder,
        )
        child = "Dynamic_Balance_Wallet"
        self.engine.process_transfer({
            "from_address": self.member1,
            "to_address": child,
            "amount_sol": 0.01,
            "recipient_balance_sol": 0.01,  # $1.50 -> DUST
        })
        self.assertNotIn(child, self.engine.deployer_watchlist)

        # Child receives additional funds: 0.05 SOL -> $7.50 -> Promoted to Deployer!
        node = self.engine.update_wallet_balance(child, balance_sol=0.05)
        self.assertIsNotNone(node)
        self.assertTrue(node.is_deployer_ready)
        self.assertIn(child, self.engine.deployer_watchlist)

        # Child deploys or spends funds: 0.001 SOL -> $0.15 -> Demoted from watchlist!
        node2 = self.engine.update_wallet_balance(child, balance_sol=0.001)
        self.assertFalse(node2.is_deployer_ready)
        self.assertNotIn(child, self.engine.deployer_watchlist)

    def test_cex_exclusion(self):
        """Verify canonical CEX addresses are never adopted into syndicate lineage."""
        self.engine.register_syndicate_members(
            syndicate_id=self.synd_id,
            wallets=[self.member1],
            root_funder=self.root_funder,
        )
        binance_hot = "5tzFkiKscXBHgVXYR9qTJaMmk7p8XQzL7"
        tx = self.engine.process_transfer({
            "from_address": self.member1,
            "to_address": binance_hot,
            "amount_sol": 10.0,
        })
        self.assertIsNone(tx)
        self.assertNotIn(binance_hot, self.engine.syndicate_wallets)

    def test_adversarial_malformed_transfers(self):
        """Verify engine does not crash on malformed or non-numeric transfer objects."""
        self.engine.register_syndicate_members(
            syndicate_id=self.synd_id,
            wallets=[self.member1],
        )
        bad_transfers = [
            {},
            {"from_address": None, "to_address": None},
            {"from_address": self.member1, "to_address": "TestChild", "amount_sol": "invalid"},
            {"from_address": "Unknown", "to_address": "AnotherUnknown"},
            "non-dict",
        ]
        for b in bad_transfers:
            if isinstance(b, dict):
                res = self.engine.process_transfer(b)
                # Should safely evaluate to None or record with 0.0 amount without raising
            else:
                pass  # Ignored

    def test_export_lineage_graph(self):
        """Verify export_lineage_graph formats nodes and edges for 2D SVG DAG rendering."""
        self.engine.register_syndicate_members(
            syndicate_id=self.synd_id,
            wallets=[self.member1],
            root_funder=self.root_funder,
            initial_balances={self.root_funder: 50.0, self.member1: 2.0},
        )
        child = "Child_1"
        self.engine.process_transfer({
            "from_address": self.member1,
            "to_address": child,
            "amount_sol": 0.5,
            "recipient_balance_sol": 0.5,
        })
        graph = self.engine.export_lineage_graph()
        self.assertGreaterEqual(graph["total_nodes"], 3)
        self.assertGreaterEqual(graph["total_transfers"], 1)
        self.assertEqual(graph["treasury_anchors_count"], 1)
        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)


    def test_cycle_transfer_loop_handling(self):
        """Verify transfers forming loops (A -> B -> A) do not cause infinite recursion or state corruption."""
        self.engine.register_syndicate_members(
            syndicate_id=self.synd_id,
            wallets=[self.member1],
        )
        child_b = "Child_Loop_B"
        # A -> B
        tx1 = self.engine.process_transfer({"from_address": self.member1, "to_address": child_b, "amount_sol": 1.0})
        self.assertIsNotNone(tx1)
        # B -> A (back to original member)
        tx2 = self.engine.process_transfer({"from_address": child_b, "to_address": self.member1, "amount_sol": 0.5})
        self.assertIsNotNone(tx2)
        # Both wallets still properly registered
        self.assertIn(self.member1, self.engine.syndicate_wallets)
        self.assertIn(child_b, self.engine.syndicate_wallets)

    def test_multiple_parallel_treasury_anchors(self):
        """Verify multiple high-value treasury anchors maintain separate descent trees."""
        self.engine.register_syndicate_members(
            syndicate_id=self.synd_id,
            wallets=[self.member1, self.member2],
            initial_balances={self.member1: 30.0, self.member2: 25.0},  # Both are Treasury Anchors!
        )
        self.assertEqual(len(self.engine.treasury_anchors), 2)

        child_from_m1 = "Child_M1"
        child_from_m2 = "Child_M2"
        self.engine.process_transfer({"from_address": self.member1, "to_address": child_from_m1, "amount_sol": 1.0})
        self.engine.process_transfer({"from_address": self.member2, "to_address": child_from_m2, "amount_sol": 1.0})

        self.assertEqual(self.engine.lineage_nodes[child_from_m1].tree_anchor_address, self.member1)
        self.assertEqual(self.engine.lineage_nodes[child_from_m2].tree_anchor_address, self.member2)

    def test_get_deployer_watchlist_filtering(self):
        """Verify deployer watchlist filtering by syndicate ID and sorting by USD balance."""
        self.engine.register_syndicate_members(
            syndicate_id="SYND-0001",
            wallets=[self.member1],
            initial_balances={self.member1: 2.0},  # $300
        )
        other_member = "Other_Member_99"
        self.engine.register_syndicate_members(
            syndicate_id="SYND-0002",
            wallets=[other_member],
            initial_balances={other_member: 5.0},  # $750
        )

        all_deployers = self.engine.get_deployer_watchlist()
        self.assertEqual(len(all_deployers), 2)
        self.assertEqual(all_deployers[0].address, other_member)  # $750 > $300 (sorted descending)

        synd1_only = self.engine.get_deployer_watchlist("SYND-0001")
        self.assertEqual(len(synd1_only), 1)
        self.assertEqual(synd1_only[0].address, self.member1)

    def test_record_token_creation_updates_node_and_watchlist(self):
        """Verify recording token creation annotates both lineage node and deployer entry."""
        self.engine.register_syndicate_members(
            syndicate_id=self.synd_id,
            wallets=[self.member1],
            initial_balances={self.member1: 2.0},
        )
        token_mint = "TokenMint_PumpFun_777777777777777777777"
        self.engine.record_token_creation_for_wallet(self.member1, token_mint)
        self.assertIn(token_mint, self.engine.lineage_nodes[self.member1].tokens_created)
        self.assertIn(token_mint, self.engine.deployer_watchlist[self.member1].tokens_created)


if __name__ == "__main__":
    unittest.main()
