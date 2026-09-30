"""Persistent Wallet Vector Store & Semantic Memory powered by Qdrant.

Integrates with sentence-transformers ('all-mpnet-base-v2', 768 dimensions)
to embed structured behavioral fingerprints from SyndicateBehavior into high-dimensional
vector space, enabling cross-token, cross-chain, and cross-session syndicate re-identification.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Union

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse
from sentence_transformers import SentenceTransformer

from crypto_syndicate.fingerprint import SyndicateBehavior

logger = logging.getLogger("crypto_syndicate.vector_store")


class WalletVectorStore:
    """Production vector database store for on-chain wallet fingerprints."""

    COLLECTION_NAME: str = "wallet_fingerprints"
    DEFAULT_MODEL: str = "all-mpnet-base-v2"

    def __init__(
        self,
        url: Optional[str] = "http://localhost:6333",
        path: Optional[str] = None,
        model_name: Optional[str] = None,
        force_memory: bool = False,
    ) -> None:
        """Initialize the Qdrant client and SentenceTransformer encoder.

        Args:
            url: Qdrant REST/gRPC server URL (e.g. 'http://localhost:6333').
            path: Local storage path for embedded on-disk Qdrant database.
            model_name: SentenceTransformer model name (defaults to 'all-mpnet-base-v2').
            force_memory: If True, uses in-memory Qdrant instance for ultra-fast ephemeral execution.
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.url = url
        self.path = path
        self.force_memory = force_memory

        self.client = self._init_client()
        self.encoder = SentenceTransformer(self.model_name)
        if hasattr(self.encoder, "get_embedding_dimension"):
            self.vector_dim = self.encoder.get_embedding_dimension()
        else:
            self.vector_dim = self.encoder.get_sentence_embedding_dimension()

        self._ensure_collection()
        logger.info(
            "WalletVectorStore initialized (collection=%s, dim=%d, model=%s)",
            self.COLLECTION_NAME,
            self.vector_dim,
            self.model_name,
        )

    def _init_client(self) -> QdrantClient:
        """Initialize Qdrant client with automatic connectivity fallback."""
        if self.force_memory:
            logger.info("Initializing in-memory QdrantClient(':memory:')")
            return QdrantClient(":memory:")

        if self.path:
            os.makedirs(self.path, exist_ok=True)
            logger.info("Initializing local embedded QdrantClient(path='%s')", self.path)
            return QdrantClient(path=self.path)

        if self.url:
            try:
                # Test connectivity to external Qdrant server with short timeout
                client = QdrantClient(url=self.url, timeout=2.0)
                client.get_collections()
                logger.info("Connected to remote Qdrant server at %s", self.url)
                return client
            except Exception as exc:
                fallback_path = os.path.join("results", "qdrant_storage")
                os.makedirs(fallback_path, exist_ok=True)
                logger.warning(
                    "Remote Qdrant server at %s unreachable (%s). Falling back to embedded on-disk storage at '%s'",
                    self.url,
                    exc,
                    fallback_path,
                )
                return QdrantClient(path=fallback_path)

        return QdrantClient(":memory:")

    def _ensure_collection(self) -> None:
        """Ensure that the vector collection exists with cosine distance metric."""
        try:
            collections_resp = self.client.get_collections()
            existing = [c.name for c in collections_resp.collections]
            if self.COLLECTION_NAME not in existing:
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_dim,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
                logger.info("Created Qdrant collection '%s'", self.COLLECTION_NAME)
        except Exception as exc:
            logger.error("Failed to ensure collection '%s': %s", self.COLLECTION_NAME, exc)
            raise

    def _address_to_id(self, address: str) -> str:
        """Convert a wallet address deterministically into a UUID string for Qdrant point IDs."""
        return str(uuid.uuid5(uuid.NAMESPACE_URL, address.lower().strip()))

    def _behavior_to_text(self, behavior: Union[SyndicateBehavior, Dict[str, Any]]) -> str:
        """Format behavioral record into high-density semantic text for embedding."""
        if isinstance(behavior, SyndicateBehavior):
            return behavior.to_text(include_jito=True)
        if isinstance(behavior, dict):
            # Dict fallback
            chain = behavior.get("chain", "sol")
            bundler = behavior.get("bundler_rate", 0.0)
            delay = behavior.get("avg_buy_delay_s", 0.0)
            hold = behavior.get("avg_hold_duration_s", 0.0)
            patterns = "|".join(sorted(behavior.get("patterns_flagged", [])))
            jito = behavior.get("is_jito_bundle", False)
            jito_conf = behavior.get("jito_confidence", 0.0)
            return (
                f"chain:{chain} bundler_rate:{bundler:.4f} buy_delay:{delay:.1f}s "
                f"hold_time:{hold:.1f}s jito_bundle:{jito} jito_conf:{jito_conf:.2f} "
                f"patterns:{patterns or 'none'}"
            )
        return str(behavior)

    def _build_payload(
        self,
        wallet_address: str,
        behavior: Union[SyndicateBehavior, Dict[str, Any]],
        cluster_id: Optional[str] = None,
        chain: str = "sol",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Construct the metadata payload stored alongside the vector point."""
        meta = metadata or {}
        if isinstance(behavior, SyndicateBehavior):
            b_dict = behavior.to_dict()
        elif isinstance(behavior, dict):
            b_dict = behavior
        else:
            b_dict = {}

        payload = {
            "address": wallet_address,
            "syndicate_id": cluster_id or b_dict.get("syndicate_id") or "UNKNOWN",
            "chain": chain or b_dict.get("chain", "sol"),
            "bundler_rate": float(b_dict.get("bundler_rate", 0.0)),
            "avg_buy_delay_s": float(b_dict.get("avg_buy_delay_s", 0.0)),
            "avg_hold_duration_s": float(b_dict.get("avg_hold_duration_s", 0.0)),
            "sniper_count": int(b_dict.get("sniper_count", 0)),
            "is_jito_bundle": bool(b_dict.get("is_jito_bundle", False)),
            "jito_confidence": float(b_dict.get("jito_confidence", 0.0)),
            "jito_signals": list(b_dict.get("jito_signals", [])),
            "patterns_flagged": list(b_dict.get("patterns_flagged", [])),
            "behavior_text": self._behavior_to_text(behavior),
            "timestamp": int(time.time()),
        }
        payload.update(meta)
        return payload

    def upsert_wallet(
        self,
        wallet_address: str,
        behavior: Union[SyndicateBehavior, Dict[str, Any]],
        cluster_id: Optional[str] = None,
        chain: str = "sol",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Embed and upsert a single wallet fingerprint.

        Returns:
            The point UUID string.
        """
        text = self._behavior_to_text(behavior)
        vector = self.encoder.encode(text).tolist()
        point_id = self._address_to_id(wallet_address)
        payload = self._build_payload(wallet_address, behavior, cluster_id, chain, metadata)

        point = qmodels.PointStruct(
            id=point_id,
            vector=vector,
            payload=payload,
        )
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[point],
        )
        logger.debug("Upserted wallet %s (point_id=%s)", wallet_address, point_id)
        return point_id

    def upsert_batch(
        self,
        wallets: List[Dict[str, Any]],
        chain: str = "sol",
    ) -> int:
        """Batch encode and upsert multiple wallets for high-throughput ingress.

        Args:
            wallets: List of dicts, each containing:
                     {'address': str, 'behavior': SyndicateBehavior | dict,
                      optional 'cluster_id': str, optional 'metadata': dict}

        Returns:
            Count of upserted points.
        """
        if not wallets:
            return 0

        texts = [self._behavior_to_text(w["behavior"]) for w in wallets]
        vectors = self.encoder.encode(texts, batch_size=32).tolist()

        points = []
        for w, v in zip(wallets, vectors):
            addr = w["address"]
            point_id = self._address_to_id(addr)
            payload = self._build_payload(
                wallet_address=addr,
                behavior=w["behavior"],
                cluster_id=w.get("cluster_id"),
                chain=w.get("chain", chain),
                metadata=w.get("metadata"),
            )
            points.append(qmodels.PointStruct(id=point_id, vector=v, payload=payload))

        self.client.upsert(collection_name=self.COLLECTION_NAME, points=points)
        logger.info("Batch upserted %d wallet vectors to Qdrant", len(points))
        return len(points)

    def find_similar(
        self,
        behavior: Union[SyndicateBehavior, Dict[str, Any]],
        top_k: int = 5,
        score_threshold: float = 0.0,
        exclude_addresses: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Find behaviorally similar wallets using vector cosine similarity.

        Args:
            behavior: Target behavior to query against.
            top_k: Maximum number of matches to return.
            score_threshold: Minimum similarity score [0.0, 1.0].
            exclude_addresses: Addresses to omit from results.

        Returns:
            List of matching records with similarity score and metadata.
        """
        text = self._behavior_to_text(behavior)
        vector = self.encoder.encode(text).tolist()

        exclude = set(a.lower() for a in (exclude_addresses or []))

        # Query Qdrant
        limit = top_k + len(exclude)
        try:
            # Query Qdrant via modern query_points API or search fallback
            if hasattr(self.client, "query_points"):
                results = self.client.query_points(
                    collection_name=self.COLLECTION_NAME,
                    query=vector,
                    limit=limit,
                    score_threshold=score_threshold,
                ).points
            else:
                results = self.client.search(
                    collection_name=self.COLLECTION_NAME,
                    query_vector=vector,
                    limit=limit,
                    score_threshold=score_threshold,
                )
        except Exception as exc:
            logger.error("Similarity search failed: %s", exc)
            return []

        matches = []
        for r in results:
            payload = getattr(r, "payload", {}) or {}
            addr = payload.get("address", "")
            if addr.lower() in exclude:
                continue

            score = getattr(r, "score", 0.0)
            matches.append({
                "address": addr,
                "similarity": round(float(score), 4),
                "similarity_pct": f"{max(0.0, min(100.0, float(score) * 100)):.1f}%",
                "syndicate_id": payload.get("syndicate_id", "UNKNOWN"),
                "chain": payload.get("chain", "sol"),
                "bundler_rate": payload.get("bundler_rate", 0.0),
                "avg_buy_delay_s": payload.get("avg_buy_delay_s", 0.0),
                "avg_hold_duration_s": payload.get("avg_hold_duration_s", 0.0),
                "is_jito_bundle": payload.get("is_jito_bundle", False),
                "jito_confidence": payload.get("jito_confidence", 0.0),
                "patterns_flagged": payload.get("patterns_flagged", []),
            })
            if len(matches) >= top_k:
                break

        return matches

    def find_similar_by_address(
        self,
        wallet_address: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Retrieve stored vector for a wallet and query for nearest neighbors."""
        point_id = self._address_to_id(wallet_address)
        try:
            points = self.client.retrieve(
                collection_name=self.COLLECTION_NAME,
                ids=[point_id],
                with_vectors=True,
            )
            if not points or not points[0].vector:
                logger.warning("Wallet %s not found in vector store", wallet_address)
                return []

            vector = points[0].vector
            limit = top_k + 1
            if hasattr(self.client, "query_points"):
                results = self.client.query_points(
                    collection_name=self.COLLECTION_NAME,
                    query=vector,
                    limit=limit,
                    score_threshold=score_threshold,
                ).points
            else:
                results = self.client.search(
                    collection_name=self.COLLECTION_NAME,
                    query_vector=vector,
                    limit=limit,
                    score_threshold=score_threshold,
                )

            matches = []
            for r in results:
                payload = getattr(r, "payload", {}) or {}
                addr = payload.get("address", "")
                if addr.lower() == wallet_address.lower():
                    continue

                score = getattr(r, "score", 0.0)
                matches.append({
                    "address": addr,
                    "similarity": round(float(score), 4),
                    "similarity_pct": f"{max(0.0, min(100.0, float(score) * 100)):.1f}%",
                    "syndicate_id": payload.get("syndicate_id", "UNKNOWN"),
                    "chain": payload.get("chain", "sol"),
                    "bundler_rate": payload.get("bundler_rate", 0.0),
                    "avg_buy_delay_s": payload.get("avg_buy_delay_s", 0.0),
                    "avg_hold_duration_s": payload.get("avg_hold_duration_s", 0.0),
                    "is_jito_bundle": payload.get("is_jito_bundle", False),
                    "jito_confidence": payload.get("jito_confidence", 0.0),
                    "patterns_flagged": payload.get("patterns_flagged", []),
                })
                if len(matches) >= top_k:
                    break
            return matches

        except Exception as exc:
            logger.error("find_similar_by_address failed: %s", exc)
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """Return collection metrics (total points, indexed vectors, status)."""
        try:
            info = self.client.get_collection(collection_name=self.COLLECTION_NAME)
            return {
                "collection_name": self.COLLECTION_NAME,
                "total_points": info.points_count or 0,
                "indexed_vectors_count": getattr(info, "indexed_vectors_count", 0),
                "status": str(info.status),
                "vector_dim": self.vector_dim,
            }
        except Exception as exc:
            logger.error("get_collection_stats failed: %s", exc)
            return {"total_points": 0, "status": "error", "error": str(exc)}

    def delete_wallet(self, wallet_address: str) -> bool:
        """Delete a wallet from vector index."""
        point_id = self._address_to_id(wallet_address)
        try:
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=qmodels.PointIdsList(points=[point_id]),
            )
            return True
        except Exception as exc:
            logger.error("delete_wallet failed: %s", exc)
            return False

    def clear_collection(self) -> None:
        """Clear and re-initialize collection."""
        try:
            self.client.delete_collection(collection_name=self.COLLECTION_NAME)
            self._ensure_collection()
            logger.info("Collection '%s' cleared and recreated", self.COLLECTION_NAME)
        except Exception as exc:
            logger.error("clear_collection failed: %s", exc)
            raise
