"""Bridge to call gmgn-cli for Cloudflare-protected GMGN endpoints."""
import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def gmgn_cli_call(args: list) -> dict:
    """Call npx gmgn-cli with given args, return parsed JSON or empty dict."""
    try:
        npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
        result = subprocess.run(
            [npx_cmd, "gmgn-cli"] + args,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        elif result.returncode != 0:
            logger.warning(
                "gmgn-cli returned exit code %s: %s",
                result.returncode,
                result.stderr.strip()[:200] if result.stderr else "No stderr",
            )
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning("gmgn-cli call failed: %s", e)
    return {}


def _normalize_envelope(res, alt_key=None):
    """Normalize GMGN CLI response so res["data"] and res["list"] are always lists.

    Handles:
      1. {"data": [...]}               -> use data list directly
      2. {"data": {"list": [...], ...}} -> unpack nested GMGN API wrapper
      3. {"list": [...]} or {alt_key: [...]} -> use that list
    """
    if not isinstance(res, dict):
        base = {"data": [], "list": []}
        if alt_key:
            base[alt_key] = []
        return base

    raw = res.get("data")
    if isinstance(raw, dict):
        items = raw.get("list") or (raw.get(alt_key) if alt_key else None) or []
        if not isinstance(items, list):
            items = []
    elif isinstance(raw, list):
        items = raw
    else:
        candidate = res.get("list") or (res.get(alt_key) if alt_key else None) or []
        items = candidate if isinstance(candidate, list) else []

    res["data"] = items
    res["list"] = items
    if alt_key:
        res[alt_key] = items
    return res


def get_token_traders(chain, address, limit=50, tag=None):
    """gmgn-cli token traders --chain=X --address=Y --limit=Z [--tag=bundler] --raw"""
    args = ["token", "traders", f"--chain={chain}", f"--address={address}", f"--limit={limit}", "--raw"]
    if tag:
        args.append(f"--tag={tag}")
    return _normalize_envelope(gmgn_cli_call(args))


def get_token_holders(chain, address, limit=20):
    """gmgn-cli token holders --chain=X --address=Y --limit=Z --raw"""
    args = ["token", "holders", f"--chain={chain}", f"--address={address}", f"--limit={limit}", "--raw"]
    return _normalize_envelope(gmgn_cli_call(args))


def get_wallet_activity(chain, address):
    """gmgn-cli portfolio activity --chain=X --wallet=Y --raw"""
    args = ["portfolio", "activity", f"--chain={chain}", f"--wallet={address}", "--raw"]
    return _normalize_envelope(gmgn_cli_call(args), alt_key="activities")


def get_created_tokens(chain, address):
    """gmgn-cli portfolio created-tokens --chain=X --wallet=Y --raw"""
    args = ["portfolio", "created-tokens", f"--chain={chain}", f"--wallet={address}", "--raw"]
    return _normalize_envelope(gmgn_cli_call(args), alt_key="tokens")
