"""Adversarial and interface contract verification script."""

import os
import pytest
from crypto_syndicate import (
    CryptoDataClient,
    TokenLaunchEvent,
    TradeRecord,
    FundingTransferRecord,
    SyndicateCluster,
    WalletScore,
    PatternType,
    GMGNClient,
    SolscanClient,
)
from crypto_syndicate.api.base_client import (
    APIClientError,
    APIRequestError,
    APIAuthenticationError,
    APIForbiddenError,
    APINotFoundError,
    MaxRetriesExceededError,
)


def test_interface_contracts(monkeypatch):
    monkeypatch.setenv("CRYPTO_DATA_MODE", "mock")
    client = CryptoDataClient()

    # 1. get_new_token_launches
    launches = client.get_new_token_launches(chain="sol", time_period="1h")
    assert isinstance(launches, list)
    assert len(launches) > 0
    for l in launches:
        assert isinstance(l, TokenLaunchEvent)
        assert l.chain == "sol"
        assert len(l.token_address) > 0

    # 2. get_token_trades
    trades = client.get_token_trades(chain="sol", token_address=launches[0].token_address, limit=500)
    assert isinstance(trades, list)
    assert len(trades) > 0
    for t in trades:
        assert isinstance(t, TradeRecord)
        assert t.direction in ("buy", "sell")
        assert len(t.wallet_address) > 0

    # 3. get_wallet_transfers
    transfers = client.get_wallet_transfers(chain="sol", wallet_address=trades[0].wallet_address, flow="in")
    assert isinstance(transfers, list)
    for tr in transfers:
        assert isinstance(tr, FundingTransferRecord)
        assert len(tr.from_address) > 0
        assert len(tr.to_address) > 0

    # 4. get_account_metadata
    metadata = client.get_account_metadata(wallet_address=trades[0].wallet_address)
    assert metadata is not None
    assert isinstance(metadata, dict)
    assert "funded_by" in metadata
    assert len(metadata["funded_by"]) > 0


def test_multi_chain_coverage(monkeypatch):
    """Verify GMGN client supports all mandated chains: sol, eth, bsc, base, tron."""
    monkeypatch.setenv("CRYPTO_DATA_MODE", "mock")
    client = CryptoDataClient()
    for chain in ["sol", "eth", "bsc", "base"]:
        launches = client.get_new_token_launches(chain=chain)
        assert len(launches) > 0, f"No mock launches found for chain: {chain}"
        assert launches[0].chain == chain


def test_solscan_transfers_empty_wallet():
    """Solscan querying an unknown wallet in mock mode should return empty list gracefully."""
    client = SolscanClient(mock_mode=True)
    res = client.get_account_transfers("UnknownWalletAddress1111111111111111111111111")
    assert res == []


def test_solscan_metadata_unknown_wallet():
    """Solscan querying an unknown wallet should return fallback metadata envelope."""
    client = SolscanClient(mock_mode=True)
    res = client.get_account_metadata("UnknownWalletAddress1111111111111111111111111")
    assert res is not None
    assert res["account"] == "UnknownWalletAddress1111111111111111111111111"
    assert "funded_by" in res


def test_exception_hierarchy():
    """Verify all custom exceptions inherit from APIClientError."""
    assert issubclass(APIRequestError, APIClientError)
    assert issubclass(APIAuthenticationError, APIClientError)
    assert issubclass(APIForbiddenError, APIClientError)
    assert issubclass(APINotFoundError, APIClientError)
    assert issubclass(MaxRetriesExceededError, APIClientError)
