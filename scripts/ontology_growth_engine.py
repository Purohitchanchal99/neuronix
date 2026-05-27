"""Ontology growth engine (first learning component)

Transforms stored unknown user phrases into *reviewable* ontology expansion suggestions.

Pipeline:
  unknown_terms.json
    -> load last N events
    -> semantic clustering
    -> nearest ontology anchors
    -> candidate aliases / concepts
    -> review queue (NO auto-mutation by default)

Design goals:
- Deterministic / LLM-free (no OpenAI/Gemini usage)
- Avoid concept drift early: only generate suggestions from repeated clusters
- Safe-by-default: writes to review queue; does not modify clinical_ontology seeds

"""

from __future__ import annotations

import argparse
import json
import math
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Ensure repo root is on sys.path so `scripts.*` imports work when executed as:
#   python scripts/ontology_growth_engine.py
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.unknown_terms_store import UnknownTermsStore

# We use canonical ontology concepts only as *anchors*.
from scripts.clinical_ontology import CANONICAL_CONCEPTS



DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REVIEW_QUEUE_PATH = DATA_DIR / "ontology_review_queue.json"
SUGGESTIONS_PATH = DATA_DIR / "ontology_growth_suggestions.json"


def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[\u2019']", "'", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _snake_case(text: str) -> str:
    t = _normalize(text)
    t = t.replace("/", " ")
    t = re.sub(r"[^a-z0-9\s]+", " ", t)
    t = re.sub(r"\s+", "_", t).strip("_")
    return t or "concept"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")



@dataclass
class UnknownPhrase:
    query: str
    normalized: str
    score: float
    timestamp: float


@dataclass
class ClusterSuggestion:
    cluster: List[str]
    cluster_size: int
    nearest_existing: str
    confidence: float
    suggested_concept: str
    suggested_aliases: List[str]
    evidence_phrases: List[str]
    rationale: str


def _last_n_events(n: int) -> List[Dict[str, Any]]:
    store = UnknownTermsStore()
    # UnknownTermsStore doesn't expose raw events; we re-load from the json path deterministically.
    # This keeps the engine independent from internal store changes.
    if not store.path.exists():
        return []
    rows = _load_json(store.path, [])
    if not isinstance(rows, list):
        return []
    return rows[-n:]


def _extract_phrases(rows: Sequence[Dict[str, Any]]) -> List[UnknownPhrase]:
    out: List[UnknownPhrase] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        q = r.get("query") or ""
        norm = r.get("normalized") or _normalize(q)
        if not q or not norm:
            continue
        out.append(
            UnknownPhrase(
                query=str(q),
                normalized=str(norm),
                score=float(r.get("score", 0.0) or 0.0),
                timestamp=float(r.get("timestamp", time.time()) or time.time()),
            )
        )
    return out


# ------------------------------
# Embedding-based clustering
# ------------------------------


def _try_embed(texts: List[str], model_name: str) -> Optional[Any]:
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        model = SentenceTransformer(model_name)
        emb = model.encode(texts, normalize_embeddings=True)
        emb_arr = emb if hasattr(emb, "shape") else np.array(emb)
        return emb_arr
    except Exception:
        return None


def _cosine_sim(a: List[float], b: List[float]) -> float:
    # expects vectors already L2-normalized ideally.
    num = 0.0
    da = 0.0
    db = 0.0
    for i in range(min(len(a), len(b))):
        num += float(a[i]) * float(b[i])
        da += float(a[i]) * float(a[i])
        db += float(b[i]) * float(b[i])
    if da <= 0 or db <= 0:
        return 0.0
    return num / math.sqrt(da * db)


def _cluster_by_threshold(
    phrases: List[UnknownPhrase],
    *,
    embed_vectors: Any,
    similarity_threshold: float,
) -> List[List[int]]:
    """Simple deterministic agglomeration.

    Creates clusters by picking an unassigned point and grouping all points
    above threshold relative to that seed.
    """

    # embed_vectors: numpy array [N, D]
    try:
        import numpy as np
    except Exception:
        return []

    arr = embed_vectors
    if getattr(arr, "shape", None) is None:
        return []

    n = int(arr.shape[0])
    if n <= 0:
        return []

    unassigned = set(range(n))
    clusters: List[List[int]] = []

    while unassigned:
        seed = min(unassigned)
        unassigned.remove(seed)

        seed_vec = arr[seed]

        cluster = [seed]
        # compare seed to others (deterministic)
        for i in sorted(list(unassigned)):
            # cosine sim
            s = float(seed_vec @ arr[i].T)
            if s >= similarity_threshold:
                cluster.append(i)

        # remove clustered indices
        for i in cluster[1:]:
            if i in unassigned:
                unassigned.remove(i)

        clusters.append(cluster)

    # deterministic ordering: largest first
    clusters.sort(key=lambda c: (-len(c), min(c) if c else 0))
    return clusters


def _fallback_cluster_by_tokens(phrases: List[UnknownPhrase], *, min_cluster_size: int) -> List[List[int]]:
    """Heuristic fallback when embeddings are unavailable.

    Clusters by Jaccard similarity over token sets.

    Note: we still return clusters even if size < min_cluster_size; the caller enforces
    MIN_CLUSTER_SIZE via `_suggest_from_cluster()`.
    """


    def tokens(s: str) -> set[str]:
        s = _normalize(s)
        return {t for t in re.split(r"\W+", s) if t and len(t) >= 3}

    tsets = [tokens(p.normalized) for p in phrases]
    n = len(phrases)
    unassigned = set(range(n))
    clusters: List[List[int]] = []

    while unassigned:
        seed = min(unassigned)
        unassigned.remove(seed)
        seed_t = tsets[seed]
        cluster = [seed]
        for i in sorted(list(unassigned)):
            a = seed_t
            b = tsets[i]
            if not a or not b:
                continue
            inter = len(a & b)
            union = len(a | b)
            jac = inter / max(1, union)
            if jac >= 0.35:
                cluster.append(i)

        for i in cluster[1:]:
            unassigned.discard(i)

        if len(cluster) >= 1:
            clusters.append(cluster)

    clusters.sort(key=lambda c: (-len(c), min(c) if c else 0))
    # keep even small for later filtering; caller will enforce MIN_CLUSTER_SIZE
    return clusters


# ------------------------------
# Nearest ontology anchors
# ------------------------------


def _nearest_anchor(
    phrase: str,
    *,
    anchor_concepts: List[str],
    anchor_vectors: Optional[Any],
    phrase_vector: Optional[Any],
    semantic_threshold: float,
) -> Tuple[str, float]:
    """Return (nearest_existing_concept, confidence)."""

    if anchor_vectors is None or phrase_vector is None:
        # fallback: token overlap with concept strings
        p = set(re.split(r"\W+", _normalize(phrase)))
        p = {t for t in p if len(t) >= 3}
        best_c = anchor_concepts[0] if anchor_concepts else ""
        best_s = 0.0
        for c in anchor_concepts:
            cset = {t for t in re.split(r"\W+", _normalize(c)) if len(t) >= 3}
            if not cset:
                continue
            inter = len(p & cset)
            union = len(p | cset)
            s = inter / max(1, union)
            if s > best_s:
                best_s = s
                best_c = c
        # map to [0,1]
        conf = float(min(1.0, best_s * 1.7))
        return best_c, conf

    # embedding case: cosine sim via dot (normalized)
    sims = (phrase_vector @ anchor_vectors.T).tolist()[0]
    best_i = max(range(len(sims)), key=lambda i: sims[i])
    best_concept = anchor_concepts[best_i]
    score = float(sims[best_i])
    # confidence calibration: clamp + slight shaping
    conf = float(max(0.0, min(1.0, (score - semantic_threshold) / (1.0 - semantic_threshold) if score >= semantic_threshold else score)))
    return best_concept, conf


def _suggest_from_cluster(
    cluster_phrases: List[str],
    *,
    min_cluster_size: int,
    anchor_concepts: List[str],
    anchor_vectors: Optional[Any],
    embed_model_name: str,
    semantic_threshold: float,
) -> Optional[ClusterSuggestion]:
    if len(cluster_phrases) < min_cluster_size:
        return None

    # Pick representative phrase: longest normalized
    rep = max(cluster_phrases, key=lambda s: len(_normalize(s)))

    # try to embed rep and compute nearest anchor
    phrase_vec = None
    try:
        phrase_vec = _try_embed([rep], embed_model_name)
    except Exception:
        phrase_vec = None

    nearest, conf = _nearest_anchor(
        rep,
        anchor_concepts=anchor_concepts,
        anchor_vectors=anchor_vectors,
        phrase_vector=phrase_vec,
        semantic_threshold=semantic_threshold,
    )

    # Suggested alias strategy: propose the cluster representative as alias for nearest anchor
    aliases = []
    seen = set()
    for p in sorted(cluster_phrases, key=lambda s: (-len(_normalize(s)), s)):
        np = _normalize(p)
        if np in seen:
            continue
        seen.add(np)
        aliases.append(p.strip())
        if len(aliases) >= 5:
            break

    # Candidate concept id (only as a label). We DO NOT mutate the ontology.
    suggested_concept = _snake_case(nearest)

    rationale = (
        f"Cluster size={len(cluster_phrases)}; representative='{rep}'. "
        f"Nearest anchor='{nearest}' with confidence={conf:.2f}."
    )

    return ClusterSuggestion(
        cluster=cluster_phrases,
        cluster_size=len(cluster_phrases),
        nearest_existing=nearest,
        confidence=conf,
        suggested_concept=suggested_concept,
        suggested_aliases=aliases,
        evidence_phrases=aliases[:3],
        rationale=rationale,
    )


# ------------------------------
# Review queue / output
# ------------------------------


def _compute_review_id(s: ClusterSuggestion) -> str:
    # deterministic hash from nearest + evidence
    payload = {
        "nearest": s.nearest_existing,
        "evidence": s.evidence_phrases,
        "cluster_size": s.cluster_size,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    import hashlib

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _append_to_queue(queue: List[Dict[str, Any]], item: Dict[str, Any], *, dedupe_key: str) -> List[Dict[str, Any]]:
    existing_keys = {q.get(dedupe_key) for q in queue}
    if item.get(dedupe_key) in existing_keys:
        return queue
    queue.append(item)
    return queue


def run_once(
    *,
    last_n: int = 500,
    min_cluster_size: int = 3,
    # Hard gate: clusters with support_count below this MUST NOT be promoted.
    min_support_count: int = 5,

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",

    cluster_similarity_threshold: float = 0.55,
    anchor_semantic_threshold: float = 0.62,
    max_review_items: int = 50,
) -> Dict[str, Any]:
    rows = _last_n_events(last_n)
    phrases = _extract_phrases(rows)

    if not phrases:
        out = {
            "status": "no_unknown_terms",
            "loaded_events": 0,
            "clusters": 0,
            "review_items_written": 0,
        }
        return out

    # Embed unknown phrases for clustering
    unknown_texts = [p.normalized for p in phrases]
    unknown_vectors = _try_embed(unknown_texts, embedding_model)

    clusters: List[List[int]]
    if unknown_vectors is not None:
        clusters = _cluster_by_threshold(
            phrases,
            embed_vectors=unknown_vectors,
            similarity_threshold=cluster_similarity_threshold,
        )
    else:
        clusters = _fallback_cluster_by_tokens(phrases, min_cluster_size=min_cluster_size)

    anchor_concepts = sorted(list(CANONICAL_CONCEPTS))

    # embed anchors too (optional)
    anchor_vectors = None
    try:
        anchor_vectors = _try_embed(anchor_concepts, embedding_model)
    except Exception:
        anchor_vectors = None

    suggestions: List[ClusterSuggestion] = []
    # Ontology quality gating signals (saved into review queue for human QC).
    # support_count is interpreted as cluster_size here.
    for cluster_indices in clusters:
        cluster_phrases = [phrases[i].query for i in cluster_indices]
        # enforce minimum
        sug = _suggest_from_cluster(
            cluster_phrases,
            min_cluster_size=min_cluster_size,
            anchor_concepts=anchor_concepts,
            anchor_vectors=anchor_vectors,
            embed_model_name=embedding_model,
            semantic_threshold=anchor_semantic_threshold,
        )
        if sug is None:
            continue

        # HARD REQUIREMENT: never promote clusters with insufficient support.
        # Only write review items when support_count >= min_support_count.
        support_count = int(sug.cluster_size)
        if support_count < int(min_support_count):
            continue

        # confidence signals
        avg_retrieval_confidence = float(sug.confidence)
        # Grounding is a placeholder in this deterministic engine; treat nearest-anchor confidence as grounding too.
        avg_grounding_confidence = float(sug.confidence)

        # Attach gating + signal fields (review queue critical later).
        sug_dict = sug.__dict__.copy()
        sug_dict["support_count"] = support_count
        sug_dict["avg_retrieval_confidence"] = avg_retrieval_confidence
        sug_dict["avg_grounding_confidence"] = avg_grounding_confidence

        suggestions.append(sug)
        if len(suggestions) >= max_review_items:
            break


    # Write suggestions file (for debugging / visibility)
    suggestions_payload = [
        {
            "cluster": s.cluster,
            "cluster_size": s.cluster_size,
            "nearest_existing": s.nearest_existing,
            "suggested_concept": s.suggested_concept,
            "suggested_aliases": s.suggested_aliases,
            "confidence": s.confidence,
            "evidence_phrases": s.evidence_phrases,
            "rationale": s.rationale,
            "generated_at": time.time(),
        }
        for s in suggestions
    ]
    _save_json(SUGGESTIONS_PATH, {
        "generated_at": time.time(),
        "last_n": last_n,
        "min_cluster_size": min_cluster_size,
        "embedding_model": embedding_model,
        "cluster_similarity_threshold": cluster_similarity_threshold,
        "anchor_semantic_threshold": anchor_semantic_threshold,
        "suggestions": suggestions_payload,
    })

    # Review queue (safe-by-default)
    queue = _load_json(REVIEW_QUEUE_PATH, default=[])
    if not isinstance(queue, list):
        queue = []

    written = 0
    for s in suggestions:
        review_id = _compute_review_id(s)
        support_count = int(getattr(s, "cluster_size", 0) or 0)
        avg_retrieval_confidence = float(getattr(s, "confidence", 0.0) or 0.0)
        avg_grounding_confidence = float(getattr(s, "confidence", 0.0) or 0.0)

        item = {
            "review_id": review_id,
            "status": "pending",
            "created_at": time.time(),
            "cluster": s.cluster,
            "nearest_existing": s.nearest_existing,
            "confidence": s.confidence,
            "support_count": support_count,
            "avg_retrieval_confidence": avg_retrieval_confidence,
            "avg_grounding_confidence": avg_grounding_confidence,
            "ontology_anchor_confidence": avg_grounding_confidence,
            "suggested_concept": s.suggested_concept,
            "suggested_aliases": s.suggested_aliases,
            "cluster_size": s.cluster_size,
            "min_cluster_size": min_cluster_size,
            "min_support_count": int(min_support_count),
            "evidence_phrases": s.evidence_phrases,
            "rationale": s.rationale,
        }

        new_queue = _append_to_queue(queue, item, dedupe_key="review_id")
        if len(new_queue) != len(queue):
            written += 1
        queue = new_queue

    _save_json(REVIEW_QUEUE_PATH, queue)

    return {
        "status": "ok",

        "loaded_events": len(rows),
        "phrases_used": len(phrases),
        "clusters": len(clusters),
        "suggestions_generated": len(suggestions),
        "review_items_written": written,
        "review_queue_path": str(REVIEW_QUEUE_PATH),
        "suggestions_path": str(SUGGESTIONS_PATH),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-once", action="store_true", help="Run ontology growth once")
    ap.add_argument("--last-n", type=int, default=500)
    ap.add_argument("--min-cluster-size", type=int, default=3)
    ap.add_argument("--cluster-sim-threshold", type=float, default=0.55)
    ap.add_argument("--embedding-model", type=str, default="sentence-transformers/all-MiniLM-L6-v2")
    args = ap.parse_args()

    if args.run_once:
        res = run_once(
            last_n=args.last_n,
            min_cluster_size=args.min_cluster_size,
            cluster_similarity_threshold=args.cluster_sim_threshold,
            embedding_model=args.embedding_model,
        )
        print(json.dumps(res, indent=2))
    else:
        print("Use --run-once to execute." )


if __name__ == "__main__":
    main()

