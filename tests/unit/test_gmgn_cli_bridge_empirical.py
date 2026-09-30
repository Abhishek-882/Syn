"""Empirical tests for gmgn_cli_bridge.py.

Tests:
- get_token_traders, get_token_holders, get_wallet_activity, get_created_tokens
- Response dictionary shape: res["data"] and res["list"] compatibility
- Failure handling: returncode != 0, empty stdout, JSON decode errors, timeouts
- Handling of nested responses from gmgn-cli
"""

import pytest
from unittest.mock import patch, MagicMock
from crypto_syndicate.api.gmgn_cli_bridge import (
    get_token_traders,
    get_token_holders,
    get_wallet_activity,
    get_created_tokens,
    gmgn_cli_call,
)


# =========================================================================
# 1. API RETURN DICTIONARY COMPATIBILITY: res["data"] AND res["list"]
# =========================================================================

def test_token_traders_empty_call_guarantees_data_and_list():
    """Verify get_token_traders returns both 'data' and 'list' as lists on empty CLI response."""
    with patch("crypto_syndicate.api.gmgn_cli_bridge.gmgn_cli_call", return_value={}):
        res = get_token_traders("sol", "4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX", limit=5)
        assert isinstance(res, dict)
        assert "data" in res, "'data' key must be in response"
        assert "list" in res, "'list' key must be in response"
        assert isinstance(res["data"], list), "res['data'] must be a list"
        assert isinstance(res["list"], list), "res['list'] must be a list"


def test_token_holders_empty_call_guarantees_data_and_list():
    """Verify get_token_holders returns both 'data' and 'list' as lists on empty CLI response."""
    with patch("crypto_syndicate.api.gmgn_cli_bridge.gmgn_cli_call", return_value={}):
        res = get_token_holders("sol", "4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX", limit=5)
        assert isinstance(res, dict)
        assert "data" in res, "'data' key must be in response"
        assert "list" in res, "'list' key must be in response"
        assert isinstance(res["data"], list)
        assert isinstance(res["list"], list)


def test_wallet_activity_guarantees_data_and_list():
    """Verify get_wallet_activity returns both 'data' and 'list' as lists."""
    with patch("crypto_syndicate.api.gmgn_cli_bridge.gmgn_cli_call", return_value={}):
        res = get_wallet_activity("sol", "4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX")
        assert isinstance(res, dict)
        assert "data" in res, "'data' key must be in response"
        assert "list" in res, "'list' key must be in response for cross-function API consistency"
        assert isinstance(res["data"], list)
        assert isinstance(res["list"], list)


def test_created_tokens_guarantees_data_and_list():
    """Verify get_created_tokens returns both 'data' and 'list' as lists."""
    with patch("crypto_syndicate.api.gmgn_cli_bridge.gmgn_cli_call", return_value={}):
        res = get_created_tokens("sol", "4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX")
        assert isinstance(res, dict)
        assert "data" in res, "'data' key must be in response"
        assert "list" in res, "'list' key must be in response for cross-function API consistency"
        assert isinstance(res["data"], list)
        assert isinstance(res["list"], list)


# =========================================================================
# 2. NESTED GMGN API RESPONSE SHAPES
# =========================================================================

def test_token_traders_nested_dict_data_structure():
    """When gmgn-cli returns standard API wrapper {'code': 0, 'data': {'list': [...]}},
    res['data'] and res['list'] must both resolve to the underlying list of items.
    """
    mock_payload = {
        "code": 0,
        "msg": "success",
        "data": {
            "list": [
                {"wallet_address": "W1", "amount": 100},
                {"wallet_address": "W2", "amount": 200},
            ]
        }
    }
    with patch("crypto_syndicate.api.gmgn_cli_bridge.gmgn_cli_call", return_value=mock_payload):
        res = get_token_traders("sol", "token_abc")
        assert isinstance(res["data"], list), f"Expected res['data'] to be list, got {type(res['data'])}"
        assert isinstance(res["list"], list), f"Expected res['list'] to be list, got {type(res.get('list'))}"
        assert len(res["data"]) == 2
        assert len(res["list"]) == 2


def test_token_holders_flat_data_list():
    """When gmgn-cli returns {'data': [{'wallet': 'W1'}]}, res['data'] and res['list'] are populated."""
    mock_payload = {
        "code": 0,
        "data": [{"wallet_address": "H1", "balance": 1000}],
    }
    with patch("crypto_syndicate.api.gmgn_cli_bridge.gmgn_cli_call", return_value=mock_payload):
        res = get_token_holders("sol", "token_abc")
        assert isinstance(res["data"], list)
        assert isinstance(res["list"], list)
        assert res["data"] == res["list"]
        assert len(res["data"]) == 1


def test_wallet_activity_with_activities_key():
    """When gmgn-cli returns {'activities': [...]}, res['data'] and res['list'] are populated."""
    mock_payload = {
        "code": 0,
        "activities": [{"tx_type": "buy", "amount": 5.0}],
    }
    with patch("crypto_syndicate.api.gmgn_cli_bridge.gmgn_cli_call", return_value=mock_payload):
        res = get_wallet_activity("sol", "wallet_abc")
        assert isinstance(res["data"], list)
        assert isinstance(res.get("list"), list), "res['list'] should be populated from activities"
        assert len(res["data"]) == 1


def test_created_tokens_with_tokens_key():
    """When gmgn-cli returns {'tokens': [...]}, res['data'] and res['list'] are populated."""
    mock_payload = {
        "code": 0,
        "tokens": [{"token_address": "T1", "name": "TestToken"}],
    }
    with patch("crypto_syndicate.api.gmgn_cli_bridge.gmgn_cli_call", return_value=mock_payload):
        res = get_created_tokens("sol", "wallet_abc")
        assert isinstance(res["data"], list)
        assert isinstance(res.get("list"), list), "res['list'] should be populated from tokens"
        assert len(res["data"]) == 1


# =========================================================================
# 3. CLI CALL ROBUSTNESS & TIMEOUT HANDLING
# =========================================================================

def test_gmgn_cli_call_subprocess_failure_returns_empty_dict():
    """When subprocess fails with non-zero exit code, return empty dict."""
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "Error: Invalid token address"
        mock_run.return_value = mock_proc

        res = gmgn_cli_call(["token", "traders"])
        assert res == {}


def test_gmgn_cli_call_json_decode_error():
    """When stdout is not valid JSON, return empty dict without crashing."""
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "502 Bad Gateway: nginx"
        mock_run.return_value = mock_proc

        res = gmgn_cli_call(["token", "traders"])
        assert res == {}


def test_gmgn_cli_call_timeout():
    """When subprocess times out, return empty dict without unhandled exception."""
    import subprocess
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="gmgn-cli", timeout=30)):
        res = gmgn_cli_call(["token", "traders"])
        assert res == {}
