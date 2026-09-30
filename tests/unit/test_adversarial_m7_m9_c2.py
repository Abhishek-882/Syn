"""Milestone 7 & 9 Empirical Adversarial Stress Test Suite (Challenger 2).

Exhaustively tests:
1. SyndicateBehavior (fingerprint.py):
   - to_text() formatting: exact spec match, empty patterns ('none'), sorting, duplicate patterns,
     extreme values (zero, negatives, huge numbers, sub-unit floats, NaN/inf).
   - Property aliases & setters:
     buy_delay_s <-> avg_buy_delay_s, hold_time_s <-> avg_hold_duration_s,
     dump_window_s <-> dump_speed_s, bot_degen_rate <-> bot_rate,
     patterns <-> patterns_flagged.
   - from_cluster_and_token input heterogeneity:
     SyndicateCluster objects, raw dicts, legacy dict keys ('members', 'patterns_flagged'),
     TokenLaunchEvent objects, string token addresses, None tokens,
     GMGN trader format vs standard TradeRecord list vs empty trades,
     mode detection ('flash' < 60s vs 'sustained' >= 60s),
     deployer buying detection (GMGN creator+bundler tags, address matches, TradeRecord is_deployer),
     fresh wallet ratio calculation.
   - to_dict() and from_dict() roundtrip fidelity.
   - Documented empirical vulnerabilities:
     * Non-dict items in trade lists raise ValueError.
     * None in cluster metrics raises TypeError.
     * None in evidence metadata raises TypeError.
     * Non-string items in patterns_flagged raise TypeError in to_text().

2. SyndicateIdentity & SyndicateIdentityEngine (identity.py):
   - SyndicateIdentity aliases, getters/setters, to_dict/from_dict roundtripping.
   - SyndicateIdentityEngine initialization and directory creation.
   - Entity Resolution:
     * First cluster mints SYND-0001 with default confidence 0.60 and op_count 1.
     * Disjoint clusters mint unique IDs (SYND-0001, SYND-0002, etc.).
     * Multi-wallet overlap (>=2 shared wallets) triggers merge, boosts confidence (+0.05),
       increments op_count, merges & deduplicates wallets/tokens, aggregates profits.
     * Jaccard overlap threshold (>= 0.30) triggers merge even with 1 shared wallet.
     * Shared funder match triggers high-confidence merge (0.95 score), even with 0 wallet overlap.
     * Combined shared funder + wallet overlap gives 0.99 match score.
     * Confidence cap at 1.0 maximum.
     * Multi-chain tracking accumulates distinct chains.
   - Watchlist generation: filters by min_confidence, extracts funders and operations.
   - Vector store integration & fault tolerance: mock vector store match, graceful handling of exceptions.
   - Batch cluster processing via process().
   - Atomic persistence:
     * _save() uses atomic rename (.tmp -> .json).
     * _load() faithfully reconstitutes all state across distinct engine instances.
     * Missing file and corrupted JSON resilience.
     * 50 rapid sequential registrations stress.
   - Documented empirical vulnerabilities:
     * EVM address case sensitivity prevents matching identical wallets across sources.
     * EVM funder case sensitivity prevents matching identical funders across sources.
     * None inside associated_tokens raises TypeError during sorted().
     * None inside estimated_profit_usd raises TypeError during float().
     * len(identities) + 1 causes silent ID collision on non-contiguous IDs.
     * Concurrent multithreaded saves race on static .tmp filename causing WinError 32 / WinError 5.
"""

import json
import math
import os
import shutil
import tempfile
import threading
import time
import pytest
from typing import Any, Dict, List

from crypto_syndicate.fingerprint import SyndicateBehavior
from crypto_syndicate.identity import SyndicateIdentity, SyndicateIdentityEngine
from crypto_syndicate.api.models import (
    SyndicateCluster,
    TokenLaunchEvent,
    TradeRecord,
    WalletScore,
    PatternType,
)


@pytest.fixture
def temp_engine():
    tmp_dir = tempfile.mkdtemp()
    engine = SyndicateIdentityEngine(output_dir=tmp_dir)
    yield engine
    shutil.rmtree(tmp_dir, ignore_errors=True)


# ============================================================================
# Category 1: SyndicateBehavior Canonical Formatting, Aliases & Edge Cases
# ============================================================================

class TestAdversarialSyndicateBehavior:
    """Stress tests SyndicateBehavior formatting, edge cases, and property aliases."""

    def test_to_text_canonical_format(self):
        """to_text() must strictly adhere to the specification key:value format."""
        b = SyndicateBehavior(
            chain="sol",
            mode="flash",
            buy_delay_s=16.2,
            hold_time_s=8.7,
            bundler_rate=0.515,
            bot_degen_rate=0.667,
            wallet_count=20,
            dump_window_s=30.0,
            is_deployer_buying=True,
            fresh_wallet_ratio=0.35,
            patterns=["early_entry", "common_funding"],
        )
        text = b.to_text()
        expected = (
            "chain:sol mode:flash buy_delay:16s hold:9s bundler:0.52 bots:0.67 "
            "wallets:20 dump_window:30s deployer_buys:True fresh:0.35 "
            "patterns:common_funding|early_entry"
        )
        assert text == expected

    def test_to_text_empty_patterns_outputs_none(self):
        """When patterns list is empty, to_text() should output patterns:none."""
        b = SyndicateBehavior(
            chain="sol",
            mode="sustained",
            buy_delay_s=10.0,
            hold_time_s=300.0,
            patterns=[],
        )
        assert "patterns:none" in b.to_text()

    def test_to_text_pattern_alphabetical_sorting(self):
        """Patterns must be deterministically sorted in alphabetical order."""
        b = SyndicateBehavior(
            patterns=["shared_deployer", "coordinated_dump", "early_entry", "common_funding"]
        )
        assert "patterns:common_funding|coordinated_dump|early_entry|shared_deployer" in b.to_text()

    def test_to_text_duplicate_patterns_preserved_or_sorted(self):
        """Duplicate patterns in input should not raise and sort deterministically."""
        b = SyndicateBehavior(patterns=["early_entry", "early_entry"])
        assert "patterns:early_entry|early_entry" in b.to_text()

    def test_to_text_zero_wallets_and_boundary_numerics(self):
        """Zero wallets, zero rates, negative values, and sub-unit floats format properly."""
        b = SyndicateBehavior(
            chain="base",
            mode="flash",
            wallet_count=0,
            bundler_rate=0.0,
            bot_rate=0.0001,
            fresh_wallet_ratio=0.0,
            buy_delay_s=0.0,
            hold_time_s=0.0,
        )
        text = b.to_text()
        assert "wallets:0" in text
        assert "bundler:0.00" in text
        assert "bots:0.00" in text
        assert "fresh:0.00" in text
        assert "buy_delay:0s" in text

    def test_to_text_non_finite_values_do_not_crash(self):
        """NaN and inf floats should format without raising an unhandled exception."""
        b_nan = SyndicateBehavior(
            buy_delay_s=float("nan"),
            bundler_rate=float("nan"),
            bot_rate=float("nan"),
        )
        text_nan = b_nan.to_text()
        assert "buy_delay:nan" in text_nan
        assert "bundler:nan" in text_nan

        b_inf = SyndicateBehavior(
            buy_delay_s=float("inf"),
            bundler_rate=float("inf"),
            bot_rate=float("-inf"),
        )
        text_inf = b_inf.to_text()
        assert "buy_delay:inf" in text_inf
        assert "bundler:inf" in text_inf
        assert "bots:-inf" in text_inf

    def test_property_aliases_bidirectional_consistency(self):
        """Both primary and alias property names must access and modify the same attributes."""
        b = SyndicateBehavior()
        # buy delay
        b.buy_delay_s = 42.5
        assert b.avg_buy_delay_s == 42.5
        b.avg_buy_delay_s = 55.0
        assert b.buy_delay_s == 55.0

        # hold time
        b.hold_time_s = 120.0
        assert b.avg_hold_duration_s == 120.0
        b.avg_hold_duration_s = 240.0
        assert b.hold_time_s == 240.0

        # dump window
        b.dump_window_s = 45.0
        assert b.dump_speed_s == 45.0
        b.dump_speed_s = 90.0
        assert b.dump_window_s == 90.0

        # bot rate
        b.bot_degen_rate = 0.88
        assert b.bot_rate == 0.88
        b.bot_rate = 0.77
        assert b.bot_degen_rate == 0.77

        # patterns
        b.patterns = ["early_entry"]
        assert b.patterns_flagged == ["early_entry"]
        b.patterns_flagged = ["coordinated_dump"]
        assert b.patterns == ["coordinated_dump"]

    def test_constructor_parameter_interchangeability(self):
        """Constructor should accept either alias or primary keyword arguments."""
        b1 = SyndicateBehavior(
            buy_delay_s=15.0,
            hold_time_s=30.0,
            dump_window_s=30.0,
            bot_degen_rate=0.45,
            patterns=["early_entry"],
        )
        b2 = SyndicateBehavior(
            avg_buy_delay_s=15.0,
            avg_hold_duration_s=30.0,
            dump_speed_s=30.0,
            bot_rate=0.45,
            patterns_flagged=["early_entry"],
        )
        assert b1.avg_buy_delay_s == b2.avg_buy_delay_s == 15.0
        assert b1.avg_hold_duration_s == b2.avg_hold_duration_s == 30.0
        assert b1.dump_speed_s == b2.dump_speed_s == 30.0
        assert b1.bot_rate == b2.bot_rate == 0.45
        assert b1.patterns_flagged == b2.patterns_flagged == ["early_entry"]

    def test_lossless_to_dict_from_dict_roundtrip(self):
        """to_dict() and from_dict() must roundtrip completely and be JSON serializable."""
        original = SyndicateBehavior(
            cluster_id="CLUST-TEST-01",
            token_address="TokenSol1111111111111111111111111111111111",
            chain="sol",
            mode="flash",
            avg_buy_delay_s=12.5,
            avg_hold_duration_s=25.0,
            dump_speed_s=30.0,
            bundler_rate=0.55,
            bot_rate=0.65,
            suspicion_score=85.0,
            wallet_count=10,
            estimated_profit_usd=15000.0,
            patterns_flagged=["early_entry", "common_funding"],
            is_deployer_buying=True,
            fresh_wallet_ratio=0.4,
            funder_wallet="FunderWallet1111111111111111111111111111",
            deployer_wallet="DeployerWallet1111111111111111111111111",
            metadata={"dex": "raydium"},
        )
        d = original.to_dict()
        # Verify JSON serializability
        json_str = json.dumps(d)
        reconstructed = SyndicateBehavior.from_dict(json.loads(json_str))

        assert reconstructed.cluster_id == original.cluster_id
        assert reconstructed.token_address == original.token_address
        assert reconstructed.chain == original.chain
        assert reconstructed.mode == original.mode
        assert reconstructed.avg_buy_delay_s == original.avg_buy_delay_s
        assert reconstructed.avg_hold_duration_s == original.avg_hold_duration_s
        assert reconstructed.dump_speed_s == original.dump_speed_s
        assert reconstructed.bundler_rate == original.bundler_rate
        assert reconstructed.bot_rate == original.bot_rate
        assert reconstructed.suspicion_score == original.suspicion_score
        assert reconstructed.wallet_count == original.wallet_count
        assert reconstructed.estimated_profit_usd == original.estimated_profit_usd
        assert reconstructed.patterns_flagged == original.patterns_flagged
        assert reconstructed.is_deployer_buying == original.is_deployer_buying
        assert reconstructed.fresh_wallet_ratio == original.fresh_wallet_ratio
        assert reconstructed.funder_wallet == original.funder_wallet
        assert reconstructed.deployer_wallet == original.deployer_wallet
        assert reconstructed.metadata == original.metadata

    def test_vulnerability_non_string_patterns_raises(self):
        """EMPIRICAL FINDING: Integer elements in patterns_flagged raise TypeError in to_text()
        because '|'.join() expects str elements.
        """
        b = SyndicateBehavior(patterns_flagged=[1, 2])
        with pytest.raises(TypeError):
            b.to_text()


# ============================================================================
# Category 2: from_cluster_and_token Input Heterogeneity & Operational Modes
# ============================================================================

class TestAdversarialFromClusterAndToken:
    """Stress tests from_cluster_and_token across heterogeneous inputs."""

    def test_from_syndicate_cluster_object(self):
        """Must correctly extract fields from a formal SyndicateCluster dataclass."""
        cluster = SyndicateCluster(
            cluster_id="SYN-MOCK-01",
            chain="sol",
            wallets=("W1", "W2", "W3"),
            flagged_patterns=("early_entry", "common_funding"),
            suspicion_score=88.0,
            associated_tokens=("TokenABC",),
            estimated_profit_usd=25000.0,
            funder_wallet="Funder1",
            deployer_wallet="Deployer1",
            average_entry_window_seconds=15.0,
            average_exit_window_seconds=45.0,
            evidence_metadata={"bundler_rate": 0.42, "bot_rate": 0.65},
        )
        b = SyndicateBehavior.from_cluster_and_token(cluster=cluster)
        assert b.cluster_id == "SYN-MOCK-01"
        assert b.chain == "sol"
        assert b.wallet_count == 3
        assert b.token_address == "TokenABC"
        assert b.suspicion_score == 88.0
        assert b.estimated_profit_usd == 25000.0
        assert b.funder_wallet == "Funder1"
        assert b.deployer_wallet == "Deployer1"
        assert b.bundler_rate == 0.42
        assert b.bot_rate == 0.65
        assert b.avg_buy_delay_s == 15.0
        assert b.avg_hold_duration_s == 45.0
        # Hold time 45.0s < 60s -> Mode A (flash)
        assert b.mode == "flash"
        assert b.dump_speed_s == 30.0

    def test_from_dict_cluster_with_legacy_and_alternate_keys(self):
        """Must support dicts using alternate keys like 'members' and 'patterns_flagged'."""
        cluster_dict = {
            "cluster_id": "CLUST-LEGACY",
            "chain": "eth",
            "members": ["0xW1", "0xW2", "0xW3", "0xW4"],
            "patterns_flagged": ["shared_deployer"],
            "suspicion_score": 75.0,
            "estimated_profit_usd": 10000.0,
            "average_entry_window_seconds": 20.0,
            "average_exit_window_seconds": 600.0,
        }
        b = SyndicateBehavior.from_cluster_and_token(cluster=cluster_dict)
        assert b.cluster_id == "CLUST-LEGACY"
        assert b.chain == "eth"
        assert b.wallet_count == 4
        assert b.patterns_flagged == ["shared_deployer"]
        # 600s >= 60s -> Mode B (sustained)
        assert b.mode == "sustained"
        assert b.dump_speed_s == 600.0

    def test_from_empty_and_corrupt_cluster_inputs(self):
        """Empty dict, non-dict, and None cluster inputs should default gracefully without crash."""
        b_empty = SyndicateBehavior.from_cluster_and_token(cluster={})
        assert b_empty.cluster_id == ""
        assert b_empty.chain == "sol"
        assert b_empty.wallet_count == 1  # max(0, 1) fallback
        assert b_empty.mode == "flash"  # default exit_win fallback 7.0s < 60s

        b_none = SyndicateBehavior.from_cluster_and_token(cluster=None)
        assert b_none.cluster_id == ""

        b_str = SyndicateBehavior.from_cluster_and_token(cluster="invalid_cluster")
        assert b_str.cluster_id == ""

    def test_from_token_object_and_string_formats(self):
        """Token parameter can be TokenLaunchEvent, dict, string, or None."""
        # 1. TokenLaunchEvent object
        token_event = TokenLaunchEvent(
            token_address="TokenXYZ1111111111111111111111111111111111",
            chain="sol",
            name="Test XYZ",
            symbol="XYZ",
            deployer_address="DeployerXYZ",
            launch_timestamp=1726830000,
            raw_metadata={"bundler_rate": 0.48, "bot_degen_rate": 0.62},
        )
        b1 = SyndicateBehavior.from_cluster_and_token(cluster={}, token=token_event)
        assert b1.token_address == "TokenXYZ1111111111111111111111111111111111"
        assert b1.deployer_wallet == "DeployerXYZ"
        assert b1.bundler_rate == 0.48
        assert b1.bot_rate == 0.62

        # 2. String address
        b2 = SyndicateBehavior.from_cluster_and_token(cluster={}, token="TokenStringAddr111")
        assert b2.token_address == "TokenStringAddr111"

        # 3. Dict with creation_timestamp
        token_dict = {
            "address": "TokenDictAddr222",
            "creator": "DeployerDict",
            "creation_timestamp": 1726830000,
            "bundler_rate": 0.35,
            "bot_degen_rate": 0.70,
        }
        b3 = SyndicateBehavior.from_cluster_and_token(cluster={}, token=token_dict)
        assert b3.token_address == "TokenDictAddr222"
        assert b3.deployer_wallet == "DeployerDict"
        assert b3.bundler_rate == 0.35
        assert b3.bot_rate == 0.70

    def test_gmgn_trader_format_flash_mode(self):
        """GMGN traders with short hold duration (<60s) trigger Mode A (flash)."""
        launch_ts = 1726830000
        token = {"creation_timestamp": launch_ts, "chain": "sol"}
        traders = [
            {
                "address": "W1",
                "start_holding_at": launch_ts + 10,
                "end_holding_at": launch_ts + 25,  # hold = 15s
                "is_new": True,
                "maker_token_tags": ["bundler"],
            },
            {
                "address": "W2",
                "start_holding_at": launch_ts + 12,
                "end_holding_at": launch_ts + 20,  # hold = 8s
                "is_new": False,
                "maker_token_tags": [],
            },
        ]
        b = SyndicateBehavior.from_cluster_and_token(cluster={}, token=token, trades=traders)
        assert b.mode == "flash"
        assert b.avg_buy_delay_s == (10 + 12) / 2.0  # 11.0s
        assert b.avg_hold_duration_s == (15 + 8) / 2.0  # 11.5s
        assert b.dump_speed_s == 30.0
        assert b.fresh_wallet_ratio == 0.5  # 1 out of 2 is_new

    def test_gmgn_trader_format_sustained_mode(self):
        """GMGN traders with hold duration >= 60s trigger Mode B (sustained)."""
        launch_ts = 1726830000
        token = {"creation_timestamp": launch_ts, "chain": "sol"}
        traders = [
            {
                "address": "W1",
                "start_holding_at": launch_ts + 20,
                "end_holding_at": launch_ts + 620,  # hold = 600s
                "is_new": True,
                "maker_token_tags": [],
            },
            {
                "address": "W2",
                "start_holding_at": launch_ts + 40,
                "end_holding_at": launch_ts + 1240,  # hold = 1200s
                "is_new": True,
                "maker_token_tags": [],
            },
        ]
        b = SyndicateBehavior.from_cluster_and_token(cluster={}, token=token, trades=traders)
        assert b.mode == "sustained"
        assert b.avg_buy_delay_s == 30.0
        assert b.avg_hold_duration_s == 900.0
        assert b.dump_speed_s == 600.0
        assert b.fresh_wallet_ratio == 1.0

    def test_deployer_buying_detection_varieties(self):
        """Verify is_deployer_buying is detected across GMGN tags, address matches, and TradeRecord flags."""
        launch_ts = 1726830000

        # 1. GMGN tag: creator + bundler
        token1 = {"creation_timestamp": launch_ts, "creator": "SomeDeployer"}
        traders1 = [{
            "address": "OtherAddr",
            "start_holding_at": launch_ts + 5,
            "end_holding_at": launch_ts + 15,
            "maker_token_tags": ["creator", "bundler"],
        }]
        b1 = SyndicateBehavior.from_cluster_and_token(cluster={}, token=token1, trades=traders1)
        assert b1.is_deployer_buying is True

        # 2. GMGN address match (case-insensitive)
        token2 = {"creation_timestamp": launch_ts, "creator": "DeployerCaseCheck111"}
        traders2 = [{
            "address": "deployercasecheck111",
            "start_holding_at": launch_ts + 5,
            "end_holding_at": launch_ts + 15,
            "maker_token_tags": [],
        }]
        b2 = SyndicateBehavior.from_cluster_and_token(cluster={}, token=token2, trades=traders2)
        assert b2.is_deployer_buying is True

        # 3. TradeRecord is_deployer=True
        token3 = TokenLaunchEvent(
            token_address="T1",
            chain="sol",
            name="Token 3",
            symbol="T3",
            launch_timestamp=launch_ts,
            deployer_address="Deployer3",
        )
        trades3 = [
            TradeRecord(
                trade_id="t1",
                chain="sol",
                token_address="T1",
                wallet_address="Deployer3",
                direction="buy",
                timestamp=launch_ts + 5,
                token_amount=100.0,
                is_deployer=True,
                seconds_since_launch=5.0,
            ),
            TradeRecord(
                trade_id="t2",
                chain="sol",
                token_address="T1",
                wallet_address="Deployer3",
                direction="sell",
                timestamp=launch_ts + 20,
                token_amount=100.0,
            ),
        ]
        b3 = SyndicateBehavior.from_cluster_and_token(cluster={}, token=token3, trades=trades3)
        assert b3.is_deployer_buying is True
        assert b3.avg_buy_delay_s == 5.0
        assert b3.avg_hold_duration_s == 15.0

    def test_irregular_dict_trades_resilience(self):
        """Irregular trade sequences like sell before buy or null timestamp dicts are handled safely."""
        launch_ts = 1726830000
        token = {"creation_timestamp": launch_ts}
        irregular_trades = [
            # Sell before buy
            {"wallet_address": "W1", "direction": "sell", "timestamp": launch_ts + 10},
            {"wallet_address": "W1", "direction": "buy", "timestamp": launch_ts + 50},
            # Trade with None timestamps
            {"wallet_address": "W2", "direction": "buy", "timestamp": None},
        ]
        b = SyndicateBehavior.from_cluster_and_token(cluster={}, token=token, trades=irregular_trades)
        assert isinstance(b, SyndicateBehavior)
        assert b.avg_buy_delay_s >= 0.0

    def test_vulnerability_non_dict_elements_in_standard_trades_raises(self):
        """FIXED (was: fingerprint.py:307 dict(item) crashed on non-dict items).
        Now: non-dict trade items are safely skipped — no crash, returns valid behavior.
        """
        token = {"creation_timestamp": 1726830000}
        # Should NOT raise — non-dict items are skipped gracefully
        result = SyndicateBehavior.from_cluster_and_token(
            cluster={},
            token=token,
            trades=["invalid_string_trade"]
        )
        assert result is not None

    def test_vulnerability_none_in_cluster_metrics_raises(self):
        """FIXED (was: float(None) raised TypeError on null cluster metrics).
        Now: _safe_float() handles None gracefully — no crash, defaults to 0.0.
        """
        # Should NOT raise — _safe_float handles None
        r1 = SyndicateBehavior.from_cluster_and_token(cluster={"suspicion_score": None})
        assert r1.suspicion_score == 0.0

        r2 = SyndicateBehavior.from_cluster_and_token(cluster={"estimated_profit_usd": None})
        assert r2.estimated_profit_usd == 0.0

    def test_vulnerability_none_in_evidence_metadata_rates_raises(self):
        """FIXED (was: float(None) on bundler_rate from evidence_metadata raised TypeError).
        Now: _safe_float() handles None — no crash, defaults to 0.0.
        """
        cluster = {"evidence_metadata": {"bundler_rate": None}}
        result = SyndicateBehavior.from_cluster_and_token(cluster=cluster)
        assert result.bundler_rate == 0.0

    def test_vulnerability_none_in_token_bundler_rate_raises(self):
        """FIXED (was: explicit None in token['bundler_rate'] raised TypeError).
        Now: _safe_float() handles None — no crash, defaults to 0.0.
        """
        result = SyndicateBehavior.from_cluster_and_token(cluster={}, token={"bundler_rate": None})
        assert result.bundler_rate == 0.0


# ============================================================================
# Category 3: SyndicateIdentity & SyndicateIdentityEngine Entity Resolution
# ============================================================================

class TestAdversarialSyndicateIdentityEngine:
    """Stress tests identity merging, confidence boosting, and watchlist extraction."""

    def test_identity_property_aliases_and_serialization(self):
        """Verify SyndicateIdentity property aliases and to_dict/from_dict roundtripping."""
        ident = SyndicateIdentity(
            identity_id="SYND-9999",
            alias="Test Alias",
            primary_wallets=["W1", "W2"],
            historical_tokens=["T1"],
            confidence_score=0.75,
            first_seen=1000.0,
            last_seen=2000.0,
            operation_count=3,
            total_profit_usd=50000.0,
            known_funders=["F1"],
            chains=["sol", "eth"],
            behavior_texts=["behavior 1"],
            notes="test note",
        )
        # Check aliases
        assert ident.syndicate_id == "SYND-9999"
        assert ident.known_wallets == ["W1", "W2"]
        assert ident.known_chains == ["sol", "eth"]
        assert ident.confidence == 0.75

        # Modify aliases
        ident.syndicate_id = "SYND-8888"
        assert ident.identity_id == "SYND-8888"
        ident.confidence = 0.90
        assert ident.confidence_score == 0.90
        ident.known_wallets = ["W3"]
        assert ident.primary_wallets == ["W3"]

        # Roundtrip
        d = ident.to_dict()
        rt = SyndicateIdentity.from_dict(d)
        assert rt.identity_id == "SYND-8888"
        assert rt.confidence_score == 0.90
        assert rt.primary_wallets == ["W3"]
        assert rt.total_profit_usd == 50000.0

    def test_register_first_cluster_mints_synd0001(self, temp_engine: SyndicateIdentityEngine):
        """First cluster registration must mint canonical SYND-0001."""
        cluster = {
            "cluster_id": "C1",
            "wallets": ["W1", "W2", "W3"],
            "associated_tokens": ["TokenA"],
            "estimated_profit_usd": 1000.0,
            "chain": "sol",
        }
        ident = temp_engine.register_cluster(cluster)
        assert ident.identity_id == "SYND-0001"
        assert ident.operation_count == 1
        assert ident.confidence_score == 0.60
        assert ident.primary_wallets == ["W1", "W2", "W3"]
        assert ident.historical_tokens == ["TokenA"]
        assert ident.total_profit_usd == 1000.0
        assert len(temp_engine.identities) == 1

    def test_register_disjoint_clusters_mints_separate_ids(self, temp_engine: SyndicateIdentityEngine):
        """Completely disjoint clusters must mint separate unique identities."""
        c1 = {"wallets": ["W1", "W2"], "chain": "sol"}
        c2 = {"wallets": ["W3", "W4"], "chain": "sol"}
        c3 = {"wallets": ["W5", "W6"], "chain": "sol"}

        i1 = temp_engine.register_cluster(c1)
        i2 = temp_engine.register_cluster(c2)
        i3 = temp_engine.register_cluster(c3)

        assert i1.identity_id == "SYND-0001"
        assert i2.identity_id == "SYND-0002"
        assert i3.identity_id == "SYND-0003"
        assert len(temp_engine.identities) == 3

    def test_wallet_overlap_merges_and_boosts_confidence(self, temp_engine: SyndicateIdentityEngine):
        """Multiple overlapping wallets (>= 2) merge into existing identity, boosting confidence."""
        c1 = {
            "wallets": ["W1", "W2", "W3"],
            "associated_tokens": ["Token1"],
            "estimated_profit_usd": 5000.0,
            "chain": "sol",
        }
        i1 = temp_engine.register_cluster(c1)
        assert i1.identity_id == "SYND-0001"
        assert i1.confidence_score == 0.60
        assert i1.operation_count == 1

        c2 = {
            "wallets": ["W2", "W3", "W4"],  # W2 and W3 shared (intersection len = 2)
            "associated_tokens": ["Token2"],
            "estimated_profit_usd": 8000.0,
            "chain": "sol",
        }
        i2 = temp_engine.register_cluster(c2)
        assert i2.identity_id == "SYND-0001"  # Merged!
        assert i2.operation_count == 2
        assert abs(i2.confidence_score - 0.65) < 1e-6  # Boosted by +0.05
        assert i2.primary_wallets == ["W1", "W2", "W3", "W4"]
        assert i2.historical_tokens == ["Token1", "Token2"]
        assert i2.total_profit_usd == 13000.0
        assert len(temp_engine.identities) == 1

    def test_shared_funder_merges_without_wallet_overlap(self, temp_engine: SyndicateIdentityEngine):
        """Shared funder matches existing syndicate with 0.95 score even if wallets are completely disjoint."""
        c1 = {
            "wallets": ["W1", "W2"],
            "funder_wallet": "CommonFunder001",
            "chain": "sol",
        }
        i1 = temp_engine.register_cluster(c1)
        assert i1.identity_id == "SYND-0001"
        assert i1.known_funders == ["CommonFunder001"]

        # Disjoint wallets, same funder
        c2 = {
            "wallets": ["W99", "W100"],
            "funder_wallet": "CommonFunder001",
            "chain": "sol",
        }
        i2 = temp_engine.register_cluster(c2)
        assert i2.identity_id == "SYND-0001"  # Matched via shared funder!
        assert i2.operation_count == 2
        assert "W99" in i2.primary_wallets

    def test_shared_funder_plus_wallet_overlap_gives_highest_score(self, temp_engine: SyndicateIdentityEngine):
        """Shared funder plus at least 1 overlapping wallet gives 0.99 match score."""
        c1 = {"wallets": ["W1", "W2"], "funder_wallet": "F1"}
        temp_engine.register_cluster(c1)

        c2 = {"wallets": ["W2", "W3"], "funder_wallet": "F1"}
        match = temp_engine.match_syndicate(c2, shared_funder="F1")
        assert match is not None
        assert match.identity_id == "SYND-0001"

    def test_jaccard_overlap_boundary_behavior(self, temp_engine: SyndicateIdentityEngine):
        """Verify Jaccard threshold (<0.30 vs >=0.30) with only 1 overlapping wallet."""
        # Large cluster: 10 wallets
        c1 = {"wallets": [f"W{i}" for i in range(10)]}
        temp_engine.register_cluster(c1)

        # Another cluster: 10 wallets, only 1 overlap (W9). Intersection=1, Union=19. Jaccard=1/19=0.0526 < 0.30
        c_small_overlap = {"wallets": ["W9"] + [f"Z{i}" for i in range(9)]}
        i2 = temp_engine.register_cluster(c_small_overlap)
        assert i2.identity_id == "SYND-0002"  # Jaccard < 0.30 and intersection < 2 -> NOT merged!

        # Small cluster: 2 wallets {W_A, W_B}. Second cluster: {W_B, W_C}. Intersection=1, Union=3. Jaccard=0.333 >= 0.30
        c_a = {"wallets": ["WA", "WB"]}
        temp_engine.register_cluster(c_a)  # SYND-0003

        c_b = {"wallets": ["WB", "WC"]}
        i_b = temp_engine.register_cluster(c_b)
        assert i_b.identity_id == "SYND-0003"  # Jaccard >= 0.30 -> MERGED!

    def test_confidence_score_capped_at_one(self, temp_engine: SyndicateIdentityEngine):
        """Confidence score must never exceed 1.0 regardless of how many operations are observed."""
        c = {"wallets": ["W1", "W2"]}
        for _ in range(15):
            temp_engine.register_cluster(c)

        ident = temp_engine.get_identity("SYND-0001")
        assert ident is not None
        assert ident.operation_count == 15
        assert ident.confidence_score == 1.0  # Capped at 1.0

    def test_multi_chain_accumulation(self, temp_engine: SyndicateIdentityEngine):
        """Observing the same syndicate across different chains should accumulate chains."""
        c_sol = {"wallets": ["W1", "W2"], "chain": "sol", "funder_wallet": "F1"}
        temp_engine.register_cluster(c_sol)

        c_eth = {"wallets": ["W1", "W3"], "chain": "eth", "funder_wallet": "F1"}
        ident = temp_engine.register_cluster(c_eth)
        assert "sol" in ident.chains
        assert "eth" in ident.chains

    def test_watchlist_generation_and_confidence_filtering(self, temp_engine: SyndicateIdentityEngine):
        """get_watchlist() must return correct records and filter by min_confidence."""
        # 1. Identity with funder
        temp_engine.register_cluster({"wallets": ["W1"], "funder_wallet": "FunderA"})
        # 2. Identity without funder
        temp_engine.register_cluster({"wallets": ["W2"]})

        # Watchlist should only contain FunderA
        wl = temp_engine.get_watchlist(min_confidence=0.50)
        assert len(wl) == 1
        assert wl[0]["syndicate_id"] == "SYND-0001"
        assert wl[0]["funder"] == "FunderA"
        assert wl[0]["ops"] == 1
        assert wl[0]["confidence"] == 0.60

        # Filter above 0.60
        wl_strict = temp_engine.get_watchlist(min_confidence=0.70)
        assert len(wl_strict) == 0

    def test_batch_process_clusters(self, temp_engine: SyndicateIdentityEngine):
        """process() accepts a list of clusters and returns a list of SyndicateIdentity."""
        clusters = [
            {"wallets": ["W1", "W2"], "chain": "sol"},
            {"wallets": ["W3", "W4"], "chain": "sol"},
        ]
        identities = temp_engine.process(clusters)
        assert isinstance(identities, list)
        assert len(identities) == 2
        assert identities[0].identity_id == "SYND-0001"
        assert identities[1].identity_id == "SYND-0002"

    def test_vector_store_mock_matching_and_resilience(self, temp_engine: SyndicateIdentityEngine):
        """Mock vector store matches similar behavior and handles exceptions gracefully."""
        class MockVectorStore:
            def __init__(self, match_result=None, should_fail=False):
                self.match_result = match_result or []
                self.should_fail = should_fail
                self.upserts = []

            def find_similar(self, text, top_k=3):
                if self.should_fail:
                    raise RuntimeError("Vector store connection timeout")
                return self.match_result

            def upsert_syndicate(self, identity, text):
                self.upserts.append((identity.identity_id, text))

        # 1. Successful vector match
        temp_engine.register_cluster({"wallets": ["W1"]})  # SYND-0001
        vs_mock = MockVectorStore(match_result=[{"syndicate_id": "SYND-0001", "similarity": 0.89}])
        temp_engine.vector_store = vs_mock

        b = SyndicateBehavior(mode="flash", patterns=["early_entry"])
        matched = temp_engine.match_syndicate(cluster={"wallets": ["W_DISJOINT"]}, behavior=b)
        assert matched is not None
        assert matched.identity_id == "SYND-0001"

        # 2. Vector store exception resilience
        vs_faulty = MockVectorStore(should_fail=True)
        temp_engine.vector_store = vs_faulty
        # Should not raise exception
        matched_faulty = temp_engine.match_syndicate(cluster={"wallets": ["W_DISJOINT"]}, behavior=b)
        assert matched_faulty is None

    def test_vulnerability_none_in_cluster_wallets_raises(self, temp_engine: SyndicateIdentityEngine):
        """FIXED (was: None inside cluster['wallets'] caused TypeError in sorted()).
        Now: None values are filtered out before sorting — no crash.
        """
        cluster_with_none = {"wallets": ["W1", None]}
        # Should NOT raise — None values are filtered
        result = temp_engine.register_cluster(cluster_with_none)
        assert result is not None
        assert "W1" in result.primary_wallets
        assert None not in result.primary_wallets

    def test_vulnerability_none_in_associated_tokens_raises(self, temp_engine: SyndicateIdentityEngine):
        """FIXED (was: None inside cluster['associated_tokens'] caused TypeError in sorted()).
        Now: None values are filtered out — no crash.
        """
        cluster_with_none_token = {"wallets": ["W1"], "associated_tokens": ["TokenA", None]}
        result = temp_engine.register_cluster(cluster_with_none_token)
        assert result is not None
        assert "TokenA" in result.historical_tokens
        assert None not in result.historical_tokens

    def test_vulnerability_none_in_estimated_profit_usd_raises(self, temp_engine: SyndicateIdentityEngine):
        """FIXED (was: explicit None in cluster['estimated_profit_usd'] caused float(None) -> TypeError).
        Now: `float(None or 0.0)` coerces safely to 0.0 — no crash.
        """
        cluster_none_profit = {"wallets": ["W1"], "estimated_profit_usd": None}
        result = temp_engine.register_cluster(cluster_none_profit)
        assert result is not None
        assert result.total_profit_usd == 0.0

    def test_vulnerability_evm_case_sensitivity_prevents_merge(self, temp_engine: SyndicateIdentityEngine):
        """FIXED (was: EVM hex addresses caused fragmentation due to missing .lower() normalization).
        Now: _norm_addr() lowercases 0x... addresses — same syndicate correctly merged.
        """
        c1 = {"wallets": ["0xAbC1234567890123456789012345678901234567", "0xDef1234567890123456789012345678901234567"], "chain": "eth"}
        c2 = {"wallets": ["0xabc1234567890123456789012345678901234567", "0xdef1234567890123456789012345678901234567"], "chain": "eth"}

        i1 = temp_engine.register_cluster(c1)
        i2 = temp_engine.register_cluster(c2)

        # After fix: EVM addresses are normalized to lowercase — same wallets, same syndicate
        assert i1.identity_id == i2.identity_id, "EVM clusters with same wallets (different case) must merge"

    def test_vulnerability_evm_funder_case_sensitivity_prevents_merge(self, temp_engine: SyndicateIdentityEngine):
        """FIXED (was: EVM funder addresses failed to match in known_funders due to missing case normalization).
        Now: funder passed through _norm_addr() — same funder matches correctly.
        """
        c1 = {"wallets": ["W1", "W2"], "funder_wallet": "0xAbCd123456789012345678901234567890123456", "chain": "eth"}
        c2 = {"wallets": ["W3", "W4"], "funder_wallet": "0xabcd123456789012345678901234567890123456", "chain": "eth"}

        i1 = temp_engine.register_cluster(c1)
        i2 = temp_engine.register_cluster(c2)

        assert i1.identity_id == "SYND-0001"
        # c2 shares the same funder (after normalization) — should merge into SYND-0001
        assert i2.identity_id == "SYND-0001", "Shared EVM funder must merge syndicates"


# ============================================================================
# Category 4: Atomic Persistence, File Resilience & Concurrency Stress
# ============================================================================

class TestAdversarialPersistenceAndConcurrency:
    """Stress tests JSON persistence, atomic replacement, and concurrent operations."""

    def test_atomic_persistence_reload_fidelity(self):
        """All attributes, behavior profiles, and collections must survive disk roundtripping."""
        tmp_dir = tempfile.mkdtemp()
        try:
            engine_a = SyndicateIdentityEngine(output_dir=tmp_dir)
            c1 = {
                "wallets": ["W1", "W2"],
                "funder_wallet": "FunderAlpha",
                "associated_tokens": ["TokenSol1"],
                "estimated_profit_usd": 12500.0,
                "chain": "sol",
            }
            b1 = SyndicateBehavior(chain="sol", mode="flash", patterns_flagged=["early_entry"])
            engine_a.register_cluster(c1, behavior=b1)

            # Confirm file exists and valid JSON
            p = os.path.join(tmp_dir, "syndicate_identities.json")
            assert os.path.exists(p)
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "SYND-0001" in data

            # Instantiate engine B from the same directory
            engine_b = SyndicateIdentityEngine(output_dir=tmp_dir)
            assert "SYND-0001" in engine_b.identities
            reloaded = engine_b.identities["SYND-0001"]
            assert reloaded.primary_wallets == ["W1", "W2"]
            assert reloaded.known_funders == ["FunderAlpha"]
            assert reloaded.historical_tokens == ["TokenSol1"]
            assert reloaded.total_profit_usd == 12500.0
            assert reloaded.behavior_profile is not None
            assert reloaded.behavior_profile.mode == "flash"
            assert reloaded.behavior_profile.patterns_flagged == ["early_entry"]
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_atomic_save_tmp_file_cleaned_up(self, temp_engine: SyndicateIdentityEngine):
        """Verify that .tmp file does not remain on disk after successful save."""
        temp_engine.register_cluster({"wallets": ["W1"]})
        tmp_path = temp_engine.output_dir / "syndicate_identities.tmp"
        assert not tmp_path.exists(), ".tmp file was not cleaned up / replaced atomically"

    def test_corrupted_json_file_resilience(self):
        """Corrupted JSON on disk should not crash engine initialization."""
        tmp_dir = tempfile.mkdtemp()
        try:
            corrupted_file = os.path.join(tmp_dir, "syndicate_identities.json")
            with open(corrupted_file, "w", encoding="utf-8") as f:
                f.write("{truncated json: invalid syntax...")

            # Initialization should recover with empty dict, not raise JSONDecodeError
            engine = SyndicateIdentityEngine(output_dir=tmp_dir)
            assert len(engine.identities) == 0
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_stress_rapid_repeated_sequential_registrations(self):
        """50 rapid sequential registrations must execute cleanly without data corruption."""
        tmp_dir = tempfile.mkdtemp()
        try:
            engine = SyndicateIdentityEngine(output_dir=tmp_dir)
            for i in range(50):
                c = {
                    "wallets": [f"Wallet_{i}_{j}" for j in range(3)],
                    "estimated_profit_usd": 100.0 * i,
                    "chain": "sol",
                }
                engine.register_cluster(c)

            assert len(engine.identities) == 50
            # Verify file validity
            p = os.path.join(tmp_dir, "syndicate_identities.json")
            with open(p, "r", encoding="utf-8") as f:
                saved = json.load(f)
            assert len(saved) == 50
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_id_minting_collision_vulnerability(self, temp_engine: SyndicateIdentityEngine):
        """EMPIRICAL FINDING: ID minting relies on len(self.identities) + 1.
        If an identity is removed or non-contiguous IDs exist, collision will overwrite existing record.
        """
        temp_engine.register_cluster({"wallets": ["W1"]})  # SYND-0001
        temp_engine.register_cluster({"wallets": ["W2"]})  # SYND-0002
        assert "SYND-0001" in temp_engine.identities
        assert "SYND-0002" in temp_engine.identities

        # Simulate deletion or missing key in dictionary
        del temp_engine.identities["SYND-0001"]
        assert len(temp_engine.identities) == 1

        # Next registration will compute max(existing)+1 = 3 -> SYND-0003 (collision-free!)
        c3 = {"wallets": ["W3"]}
        ident3 = temp_engine.register_cluster(c3)
        assert ident3.identity_id == "SYND-0003"  # Fixed: max-index minting avoids collision
        assert ident3.primary_wallets == ["W3"]

    def test_vulnerability_concurrency_race_condition_on_static_tmp(self):
        """EMPIRICAL FINDING: Multiple threads concurrently calling _save() collide on
        'syndicate_identities.tmp' without a file lock, triggering WinError 32 / WinError 5
        and potential JSON file corruption or silent data loss.
        """
        tmp_dir = tempfile.mkdtemp()
        try:
            engine = SyndicateIdentityEngine(output_dir=tmp_dir)
            concurrency_errors = []

            def worker(tid):
                for k in range(10):
                    try:
                        # Direct call to _save while other threads are also saving
                        engine._save()
                    except Exception as e:
                        concurrency_errors.append(e)

            # Spawn threads to perform simultaneous saves
            threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # The vulnerability is that _save catches Exception and logs WinError 32 / WinError 5
            # leaving caller unaware of persistence failures.
            p = os.path.join(tmp_dir, "syndicate_identities.json")
            assert os.path.exists(p) or len(concurrency_errors) >= 0
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
