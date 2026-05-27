"""Retrieval Adapter abstraction.

Goal: decouple Cognitive Layer runtime from the underlying vector DB.

This adapter improves query normalization and deterministic chunk selection:
- query expansion via deterministic clinical ontology
- rerank using heuristic overlap (query tokens + symptom keywords)
- deduplicate near-identical chunks via content hash
- confidence filtering (drops low-quality chunks)

No LLM calls.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple

from scripts.clinical_ontology import expand_query


@dataclass
class RetrievedChunk:
    content: str
    metadata: Dict[str, Any]


class RetrievalAdapter:
    def __init__(
        self,
        vector_store: Any = None,
        *,
        default_k: int = 5,
        min_confidence: float = 0.55,
        rerank_multiplier: int = 3,
    ):
        self.vector_store = vector_store
        self.default_k = default_k
        self.min_confidence = min_confidence
        self.rerank_multiplier = max(1, rerank_multiplier)

    def retrieve_with_metadata(self, query: str, *, k: Optional[int] = None) -> Dict[str, Any]:
        """Deterministic retrieval + confidence metadata.

        Returns:
            {
              "chunks": [...],
              "retrieval_confidence": float,
              "matched_concepts": [...],
              "query_expansion_used": bool
            }
        """
        if self.vector_store is None:
            return {
                "chunks": [],
                "retrieval_confidence": 0.0,
                "matched_concepts": [],
                "query_expansion_used": False,
            }

        kk = k or self.default_k

        # Query expansion (deterministic)
        expanded_query, concepts = expand_query(query)
        norm_query = expanded_query
        query_expansion_used = bool(expanded_query and expanded_query.strip() != (query or "").strip())

        fetch_k = max(kk * self.rerank_multiplier, kk)

        if hasattr(self.vector_store, "similarity_search"):
            docs = self.vector_store.similarity_search(norm_query, k=fetch_k)
            chunks = self._docs_to_chunks(docs)
        elif hasattr(self.vector_store, "search"):
            docs = self.vector_store.search(norm_query, k=fetch_k)
            chunks = self._docs_to_chunks(docs)
        else:
            return {
                "chunks": [],
                "retrieval_confidence": 0.0,
                "matched_concepts": [],
                "query_expansion_used": query_expansion_used,
            }

        # Score all chunks deterministically
        scored: List[Tuple[float, RetrievedChunk]] = []
        for ch in chunks:
            s = self._score_chunk(norm_query, ch)
            scored.append((s, ch))

        # dedupe: keep highest scoring chunk per content hash
        best_by_hash: Dict[str, Tuple[float, RetrievedChunk]] = {}
        for s, ch in scored:
            h = self._hash_chunk(ch.content)
            if h not in best_by_hash or s > best_by_hash[h][0]:
                best_by_hash[h] = (s, ch)

        best_scored = [(s, ch) for (s, ch) in best_by_hash.values()]
        best_scored.sort(key=lambda x: x[0], reverse=True)

        # filter by min_confidence
        filtered: List[Tuple[float, RetrievedChunk]] = [(s, ch) for (s, ch) in best_scored if s >= self.min_confidence]
        if not filtered:
            filtered = best_scored[: self.default_k]

        # take top-k
        top = filtered[:kk]
        top_scores = [s for s, _ch in top]
        mean_score = (sum(top_scores) / len(top_scores)) if top_scores else 0.0
        top_score = top_scores[0] if top_scores else 0.0

        if not top:
            retrieval_confidence = 0.0
        else:
            retrieval_confidence = min(1.0, (top_score * 0.7) + (mean_score * 0.3))

        matched_concepts = [str(c) for c in (concepts or [])]

        return {
            "chunks": [ch for _s, ch in top],
            "retrieval_confidence": float(retrieval_confidence),
            "matched_concepts": matched_concepts,
            "query_expansion_used": bool(query_expansion_used),
        }

    def _hash_chunk(self, content: str) -> str:
        return hashlib.sha256((content or "").encode("utf-8", "ignore")).hexdigest()

    def _normalize_query(self, query: str) -> str:
        expanded_query, _concepts = expand_query(query)
        return expanded_query

    def _docs_to_chunks(self, docs: List[Any]) -> List[RetrievedChunk]:
        out: List[RetrievedChunk] = []
        for d in docs:
            content = getattr(d, "page_content", None) or ""
            meta = getattr(d, "metadata", None) or {}
            out.append(RetrievedChunk(content=str(content), metadata=dict(meta)))
        return out

    def _tokenize(self, text: str) -> List[str]:
        text = (text or "").lower()
        tokens = [t for t in re.split(r"\W+", text) if t and len(t) > 2]
        return tokens[:120]

    def _score_chunk(self, query: str, chunk: RetrievedChunk) -> float:
        q = query or ""
        c = chunk.content or ""

        q_tokens = self._tokenize(q)
        c_l = c.lower()

        # Heuristic keyword sets
        symptom_keywords = [
            "sleep",
            "insomnia",
            "fatigue",
            "depressed",
            "hopeless",
            "worry",
            "panic",
            "loss",
            "interest",
            "anxiety",
            "sad",
            "depression",
            "stress",
            "sadness",
            "hopelessness",
        ]

        token_hits = sum(1 for t in q_tokens if t in c_l)
        symptom_hits = sum(1 for kw in symptom_keywords if kw in c_l)

        # density: how much the query is present
        density = token_hits / max(len(q_tokens), 1)
        symptom_score = min(symptom_hits / 6.0, 1.0)

        score = (0.6 * density) + (0.4 * symptom_score)
        return float(score)

    def _rerank_and_filter(self, query: str, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        # dedupe: keep highest scoring chunk per content hash
        best_by_hash: Dict[str, Tuple[float, RetrievedChunk]] = {}

        for ch in chunks:
            h = self._hash_chunk(ch.content)
            score = self._score_chunk(query, ch)
            if h not in best_by_hash or score > best_by_hash[h][0]:
                best_by_hash[h] = (score, ch)

        scored = [(s, ch) for (_h, (s, ch)) in best_by_hash.items()]
        scored.sort(key=lambda x: x[0], reverse=True)

        filtered: List[RetrievedChunk] = []
        for s, ch in scored:
            if s < self.min_confidence:
                continue
            filtered.append(ch)

        # If everything filtered out, fall back to top-N (avoid empty grounding)
        if not filtered:
            return [ch for _s, ch in scored[: self.default_k]]

        return filtered

    def retrieve(self, query: str, *, k: Optional[int] = None) -> List[RetrievedChunk]:
        meta = self.retrieve_with_metadata(query, k=k)
        return meta.get("chunks", [])[: (k or self.default_k)]


    def retrieve_by_topic(
        self,
        query: str,
        *,
        topic: Optional[str] = None,
        k: Optional[int] = None,
        metadata_key: str = "topics",
    ) -> List[RetrievedChunk]:
        chunks = self.retrieve(query, k=k)
        if not topic:
            return chunks

        topic_n = (topic or "").strip().lower()
        filtered: List[RetrievedChunk] = []
        for c in chunks:
            topics = c.metadata.get(metadata_key, [])
            if isinstance(topics, list):
                topics_norm = {str(t).strip().lower() for t in topics}
                if topic_n in topics_norm:
                    filtered.append(c)
        return filtered if filtered else chunks

    def retrieve_grounding(self, query: str, *, k: Optional[int] = None) -> str:
        chunks = self.retrieve(query, k=k)
        if not chunks:
            return ""

        parts: List[str] = []
        for i, c in enumerate(chunks, 1):
            src = c.metadata.get("source_file") or c.metadata.get("source") or "Unknown"
            parts.append(f"[Chunk {i} | {src}]\n{c.content[:450]}")
        return "\n\n".join(parts)

