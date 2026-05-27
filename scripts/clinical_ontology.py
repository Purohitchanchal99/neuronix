"""Clinical ontology.

Deterministic base ontology + (optional) embedding-based semantic expansion.

Seed mappings cover common Hindi/Hinglish/typos.
If sentence-transformers embeddings are available and enabled, unknown phrases can
be mapped to the nearest ontology concepts via cosine similarity.

No LLM calls.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


# -------------------------------
# Seed ontology concepts
# -------------------------------

CANONICAL_CONCEPTS = {
    "depression",
    "major depressive disorder",
    "anxiety",
    "panic attack",
    "insomnia",
    "stress",
    "hopelessness",
    "sad mood",
    "low mood",
    "suicidal ideation",
    "self-harm",
    "fatigue",
    "sleep disturbance",
    "loss of interest",
    "depressed mood",
    "anhedonia",
    "rumination",
    "cognitive fatigue",
}


# -------------------------------
# Seed term map: user phrase -> expansions
# -------------------------------

TERM_MAP: Dict[str, List[str]] = {
    # Depression
    "depression": ["major depressive disorder", "depressed mood", "low mood", "hopelessness"],
    "dipression": ["major depressive disorder", "depressed mood", "low mood", "hopelessness"],
    "sad": ["sad mood", "low mood"],
    "low mood": ["low mood"],
    "hopeless": ["hopelessness"],
    "hopelessness": ["hopelessness"],

    # Anxiety / stress
    "anxiety": ["anxiety", "excess worry", "stress"],
    "axienty": ["anxiety", "excess worry", "stress"],
    "anxious": ["anxiety", "stress"],
    "worried": ["anxiety", "stress"],
    "tension": ["stress", "anxiety"],
    "stress": ["stress", "anxiety"],
    "panic": ["panic attack", "anxiety"],
    "panic attack": ["panic attack", "anxiety"],

    # Insomnia
    "insomnia": ["insomnia", "sleep disturbance"],
    "neend nahi aa rahi": ["insomnia", "sleep disturbance"],
    "neend nhi aa rahi": ["insomnia", "sleep disturbance"],
    "neend nahi aati": ["insomnia", "sleep disturbance"],
    "sleep issue": ["insomnia", "sleep disturbance"],
    "sleep disturbance": ["sleep disturbance", "insomnia"],

    # Crisis keywords
    "suicidal": ["suicidal ideation"],
    "suicidal ideation": ["suicidal ideation"],
    "self-harm": ["self-harm"],
    "self harm": ["self-harm"],
    "harm": ["self-harm"],
}


# -------------------------------
# Embedding-based expansion (optional)
# -------------------------------

@dataclass
class EmbeddingExpansionConfig:
    enabled: bool = True
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    semantic_threshold: float = 0.62
    top_k: int = 3
    # avoid expanding if query already has good seed matches
    min_seed_matches_to_bypass_embedding: int = 1


_EMB_CFG = EmbeddingExpansionConfig()

# cached runtime objects
_concept_embeddings = None
_concept_list: List[str] = []

# cache expanded query
_expanded_query_cache: Dict[str, Tuple[str, List[str]]] = {}


def _normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[\u2019']", "'", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _apply_term_map(norm_query: str) -> List[str]:
    expansions: List[str] = []

    # phrase match first (longer keys first)
    for k in sorted(TERM_MAP.keys(), key=lambda x: len(x), reverse=True):
        if k in norm_query:
            for t in TERM_MAP[k]:
                if t not in expansions:
                    expansions.append(t)

    return expansions


def _ensure_concept_embeddings() -> None:
    global _concept_embeddings, _concept_list
    if _concept_embeddings is not None:
        return

    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except Exception:
        # If sentence-transformers isn't available, silently degrade to seed only.
        _concept_embeddings = None
        return

    model = SentenceTransformer(_EMB_CFG.model_name)

    _concept_list = sorted(list(CANONICAL_CONCEPTS))
    concept_texts = [
        # combine short labels into a richer semantic anchor
        c,
        c.replace("-", " "),
    ]

    # encode and keep
    emb = model.encode(_concept_list, normalize_embeddings=True)

    # Some ST versions return list; coerce
    try:
        emb_arr = emb if hasattr(emb, "shape") else np.array(emb)
    except Exception:
        emb_arr = emb

    _concept_embeddings = emb_arr


def _semantic_expand(query: str) -> List[str]:
    """Return concept expansions (canonical concepts) for query via embeddings."""

    _ensure_concept_embeddings()
    if _concept_embeddings is None or not _concept_list:
        return []

    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        model = SentenceTransformer(_EMB_CFG.model_name)
        q_emb = model.encode([query], normalize_embeddings=True)
        # cosine similarity since normalized embeddings
        sims = (q_emb @ _concept_embeddings.T).tolist()[0]
        # top indices
        ranked = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)

        out: List[str] = []
        for idx in ranked[: _EMB_CFG.top_k]:
            score = float(sims[idx])
            if score >= _EMB_CFG.semantic_threshold:
                concept = _concept_list[idx]
                if concept not in out:
                    out.append(concept)
        return out
    except Exception:
        return []


# -------------------------------
# Public API used by retrieval_adapter
# -------------------------------


def expand_query(query: str) -> Tuple[str, List[str]]:
    """Return (expanded_query, concepts_found).

    expanded_query is safe to pass into vector search.
    concepts_found are the normalized expansions applied.
    """

    cache_key = (query or "").strip().lower()
    if cache_key in _expanded_query_cache:
        return _expanded_query_cache[cache_key]

    norm = _normalize(query)
    seed_expansions = _apply_term_map(norm)

    concepts: List[str] = list(seed_expansions)

    # optional embedding expansion only if seed didn't already match heavily
    if _EMB_CFG.enabled and (len(seed_expansions) < _EMB_CFG.min_seed_matches_to_bypass_embedding):
        sem_exp = _semantic_expand(norm)
        for c in sem_exp:
            if c not in concepts:
                concepts.append(c)

    if not concepts:
        res = (query, [])
        _expanded_query_cache[cache_key] = res
        return res

    expanded_query = query.strip() + " " + " ".join(concepts)
    res = (expanded_query, concepts)
    _expanded_query_cache[cache_key] = res
    return res


def ontology_match_count(query: str) -> int:
    _, concepts = expand_query(query)
    return len(concepts)

