"""Unit tests for SyndicateGraph (M3).

Tests graph construction, WCC + Louvain clustering, edge types, and D3 JSON export.
"""

import pytest

from crypto_syndicate.graph import SyndicateGraph, MIN_CLUSTER_SIZE
from crypto_syndicate.api.models import SyndicateCluster


@pytest.fixture
def empty_graph():
    return SyndicateGraph()


def test_build_graph_adds_wallet_nodes(empty_graph):
    """Test that nodes are created for each wallet with appropriate metadata."""
    wallets = [
        {
            "wallet_address": "w1",
            "chain": "sol",
            "suspicion_score": 50.0,
            "patterns_flagged": ["early_entry"],
            "tokens_traded": ["tok1"],
            "estimated_profit_usd": 100.0,
        },
        {
            "wallet_address": "w2",
            "chain": "sol",
            "suspicion_score": 75.0,
            "patterns_flagged": ["early_entry", "common_funding"],
            "tokens_traded": ["tok1"],
            "estimated_profit_usd": 250.0,
        },
    ]
    empty_graph.build_graph(wallets)
    assert "w1" in empty_graph.graph.nodes
    assert "w2" in empty_graph.graph.nodes
    assert empty_graph.graph.nodes["w1"]["suspicion_score"] == 50.0
    assert empty_graph.graph.nodes["w2"]["suspicion_score"] == 75.0
    assert empty_graph.graph.nodes["w1"]["chain"] == "sol"
    assert empty_graph.graph.nodes["w1"]["estimated_profit_usd"] == 100.0


def test_build_graph_co_buy_edges(empty_graph):
    """Test that wallets sharing a token receive a bidirectional co_buy edge."""
    wallets = [
        {"wallet_address": "wallet_a", "tokens_traded": ["token_xyz"]},
        {"wallet_address": "wallet_b", "tokens_traded": ["token_xyz"]},
    ]
    empty_graph.build_graph(wallets)
    assert empty_graph.graph.has_edge("wallet_a", "wallet_b")
    assert empty_graph.graph.has_edge("wallet_b", "wallet_a")

    edge_ab = empty_graph.graph["wallet_a"]["wallet_b"]
    assert edge_ab["type"] == "co_buy"
    assert edge_ab["weight"] == 1
    assert "token_xyz" in edge_ab["shared_tokens"]


def test_build_graph_funding_edges(empty_graph):
    """Test that funding relationships become directed edges with weight=2."""
    wallets = [{"wallet_address": "recipient_wallet"}]
    funding = [
        {
            "funder": "master_funder",
            "funded": "recipient_wallet",
            "amount": 10.0,
            "amount_usd": 1500.0,
            "chain": "sol",
        }
    ]
    empty_graph.build_graph(wallets, funding)
    assert empty_graph.graph.has_edge("master_funder", "recipient_wallet")
    assert not empty_graph.graph.has_edge("recipient_wallet", "master_funder")

    edge = empty_graph.graph["master_funder"]["recipient_wallet"]
    assert edge["type"] == "funding"
    assert edge["weight"] == 2
    assert edge["amount"] == 10.0


def test_build_graph_empty_input(empty_graph):
    """Test that build_graph handles empty wallet list without crashing."""
    empty_graph.build_graph([])
    assert empty_graph.graph.number_of_nodes() == 0
    assert empty_graph.graph.number_of_edges() == 0


def test_detect_clusters_returns_syndicate_clusters(empty_graph):
    """Test that clusters are returned for connected mock graph."""
    wallets = [
        {
            "wallet_address": f"cluster_w{i}",
            "chain": "sol",
            "tokens_traded": ["shared_token_1"],
            "patterns_flagged": ["early_entry"],
            "suspicion_score": 45.0,
        }
        for i in range(1, 5)
    ]
    empty_graph.build_graph(wallets)
    clusters = empty_graph.detect_clusters()
    assert len(clusters) >= 1
    assert isinstance(clusters[0], SyndicateCluster)
    assert len(clusters[0].wallets) >= 3
    assert clusters[0].chain == "sol"
    assert clusters[0].suspicion_score > 0.0


def test_detect_clusters_min_size_3(empty_graph):
    """Test that clusters strictly require at least 3 members."""
    # Only 2 wallets connected (size 2 < MIN_CLUSTER_SIZE 3)
    wallets = [
        {"wallet_address": "pair_w1", "tokens_traded": ["pair_token"]},
        {"wallet_address": "pair_w2", "tokens_traded": ["pair_token"]},
    ]
    empty_graph.build_graph(wallets)
    clusters = empty_graph.detect_clusters()
    assert len(clusters) == 0

    # 3 wallets connected (size 3 >= MIN_CLUSTER_SIZE 3)
    wallets_3 = [
        {"wallet_address": "triplet_w1", "tokens_traded": ["triplet_token"]},
        {"wallet_address": "triplet_w2", "tokens_traded": ["triplet_token"]},
        {"wallet_address": "triplet_w3", "tokens_traded": ["triplet_token"]},
    ]
    empty_graph.build_graph(wallets_3)
    clusters_3 = empty_graph.detect_clusters()
    assert len(clusters_3) == 1
    assert len(clusters_3[0].wallets) == 3


def test_detect_clusters_empty_graph(empty_graph):
    """Test that detect_clusters returns [] on empty graph."""
    clusters = empty_graph.detect_clusters()
    assert clusters == []


def test_export_graph_json_structure(empty_graph):
    """Test that export_graph_json returns dict with 'nodes' and 'links' keys."""
    wallets = [
        {"wallet_address": f"w{i}", "tokens_traded": ["token_alpha"]}
        for i in range(1, 4)
    ]
    empty_graph.build_graph(wallets)
    clusters = empty_graph.detect_clusters()
    json_data = empty_graph.export_graph_json(clusters)

    assert isinstance(json_data, dict)
    assert "nodes" in json_data
    assert "links" in json_data
    assert len(json_data["nodes"]) == 3
    assert len(json_data["links"]) > 0


def test_export_graph_json_node_has_cluster_id(empty_graph):
    """Test that each node in exported JSON has a cluster_id field."""
    wallets = [
        {"wallet_address": f"w{i}", "tokens_traded": ["token_alpha"]}
        for i in range(1, 4)
    ]
    # Also add an isolated node not in any cluster
    wallets.append({"wallet_address": "w_isolated", "tokens_traded": ["token_other"]})

    empty_graph.build_graph(wallets)
    clusters = empty_graph.detect_clusters()
    json_data = empty_graph.export_graph_json(clusters)

    nodes_by_id = {n["id"]: n for n in json_data["nodes"]}
    assert "w1" in nodes_by_id
    assert "cluster_id" in nodes_by_id["w1"]
    assert nodes_by_id["w1"]["cluster_id"] != "unclustered"

    assert "w_isolated" in nodes_by_id
    assert nodes_by_id["w_isolated"]["cluster_id"] == "unclustered"
