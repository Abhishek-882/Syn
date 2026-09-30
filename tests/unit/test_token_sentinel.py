"""Unit tests for Syndicate Token Creation Sentinel."""

import time
import unittest
from crypto_syndicate.lineage_sentry import RecursiveLineageEngine
from crypto_syndicate.token_sentinel import (
    PUMP_FUN_PROGRAM_ID,
    RAYDIUM_POOL_V4_PROGRAM_ID,
    SPL_TOKEN_PROGRAM_ID,
    SyndicateTokenLaunch,
    TokenCreationSentinel,
)


class TestTokenCreationSentinel(unittest.TestCase):
    """Test suite verifying token creation interception across Pump.fun, Raydium, and SPL."""

    def setUp(self):
        self.lineage_engine = RecursiveLineageEngine()
        self.root_funder = "Root_Treasury_Funder_8p7Z2M9tq4F1kL5n6uR8vX7y"
        self.deployer_wallet = "Deployer_Snip1_4dNj3yuR8vX7yT9wQ2pM3kL4n5"
        self.unwatched_wallet = "Random_Unwatched_Trader_Wallet_11111111"
        self.synd_id = "SYND-0001"

        self.lineage_engine.register_syndicate_members(
            syndicate_id=self.synd_id,
            wallets=[self.deployer_wallet],
            root_funder=self.root_funder,
            initial_balances={self.root_funder: 50.0, self.deployer_wallet: 2.5},
        )
        self.sentinel = TokenCreationSentinel(lineage_engine=self.lineage_engine)

    def test_pump_fun_create_interception(self):
        """Verify sentinel intercepts Pump.fun token creation from a watched deployer."""
        tx = {
            "creator_wallet": self.deployer_wallet,
            "program_id": PUMP_FUN_PROGRAM_ID,
            "instruction": "create",
            "mint_address": "PumpMint_BELUGA2_77777777777777777777",
            "symbol": "BELUGA2",
            "name": "Beluga Syndicate Sequel",
            "bonding_curve_address": "Curve_BELUGA2_888888888888888888",
            "initial_sol_injected": 0.05,
            "timestamp": time.time(),
            "signature": "sig_pump_001",
        }
        launch = self.sentinel.inspect_transaction(tx)
        self.assertIsNotNone(launch)
        self.assertEqual(launch.launch_type, "PUMP_FUN")
        self.assertEqual(launch.symbol, "BELUGA2")
        self.assertEqual(launch.parent_syndicate_id, self.synd_id)
        self.assertIn("dexscreener.com/solana/", launch.dex_screener_url)
        self.assertIn("photon-sol.tinyastro.io", launch.photon_url)
        self.assertIn("pump.fun/", launch.pump_fun_url)
        self.assertEqual(len(self.sentinel.recent_launches), 1)

    def test_raydium_pool_initialization_interception(self):
        """Verify sentinel intercepts Raydium liquidity pool initialization."""
        tx = {
            "signer": self.deployer_wallet,
            "programs": [RAYDIUM_POOL_V4_PROGRAM_ID],
            "instruction": "initializePool",
            "mint_address": "RayMint_SNIPEX2_999999999999999999",
            "symbol": "SNIPEX2",
            "name": "Snipex V2 Raydium Pool",
            "amount_sol": 10.0,
            "timestamp": time.time(),
            "tx_hash": "tx_raydium_001",
        }
        launch = self.sentinel.inspect_transaction(tx)
        self.assertIsNotNone(launch)
        self.assertEqual(launch.launch_type, "RAYDIUM")
        self.assertEqual(launch.symbol, "SNIPEX2")
        self.assertEqual(launch.initial_sol_injected, 10.0)

    def test_spl_token_initialize_mint_interception(self):
        """Verify sentinel intercepts standard SPL Token InitializeMint."""
        tx = {
            "from_address": self.deployer_wallet,
            "program_id": SPL_TOKEN_PROGRAM_ID,
            "instruction": "initializeMint2",
            "mint_address": "SPLMint_SOLCAT_123456789012345678",
            "symbol": "SOLCAT",
            "timestamp": time.time(),
        }
        launch = self.sentinel.inspect_transaction(tx)
        self.assertIsNotNone(launch)
        self.assertEqual(launch.launch_type, "SPL_MINT")
        self.assertEqual(launch.symbol, "SOLCAT")

    def test_unwatched_wallet_rejection(self):
        """Verify sentinel strictly ignores transactions from unwatched wallets."""
        tx = {
            "creator_wallet": self.unwatched_wallet,
            "program_id": PUMP_FUN_PROGRAM_ID,
            "instruction": "create",
            "mint_address": "RandomMint_Unwatched_0000000000000000",
            "symbol": "RANDOM",
        }
        launch = self.sentinel.inspect_transaction(tx)
        self.assertIsNone(launch)
        self.assertEqual(len(self.sentinel.recent_launches), 0)

    def test_lineage_path_annotation(self):
        """Verify launch record inherits the full lineage path from Root to Deployer."""
        # Member funds Child 1, Child 1 funds Deployer
        child1 = "Intermediary_Child1"
        self.lineage_engine.process_transfer({
            "from_address": self.deployer_wallet,
            "to_address": child1,
            "amount_sol": 1.0,
            "recipient_balance_sol": 1.0,
        })
        actual_deployer = "Fresh_Child_Deployer_99"
        self.lineage_engine.process_transfer({
            "from_address": child1,
            "to_address": actual_deployer,
            "amount_sol": 0.5,
            "recipient_balance_sol": 0.5,
        })

        tx = {
            "creator_wallet": actual_deployer,
            "launch_type": "PUMP_FUN",
            "mint_address": "Mint_DeepLineage_Token",
            "symbol": "DEEP",
        }
        launch = self.sentinel.inspect_transaction(tx)
        self.assertIsNotNone(launch)
        self.assertIn(actual_deployer, launch.lineage_path)
        self.assertIn(child1, launch.lineage_path)

    def test_deduplicate_identical_mint_addresses(self):
        """Verify recording the same token mint multiple times does not create duplicates."""
        tx = {
            "creator_wallet": self.deployer_wallet,
            "launch_type": "PUMP_FUN",
            "mint_address": "Mint_Duplicate_Check_111111111111111",
            "symbol": "DUP",
        }
        l1 = self.sentinel.inspect_transaction(tx)
        l2 = self.sentinel.inspect_transaction(tx)
        self.assertIsNotNone(l1)
        self.assertEqual(len(self.sentinel.recent_launches), 1)

    def test_event_listener_callback_dispatch(self):
        """Verify registered listener callbacks are triggered upon launch detection."""
        dispatched_events = []

        def my_listener(launch: SyndicateTokenLaunch):
            dispatched_events.append(launch.symbol)

        self.sentinel.add_listener(my_listener)
        tx = {
            "creator_wallet": self.deployer_wallet,
            "launch_type": "PUMP_FUN",
            "mint_address": "Mint_Listener_Check_2222222222222",
            "symbol": "ALERTME",
        }
        self.sentinel.inspect_transaction(tx)
        self.assertEqual(dispatched_events, ["ALERTME"])

    def test_get_active_pinned_launch(self):
        """Verify get_active_pinned_launch returns the latest launch if within age limit."""
        tx = {
            "creator_wallet": self.deployer_wallet,
            "launch_type": "PUMP_FUN",
            "mint_address": "Mint_Pinned_33333333333333333333",
            "symbol": "PINNED",
            "timestamp": time.time(),
        }
        self.sentinel.inspect_transaction(tx)
        pinned = self.sentinel.get_active_pinned_launch(max_age_seconds=60.0)
        self.assertIsNotNone(pinned)
        self.assertEqual(pinned["symbol"], "PINNED")

        # When max_age_seconds has passed
        old_pinned = self.sentinel.get_active_pinned_launch(max_age_seconds=0.0001)
        # Should be None if age is older than max_age
        time.sleep(0.01)
        old_pinned = self.sentinel.get_active_pinned_launch(max_age_seconds=0.005)
        self.assertIsNone(old_pinned)

    def test_adversarial_malformed_transactions(self):
        """Verify sentinel safely handles empty or malformed transaction objects."""
        bad_txs = [
            None,
            {},
            "non-dict",
            {"creator_wallet": None},
            {"creator_wallet": self.deployer_wallet, "amount_sol": "invalid"},
            {"creator_wallet": self.deployer_wallet, "timestamp": "invalid_ts"},
        ]
        for b in bad_txs:
            res = self.sentinel.inspect_transaction(b)
            # Should not raise exception
            if b and isinstance(b, dict) and b.get("creator_wallet") == self.deployer_wallet:
                # May or may not return launch, but must not crash
                pass


    def test_generic_token_creation_fallback(self):
        """Verify sentinel detects generic token creation signals when specific program is omitted."""
        tx = {
            "creator_wallet": self.deployer_wallet,
            "is_token_creation": True,
            "mint_address": "GenericMint_999999999999999999",
            "symbol": "FALLBACK",
            "name": "Generic Fallback Token",
            "initial_sol_injected": 1.25,
        }
        launch = self.sentinel.inspect_transaction(tx)
        self.assertIsNotNone(launch)
        self.assertEqual(launch.launch_type, "GENERIC")
        self.assertEqual(launch.symbol, "FALLBACK")
        self.assertEqual(launch.initial_sol_injected, 1.25)
        self.assertTrue(launch.dex_screener_url.startswith("https://dexscreener.com"))
        self.assertTrue(launch.photon_url.startswith("https://photon-sol.tinyastro.io"))
        self.assertTrue(launch.pump_fun_url.startswith("https://pump.fun"))


if __name__ == "__main__":
    unittest.main()
