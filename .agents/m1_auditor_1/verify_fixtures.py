"""Independent Forensic Audit of Golden Fixtures."""

import sys
import re

sys.path.insert(0, r"C:\Users\Asus\Documents\antigravity\hopeful-curie\src")

from crypto_syndicate.api.fixtures import (
    get_mock_clusters,
    get_mock_token_launches,
    get_mock_token_trades,
    get_mock_wallet_transfers,
    get_mock_account_metadata,
)
from crypto_syndicate.api.models import PatternType

print("Starting Golden Fixtures forensic audit...")

clusters = get_mock_clusters()
if len(clusters) != 5:
    print(f"FAIL: Expected exactly 5 golden clusters, found {len(clusters)}")
    sys.exit(1)
print(f"PASS: Exactly 5 golden clusters: {[c.cluster_id for c in clusters]}")

valid_patterns = {p.value for p in PatternType}
evm_re = re.compile(r"^0x[a-fA-F0-9]{40}$")
base58_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")

for c in clusters:
    # Check 1: >= 3 wallets
    if len(c.wallets) < 3:
        print(f"FAIL: Cluster {c.cluster_id} has only {len(c.wallets)} wallets (<3)")
        sys.exit(1)
    
    # Check 2: >= 2 patterns
    patterns = set(c.flagged_patterns)
    if len(patterns) < 2:
        print(f"FAIL: Cluster {c.cluster_id} has only {len(patterns)} patterns (<2)")
        sys.exit(1)
    if not patterns.issubset(valid_patterns):
        print(f"FAIL: Invalid patterns {patterns - valid_patterns} in {c.cluster_id}")
        sys.exit(1)
        
    # Check 3: Address formats
    for w in c.wallets:
        if c.chain in ("eth", "bsc", "base"):
            if not evm_re.match(w):
                print(f"FAIL: Invalid EVM address format: {w}")
                sys.exit(1)
        elif c.chain == "sol":
            if not (32 <= len(w) <= 44 and set(w).issubset(base58_chars)):
                print(f"FAIL: Invalid Solana address format: {w}")
                sys.exit(1)

    # Check 4: PnL math
    wallet_sum = sum(ws.net_profit_usd for ws in c.wallet_scores.values())
    if abs(c.estimated_profit_usd - wallet_sum) > 0.05:
        print(f"FAIL: PnL mismatch in {c.cluster_id}: cluster={c.estimated_profit_usd}, sum={wallet_sum}")
        sys.exit(1)
        
    # Check 5: Chronology in trades
    for token in c.associated_tokens:
        trades = get_mock_token_trades(c.chain, token)
        buys = [t for t in trades if t.direction == "buy"]
        sells = [t for t in trades if t.direction == "sell"]
        if buys and sells:
            avg_buy = sum(t.timestamp for t in buys) / len(buys)
            avg_sell = sum(t.timestamp for t in sells) / len(sells)
            if avg_sell <= avg_buy:
                print(f"FAIL: Exit dump preceded buy in {c.cluster_id}")
                sys.exit(1)

print("PASS: All 5 golden clusters conform to criteria, valid address formats, and reconciled PnL math.")
print("ALL GOLDEN FIXTURES FORENSIC CHECKS PASSED.")
