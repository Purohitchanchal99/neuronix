"""
🎯 QUERY PRECISION LAYER FOR NEURONIX
======================================
Dual filtering: metadata + embedding similarity
Ensures precise, context-aligned retrieval
"""

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# PRECISION QUERY ENGINE
# ============================================================================

@dataclass
class QueryContext:
    """Context for precision query"""
    query_text: str
    domain_filters: Optional[List[str]] = None
    chapter_filter: Optional[int] = None
    difficulty_level: Optional[str] = None
    min_similarity: float = 0.7  # Minimum embedding similarity
    max_results: int = 5


class QueryPrecisionLayer:
    """
    Dual filtering for precise query results:
    1. Metadata filtering (domain, chapter, difficulty)
    2. Embedding similarity filtering (semantic relevance)
    """
    
    def __init__(self, metadata_manager, embedding_model):
        self.metadata_manager = metadata_manager
        self.embedding_model = embedding_model
        logger.info("✅ QueryPrecisionLayer initialized")
    
    def execute_precision_query(self, 
                               query_context: QueryContext,
                               candidates: List[Tuple[str, Dict]]) -> List[Dict]:
        """
        Execute query with dual filtering
        
        Process:
        1. Apply metadata filters (narrow down candidates)
        2. Calculate embedding similarity
        3. Rank by combined score
        4. Return top results
        
        Returns:
        List of results with scores and metadata
        """
        
        # Step 1: Apply metadata filters
        metadata_filtered = self._metadata_filter(query_context, candidates)
        logger.info(f"📊 Metadata filter: {len(candidates)} → {len(metadata_filtered)} results")
        
        if not metadata_filtered:
            logger.warning("⚠️ No results after metadata filtering")
            return []
        
        # Step 2: Calculate embedding similarity
        embedding_scored = self._embedding_filter(
            query_context.query_text,
            metadata_filtered,
            query_context.min_similarity
        )
        logger.info(f"📊 Embedding filter: {len(metadata_filtered)} → {len(embedding_scored)} results")
        
        # Step 3: Rank by combined score
        ranked = self._rank_results(embedding_scored)
        
        # Step 4: Return top results
        return ranked[:query_context.max_results]
    
    def _metadata_filter(self, 
                        query_context: QueryContext,
                        candidates: List[Tuple[str, Dict]]) -> List[Tuple[str, Dict]]:
        """Apply metadata filters"""
        filtered = candidates
        
        # Filter by domain
        if query_context.domain_filters:
            filtered = [
                (text, meta) for text, meta in filtered
                if any(tag in meta.get('domain_tags', []) 
                      for tag in query_context.domain_filters)
            ]
        
        # Filter by chapter
        if query_context.chapter_filter:
            filtered = [
                (text, meta) for text, meta in filtered
                if meta.get('chapter') == query_context.chapter_filter
            ]
        
        # Filter by difficulty
        if query_context.difficulty_level:
            filtered = [
                (text, meta) for text, meta in filtered
                if meta.get('difficulty_level') == query_context.difficulty_level
            ]
        
        return filtered
    
    def _embedding_filter(self, 
                         query: str,
                         candidates: List[Tuple[str, Dict]],
                         min_similarity: float) -> List[Dict]:
        """
        Filter by embedding similarity
        Returns results with similarity scores
        """
        
        # Get query embedding
        query_embedding = self.embedding_model.embed_query(query)
        
        scored_results = []
        
        for candidate_text, metadata in candidates:
            # Get candidate embedding
            candidate_embedding = self.embedding_model.embed_query(candidate_text)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, candidate_embedding)
            
            # Apply minimum threshold
            if similarity >= min_similarity:
                scored_results.append({
                    "text": candidate_text,
                    "metadata": metadata,
                    "embedding_similarity": similarity,
                    "embedding_score_norm": (similarity + 1) / 2  # Normalize to 0-1
                })
        
        return scored_results
    
    def _rank_results(self, scored_results: List[Dict]) -> List[Dict]:
        """Rank results by combined score"""
        
        # Calculate combined score
        for result in scored_results:
            # Weights
            embedding_weight = 0.7
            quality_weight = 0.3
            
            embedding_score = result["embedding_score_norm"]
            quality_score = result["metadata"].get("quality_score", 0.8)
            
            combined_score = (embedding_weight * embedding_score + 
                            quality_weight * quality_score)
            
            result["combined_score"] = combined_score
            result["rank"] = 0  # Will be set after sorting
        
        # Sort by combined score
        scored_results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Add rank
        for i, result in enumerate(scored_results, 1):
            result["rank"] = i
        
        return scored_results
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
            
            if norm_product == 0:
                return 0.0
            
            return float(dot_product / norm_product)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0


class DualFilterQueryRouter:
    """Intelligently routes precision queries"""
    
    def __init__(self, precision_layer: QueryPrecisionLayer):
        self.precision_layer = precision_layer
        self.query_log = []
        logger.info("✅ DualFilterQueryRouter initialized")
    
    def route_query(self, 
                   query_text: str,
                   domain_tags: Optional[List[str]] = None,
                   max_results: int = 5,
                   min_similarity: float = 0.7) -> Dict:
        """
        Route query through precision layer
        
        Returns:
        {
            "original_query": str,
            "results": List[Dict],
            "metadata": {
                "candidates_checked": int,
                "filtering_stages": Dict,
                "execution_time_ms": float
            }
        }
        """
        
        start_time = datetime.now()
        
        # Create query context
        context = QueryContext(
            query_text=query_text,
            domain_filters=domain_tags,
            max_results=max_results,
            min_similarity=min_similarity
        )
        
        # Get candidates (placeholder - would be from vector DB)
        candidates = self._get_candidates(query_text)
        
        # Execute precision query
        results = self.precision_layer.execute_precision_query(context, candidates)
        
        # Log query
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        log_entry = {
            "query": query_text,
            "domain_filters": domain_tags,
            "results_count": len(results),
            "execution_time_ms": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        self.query_log.append(log_entry)
        
        return {
            "original_query": query_text,
            "results": results,
            "metadata": {
                "results_found": len(results),
                "execution_time_ms": execution_time,
                "filters_applied": {
                    "domains": domain_tags,
                    "min_similarity": min_similarity
                }
            }
        }
    
    def _get_candidates(self, query: str) -> List[Tuple[str, Dict]]:
        """
        Get candidate chunks from vector database
        This is a placeholder - would integrate with ChromaDB
        """
        # In production, this would:
        # 1. Query ChromaDB for similar chunks
        # 2. Return top-k candidates with metadata
        # 3. Pass to dual filter
        
        return []


# ============================================================================
# PRECISION CONFIGURATION
# ============================================================================

class PrecisionConfig:
    """Configuration for precision layer"""
    
    # Default filter thresholds
    MIN_EMBEDDING_SIMILARITY = 0.7
    MAX_RESULTS = 5
    
    # Domain priority (for weighted filtering)
    DOMAIN_PRIORITY = {
        "diagnostic": 1.0,
        "psychiatric": 0.9,
        "therapeutic": 0.8,
        "pharmacological": 0.7,
        "psychological": 0.6
    }
    
    # Quality thresholds
    MIN_QUALITY_SCORE = 0.7
    
    @staticmethod
    def get_config_for_difficulty(difficulty: str) -> Dict:
        """Get configuration based on user difficulty level"""
        configs = {
            "beginner": {
                "min_similarity": 0.8,  # Higher threshold for clarity
                "max_results": 3,
                "prefer_difficulty": "beginner"
            },
            "intermediate": {
                "min_similarity": 0.7,
                "max_results": 5,
                "prefer_difficulty": "intermediate"
            },
            "advanced": {
                "min_similarity": 0.6,  # Lower threshold for depth
                "max_results": 7,
                "prefer_difficulty": "advanced"
            }
        }
        
        return configs.get(difficulty, configs["intermediate"])


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    print(r"""
    🎯 Query Precision Layer
    ========================
    
    This module provides dual filtering:
    1. Metadata filtering (domain, chapter, quality)
    2. Embedding similarity (semantic relevance)
    
    Integration:
    - Use QueryContext to define query parameters
    - Use QueryPrecisionLayer.execute_precision_query()
    - Returns ranked results with combined scores
    
    Example:
    from query_precision_layer import QueryContext, QueryPrecisionLayer
    
    # Create context
    context = QueryContext(
        query_text="What is anxiety?",
        domain_filters=["psychiatric", "diagnostic"],
        min_similarity=0.7,
        max_results=5
    )
    
    # Execute precision query
    results = precision_layer.execute_precision_query(context, candidates)
    """)
