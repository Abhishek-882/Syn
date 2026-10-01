"""Unit tests for Milestone 24 Interactive Syndicate Chained-Link Flowchart & Proof Engine.

Verifies:
1. GroundTruthLoader.get_token_lineage() resolves complete 5-stage proof graphs.
2. Verification of Genesis CEX Funder provenance.
3. Verification of Syndicate Deployer attribution.
4. Verification of Token Mint with peak ATH metrics.
5. Verification of Co-Slot Jito Bundlers & Early Snipers.
6. Symbol search resolution ($BITDOG, $LEVERAGE).
"""

import pytest
from crypto_syndicate.ground_truth_loader import get_ground_truth_loader


@pytest.fixture
def loader():
    """Return reloaded ground truth loader instance."""
    instance = get_ground_truth_loader()
    instance.reload()
    return instance


def test_get_token_lineage_leverage(loader):
    """Test full 5-stage proof resolution for primary token $LEVERAGE."""
    lineage = loader.get_token_lineage("BM2k8mJUbMthHoioykyUm2NjMrXvLBYhoXruwYLpump")
    assert lineage is not None
    assert lineage["status"] == "ok"
    assert lineage["symbol"] == "LEVERAGE"
    assert lineage["syndicate_id"] == "SYND-0095"
    assert lineage["is_syndicate_verified"] is True
    assert lineage["suspicion_score"] >= 80.0
    assert "Binance" in lineage["proof_summary"]

    nodes = lineage["nodes"]
    assert len(nodes) == 7

    # Stage 1: Genesis Funder
    funder = nodes[0]
    assert funder["stage"] == 1
    assert "Binance" in funder["label"]
    assert funder["type"] == "treasury"

    # Stage 2: Intermediate Hop Anchor
    hop = nodes[1]
    assert hop["stage"] == 2
    assert "Hop Anchor" in hop["label"]
    assert hop["type"] == "hop"

    # Stage 3: Syndicate Deployer
    deployer = nodes[2]
    assert deployer["stage"] == 3
    assert deployer["address"] == "DFZ497f4YTS4RXjPeKPuECHXSmoVnvoFMpmErnZK61cc"
    assert deployer["type"] == "deployer"

    # Stage 4: Token Mint
    mint = nodes[3]
    assert mint["stage"] == 4
    assert mint["address"] == "BM2k8mJUbMthHoioykyUm2NjMrXvLBYhoXruwYLpump"
    assert mint["type"] == "token"
    assert float(mint["sol_value"].replace("$", "").replace(" ATH", "").replace(",", "")) >= 1000000.0

    # Stage 5: Co-Slot Bundlers & Snipers
    bundlers = [n for n in nodes if n["type"] == "bundler"]
    snipers = [n for n in nodes if n["type"] == "sniper"]
    assert len(bundlers) == 2
    assert len(snipers) == 1

    # Verify Edges
    edges = lineage["edges"]
    assert len(edges) == 6
    assert any(e["from"] == "STAGE_1_FUNDER" and e["to"] == "STAGE_2_HOP" for e in edges)
    assert any(e["from"] == "STAGE_2_HOP" and e["to"] == "STAGE_3_DEPLOYER" for e in edges)
    assert any(e["from"] == "STAGE_3_DEPLOYER" and e["to"] == "STAGE_4_MINT" for e in edges)


def test_get_token_lineage_by_symbol_bitdog(loader):
    """Test resolving token lineage by symbol query (case-insensitive)."""
    lineage = loader.get_token_lineage("bitdog")
    assert lineage is not None
    assert lineage["symbol"] == "BITDOG"
    assert lineage["syndicate_id"] == "SYND-0096"
    assert lineage["deployer_address"] == "35EeJFfuRRU5hZHtB7g1DFjx2TokQf2ibaJeWSskw8nx"
    assert lineage["is_syndicate_verified"] is True


def test_get_token_lineage_fallback(loader):
    """Test fallback when given an unknown mint string."""
    lineage = loader.get_token_lineage("UnknownMintAddress1111111111111111111111111111")
    assert lineage is not None
    assert lineage["status"] == "ok"
    assert len(lineage["nodes"]) == 7
