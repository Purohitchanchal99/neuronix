# Feature Enablement - Implementation Guide

## 🚀 Quick Start (Copy-Paste Ready)

### Current Production (Already Installed)
```python
from scripts.query_rag_system import NeuronixRAGQuerySystem

system = NeuronixRAGQuerySystem()
answer = system.query("anxiety symptoms")

# What's running:
# ✅ Hybrid search (60% semantic, 40% keyword)
# ✅ Query caching (200 entry LRU)
# ✅ Auto-fallback if Advanced RAG fails
# No code changes needed!
```

---

## 📊 Monitor Current Performance

### Check Statistics
```python
# Get real-time stats
stats = system.advanced_retriever.get_stats()

print("=== HYBRID SEARCH ===")
print(f"Enabled: {stats['hybrid']['enabled']}")
print(f"Alpha: {stats['hybrid']['alpha']}")

print("\n=== CACHE PERFORMANCE ===")
print(f"Entries: {stats['cache']['entries']}")
print(f"Hits: {stats['cache']['hits']}")
print(f"Misses: {stats['cache']['misses']}")
print(f"Hit rate: {stats['cache']['hit_rate_percent']}%")

print("\n=== CHUNK ANALYSIS ===")
chunks = stats.get('chunk_analysis', {})
if chunks:
    print(f"Avg chunk: {chunks['avg_chunk_size']} words")
    print(f"Min: {chunks['min_chunk_size']} words")
    print(f"Max: {chunks['max_chunk_size']} words")
```

### Track Over Time (Week 1+)
```python
from scripts.monitor_advanced_rag import RAGMonitor

monitor = RAGMonitor()

# Log each query
for query in ["anxiety", "depression", "anxiety", "stress", "anxiety"]:
    results = system.query(query)
    cache_hit = monitor.last_query_cached  # Or track manually
    monitor.log_query(query, 5, 0.15, cache_hit)

# Get insights
print(monitor.get_insights())
```

---

## 🔲 Week 2: Enable Metadata Filtering

### Step 1: Add Metadata to Documents

```python
# During document ingestion
from langchain_core.documents import Document

def create_document_with_metadata(text, source, topic, severity):
    """Create document with clinical metadata"""
    return Document(
        page_content=text,
        metadata={
            'source': source,           # "DSM-5", "ICD-11", "Clinical"
            'topic': topic,             # "anxiety", "depression", "stress"
            'subtopic': '',             # "panic", "generalized", etc.
            'severity': severity,       # "mild", "moderate", "severe"
            'language': 'medical',      # Content language
            'confidence': 0.95,
            'date': '2026-05-12'
        }
    )

# Example
doc = create_document_with_metadata(
    text="Generalized anxiety disorder involves persistent worry...",
    source="DSM-5",
    topic="anxiety",
    severity="moderate"
)
```

### Step 2: Enable Metadata Filtering in Queries

**Option A: Simple filtering**
```python
def retrieve_by_source(query: str, source: str = "DSM-5", k: int = 5):
    """Retrieve only from specific clinical source"""
    
    # Get more results initially
    results = system.advanced_retriever.retrieve(query, k=k*2)
    
    # Filter by metadata
    filtered = [
        doc for doc in results
        if doc.metadata.get('source') == source
    ]
    
    return filtered[:k]

# Usage
results = retrieve_by_source("anxiety treatment", source="DSM-5")
```

**Option B: Complex filtering**
```python
def retrieve_with_criteria(query: str, **metadata_filters):
    """Retrieve with multiple metadata criteria"""
    
    results = system.advanced_retriever.retrieve(query, k=10)
    
    # Apply all filters
    for key, value in metadata_filters.items():
        results = [
            doc for doc in results
            if doc.metadata.get(key) == value
        ]
    
    return results

# Usage
results = retrieve_with_criteria(
    "anxiety treatment",
    source="DSM-5",
    topic="anxiety",
    severity="moderate"
)
```

**Option C: Priority-based filtering**
```python
def retrieve_intelligent(query: str, k: int = 5):
    """Smart filtering with clinical authority priority"""
    
    results = system.advanced_retriever.retrieve(query, k=k*2)
    
    # Priority 1: DSM-5 results
    dsm5_results = [d for d in results if d.metadata.get('source') == 'DSM-5']
    if len(dsm5_results) >= k:
        return dsm5_results[:k]
    
    # Priority 2: Any clinical source
    clinical_results = [d for d in results if d.metadata.get('language') == 'medical']
    return clinical_results[:k]

# Usage
results = retrieve_intelligent("anxiety symptoms")
```

### Step 3: Integrate into Query System

```python
# Update retrieve_context() in scripts/query_rag_system.py

def retrieve_context(self, query: str, k: Optional[int] = None, 
                    source_filter: Optional[str] = None) -> List[Document]:
    """Retrieve with optional metadata filtering"""
    
    k = k or self.num_chunks
    k = max(MIN_CHUNKS, min(k, MAX_CHUNKS))
    
    try:
        logger.info(f"🔍 Query: '{query}'")
        
        # Advanced retrieval
        results = self.advanced_retriever.retrieve(query, k=k)
        
        # Apply metadata filter if requested
        if source_filter:
            results = [
                doc for doc in results
                if doc.metadata.get('source') == source_filter
            ]
            logger.info(f"   📌 Filtered by source: {source_filter}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return []

# Usage
answer = system.query("anxiety treatment")  # Uses both sources
answer = system.query("anxiety treatment", source_filter="DSM-5")  # Only DSM-5
```

---

## 📊 Week 3: Run Chunk Analysis

### Analyze Current Chunking
```python
from rag_advanced import ChunkingAnalyzer

def analyze_current_chunks():
    """Analyze and report on chunking"""
    
    analyzer = ChunkingAnalyzer(system.vector_store)
    analysis = analyzer.analyze()
    
    print("\n" + "="*60)
    print("📊 CHUNK ANALYSIS REPORT")
    print("="*60)
    
    print(f"\nCurrent Chunking:")
    print(f"  Average: {analysis['avg_chunk_size']:.0f} words")
    print(f"  Min: {analysis['min_chunk_size']:.0f} words")
    print(f"  Max: {analysis['max_chunk_size']:.0f} words")
    
    print(f"\nRecommendations:")
    for content_type, config in analysis['recommendations'].items():
        print(f"  {content_type}:")
        print(f"    - Chunk size: {config['chunk_size']} words")
        print(f"    - Overlap: {config['overlap']} words")
    
    return analysis

# Run it
analysis = analyze_current_chunks()
```

### Decide on Re-indexing
```python
def evaluate_reindexing(analysis):
    """Decide if re-indexing is needed"""
    
    avg_size = analysis['avg_chunk_size']
    recommended = analysis['recommendations']['good_default']['chunk_size']
    
    if abs(avg_size - recommended) < 50:
        print("✅ Current chunking is close to optimal - no re-indexing needed")
        return False
    
    if avg_size > recommended * 1.5:
        print("⚠️  Chunks are too large - consider re-indexing with smaller chunks")
        print(f"   Current: {avg_size:.0f} words → Recommended: {recommended} words")
        return True
    
    if avg_size < recommended * 0.5:
        print("⚠️  Chunks are too small - consider re-indexing with larger chunks")
        print(f"   Current: {avg_size:.0f} words → Recommended: {recommended} words")
        return True
    
    print("✅ Current chunking is optimal")
    return False

# Evaluate
should_reindex = evaluate_reindexing(analysis)
```

---

## ⚙️ Optional: Enable Cross-Encoder Reranking

### When to Use
```python
# NOT FOR PRODUCTION - TOO SLOW
# Use ONLY for:
# - Critical medical decisions
# - Research documentation
# - When quality >> speed

# Good use case:
if query_type == "critical_diagnosis":
    enable_reranking = True
else:
    enable_reranking = False  # Keep disabled for general queries
```

### Implementation

**Option 1: Create reranking-enabled retriever**
```python
from rag_advanced import AdvancedRAGRetriever

def create_critical_retriever(vector_store):
    """For critical queries - best quality"""
    return AdvancedRAGRetriever(
        vector_store=vector_store,
        enable_hybrid=True,
        enable_cache=True,
        enable_reranking=True,
        reranker_model='cross-encoder/ms-marco-MiniLM-L-6-v2',
        hybrid_alpha=0.6
    )

def create_fast_retriever(vector_store):
    """For general queries - best speed"""
    return AdvancedRAGRetriever(
        vector_store=vector_store,
        enable_hybrid=True,
        enable_cache=True,
        enable_reranking=False,  # No reranking
        hybrid_alpha=0.6
    )

# Usage - route by query type
if "diagnosis" in query.lower():
    retriever = create_critical_retriever(system.vector_store)
else:
    retriever = create_fast_retriever(system.vector_store)

results = retriever.retrieve(query, k=5)
```

**Option 2: Selective reranking**
```python
def retrieve_and_optionally_rerank(query: str, rerank: bool = False):
    """Retrieve with optional reranking"""
    
    # Always use hybrid search + cache
    results = system.advanced_retriever.retrieve(query, k=8)
    
    # Optional: rerank if critical
    if rerank and results:
        from rag_advanced import CrossEncoderReranker
        
        reranker = CrossEncoderReranker(
            model_name='cross-encoder/ms-marco-MiniLM-L-6-v2'
        )
        results = reranker.rerank(results, query, k=5)
        logger.info("🎯 Results reranked for maximum quality")
    
    return results

# Usage
results = retrieve_and_optionally_rerank("anxiety diagnosis", rerank=False)  # Fast
results = retrieve_and_optionally_rerank("anxiety diagnosis", rerank=True)   # Best quality
```

---

## 🎯 Decision Tree: Which Features to Enable?

```
┌─ Is query type CRITICAL (diagnosis)?
│  ├─ YES → Enable reranking: True
│  └─ NO → Enable reranking: False

├─ Is document metadata CONSISTENT?
│  ├─ YES → Enable metadata filtering: True
│  └─ NO → Enable metadata filtering: False (wait 2 weeks)

├─ Is it FIRST TIME deployment?
│  ├─ YES → Run chunk analysis in week 3
│  └─ NO → No need

└─ Check cache hit rate after 2 weeks:
   ├─ > 40% → Everything is optimal! ✅
   ├─ 20-40% → Good, monitor more
   └─ < 20% → Queries are diverse (normal)
```

---

## 📈 Timeline Implementation

### Day 1 (Today)
```python
# Current state - nothing to do
system = NeuronixRAGQuerySystem()
answer = system.query("anxiety")
# ✅ Hybrid + cache already running
```

### Week 1: Monitor
```python
# Track cache performance
from scripts.monitor_advanced_rag import RAGMonitor

monitor = RAGMonitor()
# Log queries during week...
insights = monitor.get_insights()  # See if ready for metadata

print(f"Week 1 summary: {insights}")
```

### Week 2: Add Metadata (If Ready)
```python
# If data looks good and metadata is available:
results = retrieve_by_source(
    query="anxiety treatment",
    source="DSM-5"
)

# Generate answers with better clinical authority
answer = system.generate_answer("anxiety treatment", results)
```

### Week 3: Analyze Chunks
```python
# Run analysis
analysis = analyze_current_chunks()

# Decide on optimization
should_reindex = evaluate_reindexing(analysis)

if should_reindex:
    print("Plan re-indexing with new chunk settings")
else:
    print("Current setup is optimal!")
```

### Month 2+: Consider Reranking (Optional)
```python
# For critical queries only
critical_results = retrieve_and_optionally_rerank(
    query=critical_query,
    rerank=True  # Best quality
)
```

---

## ✅ Implementation Checklist

### Phase 1: Production (Current)
- [x] Hybrid search enabled
- [x] Query caching enabled
- [x] Monitoring setup
- [ ] Wait for 1 week of data

### Phase 2: Enhanced (Week 2)
- [ ] Add metadata to documents
- [ ] Enable metadata filtering
- [ ] Test filtered queries
- [ ] Verify metadata quality

### Phase 3: Optimized (Week 3)
- [ ] Run chunk analysis
- [ ] Review recommendations
- [ ] Plan re-indexing (if needed)
- [ ] Document findings

### Phase 4: Advanced (Month 2, Optional)
- [ ] Test cross-encoder reranking
- [ ] Measure quality vs speed
- [ ] Deploy for critical queries only
- [ ] Monitor impact

---

## 🎊 Code Copy-Paste Templates

### Template 1: Monitor Cache (Week 1)
```python
from scripts.query_rag_system import NeuronixRAGQuerySystem
from scripts.monitor_advanced_rag import RAGMonitor

system = NeuronixRAGQuerySystem()
monitor = RAGMonitor()

# Simulate queries
queries = [
    "anxiety symptoms",
    "depression treatment",
    "anxiety symptoms",  # Will hit cache
    "stress management",
    "anxiety symptoms",  # Will hit cache
]

for query in queries:
    results = system.query(query)
    # Log to monitor...

print(monitor.get_insights())
```

### Template 2: Filter by Source (Week 2)
```python
def query_with_source(question: str, source: str = "DSM-5"):
    """Query with clinical source priority"""
    
    results = system.advanced_retriever.retrieve(question, k=8)
    
    # Filter to source
    filtered = [
        doc for doc in results
        if doc.metadata.get('source') == source
    ]
    
    # Fallback if no results from source
    if not filtered:
        return results[:5]
    
    return filtered[:5]

# Usage
answer = query_with_source("anxiety disorder", source="DSM-5")
```

### Template 3: Analyze Chunks (Week 3)
```python
from rag_advanced import ChunkingAnalyzer

analyzer = ChunkingAnalyzer(system.vector_store)
analysis = analyzer.analyze()

print(f"Average chunk: {analysis['avg_chunk_size']:.0f} words")
print(f"Recommendation: {analysis['recommendations']['good_default']}")
```

### Template 4: Optional Reranking
```python
def get_best_results(query: str, quality_critical: bool = False):
    """Get results with optional best-quality reranking"""
    
    results = system.advanced_retriever.retrieve(query, k=10)
    
    if quality_critical:  # Only for critical queries
        from rag_advanced import CrossEncoderReranker
        reranker = CrossEncoderReranker()
        results = reranker.rerank(results, query, k=5)
    
    return results

# Usage
best = get_best_results("anxiety diagnosis", quality_critical=True)  # Best quality
fast = get_best_results("general anxiety", quality_critical=False)  # Fast
```

---

## 🚀 You're All Set!

**Current state:** ✅ Hybrid + Cache running  
**Week 1 goal:** Monitor hit rates  
**Week 2 goal:** Add metadata filtering  
**Week 3 goal:** Analyze & optimize chunking  
**Month 2 goal:** Optional reranking  

Copy the templates above and implement step-by-step. No rush - you're already running optimal configuration! 🎉
