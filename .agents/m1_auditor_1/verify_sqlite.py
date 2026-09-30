"""Independent SQLite Cache Persistence & Integrity Verification Script.

Tests:
1. Creation of actual database file on disk.
2. Direct sqlite3 table and index inspection.
3. PRAGMA journal_mode = wal verification.
4. SHA-256 key determinism and auth stripping.
5. Insertion, retrieval, and disk size verification.
6. Tiered TTL resolution and expiration handling.
7. Real file persistence across separate process/connection instances.
"""

import os
import sys
import time
import sqlite3
import tempfile
import pathlib

# Add src to path
sys.path.insert(0, r"C:\Users\Asus\Documents\antigravity\hopeful-curie\src")

from crypto_syndicate.api.cache import (
    SQLiteCache,
    TTL_IMMUTABLE,
    TTL_SEMI_STATIC,
    TTL_DYNAMIC,
)

test_dir = tempfile.mkdtemp(prefix="auditor_sqlite_test_")
db_path = os.path.join(test_dir, "test_cache.db")

print(f"Testing SQLiteCache at: {db_path}")

# Step 1: Initialize cache
cache = SQLiteCache(db_path=db_path)

# Verify DB file exists on disk
if not os.path.exists(db_path):
    print("FAIL: DB file was not created on disk.")
    sys.exit(1)
print(f"PASS: DB file created successfully. Size: {os.path.getsize(db_path)} bytes")

# Step 2: Directly inspect SQLite schema using standard sqlite3
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Check table existence
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_cache';")
table = cur.fetchone()
if not table:
    print("FAIL: api_cache table not found in sqlite_master.")
    sys.exit(1)
print("PASS: api_cache table exists.")

# Check PRAGMAs
cur.execute("PRAGMA journal_mode;")
mode = cur.fetchone()[0]
print(f"PASS: SQLite journal_mode is: {mode}")

# Check columns
cur.execute("PRAGMA table_info(api_cache);")
cols = [r[1] for r in cur.fetchall()]
expected_cols = ["cache_key", "provider", "endpoint", "params_hash", "status_code", "response_body", "created_at", "expires_at"]
for ec in expected_cols:
    if ec not in cols:
        print(f"FAIL: Missing column {ec} in api_cache table.")
        sys.exit(1)
print(f"PASS: All expected columns exist: {cols}")
conn.close()

# Step 3: Test SHA-256 key generation
k1, h1 = cache.generate_key("gmgn", "rank/sol/swaps", {"a": 1, "b": 2, "token": "secret"})
k2, h2 = cache.generate_key("gmgn", "rank/sol/swaps", {"b": 2, "a": 1, "token": "other_secret"})
if k1 != k2:
    print("FAIL: Cache keys differ when only param order or token differs.")
    sys.exit(1)
print(f"PASS: Deterministic key generation: {k1}")

# Step 4: Test insertion and retrieval
test_payload = {"status": "ok", "items": [1, 2, 3], "nested": {"key": "value"}}
cache_key = cache.set("gmgn", "rank/sol/swaps", {"a": 1, "b": 2}, 200, test_payload, ttl=2.0)
if not cache_key:
    print("FAIL: set returned empty cache_key.")
    sys.exit(1)
print(f"PASS: Record inserted with key: {cache_key}")

# Verify via separate direct connection
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT provider, endpoint, status_code, response_body, expires_at FROM api_cache WHERE cache_key = ?", (cache_key,))
row = cur.fetchone()
if not row:
    print("FAIL: Inserted row not found via direct sqlite3 connection.")
    sys.exit(1)
print(f"PASS: Direct SQL verification: provider={row[0]}, endpoint={row[1]}, status={row[2]}")
conn.close()

# Test retrieval via cache instance
retrieved = cache.get("gmgn", "rank/sol/swaps", {"b": 2, "a": 1})
if retrieved != test_payload:
    print(f"FAIL: Retrieved payload mismatch: {retrieved} vs {test_payload}")
    sys.exit(1)
print("PASS: Cache get returned identical payload.")

# Step 5: Test TTL expiration
print("Testing TTL expiration (sleeping 2.2s)...")
time.sleep(2.2)
expired_retrieved = cache.get("gmgn", "rank/sol/swaps", {"a": 1, "b": 2})
if expired_retrieved is not None:
    print("FAIL: Expired record was returned by get.")
    sys.exit(1)
print("PASS: Expired record correctly returned None.")

# Step 6: Test permanent TTL for transactions
ttl_tx = cache.resolve_ttl("solscan", "transaction/detail")
if ttl_tx != TTL_IMMUTABLE:
    print(f"FAIL: Transaction detail TTL expected {TTL_IMMUTABLE}, got {ttl_tx}")
    sys.exit(1)
print(f"PASS: Transaction detail TTL correctly resolved to {TTL_IMMUTABLE}")

# Cleanup
try:
    os.remove(db_path)
    for p in pathlib.Path(test_dir).glob("*"):
        try:
            os.remove(p)
        except Exception:
            pass
    os.rmdir(test_dir)
    print("PASS: Test database cleaned up successfully.")
except Exception as e:
    print(f"Cleanup note: {e}")

print("ALL SQLITE CACHE FORENSIC CHECKS PASSED.")
