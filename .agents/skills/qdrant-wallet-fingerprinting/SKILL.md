---
name: qdrant-wallet-fingerprinting
description: >-
  Adds Qdrant vector database to the crypto syndicate system for persistent
  wallet fingerprinting, semantic similarity search, and cross-session
  syndicate memory. Activate when the user asks to "remember syndicates",
  "find similar wallets", "add vector search", or "M7".
---

# Qdrant Wallet Fingerprinting — Integration Guide

## What This Adds

Current system detects wallets sharing the SAME token at the SAME time.
Qdrant adds: find wallets with SIMILAR BEHAVIOR across different tokens,
chains, and time periods. Syndicates cannot evade detection by switching tokens.

## GitHub
https://github.com/qdrant/qdrant -- 34.6K stars

## Project Location
C:\Users\Asus\Documents\antigravity\hopeful-curie

## Install
```powershell
pip install qdrant-client sentence-transformers
docker run -p 6333:6333 qdrant/qdrant
```

## New File to Create
src/crypto_syndicate/vector_store.py

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

class WalletVectorStore:
    COLLECTION = "wallet_fingerprints"
    VECTOR_DIM = 384

    def __init__(self, url="http://localhost:6333"):
        self.client = QdrantClient(url=url)
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self._ensure_collection()

    def _wallet_to_text(self, wallet):
        patterns = "|".join(sorted(wallet.get("patterns_flagged", [])))
        return (f"chain:{wallet.get('chain','sol')} "
                f"score:{wallet.get('suspicion_score',0):.0f} "
                f"patterns:{patterns or 'none'} "
                f"tokens_traded:{len(wallet.get('tokens_traded',[]))}")

    def upsert(self, wallets):
        texts = [self._wallet_to_text(w) for w in wallets]
        vectors = self.encoder.encode(texts).tolist()
        points = [PointStruct(
            id=abs(hash(w["wallet_address"])) % (2**63),
            vector=v,
            payload={"address": w["wallet_address"],
                     "score": w.get("suspicion_score", 0),
                     "patterns": list(w.get("patterns_flagged", []))}
        ) for w, v in zip(wallets, vectors)]
        self.client.upsert(collection_name=self.COLLECTION, points=points)
        return len(points)

    def find_similar(self, wallet, top_k=10):
        vector = self.encoder.encode([self._wallet_to_text(wallet)])[0].tolist()
        results = self.client.search(collection_name=self.COLLECTION,
                                     query_vector=vector, limit=top_k)
        return [{"address": r.payload["address"],
                 "similarity": r.score,
                 "patterns": r.payload["patterns"]} for r in results]
```

## CLI Flags to Add to run_analysis.py
--vector-store    Upsert discovered wallets into Qdrant after analysis
--find-similar    Find wallets behaviorally similar to a given address

## Use Cases
- Find wallets like a known bad actor (semantic, not exact match)
- Detect same syndicate using different tokens months later
- Cross-chain matching: ETH wallet behaving like a known SOL syndicate
- Permanent memory across sessions (unlike seen_clusters.json)

## References
- Qdrant docs: https://qdrant.tech/documentation/
- agent-skills repo (frontend skills reference): https://github.com/addyosmani/agent-skills