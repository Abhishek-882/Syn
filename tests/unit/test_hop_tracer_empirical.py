"""Empirical tests for HopTracer (M8).

Tests:
- Cyclical graph transfers (A -> B -> C -> A, self-loops, figure-8 cycles)
- Depth limit cutoff at MAX_HOPS=5
- Min transfer filtering (MIN_TRANSFER_SOL=0.05)
- CEX hot wallet pruning and non-syndicate classification
- Disconnected wallets and empty / malformed input scenarios
"""

import pytest
from unittest.mock import MagicMock
from crypto_syndicate.hop_tracer import HopTracer, KNOWN_CEX_ADDRESSES, SharedRootResult
from crypto_syndicate.api.models import FundingTransferRecord


class MockSolscanClient:
    """Configurable mock Solscan client for graph topology testing."""

    def __init__(self, transfer_map=None):
        # transfer_map: dict of wallet -> list of FundingTransferRecord or dicts
        self.transfer_map = transfer_map or {}
        self.call_log = []

    def get_account_transfers(self, wallet: str, flow: str = "in", limit: int = 50):
        self.call_log.append((wallet, flow))
        raw_list = self.transfer_map.get(wallet, [])
        records = []
        for item in raw_list:
            if isinstance(item, (FundingTransferRecord, MagicMock)):
                records.append(item)
            elif isinstance(item, dict):
                records.append(FundingTransferRecord(
                    transfer_id=item.get("transfer_id", f"tx_{item['from_address']}_{wallet}"),
                    chain="sol",
                    from_address=item["from_address"],
                    to_address=wallet,
                    amount=float(item["amount"]),
                    timestamp=int(item.get("timestamp", 1700000000)),
                    asset_symbol="SOL",
                ))
            elif isinstance(item, tuple):
                # (from_address, amount)
                records.append(FundingTransferRecord(
                    transfer_id=f"tx_{item[0]}_{wallet}",
                    chain="sol",
                    from_address=item[0],
                    to_address=wallet,
                    amount=float(item[1]),
                    timestamp=1700000000,
                    asset_symbol="SOL",
                ))
        return records


# =========================================================================
# 1. CYCLICAL GRAPH TRANSFERS
# =========================================================================

def test_cycle_3_nodes_termination():
    """Test A -> B -> C -> A cycle terminates without infinite loop."""
    # wallet_A receives from wallet_B
    # wallet_B receives from wallet_C
    # wallet_C receives from wallet_A
    topology = {
        "wallet_A": [("wallet_B", 1.0)],
        "wallet_B": [("wallet_C", 1.0)],
        "wallet_C": [("wallet_A", 1.0)],
    }
    client = MockSolscanClient(topology)
    tracer = HopTracer(client, max_hops=5)

    # 1. find_shared_root must terminate and return result
    res = tracer.find_shared_root(["wallet_A", "wallet_B"])
    assert isinstance(res, SharedRootResult)
    # Both A and B have ancestors {A, B, C} (excluding themselves depending on start)
    # The common set should be non-empty and finite
    assert len(res.get("shared_funders", [])) > 0
    assert "wallet_C" in res["wallet_ancestors"]["wallet_A"]

    # 2. trace_funding must terminate without hanging or blowing stack
    trace_res = tracer.trace_funding(["wallet_A"])
    assert isinstance(trace_res, dict)
    assert "wallet_A" in trace_res["start_wallets"]
    assert len(trace_res["edges"]) <= 3


def test_self_loop_termination():
    """Test wallet transferring to itself does not loop infinitely or self-fund."""
    topology = {
        "wallet_A": [("wallet_A", 5.0), ("wallet_B", 1.0)],
        "wallet_B": [],
    }
    client = MockSolscanClient(topology)
    tracer = HopTracer(client, max_hops=5)

    res = tracer.find_shared_root(["wallet_A"])
    # Self should not be an ancestor of itself
    assert "wallet_A" not in res["wallet_ancestors"]["wallet_A"]
    assert "wallet_B" in res["wallet_ancestors"]["wallet_A"]


def test_figure_eight_nested_cycles():
    """Test complex tangled cycles: A <-> B and B <-> C <-> D."""
    topology = {
        "A": [("B", 1.0)],
        "B": [("A", 1.0), ("C", 2.0)],
        "C": [("D", 1.0)],
        "D": [("B", 1.5)],
    }
    client = MockSolscanClient(topology)
    tracer = HopTracer(client, max_hops=5)

    res = tracer.find_shared_root(["A", "C"])
    assert isinstance(res, dict)
    # Must terminate without Timeout / RecursionError / MemoryError
    trace_res = tracer.trace_funding(["A", "C"])
    assert len(trace_res["visited_nodes"]) > 0


# =========================================================================
# 2. DEPTH LIMIT CUTOFF (MAX_HOPS=5)
# =========================================================================

def test_depth_limit_strictly_enforced():
    """Test that BFS strictly stops at MAX_HOPS=5 and does not query beyond hop 5."""
    # Chain of 10 wallets: W0 <- W1 <- W2 <- W3 <- W4 <- W5 <- W6 <- W7 <- W8 <- W9
    topology = {
        f"W{i}": [(f"W{i+1}", 1.0)] for i in range(9)
    }
    topology["W9"] = []

    client = MockSolscanClient(topology)
    tracer = HopTracer(client, max_hops=5)

    res = tracer.find_shared_root(["W0"])
    ancestors = res["wallet_ancestors"]["W0"]

    # W1 to W5 must be present (5 hops)
    for i in range(1, 6):
        assert f"W{i}" in ancestors, f"W{i} should be in ancestors"

    # W6, W7, W8, W9 must NOT be present (exceeds max_hops=5)
    for i in range(6, 10):
        assert f"W{i}" not in ancestors, f"W{i} exceeds max_hops=5 and must be excluded"

    # Verify that client was never queried for W5's funders or beyond
    queried_wallets = {call[0] for call in client.call_log}
    assert "W5" not in queried_wallets, "W5 is at depth 5, its upstream should not be queried"
    assert "W6" not in queried_wallets


def test_trace_funding_max_depth_paths():
    """Test trace_funding hop_paths do not exceed max_hops=5."""
    topology = {f"W{i}": [(f"W{i+1}", 1.0)] for i in range(9)}
    topology["W9"] = []

    client = MockSolscanClient(topology)
    tracer = HopTracer(client, max_hops=5)

    trace = tracer.trace_funding(["W0"])
    paths = trace["hop_paths"]["W0"]
    assert len(paths) > 0
    for p in paths:
        # A path starting with W0 and traversing 5 hops has length 6: [W0, W1, W2, W3, W4, W5]
        assert len(p) <= 6, f"Path {p} exceeds max_hops 5 (node count {len(p)})"

    # Max edge depth in trace should be <= 5
    for edge in trace["edges"]:
        assert edge["depth"] <= 5


def test_custom_max_hops():
    """Test HopTracer with custom max_hops=2."""
    topology = {f"W{i}": [(f"W{i+1}", 1.0)] for i in range(5)}
    client = MockSolscanClient(topology)
    tracer = HopTracer(client, max_hops=2)

    res = tracer.find_shared_root(["W0"])
    ancestors = res["wallet_ancestors"]["W0"]
    assert "W1" in ancestors
    assert "W2" in ancestors
    assert "W3" not in ancestors


# =========================================================================
# 3. MIN TRANSFER FILTERING (MIN_TRANSFER_SOL=0.05)
# =========================================================================

def test_min_transfer_filtering_boundary():
    """Test exact boundary: 0.049 excluded, 0.05 included, 0.051 included."""
    topology = {
        "W0": [
            ("dust_funder_1", 0.049),
            ("exact_funder", 0.050),
            ("above_funder", 0.051),
            ("zero_funder", 0.0),
            ("negative_funder", -1.0),
        ],
        "dust_funder_1": [("deep_funder_1", 10.0)],
        "exact_funder": [("deep_funder_2", 10.0)],
        "above_funder": [],
    }
    client = MockSolscanClient(topology)
    tracer = HopTracer(client, min_transfer_sol=0.05)

    res = tracer.find_shared_root(["W0"])
    ancestors = res["wallet_ancestors"]["W0"]

    assert "exact_funder" in ancestors
    assert "above_funder" in ancestors
    assert "deep_funder_2" in ancestors

    assert "dust_funder_1" not in ancestors
    assert "deep_funder_1" not in ancestors  # Upstream of dust funder should not be traversed
    assert "zero_funder" not in ancestors
    assert "negative_funder" not in ancestors


def test_trace_funding_filters_sub_threshold():
    """Test trace_funding edges only contain transfers >= min_transfer_sol."""
    topology = {
        "W0": [("funder_a", 0.0499), ("funder_b", 0.05)],
    }
    client = MockSolscanClient(topology)
    tracer = HopTracer(client, min_transfer_sol=0.05)

    trace = tracer.trace_funding(["W0"])
    assert len(trace["edges"]) == 1
    assert trace["edges"][0]["from_address"] == "funder_b"
    assert trace["edges"][0]["amount"] == 0.05


# =========================================================================
# 4. CEX ADDRESS PRUNING & SYNDICATE ISOLATION
# =========================================================================

def test_cex_address_pruning():
    """Test that CEX address is not traversed further and excluded from syndicate root."""
    binance_hot_wallet = "5tzFkiKscXBHgVXYR9qTJaMmk7p8XQzL7"
    assert binance_hot_wallet in KNOWN_CEX_ADDRESSES

    topology = {
        "wallet_1": [(binance_hot_wallet, 10.0)],
        "wallet_2": [(binance_hot_wallet, 5.0)],
        # Binance receives funds from an upstream whale:
        binance_hot_wallet: [("upstream_whale", 1000.0)],
    }
    client = MockSolscanClient(topology)
    tracer = HopTracer(client)

    # 1. find_shared_root:
    # Binance is in common shared_funders, BUT excluded from syndicate_shared_roots
    res = tracer.find_shared_root(["wallet_1", "wallet_2"])
    assert binance_hot_wallet in res["shared_funders"]
    assert binance_hot_wallet not in res["syndicate_shared_roots"]
    assert res.shared_root is None  # Not flagged as a private syndicate root!

    # 2. Verify upstream of CEX was never queried/traversed
    queried_wallets = {call[0] for call in client.call_log}
    assert binance_hot_wallet not in queried_wallets, "CEX upstream must not be queried"
    assert "upstream_whale" not in res["wallet_ancestors"]["wallet_1"]


def test_cex_with_genuine_syndicate_root():
    """Test wallet cluster with BOTH a CEX deposit and a genuine shared private funder."""
    binance = "5tzFkiKscXBHgVXYR9qTJaMmk7p8XQzL7"
    syndicate_funder = "GenuineSyndicateRootFunder11111111111111111"

    topology = {
        "wallet_1": [(binance, 1.0), (syndicate_funder, 2.5)],
        "wallet_2": [(binance, 1.0), (syndicate_funder, 3.0)],
        syndicate_funder: [],
    }
    client = MockSolscanClient(topology)
    tracer = HopTracer(client)

    res = tracer.find_shared_root(["wallet_1", "wallet_2"])
    assert res.shared_root == syndicate_funder
    assert syndicate_funder in res["syndicate_shared_roots"]
    assert binance in res["shared_funders"]
    assert binance not in res["syndicate_shared_roots"]


def test_trace_funding_identifies_cex():
    """Test trace_funding flags CEX wallets in cex_wallets and edge metadata."""
    binance = "5tzFkiKscXBHgVXYR9qTJaMmk7p8XQzL7"
    topology = {
        "wallet_1": [(binance, 2.0)],
    }
    client = MockSolscanClient(topology)
    tracer = HopTracer(client)

    trace = tracer.trace_funding(["wallet_1"])
    assert binance in trace["cex_wallets"]
    assert len(trace["edges"]) == 1
    assert trace["edges"][0]["is_cex"] is True


# =========================================================================
# 5. EMPTY INPUTS, DISCONNECTED WALLETS & MALFORMED TRANSFERS
# =========================================================================

def test_empty_wallet_inputs():
    """Test empty input lists return safe defaults without throwing exceptions."""
    client = MockSolscanClient({})
    tracer = HopTracer(client)

    # find_shared_root([])
    res1 = tracer.find_shared_root([])
    assert isinstance(res1, SharedRootResult)
    assert res1.shared_root is None
    assert res1.get("shared_funders") is None or res1.get("shared_funders") == []

    # get_shared_root([])
    res2 = tracer.get_shared_root([])
    assert res2 is None

    # trace_funding([])
    res3 = tracer.trace_funding([])
    assert res3["start_wallets"] == []
    assert res3["edges"] == []
    assert res3["confidence"] == 0.0


def test_disconnected_wallets():
    """Test wallets with disjoint funding trees have no shared root and 0 confidence."""
    topology = {
        "wallet_A": [("funder_A", 1.0)],
        "wallet_B": [("funder_B", 1.0)],
        "funder_A": [],
        "funder_B": [],
    }
    client = MockSolscanClient(topology)
    tracer = HopTracer(client)

    res = tracer.find_shared_root(["wallet_A", "wallet_B"])
    assert res.shared_root is None
    assert res["shared_funders"] == []
    assert res["confidence"] == 0.0


def test_client_exception_resilience():
    """Test tracer handles Solscan client exceptions gracefully."""
    client = MagicMock()
    client.get_account_transfers.side_effect = RuntimeError("Solscan 500 Internal Server Error")

    tracer = HopTracer(client)
    res = tracer.find_shared_root(["wallet_err"])
    assert res.shared_root is None
    assert res["wallet_ancestors"]["wallet_err"] == []

    trace = tracer.trace_funding(["wallet_err"])
    assert trace["edges"] == []
    assert trace["confidence"] == 0.0


def test_dict_and_object_transfers_interoperability():
    """Test _get_funders handles dict transfers and FundingTransferRecord objects."""
    record_obj = FundingTransferRecord(
        transfer_id="tx_1",
        chain="sol",
        from_address="obj_funder",
        to_address="W0",
        amount=1.5,
        timestamp=1700000000,
        asset_symbol="SOL",
    )
    dict_record = {
        "from_address": "dict_funder",
        "amount": 2.5,
        "timestamp": 1700000010,
        "transfer_id": "tx_2",
    }
    client = MagicMock()
    client.get_account_transfers.return_value = [record_obj, dict_record, None, {}]

    tracer = HopTracer(client)
    res = tracer.find_shared_root(["W0"])
    ancestors = res["wallet_ancestors"]["W0"]
    assert "obj_funder" in ancestors
    assert "dict_funder" in ancestors
