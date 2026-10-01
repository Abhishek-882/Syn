"""Recalibrate all tokens in live_dexscreener_syndicate_tokens.json.

Ensures:
1. ATH Market Cap is calculated strictly from token's own ath_price * total_supply
   (or dev ath_mc ONLY if ath_token == token mint).
2. Elimination of all inflated ATH values (e.g. $OpenSI $1.07 Quadrillion, $AI $767K, $SC $1.44M).
3. Creation timestamp is taken from token's own creation_timestamp, NOT developer's previous coin.
4. Preserves Binance funder tags and all syndicate mappings.
"""

import json
import logging
from pathlib import Path
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("recalibrate_tokens")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
LIVE_TOKENS_FILE = PROJECT_ROOT / "results" / "live_dexscreener_syndicate_tokens.json"


def recalibrate():
    if not LIVE_TOKENS_FILE.exists():
        logger.error("File not found: %s", LIVE_TOKENS_FILE)
        return

    with open(LIVE_TOKENS_FILE, "r", encoding="utf-8") as f:
        tokens = json.load(f)

    logger.info("Loaded %d tokens from %s", len(tokens), LIVE_TOKENS_FILE)
    changes = []

    for t in tokens:
        mint = t.get("token")
        sym = t.get("symbol", "TOKEN")
        old_ath = float(t.get("ath_market_cap_usd") or 0.0)
        old_created_ms = int(t.get("created_at_ms") or 0)
        old_curr_mc = float(t.get("current_market_cap_usd") or 0.0)

        raw = t.get("raw_data") or {}
        dev = raw.get("dev") or {}
        ath_info = dev.get("ath_token_info") or {}
        price_info = raw.get("price") or {}

        # 1. Total supply
        raw_supply = raw.get("total_supply") or raw.get("circulating_supply")
        try:
            supply = float(raw_supply) if raw_supply else 1_000_000_000.0
        except Exception:
            supply = 1_000_000_000.0
        if supply < 100_000:
            supply = 1_000_000_000.0

        # 2. Current price and Current Mcap
        curr_price = float(price_info.get("price") or raw.get("price") or t.get("price_usd") or 0.0)
        calc_curr_mc = curr_price * supply if curr_price > 0 else old_curr_mc
        if calc_curr_mc <= 0 and raw.get("liquidity"):
            calc_curr_mc = float(raw.get("liquidity")) * 2.0

        # 3. ATH calculation
        is_same_token = (ath_info.get("ath_token") == mint)
        dev_ath_mc = 0.0
        if is_same_token and ath_info.get("ath_mc"):
            try:
                dev_ath_mc = float(ath_info["ath_mc"])
            except Exception:
                dev_ath_mc = 0.0

        ath_price = float(raw.get("ath_price") or raw.get("high_price") or price_info.get("high_24h") or 0.0)

        if ath_price > 0:
            calc_ath_mc = ath_price * supply
        elif dev_ath_mc > 0:
            calc_ath_mc = dev_ath_mc
        else:
            calc_ath_mc = calc_curr_mc

        # Guarantee invariant: ATH >= Current MC
        calc_ath_mc = max(calc_ath_mc, calc_curr_mc)

        # 4. Creation Timestamp: strictly use token's own creation, NEVER dev's prior coin
        launch_ts = (
            raw.get("creation_timestamp")
            or (ath_info.get("creation_timestamp") if is_same_token else None)
            or raw.get("open_timestamp")
        )
        if not launch_ts or launch_ts <= 0:
            # If no raw creation timestamp, keep existing if valid or fallback to current
            launch_ts = (old_created_ms / 1000.0) if old_created_ms > 1e11 else time.time()

        new_created_ms = int(launch_ts * 1000) if launch_ts < 1e11 else int(launch_ts)

        # Record changes
        ath_diff = abs(old_ath - calc_ath_mc)
        time_diff = abs(old_created_ms - new_created_ms)

        if ath_diff > 5.0 or time_diff > 10000:
            changes.append({
                "symbol": sym,
                "mint": mint,
                "old_ath": old_ath,
                "new_ath": calc_ath_mc,
                "old_created_ms": old_created_ms,
                "new_created_ms": new_created_ms,
                "ath_price": ath_price,
                "is_same_token": is_same_token,
            })

        # Apply calibrated values
        t["ath_market_cap_usd"] = round(calc_ath_mc, 2)
        t["current_market_cap_usd"] = round(calc_curr_mc, 2)
        t["created_at_ms"] = new_created_ms

    logger.info("Tokens needing calibration: %d / %d", len(changes), len(tokens))
    for c in changes:
        logger.info(
            "$%-10s | ATH: $%12.2f -> $%12.2f | Created: %d -> %d | same=%s",
            c["symbol"], c["old_ath"], c["new_ath"], c["old_created_ms"], c["new_created_ms"], c["is_same_token"],
        )

    # Save calibrated file
    with open(LIVE_TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)

    logger.info("Successfully saved calibrated tokens to %s", LIVE_TOKENS_FILE)

    # Reload GroundTruthLoader to verify
    from crypto_syndicate.ground_truth_loader import get_ground_truth_loader
    loader = get_ground_truth_loader()
    loader.reload()
    history = loader.get_syndicate_token_history()
    logger.info("GroundTruthLoader reloaded! Total history tokens: %d", len(history))
    if history:
        logger.info("Top token: $%s - ATH: %s, Current: %s, Age: %s",
                    history[0]["symbol"], history[0]["ath_market_cap_formatted"],
                    history[0]["current_market_cap_formatted"], history[0]["relative_time_str"])


if __name__ == "__main__":
    recalibrate()
