"""Unit test verifying the past 7 days token filtering on backend and API layers."""

from pathlib import Path
import sys
import time
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from crypto_syndicate.ground_truth_loader import get_ground_truth_loader


def test_ground_truth_loader_past_7_days_filter():
    """Verify get_syndicate_token_history respects max_age_days."""
    loader = get_ground_truth_loader()
    loader.reload()

    # 1. Full history (no filter)
    all_tokens = loader.get_syndicate_token_history(max_age_days=None)
    assert len(all_tokens) >= 30, f"Expected >= 30 tokens in full history, got {len(all_tokens)}"

    # Confirm older tokens exist in full history
    symbols_all = {t["symbol"] for t in all_tokens}
    assert "BITDOG" in symbols_all, "BITDOG (16d old) should be present in unfiltered history"

    # 2. Filtered history (7 days)
    tokens_7d = loader.get_syndicate_token_history(max_age_days=7.0)
    assert len(tokens_7d) > 0, "Expected tokens within past 7 days"
    assert len(tokens_7d) < len(all_tokens), "Filtered tokens should exclude older tokens"

    now = time.time()
    for t in tokens_7d:
        age_days = (now - t["launch_timestamp"]) / 86400.0
        assert age_days <= 7.001, f"Token {t['symbol']} has age {age_days:.2f}d > 7.0d"

    symbols_7d = {t["symbol"] for t in tokens_7d}
    assert "BITDOG" not in symbols_7d, "BITDOG (16d old) must be excluded from past 7 days"
    assert "LEVERAGE" in symbols_7d, "LEVERAGE (~4d old) must be included in past 7 days"
    assert "BAGWORK" in symbols_7d, "BAGWORK (~1d old) must be included in past 7 days"
    assert "PUZZLE" in symbols_7d, "PUZZLE (~1d old) must be included in past 7 days"


def test_binance_tokens_past_7_days():
    """Verify Binance-funded tokens within past 7 days."""
    loader = get_ground_truth_loader()
    loader.reload()

    tokens_7d = loader.get_syndicate_token_history(max_age_days=7.0)
    binance_7d = [t for t in tokens_7d if t.get("is_binance_funded")]

    # All returned Binance tokens must be <= 7 days old
    now = time.time()
    for t in binance_7d:
        age_days = (now - t["launch_timestamp"]) / 86400.0
        assert age_days <= 7.001
        assert t["is_binance_funded"] is True

    binance_symbols = {t["symbol"] for t in binance_7d}
    assert "LEVERAGE" in binance_symbols
    assert "BAGWORK" in binance_symbols
    assert "BITDOG" not in binance_symbols
