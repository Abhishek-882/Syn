"""Independent Forensic Audit of TokenBucketRateLimiter."""

import sys
import time
import threading

sys.path.insert(0, r"C:\Users\Asus\Documents\antigravity\hopeful-curie\src")

from crypto_syndicate.api.rate_limiter import (
    TokenBucketRateLimiter,
    RateLimitTimeoutError,
    get_rate_limiter,
)

print("Starting Rate Limiter forensic tests...")

# Test 1: GMGN 1 RPS limiter
gmgn_limiter = get_rate_limiter("gmgn")
if gmgn_limiter.refill_rate != 1.0 or gmgn_limiter.capacity != 1.0:
    print(f"FAIL: GMGN limiter config incorrect: rate={gmgn_limiter.refill_rate}, cap={gmgn_limiter.capacity}")
    sys.exit(1)
print("PASS: GMGN limiter configured at 1.0 RPS / 1.0 cap.")

# Test 2: Solscan 10 RPS limiter
sol_limiter = get_rate_limiter("solscan")
if sol_limiter.refill_rate != 10.0 or sol_limiter.capacity != 15.0:
    print(f"FAIL: Solscan limiter config incorrect: rate={sol_limiter.refill_rate}, cap={sol_limiter.capacity}")
    sys.exit(1)
print("PASS: Solscan limiter configured at 10.0 RPS / 15.0 cap.")

# Test 3: Burst behavior on Solscan (should consume 15 tokens instantly)
t0 = time.monotonic()
for _ in range(15):
    sol_limiter.acquire(1.0, timeout=1.0)
burst_duration = time.monotonic() - t0
if burst_duration > 0.1:
    print(f"FAIL: Solscan burst of 15 tokens took {burst_duration:.3f}s, expected < 0.1s")
    sys.exit(1)
print(f"PASS: Solscan burst of 15 tokens took {burst_duration:.4f}s (<0.1s)")

# Test 4: Throttling after capacity exhausted (16th token should take ~0.1s)
t1 = time.monotonic()
sol_limiter.acquire(1.0, timeout=1.0)
throttle_duration = time.monotonic() - t1
if throttle_duration < 0.05 or throttle_duration > 0.25:
    print(f"FAIL: Throttled acquire took {throttle_duration:.3f}s, expected ~0.10s")
    sys.exit(1)
print(f"PASS: Solscan throttled acquire took {throttle_duration:.4f}s (~0.10s)")

# Test 5: Timeout enforcement
strict_limiter = TokenBucketRateLimiter(refill_rate=0.01, capacity=1.0)
strict_limiter.acquire(1.0) # exhaust
try:
    strict_limiter.acquire(1.0, timeout=0.05)
    print("FAIL: Expected RateLimitTimeoutError not raised.")
    sys.exit(1)
except RateLimitTimeoutError:
    print("PASS: RateLimitTimeoutError correctly raised upon timeout.")

print("ALL RATE LIMITER FORENSIC CHECKS PASSED.")
