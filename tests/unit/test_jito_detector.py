"""Unit and adversarial test suite for M12 Jito Bundle Detector.

Tests all canonical tip accounts, CPI transfers, metadata flags, co-slot bursts,
adversarial lookalike spoofing, boundary conditions, and cross-module integration.
"""

import json
from typing import Any, Dict
import pytest

from crypto_syndicate.api.fixtures import (
    get_mock_jito_fixtures,
    get_mock_non_jito_fixtures,
)
from crypto_syndicate.api.models import TradeRecord
from crypto_syndicate.fingerprint import SyndicateBehavior
from crypto_syndicate.jito_detector import (
    CANONICAL_JITO_TIP_ACCOUNTS,
    CANONICAL_TIP_ACCOUNTS_SET,
    DETECTION_THRESHOLD,
    SIGNAL_BUNDLE_ID_METADATA,
    SIGNAL_CANONICAL_TIP,
    SIGNAL_CO_SLOT_INGRESS,
    SIGNAL_EXPLICIT_JITO_FLAG,
    SIGNAL_HIGH_BUNDLER_RATE,
    SIGNAL_INNER_CPI_TIP,
    JitoDetectionResult,
    JitoDetector,
)
from crypto_syndicate.scanner import LiveSyndicateScanner


class TestJitoDetectorUnit:
    """Core functional and algorithmic tests for JitoDetector."""

    def test_canonical_tip_direct_transfer(self):
        detector = JitoDetector()
        tx = {
            "chain": "sol",
            "tip_account": CANONICAL_JITO_TIP_ACCOUNTS[0],
            "tip_lamports": 10_000_000,
        }
        res = detector.detect(tx)
        assert res.is_jito_bundle is True
        assert res.confidence >= 0.50
        assert SIGNAL_CANONICAL_TIP in res.signals
        assert res.tip_account_matched == CANONICAL_JITO_TIP_ACCOUNTS[0]
        assert res.tip_lamports == 10_000_000

    def test_all_eight_canonical_tip_accounts(self):
        detector = JitoDetector()
        assert len(CANONICAL_JITO_TIP_ACCOUNTS) == 8
        for acc in CANONICAL_JITO_TIP_ACCOUNTS:
            tx = {"chain": "sol", "tip_account": acc, "tip_lamports": 5000}
            res = detector.detect(tx)
            assert res.is_jito_bundle is True
            assert res.tip_account_matched == acc
            assert SIGNAL_CANONICAL_TIP in res.signals

    def test_inner_cpi_tip_transfer(self):
        detector = JitoDetector()
        tx = {
            "chain": "sol",
            "inner_instructions": [
                {
                    "program": "11111111111111111111111111111111",
                    "to": CANONICAL_JITO_TIP_ACCOUNTS[2],
                    "lamports": 2_500_000,
                }
            ],
        }
        res = detector.detect(tx)
        assert res.is_jito_bundle is True
        assert SIGNAL_INNER_CPI_TIP in res.signals
        assert res.tip_account_matched == CANONICAL_JITO_TIP_ACCOUNTS[2]
        assert res.tip_lamports == 2_500_000

    def test_bundle_id_metadata_extraction(self):
        detector = JitoDetector()
        tx = {
            "chain": "sol",
            "bundle_id": "jito_bundle_abc1234567890",
        }
        res = detector.detect(tx)
        assert res.is_jito_bundle is True
        assert res.bundle_id == "jito_bundle_abc1234567890"
        assert SIGNAL_BUNDLE_ID_METADATA in res.signals

    def test_nested_bundle_id_in_metadata_dict(self):
        detector = JitoDetector()
        tx = {
            "chain": "sol",
            "metadata": {"bundle_id": "bundle_nested_998877"},
        }
        res = detector.detect(tx)
        assert res.is_jito_bundle is True
        assert res.bundle_id == "bundle_nested_998877"

    def test_explicit_jito_flag(self):
        detector = JitoDetector()
        tx = {"chain": "sol", "is_jito": True}
        res = detector.detect(tx)
        assert SIGNAL_EXPLICIT_JITO_FLAG in res.signals
        assert res.confidence >= 0.30

    def test_high_bundler_rate_signal(self):
        detector = JitoDetector()
        tx = {"chain": "sol", "bundler_rate": 0.55}
        res = detector.detect(tx)
        assert SIGNAL_HIGH_BUNDLER_RATE in res.signals
        assert res.confidence >= 0.20

    def test_combined_signals_trigger_threshold(self):
        # Explicit flag (0.30) + high bundler rate (0.20) = 0.50 >= 0.45 threshold
        detector = JitoDetector()
        tx = {"chain": "sol", "is_jito": True, "bundler_rate": 0.50}
        res = detector.detect(tx)
        assert res.confidence >= 0.50
        assert res.is_jito_bundle is True

    def test_co_slot_burst_detection(self):
        detector = JitoDetector()
        batch = [
            {"chain": "sol", "slot": 284000100, "timestamp": 1726830000.100, "bundler_rate": 0.25},
            {"chain": "sol", "slot": 284000100, "timestamp": 1726830000.250, "bundler_rate": 0.25},
        ]
        results = detector.detect_co_slot_bundles(batch, window_ms=400.0)
        assert len(results) == 2
        for r in results:
            assert SIGNAL_CO_SLOT_INGRESS in r.signals
            assert r.confidence >= 0.25

    def test_co_slot_burst_outside_window(self):
        detector = JitoDetector()
        batch = [
            {"chain": "sol", "slot": 284000100, "timestamp": 1726830000.000},
            {"chain": "sol", "slot": 284000100, "timestamp": 1726830002.500},  # 2.5s later (>400ms)
        ]
        results = detector.detect_co_slot_bundles(batch, window_ms=400.0)
        assert len(results) == 2
        assert SIGNAL_CO_SLOT_INGRESS not in results[0].signals
        assert SIGNAL_CO_SLOT_INGRESS not in results[1].signals

    def test_negative_control_raydium_swap(self):
        detector = JitoDetector()
        non_jito = get_mock_non_jito_fixtures()
        res = detector.detect(non_jito[0])
        assert res.is_jito_bundle is False
        assert res.confidence == 0.0
        assert len(res.signals) == 0

    def test_negative_control_orca_swap(self):
        detector = JitoDetector()
        non_jito = get_mock_non_jito_fixtures()
        res = detector.detect(non_jito[1])
        assert res.is_jito_bundle is False
        assert res.confidence == 0.0

    def test_anti_spoofing_lookalike_address(self):
        detector = JitoDetector()
        non_jito = get_mock_non_jito_fixtures()
        spoofed = non_jito[2]
        res = detector.detect(spoofed)
        # Should not match canonical tip because last char is 'r' instead of 'q'
        assert res.is_jito_bundle is False
        assert res.tip_account_matched is None
        assert SIGNAL_CANONICAL_TIP not in res.signals

    def test_non_solana_chain_rejected(self):
        detector = JitoDetector()
        tx = {
            "chain": "eth",
            "tip_account": CANONICAL_JITO_TIP_ACCOUNTS[0],
            "tip_lamports": 1000000,
        }
        res = detector.detect(tx)
        assert res.is_jito_bundle is False
        assert res.confidence == 0.0
        assert "rejected_reason" in res.metadata

    def test_malformed_input_none_or_empty(self):
        detector = JitoDetector()
        res1 = detector.detect(None)
        assert res1.is_jito_bundle is False
        res2 = detector.detect({})
        assert res2.is_jito_bundle is False

    def test_malformed_input_wrong_types(self):
        detector = JitoDetector()
        for bad_input in ("not_a_dict", 12345, [1, 2, 3]):
            res = detector.detect(bad_input)
            assert res.is_jito_bundle is False

    def test_missing_slot_and_timestamp(self):
        detector = JitoDetector()
        tx = {"chain": "sol", "tip_account": CANONICAL_JITO_TIP_ACCOUNTS[4]}
        res = detector.detect(tx)
        assert res.is_jito_bundle is True
        assert res.slot is None
        assert res.timestamp is None

    def test_tip_lamports_coercion(self):
        detector = JitoDetector()
        # String lamports
        res_str = detector.detect({
            "chain": "sol",
            "tip_account": CANONICAL_JITO_TIP_ACCOUNTS[0],
            "tip_lamports": "7500000",
        })
        assert res_str.tip_lamports == 7500000

        # Float lamports
        res_flt = detector.detect({
            "chain": "sol",
            "tip_account": CANONICAL_JITO_TIP_ACCOUNTS[0],
            "tip_lamports": 7500000.0,
        })
        assert res_flt.tip_lamports == 7500000

        # None lamports
        res_none = detector.detect({
            "chain": "sol",
            "tip_account": CANONICAL_JITO_TIP_ACCOUNTS[0],
            "tip_lamports": None,
        })
        assert res_none.tip_lamports == 0

    def test_batch_detection(self):
        detector = JitoDetector()
        fixtures = get_mock_jito_fixtures()
        results = detector.detect_batch(fixtures)
        assert len(results) == len(fixtures)
        assert all(r.is_jito_bundle for r in results)

    def test_empty_batch(self):
        detector = JitoDetector()
        assert detector.detect_batch([]) == []
        assert detector.detect_co_slot_bundles([]) == []

    def test_co_slot_single_item(self):
        detector = JitoDetector()
        single = [{"chain": "sol", "slot": 100, "timestamp": 10.0}]
        res = detector.detect_co_slot_bundles(single)
        assert len(res) == 1
        assert SIGNAL_CO_SLOT_INGRESS not in res[0].signals

    def test_confidence_bounds_clamped(self):
        detector = JitoDetector()
        # Stack all signals to exceed 1.0 mathematically
        tx = {
            "chain": "sol",
            "tip_account": CANONICAL_JITO_TIP_ACCOUNTS[0],  # +0.50
            "bundle_id": "b123",                           # +0.50
            "is_jito": True,                               # +0.30
            "bundler_rate": 0.60,                          # +0.20
        }
        res = detector.detect(tx)
        assert res.confidence == 1.0
        assert res.is_jito_bundle is True

    def test_result_to_dict_serialization(self):
        detector = JitoDetector()
        res = detector.detect({
            "chain": "sol",
            "tip_account": CANONICAL_JITO_TIP_ACCOUNTS[1],
            "tip_lamports": 12345,
            "slot": 99999,
            "timestamp": 1726830000.5,
        })
        d = res.to_dict()
        assert isinstance(d, dict)
        assert d["is_jito_bundle"] is True
        assert d["tip_lamports"] == 12345
        assert d["slot"] == 99999
        assert json.dumps(d)  # Must be JSON-serializable

    def test_trade_record_model_compatibility(self):
        detector = JitoDetector()
        rec = TradeRecord(
            trade_id="tx_test_123",
            chain="sol",
            token_address="TokenA1111111111111111111111111111111111111",
            wallet_address="Wallet1111111111111111111111111111111111111",
            direction="buy",
            token_amount=1000.0,
            volume_usd=50.0,
            timestamp=1726830015,
            slot_or_block=284000999,
        )
        res = detector.detect(rec)
        assert res.is_jito_bundle is False
        assert res.slot == 284000999

    def test_custom_canonical_accounts_override(self):
        custom_tip = "CustomTipAddress1111111111111111111111111111"
        detector = JitoDetector(canonical_tip_accounts=[custom_tip])
        res = detector.detect({"chain": "sol", "tip_account": custom_tip})
        assert res.is_jito_bundle is True
        assert res.tip_account_matched == custom_tip

    def test_custom_threshold_override(self):
        detector = JitoDetector(detection_threshold=0.80)
        # Tip transfer has 0.50 confidence:
        # with default 0.45 it matches; with 0.80 and no tip override?
        # Note: canonical tip account sets is_bundle=True directly.
        # Let's test non-canonical signals below 0.80:
        tx = {"chain": "sol", "is_jito": True, "bundler_rate": 0.50}  # 0.30 + 0.20 = 0.50 < 0.80
        res = detector.detect(tx)
        assert res.confidence == 0.50
        assert res.is_jito_bundle is False


class TestJitoDetectorIntegration:
    """Integration tests verifying cross-module interaction with scanner and fingerprint."""

    def test_fingerprint_preserves_jito_fields(self):
        b = SyndicateBehavior(
            cluster_id="SYND-TEST-01",
            chain="sol",
            mode="flash",
            is_jito_bundle=True,
            jito_confidence=0.92,
            jito_signals=[SIGNAL_CANONICAL_TIP, SIGNAL_CO_SLOT_INGRESS],
        )
        d = b.to_dict()
        assert d["is_jito_bundle"] is True
        assert d["jito_confidence"] == 0.92
        assert SIGNAL_CANONICAL_TIP in d["jito_signals"]

        # Test from_dict reconstruction
        b2 = SyndicateBehavior.from_dict(d)
        assert b2.is_jito_bundle is True
        assert b2.jito_confidence == 0.92

        # Test semantic to_text
        text_with_jito = b.to_text(include_jito=True)
        assert "jito:yes" in text_with_jito
        text_without_jito = b.to_text(include_jito=False)
        assert "jito:" not in text_without_jito

    def test_scanner_attaches_jito_fields_to_state(self):
        scanner = LiveSyndicateScanner(mock_mode=True)
        # Scan mock token
        cluster_rec = scanner.scan_token({
            "address": "BELUGAnA11111111111111111111111111111111111",
            "symbol": "BELUGA",
        })
        assert "is_jito_bundle" in cluster_rec
        assert "jito_confidence" in cluster_rec
        assert "jito_signals" in cluster_rec

        # Generate 4D state
        state = scanner.generate_4d_temporal_state([cluster_rec])
        assert "clusters" in state
        c0 = state["clusters"][0]
        assert "is_jito_bundle" in c0
        assert "jito_confidence" in c0
        assert "jito_signals" in c0
