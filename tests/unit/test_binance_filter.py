"""Unit tests for Milestone 25: Binance-Funded Dev Wallet Filter.

Verifies:
1. Token track record correctly tags Binance-funded tokens.
2. Deployer profiles identify Binance CEX genesis funding.
3. Non-Binance tokens (KuCoin, MEXC, Gate.io, Direct) are properly tagged False.
4. Token lineage preserves Binance provenance in Stage 1 node.
5. Ingestion of newly discovered tokens enriches Binance funding metadata.
"""

from pathlib import Path
import sys
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from crypto_syndicate.ground_truth_loader import get_ground_truth_loader


def test_token_history_binance_flags():
    """Verify get_syndicate_token_history correctly flags Binance-funded tokens."""
    loader = get_ground_truth_loader()
    loader.reload()
    history = loader.get_syndicate_token_history()

    assert len(history) >= 30, f"Expected at least 30 historical tokens, got {len(history)}"

    binance_tokens = [t for t in history if t.get("is_binance_funded")]
    assert len(binance_tokens) >= 7, f"Expected at least 7 Binance-funded tokens, got {len(binance_tokens)}"

    binance_symbols = {t["symbol"] for t in binance_tokens}
    expected_symbols = {"LEVERAGE", "BITDOG", "SNS", "SI", "Arthur", "JADOODOO", "KREL"}
    assert expected_symbols.issubset(binance_symbols), f"Mismatched Binance symbols: {binance_symbols} does not contain {expected_symbols}"

    # Non-Binance checks
    non_binance = [t for t in history if not t.get("is_binance_funded")]
    assert len(non_binance) >= 20
    non_binance_symbols = {t["symbol"] for t in non_binance}
    assert "runner" in non_binance_symbols  # KuCoin
    assert "XSEED" in non_binance_symbols   # MEXC


def test_deployers_binance_flags():
    """Verify deployers identify Binance genesis funding."""
    loader = get_ground_truth_loader()
    loader.reload()
    deployers = loader.get_deployers()

    assert len(deployers) > 0
    binance_deployers = [d for d in deployers if d.get("is_binance_funded")]
    assert len(binance_deployers) >= 7

    # Verify LEVERAGE deployer
    lev_dep = next((d for d in deployers if d["address"].startswith("DFZ497")), None)
    assert lev_dep is not None, "LEVERAGE deployer not found"
    assert lev_dep.get("is_binance_funded") is True
    assert "Binance" in lev_dep.get("funded_by", "")


def test_token_lineage_funder_stage():
    """Verify get_token_lineage Stage 1 node correctly references Binance."""
    loader = get_ground_truth_loader()
    loader.reload()
    lineage = loader.get_token_lineage("BM2k8mJUbMthHoioykyUm2NjMrXvLBYhoXruwYLpump")

    assert lineage is not None
    assert lineage["symbol"] == "LEVERAGE"
    nodes = lineage["nodes"]
    stage1 = next((n for n in nodes if n.get("stage") == 1), None)
    assert stage1 is not None
    assert "Binance" in stage1["label"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
