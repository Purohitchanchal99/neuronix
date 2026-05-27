#!/usr/bin/env python3
"""
Advanced RAG Features - Integration Examples
==============================================

How to use hybrid search, caching, metadata filtering, and reranking
"""

# Example 1: Hybrid Search (Semantic + Keyword)
print("""
=== EXAMPLE 1: HYBRID SEARCH ===

Medical queries often need both semantic understanding AND exact keyword matching.

Example:
  Query: "What is generalized anxiety disorder?"
  
  - Semantic search finds: Similar mental health conditions, anxiety info
  - Keyword search finds: "anxiety", "disorder", matching exact terms
  - Hybrid combines both → Better results for clinical terms

Code:
""")

code_ex1 = '''from rag_advanced import HybridSearcher
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Setup
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = Chroma(
    collection_name="neuronix_medical_kb",
    persist_directory="data/vector_db",
    embedding_function=embeddings
)

# Create hybrid searcher
hybrid = HybridSearcher(vector_store, alpha=0.6)  # 60% semantic, 40% keyword

# Search with metadata filter
results = hybrid.search_hybrid(
    query="What is GAD?",
    k=5,
    filters={"source": "DSM-5"}  # Optional: filter by source
)

# Results are (Document, combined_score) tuples
for doc, score in results:
    print(f"Score: {score:.2f} - {doc.page_content[:100]}...")
'''

print(code_ex1)

# Example 2: Query Caching
print("""
=== EXAMPLE 2: QUERY CACHING ===

Frequently asked medical questions should be cached for speed:
  - "What is anxiety?"
  - "Depression symptoms"
  - "Panic attack causes"

Code:
""")

code_ex2 = '''from rag_advanced import QueryCache

# Initialize cache (max 100 entries, 1 hour TTL)
cache = QueryCache(max_size=100, ttl_seconds=3600)

def search_with_cache(query, retriever):
    # Check cache first
    cached = cache.get(query)
    if cached:
        print("Using cached results!")
        return cached
    
    # Retrieve & cache
    results = retriever.retrieve_context(query)
    cache.set(query, results)
    return results

# Get stats
stats = cache.stats()
print(f"Cache hit rate: {stats['hit_rate_percent']:.1f}%")
print(f"Cached entries: {stats['entries']}/{stats['max_size']}")
'''

print(code_ex2)

# Example 3: Metadata Filtering
print("""
=== EXAMPLE 3: METADATA FILTERING ===

Filter retrieval results by clinical source:
  - source: DSM-5, ICD-11, WHO, Indian guidelines
  - topic: anxiety, depression, OCD, PTSD
  - severity: mild, moderate, severe
  - language: en, hi (Hinglish)

Code:
""")

code_ex3 = '''from rag_advanced import HybridSearcher

hybrid = HybridSearcher(vector_store)

# Filter for DSM-5 anxiety disorder definitions
results = hybrid.search_hybrid(
    query="Generalized anxiety disorder",
    k=5,
    filters={
        "source": "DSM-5",
        "clinical_domain": "anxiety"
    }
)

# Filter for Indian clinical guidelines
results = hybrid.search_hybrid(
    query="Depression treatment India",
    k=5,
    filters={
        "source": "Indian psychiatric association",
        "region": "India"
    }
)
'''

print(code_ex3)

# Example 4: Cross-Encoder Reranking
print("""
=== EXAMPLE 4: CROSS-ENCODER RERANKING ===

Use high-quality model for precise ranking (slower but better quality):

Models:
  - bge-reranker-base: Best quality (440M params) 
  - ms-marco-MiniLM: Balanced (33M params)
  - mmarco-mMiniLMv2: Small & multilingual

Code:
""")

code_ex4 = '''from rag_advanced import CrossEncoderReranker

# Initialize reranker (downloads ~1GB model first time)
reranker = CrossEncoderReranker(
    model_name="bge-reranker-base",
    use_gpu=True  # Use GPU if available for speed
)

# Get documents from basic search
basic_results = vector_store.similarity_search(query="anxiety symptoms", k=20)

# Rerank with cross-encoder
reranked = reranker.rerank(
    query="What are anxiety symptoms?",
    documents=basic_results,
    top_k=5
)

# Results are (Document, score) sorted by relevance
for doc, score in reranked:
    print(f"Relevance: {score:.2f} - {doc.page_content[:100]}...")
'''

print(code_ex4)

# Example 5: Complete Advanced RAG
print("""
=== EXAMPLE 5: COMPLETE ADVANCED RETRIEVER ===

All features together:
  ✅ Hybrid search (semantic + keywords)
  ✅ Query caching (frequent questions)
  ✅ Metadata filtering (by clinical source)
  ✅ Cross-encoder reranking (high quality)

Code:
""")

code_ex5 = '''from rag_advanced import AdvancedRAGRetriever

# Initialize with all features
advanced_rag = AdvancedRAGRetriever(
    vector_store=vector_store,
    enable_hybrid=True,           # Semantic + keyword search
    enable_cache=True,             # Cache frequent queries
    enable_reranking=False,        # Disable for speed (True for best quality)
    cache_size=100,                # Cache up to 100 queries
    hybrid_alpha=0.6               # 60% semantic, 40% keywords
)

# Simple interface
results = advanced_rag.retrieve(
    query="What is generalized anxiety disorder?",
    k=5,
    metadata_filters={"source": "DSM-5"}
)

# Get statistics
stats = advanced_rag.get_stats()
print(f"Cache hit rate: {stats['cache']['hit_rate_percent']:.1f}%")
print(f"Current chunking: {stats['chunking']['avg_chunk_size_words']} words")
print(f"Recommendation: {stats['chunking']['recommendation']['suggested']}")
'''

print(code_ex5)

# Example 6: Integration into Query System
print("""
=== EXAMPLE 6: INTEGRATION WITH EXISTING SYSTEM ===

Replace basic retrieval with advanced:

Code:
""")

code_ex6 = '''# In scripts/query_rag_system.py or neuronix_query.py:

from rag_advanced import AdvancedRAGRetriever

class NeuronixRAGQuerySystem:
    def __init__(self, num_chunks=5):
        # ... existing init code ...
        
        # REPLACE basic retriever with advanced one
        self.advanced_retriever = AdvancedRAGRetriever(
            vector_store=self.vector_store,
            enable_hybrid=True,
            enable_cache=True,
            enable_reranking=False  # Set True for production quality
        )
    
    def retrieve_context(self, query, k=None):
        """Use advanced retriever instead of basic"""
        k = k or self.num_chunks
        
        # Advanced retrieval with filtering
        results = self.advanced_retriever.retrieve(
            query=query,
            k=k,
            metadata_filters={"clinical_domain": "mental_health"}
        )
        
        return results
'''

print(code_ex6)

# Summary
print("""
=== SUMMARY: WHEN TO USE EACH ===

1. HYBRID SEARCH - ALWAYS
   ✅ Better for medical terms and clinical queries
   ✅ No additional dependencies
   ✅ ~10-20% quality improvement

2. QUERY CACHING - PRODUCTION
   ✅ Speeds up frequent questions
   ✅ Top-100 medical questions repeat often
   ✅ Reduces latency 100x for cached queries

3. METADATA FILTERING - RECOMMENDED
   ✅ Filter by clinical source (DSM-5, ICD-11)
   ✅ Improves content quality
   ✅ Must have proper metadata first

4. CROSS-ENCODER - OPTIONAL
   ⚠️  Slow (50-200ms per query)
   ⚠️  Download 440MB+ model
   ✅ Best for production quality
   ✅ Worth it for critical queries

5. CHUNK ANALYSIS - INFORMATIONAL
   ✅ Understand current chunking
   ✅ Get recommendations
   ✅ Plan re-indexing if needed

=== PERFORMANCE IMPACT ===

Basic retrieval:           ~0.5s    (fast)
Hybrid search:            ~0.6s    (minimal impact)
+ Caching hits:           ~0.01s   (100x faster!)
+ Cross-encoder:          ~1-2s    (slower, best quality)

=== NEXT STEPS ===

1. Run: python validate_advanced_rag.py
2. Test hybrid search vs basic
3. Monitor cache hit rate
4. Plan metadata tagging
5. (Optional) Add cross-encoder for production
""")
