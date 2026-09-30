# DISPATCH - Explorer 2 (fingerprint.py & identity.py)

## 2026-09-20T16:21:14Z

## Working Directory
`C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m7_m9_explorer_2`

## Objectives
1. Inspect `src/crypto_syndicate/api/models.py` and `src/crypto_syndicate/discovery.py`:
   - Study existing dataclasses: `SyndicateCluster`, `TokenLaunchEvent`, `TradeRecord`, `WalletScore`, `PatternType`.
2. Design `src/crypto_syndicate/fingerprint.py`:
   - `SyndicateBehavior` dataclass:
     * attributes capturing behavioral profile: cluster_id, token_address, chain, avg_buy_delay_s, avg_hold_duration_s, dump_speed_s, bundler_rate, bot_rate, suspicion_score, patterns_flagged, wallet_count, estimated_profit_usd, etc.
     * `to_text() -> str` method returning concise semantic string representation (useful for sentence transformers / vector embedding or display).
     * `from_cluster_and_token(cls, cluster: Any, token: Any, trades: Any = None) -> SyndicateBehavior` classmethod extracting metrics accurately from a SyndicateCluster and TokenLaunchEvent (and optional trades / evidence metadata).
3. Design `src/crypto_syndicate/identity.py`:
   - `SyndicateIdentity` dataclass:
     * identity_id, alias/label, primary_wallets: list[str], historical_tokens: list[str], behavior_profile: Optional[SyndicateBehavior], confidence_score: float, first_seen: float, last_seen: float, metadata: dict
   - `SyndicateIdentityEngine` class:
     * memory / registry of known identities
     * `register_cluster(cluster, token, trades=None) -> SyndicateIdentity`
     * `match_syndicate(cluster) -> Optional[SyndicateIdentity]` (or list of matches with similarity)
     * `get_all_identities() -> list[SyndicateIdentity]`
4. Write your report to `.agents/m7_m9_explorer_2/report.md` and `handoff.md`.
