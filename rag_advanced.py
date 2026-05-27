"""
Advanced RAG Enhancements
=========================

Improvements over basic retrieval:
1. Hybrid Search (Semantic + BM25 keyword matching)
2. Metadata Filtering (source, topic, clinical_domain)
3. Query Caching (Redis-optional, local cache fallback)
4. Cross-Encoder Reranking (optional, high-quality model)
5. Smart Chunking Analysis
"""

import sys
import os
import json
import logging
import hashlib
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from functools import lru_cache
from collections import defaultdict
import time

# Imports
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridSearcher:
    """
    Combines semantic search (embeddings) with keyword search (BM25)
    Useful for medical terms, ICD codes, exact symptom names
    """
    
    def __init__(self, vector_store, alpha: float = 0.6):
        """
        Initialize hybrid search
        
        Args:
            vector_store: ChromaDB vector store
            alpha: Weight for semantic search (0.6 = 60% semantic, 40% keyword)
                   - 0.5 = equal weight
                   - 0.7 = prioritize semantic
                   - 0.3 = prioritize keywords
        """
        self.vector_store = vector_store
        self.alpha = alpha
        self.bm25_cache = {}
        
    def _bm25_score(self, query: str, texts: List[str]) -> List[float]:
        """Simple BM25-like scoring (keyword matching)"""
        query_terms = set(query.lower().split())
        
        scores = []
        for text in texts:
            text_terms = set(text.lower().split())
            overlap = len(query_terms & text_terms)
            score = overlap / max(len(query_terms), 1)
            scores.append(score)
        
        return scores
    
    def search_hybrid(
        self,
        query: str,
        k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """
        Hybrid search combining semantic + keyword matching
        
        Args:
            query: Search query
            k: Number of results
            filters: Metadata filters {"source": "DSM-5", "topic": "anxiety"}
            
        Returns:
            List of (Document, combined_score) tuples
        """
        # Step 1: Semantic search
        try:
            semantic_results = self.vector_store.similarity_search_with_score(
                query, k=k*2  # Get more to rerank
            )
        except:
            semantic_results = [(doc, 0.0) for doc in self.vector_store.similarity_search(query, k=k*2)]
        
        # Step 2: Extract texts for BM25
        docs = [doc for doc, _ in semantic_results]
        texts = [doc.page_content for doc in docs]
        
        # Step 3: BM25 keyword scoring
        keyword_scores = self._bm25_score(query, texts)
        
        # Step 4: Normalize and combine scores
        max_semantic = max([s for _, s in semantic_results], default=1.0)
        max_keyword = max(keyword_scores, default=1.0)
        
        combined_results = []
        for i, (doc, semantic_score) in enumerate(semantic_results):
            # Normalize scores to 0-1
            norm_semantic = semantic_score / max_semantic if max_semantic > 0 else 0
            norm_keyword = keyword_scores[i] / max_keyword if max_keyword > 0 else 0
            
            # Weighted combination
            combined_score = (self.alpha * norm_semantic + 
                            (1 - self.alpha) * norm_keyword)
            
            combined_results.append((doc, combined_score))
        
        # Step 5: Sort by combined score and return top k
        combined_results.sort(key=lambda x: x[1], reverse=True)
        
        if filters:
            combined_results = self._apply_filters(combined_results, filters)
        
        return combined_results[:k]
    
    def _apply_filters(
        self,
        results: List[Tuple[Document, float]],
        filters: Dict
    ) -> List[Tuple[Document, float]]:
        """Apply metadata filters to results"""
        filtered = []
        
        for doc, score in results:
            metadata = doc.metadata or {}
            match = True
            
            for key, value in filters.items():
                # Case-insensitive matching
                if str(metadata.get(key, "")).lower() != str(value).lower():
                    match = False
                    break
            
            if match:
                filtered.append((doc, score))
        
        return filtered


class QueryCache:
    """
    Cache frequently asked questions locally
    Useful for medical questions that are asked multiple times
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize query cache
        
        Args:
            max_size: Maximum cache entries (LRU)
            ttl_seconds: Time to live for cache entries
        """
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
        
    def _hash_query(self, query: str) -> str:
        """Create hash of query for cache key"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get(self, query: str) -> Optional[List[Document]]:
        """Get cached results if available"""
        key = self._hash_query(query)
        
        if key in self.cache:
            # Check if expired
            age = time.time() - self.timestamps[key]
            if age < self.ttl_seconds:
                self.hits += 1
                logger.info(f"🎯 Cache HIT (age: {age:.1f}s)")
                return self.cache[key]
            else:
                # Expired, remove
                del self.cache[key]
                del self.timestamps[key]
        
        self.misses += 1
        return None
    
    def set(self, query: str, results: List[Document]) -> None:
        """Store results in cache"""
        key = self._hash_query(query)
        
        # Simple LRU: if at capacity, remove oldest
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps, key=self.timestamps.get)
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        self.cache[key] = results
        self.timestamps[key] = time.time()
    
    def stats(self) -> Dict:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_rate_percent": hit_rate,
            "entries": len(self.cache),
            "max_size": self.max_size
        }
    
    def clear(self) -> None:
        """Clear cache"""
        self.cache.clear()
        self.timestamps.clear()
        logger.info("Cache cleared")


class CrossEncoderReranker:
    """
    High-quality reranking using cross-encoder models
    Better than BM25 for semantic relevance
    
    Models:
    - bge-reranker-base: Good balance, 440M params
    - ms-marco-MiniLM: smaller, faster, 33M params
    - mmarco-mMiniLMv2-L12-H384-v1: even smaller, multilingual
    """
    
    def __init__(self, model_name: str = "bge-reranker-base", use_gpu: bool = False):
        """
        Initialize cross-encoder reranker
        
        Args:
            model_name: HuggingFace model to use
            use_gpu: Use GPU if available
        """
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.model = None
        
        self._load_model()
    
    def _load_model(self):
        """Lazy load the model"""
        try:
            from sentence_transformers import CrossEncoder
            
            logger.info(f"Loading cross-encoder: {self.model_name}")
            device = "cuda" if self.use_gpu else "cpu"
            self.model = CrossEncoder(self.model_name, max_length=512, device=device)
            logger.info(f"✅ Cross-encoder ready on {device}")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
            self.model = None
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 5
    ) -> List[Tuple[Document, float]]:
        """
        Rerank documents using cross-encoder
        
        Args:
            query: Search query
            documents: Documents to rerank
            top_k: Return top-k results
            
        Returns:
            List of (Document, score) sorted by relevance
        """
        if self.model is None:
            logger.warning("Cross-encoder not available, returning unranked")
            return [(doc, 1.0) for doc in documents][:top_k]
        
        # Prepare pairs for cross-encoder
        pairs = [(query, doc.page_content) for doc in documents]
        
        # Score all pairs
        scores = self.model.predict(pairs)
        
        # Combine and sort
        ranked = list(zip(documents, scores))
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked[:top_k]


class ChunkingAnalyzer:
    """
    Analyze and recommend optimal chunking for medical documents
    """
    
    @staticmethod
    def analyze_collection(vector_store) -> Dict:
        """Analyze current chunking in vector store"""
        try:
            # Get sample documents
            results = vector_store.similarity_search("medical", k=20)
            
            if not results:
                return {}
            
            chunk_sizes = [len(doc.page_content.split()) for doc in results]
            
            stats = {
                "avg_chunk_size_words": sum(chunk_sizes) / len(chunk_sizes),
                "min_chunk_size": min(chunk_sizes),
                "max_chunk_size": max(chunk_sizes),
                "samples_analyzed": len(results),
                "recommendation": ChunkingAnalyzer.recommend_chunking(
                    sum(chunk_sizes) / len(chunk_sizes)
                )
            }
            
            return stats
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {}
    
    @staticmethod
    def recommend_chunking(avg_size: int) -> Dict:
        """Recommend optimal chunking for medical content"""
        
        recommendations = {
            "general": {
                "chunk_size": 500,
                "chunk_overlap": 100,
                "description": "Good for general medical content"
            },
            "clinical": {
                "chunk_size": 300,
                "chunk_overlap": 60,
                "description": "Tighter chunks for clinical notes"
            },
            "detailed": {
                "chunk_size": 800,
                "chunk_overlap": 150,
                "description": "Larger chunks for detailed articles"
            },
            "current": {
                "avg_size": round(avg_size),
                "assessment": "Current chunking is working"
            }
        }
        
        # Recommend based on current size
        if avg_size < 200:
            recommendations["suggested"] = recommendations["clinical"]
        elif avg_size > 800:
            recommendations["suggested"] = recommendations["detailed"]
        else:
            recommendations["suggested"] = recommendations["general"]
        
        return recommendations


class AdvancedRAGRetriever:
    """
    Complete advanced RAG system with all enhancements
    """
    
    def __init__(
        self,
        vector_store,
        enable_hybrid: bool = True,
        enable_cache: bool = True,
        enable_reranking: bool = False,
        cache_size: int = 100,
        hybrid_alpha: float = 0.6
    ):
        """
        Initialize advanced RAG retriever
        
        Args:
            vector_store: ChromaDB vector store
            enable_hybrid: Use hybrid search (semantic + keyword)
            enable_cache: Cache frequent queries
            enable_reranking: Use cross-encoder reranking (slow but high quality)
            cache_size: Number of cached queries to keep
            hybrid_alpha: Weight for semantic in hybrid search
        """
        self.vector_store = vector_store
        self.enable_hybrid = enable_hybrid
        self.enable_cache = enable_cache
        self.enable_reranking = enable_reranking
        
        # Initialize components
        self.hybrid_searcher = HybridSearcher(vector_store, alpha=hybrid_alpha) if enable_hybrid else None
        self.cache = QueryCache(max_size=cache_size) if enable_cache else None
        self.reranker = CrossEncoderReranker() if enable_reranking else None
        
        logger.info("Advanced RAG Retriever initialized")
        logger.info(f"  Hybrid search: {'ENABLED' if enable_hybrid else 'DISABLED'}")
        logger.info(f"  Query cache: {'ENABLED' if enable_cache else 'DISABLED'}")
        logger.info(f"  Cross-encoder reranking: {'ENABLED' if enable_reranking else 'DISABLED'}")
    
    def retrieve(
        self,
        query: str,
        k: int = 5,
        metadata_filters: Optional[Dict] = None,
        use_hybrid: Optional[bool] = None
    ) -> List[Document]:
        """
        Advanced retrieval with all features
        
        Args:
            query: Search query
            k: Number of results
            metadata_filters: Filter by metadata (source, topic, etc.)
            use_hybrid: Override hybrid setting for this query
            
        Returns:
            List of relevant documents
        """
        use_hybrid = self.enable_hybrid if use_hybrid is None else use_hybrid
        
        # Step 1: Check cache
        if self.enable_cache:
            cached = self.cache.get(query)
            if cached:
                return cached[:k]
        
        # Step 2: Retrieve documents
        if use_hybrid and self.hybrid_searcher:
            results = self.hybrid_searcher.search_hybrid(query, k=k*2, filters=metadata_filters)
            docs = [doc for doc, score in results]
        else:
            # Basic search
            docs = self.vector_store.similarity_search(query, k=k)
        
        # Step 3: Optional reranking
        if self.enable_reranking and self.reranker:
            reranked = self.reranker.rerank(query, docs, top_k=k)
            docs = [doc for doc, score in reranked]
        else:
            docs = docs[:k]
        
        # Step 4: Cache results
        if self.enable_cache:
            self.cache.set(query, docs)
        
        return docs
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        stats = {
            "hybrid_search": self.enable_hybrid,
            "caching": self.enable_cache,
            "reranking": self.enable_reranking,
        }
        
        if self.enable_cache and self.cache:
            stats["cache"] = self.cache.stats()
        
        # Chunk analysis
        try:
            chunk_stats = ChunkingAnalyzer.analyze_collection(self.vector_store)
            stats["chunking"] = chunk_stats
        except:
            pass
        
        return stats


# Export key classes
__all__ = [
    'HybridSearcher',
    'QueryCache',
    'CrossEncoderReranker',
    'ChunkingAnalyzer',
    'AdvancedRAGRetriever'
]
