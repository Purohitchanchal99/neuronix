# RAG PIPELINE IMPLEMENTATION PLAN
**Project:** NEURONIX TextBook Library RAG System  
**Date:** April 22, 2026  
**Status:** Architecture & Strategy Document

---

## 📋 EXECUTIVE SUMMARY

**Your Current State:**
- ✅ 279 verified PDFs across 16 countries
- ✅ Python 3.11 with LangChain, ChromaDB, Transformers
- ✅ Master JSON with metadata
- ✅ 88% syllabus coverage automated

**Goal:** Build a semantic search RAG system that allows querying across all psychology textbooks by subject, country, and academic year.

**Success Criteria:**
1. Index all 279 PDFs with extractable text
2. Generate semantic embeddings (vector representations)
3. Store in ChromaDB (vector database already installed)
4. Create retrieval layer with ranking/filtering
5. Integrate with LLM for answer generation
6. Deploy with REST API

---

## 🏗️ SYSTEM ARCHITECTURE

### Layer 1: PDF Processing Pipeline
```
279 PDFs (on disk)
    ↓
Extract text (PyPDF2/pdfplumber)
    ↓
Split into chunks (LangChain TextSplitter)
    ↓
Add metadata (country, subject, year, book)
    ↓
Cleaned documents ready for embedding
```

### Layer 2: Embedding & Vectorization
```
Document chunks
    ↓
Sentence Transformers (sentence-transformers already installed)
    ↓
Generate 384-dim vectors (all-MiniLM-L6-v2 model)
    ↓
Store in ChromaDB with metadata
    ↓
Indexed vector database
```

### Layer 3: Retrieval System
```
User Query
    ↓
Embed query (same model)
    ↓
Semantic search in ChromaDB
    ↓
Rank by relevance + metadata filters
    ↓
Return top-K most relevant chunks
    ↓
Include citation info (file, page, country)
```

### Layer 4: RAG Generation
```
Retrieved context chunks
    ↓
Format as context window
    ↓
Send to LLM (OpenAI GPT-4 or local model)
    ↓
Generate answer with sources
    ↓
Return answer + citations
```

### Layer 5: Deployment
```
FastAPI server
    ↓
/search endpoint (semantic search)
    ↓
/rag endpoint (full RAG query)
    ↓
Frontend web interface (optional)
    ↓
Accessible to users
```

---

## 📊 DETAILED IMPLEMENTATION ROADMAP

### PHASE 1: PDF Text Extraction (Week 1, Day 1-2)

**Goal:** Extract clean text from all 279 PDFs

**Technology Stack:**
- `pdfplumber` (best for text extraction with layout preservation)
- `PyPDF2` (fallback for corrupted PDFs)
- LangChain `PyPDFLoader` (built-in integration)

**Script:** `1_extract_pdf_texts.py`

**Process:**
```
For each PDF in /docs:
  1. Load PDF metadata (filename → country, subject)
  2. Extract text page-by-page
  3. Preserve page numbers for citations
  4. Handle errors gracefully
  5. Save extracted text to JSON structure
Output: documents.json with text + metadata
```

**Expected Output:**
```json
{
  "total_documents": 279,
  "total_pages": 50000+,
  "sample": {
    "file": "United_States/General Psychology_Psychology2e_WEB.pdf",
    "country": "United States",
    "subject": "General Psychology",
    "pages": 1180,
    "text_extracted": "✓ 2.3 MB text data"
  }
}
```

**Time Estimate:** 10-15 minutes

---

### PHASE 2: Document Chunking & Preparation (Week 1, Day 2)

**Goal:** Split large documents into indexable chunks

**Technology Stack:**
- LangChain `RecursiveCharacterTextSplitter`
- Metadata preservation
- Overlap strategy (10% for context)

**Script:** `2_chunk_documents.py`

**Process:**
```
For each extracted document:
  1. Load text and metadata
  2. Split into 1000-char chunks (optimal for embeddings)
  3. Add 100-char overlap between chunks
  4. Preserve metadata for each chunk:
     - Country
     - Subject
     - Academic year
     - Original filename
     - Page number
  5. Filter out empty/noise chunks
Output: chunks.json with 50,000+ indexed chunks
```

**Configuration:**
```python
chunk_size = 1000          # Characters per chunk
chunk_overlap = 100        # 10% overlap
separator = "\n\n"        # Split on paragraphs first
```

**Time Estimate:** 5 minutes

---

### PHASE 3: Generate Embeddings (Week 1, Day 2-3)

**Goal:** Convert text chunks to 384-dimensional vectors

**Technology Stack:**
- `sentence-transformers` (all-MiniLM-L6-v2)
- Batch processing for efficiency
- GPU acceleration (if available)

**Script:** `3_generate_embeddings.py`

**Process:**
```
For each chunk in chunks.json:
  1. Load chunk text
  2. Pass to SentenceTransformer model
  3. Receive 384-dim vector
  4. Pair with metadata
  5. Batch 100 chunks at a time
  6. Save embeddings + metadata
Output: embeddings.json (vector database format)
```

**Batch Configuration:**
```python
batch_size = 100
embedding_model = "all-MiniLM-L6-v2"  # 384 dimensions
progress_bar = True
```

**Performance:**
- ~1000 chunks/minute on CPU
- 50,000 chunks = ~50 minutes total
- GPU: ~5000 chunks/minute (~10 minutes)

**Time Estimate:** 30-50 minutes

---

### PHASE 4: Index into ChromaDB (Week 1, Day 3)

**Goal:** Store embeddings in vector database for fast retrieval

**Technology Stack:**
- ChromaDB (already installed)
- Persistence to disk
- Metadata filtering support

**Script:** `4_index_chromadb.py`

**Process:**
```
Initialize ChromaDB connection
Create collection: "psychology_textbooks"

For each embedding + metadata pair:
  1. Add embedding vector
  2. Store metadata (country, subject, year, source)
  3. Store chunk ID and text for retrieval
  4. Persist to disk

Enable filtering by:
  - Country (16 values)
  - Subject (22+ values)
  - Academic year (1-4)
  - Text search (full-text)
```

**ChromaDB Configuration:**
```python
chroma_db_path = "./chromadb_data"
collection_name = "psychology_textbooks"
embedding_function = "sentence-transformers"
```

**Time Estimate:** 10 minutes

---

### PHASE 5: Retrieval Layer (Week 1, Day 4)

**Goal:** Create semantic search interface

**Technology Stack:**
- ChromaDB similarity search
- Metadata filtering
- Result ranking and deduplication

**Script:** `5_retrieval_system.py`

**Features:**
```
Class: AdvancedRetriever
  
Methods:
  1. search(query, top_k=10, country=None, subject=None, year=None)
     - Embed query
     - Search ChromaDB
     - Apply filters
     - Return ranked results with scores
  
  2. search_by_subject(subject, query)
     - Filter to specific subject
     - Search within filtered set
  
  3. search_by_country(country, query)
     - Filter to specific country
     - Search within filtered set
  
  4. search_by_year(year, query)
     - Filter to academic year (1-4)
     - Search within filtered set
  
  5. cross_country_search(query, countries=[])
     - Compare results across countries
     - Return country-specific variants
```

**Example Usage:**
```python
retriever = AdvancedRetriever()

# Simple semantic search
results = retriever.search("How does cognitive psychology explain memory?", top_k=5)

# Filtered search
results = retriever.search(
    "Abnormal psychology disorders",
    country="United States",
    subject="Abnormal Psychology",
    top_k=10
)

# Cross-country comparison
results = retriever.search_by_country("Germany", "Was ist Psychologie?")
```

**Output Format:**
```json
{
  "query": "cognitive mechanisms",
  "results": [
    {
      "content": "Memory is a cognitive process...",
      "score": 0.92,
      "metadata": {
        "country": "USA",
        "subject": "Cognitive Psychology",
        "year": 1,
        "source_file": "General_Psychology_Psychology2e_WEB.pdf",
        "page": 245,
        "chunk_id": "psych_us_cog_0245_1"
      }
    }
  ]
}
```

**Time Estimate:** 5 minutes (code writing)

---

### PHASE 6: RAG Integration (Week 1, Day 4-5)

**Goal:** Integrate LLM for answer generation

**Technology Stack:**
- OpenAI API (GPT-4 or GPT-3.5-turbo)
- LangChain for orchestration
- Prompt templates

**Script:** `6_rag_generator.py`

**Architecture:**
```
User Query
    ↓
Retrieve relevant context (Retrieval layer)
    ↓
Format context for LLM
    ↓
Create prompt: [SYSTEM] + [CONTEXT] + [QUESTION]
    ↓
Call OpenAI API
    ↓
Extract answer
    ↓
Add citations from metadata
    ↓
Return formatted response
```

**Prompt Template:**
```
You are an expert psychology educator with access to a comprehensive textbook library.

CONTEXT:
{retrieved_context}

QUESTION:
{user_question}

INSTRUCTIONS:
1. Answer based ONLY on the provided context
2. Be precise and cite specific concepts
3. Include page references if available
4. Acknowledge if information cannot be found
5. Suggest related topics

ANSWER:
```

**Example Features:**
```python
class RAGGenerator:
    def answer_question(self, question, country=None, subject=None, top_k=5):
        """Generate answer with citations"""
        # 1. Retrieve context
        # 2. Format for LLM
        # 3. Call OpenAI
        # 4. Add citations
        # 5. Return formatted answer
    
    def compare_across_countries(self, question, countries=None):
        """Get perspective from different textbooks"""
        
    def generate_essay(self, topic, academic_level="year1"):
        """Generate comprehensive essay with citations"""
        
    def explain_concept(self, concept, country=None):
        """Detailed explanation with examples"""
```

**Time Estimate:** 20 minutes

---

### PHASE 7: API & Deployment (Week 1, Day 5)

**Goal:** Create REST API for access

**Technology Stack:**
- FastAPI (lightweight, async)
- Uvicorn (ASGI server)
- Pydantic (validation)

**Script:** `7_api_server.py`

**Endpoints:**
```
POST /search
  Input: {query, top_k?, country?, subject?, year?}
  Output: [{content, score, metadata, source}, ...]

POST /rag
  Input: {question, country?, subject?, year?}
  Output: {answer, sources, confidence}

POST /compare
  Input: {question, countries: [list]}
  Output: {results_by_country: {...}}

GET /info
  Returns: library statistics, available countries/subjects

GET /health
  Returns: server status, index size
```

**Example Usage:**
```bash
# Search
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cognitive development",
    "country": "USA",
    "top_k": 5
  }'

# RAG Query
curl -X POST "http://localhost:8000/rag" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main theories of memory?",
    "subject": "Cognitive Psychology"
  }'
```

**Deployment:**
```bash
# Local development
uvicorn api_server:app --reload --port 8000

# Production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_server:app --bind 0.0.0.0:8000
```

**Time Estimate:** 30 minutes

---

## 🎯 IMPLEMENTATION SEQUENCE

### Week 1 (This Week) - MVP
```
Day 1: Extract PDFs → ~30 min
Day 2: Chunk + Embed → ~60 min
Day 3: Index ChromaDB → ~20 min
Day 4: Retrieval + RAG → ~30 min
Day 5: API + Testing → ~40 min
───────────────────────────
Total: ~180 minutes (3 hours)
```

### Week 2 - Enhancements
```
- Advanced filtering (multi-country queries)
- Caching layer for speed
- Analytics dashboard
- Quality metrics
- Feedback loop
```

### Week 3+ - Production
```
- Frontend UI
- User authentication
- Usage monitoring
- Performance optimization
- Scaling infrastructure
```

---

## 💾 DATA FLOW & STORAGE

### Directory Structure:
```
/NEURO_MENTAL
├── /docs (279 PDFs) ← Source
├── /data
│   ├── master_mapping.json
│   ├── documents.json (Phase 1 output)
│   ├── chunks.json (Phase 2 output)
│   ├── embeddings.json (Phase 3 output)
│   └── chromadb/ (Phase 4 persistent store)
├── /scripts
│   ├── rag_pipeline/ (new folder)
│   │   ├── 1_extract_pdf_texts.py
│   │   ├── 2_chunk_documents.py
│   │   ├── 3_generate_embeddings.py
│   │   ├── 4_index_chromadb.py
│   │   ├── 5_retrieval_system.py
│   │   ├── 6_rag_generator.py
│   │   └── 7_api_server.py
│   ├── config.py
│   └── utils/
├── /models (embeddings cache)
└── /logs
```

---

## 🔧 CONFIGURATION & PARAMETERS

### Embedding Configuration
```python
MODEL_NAME = "all-MiniLM-L6-v2"        # 384 dims, 33M params
BATCH_SIZE = 100                        # Chunks per batch
EMBEDDING_DIM = 384
SIMILARITY_METRIC = "cosine"
```

### Chunking Configuration
```python
CHUNK_SIZE = 1000                       # Characters
CHUNK_OVERLAP = 100                     # 10% overlap
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]
```

### RAG Configuration
```python
TOP_K_RETRIEVAL = 5                     # Top results
SIMILARITY_THRESHOLD = 0.5              # Min relevance
LLM_MODEL = "gpt-4"                     # or gpt-3.5-turbo
LLM_TEMPERATURE = 0.7
MAX_CONTEXT_LENGTH = 2000               # Tokens
```

### ChromaDB Configuration
```python
CHROMA_DB_PATH = "./data/chromadb"
COLLECTION_NAME = "psychology_textbooks"
PERSIST = True
```

---

## 📈 EXPECTED PERFORMANCE

### Indexing Performance
```
PDF Processing:     ~50 minutes (279 PDFs)
Chunking:           ~5 minutes (50K chunks)
Embedding:          ~30-50 minutes (CPU) / ~10 min (GPU)
ChromaDB Index:     ~10 minutes
─────────────────────────────────────────
Total first run:    ~2-2.5 hours

Incremental:        ~10 minutes for new PDFs
```

### Query Performance
```
Embedding query:    ~100ms
ChromaDB search:    ~50-100ms
LLM generation:     ~2-5 seconds
─────────────────────────────────────────
Total RAG latency:  ~2.5-6 seconds per query
```

### Storage Requirements
```
Embeddings (50K × 384 dims × 4 bytes): ~77 MB
Chunks data:                             ~500 MB
ChromaDB index:                          ~100 MB
─────────────────────────────────────────
Total:                                   ~680 MB
```

---

## ✅ SUCCESS METRICS

### Indexing Quality
- [ ] 100% of PDFs successfully processed
- [ ] All chunks have metadata
- [ ] No corrupted embeddings
- [ ] Full-text search available

### Retrieval Quality
- [ ] Semantic search latency < 200ms
- [ ] Top-K precision > 0.85
- [ ] Country-filtered accuracy > 0.9
- [ ] Subject-filtered accuracy > 0.85

### RAG Quality
- [ ] Answer relevance > 0.8 (human eval)
- [ ] Citation accuracy > 0.95
- [ ] No hallucinations (verified)
- [ ] Context appropriateness > 0.8

### System Performance
- [ ] API response time < 5 seconds
- [ ] Concurrent queries: 10+ simultaneous
- [ ] Uptime: > 99.5%
- [ ] Zero data loss

---

## 🚀 QUICK START

**Command to begin implementation:**
```bash
cd C:\Users\admin\Desktop\desktop\NEURO_MENTAL
python scripts/rag_pipeline/1_extract_pdf_texts.py
```

**Monitor progress:**
```bash
# Watch indexing progress
tail -f logs/rag_pipeline.log

# Check ChromaDB status
python -c "import chromadb; db = chromadb.Client(); print(db.heartbeat())"
```

---

## 📞 SUPPORT & TROUBLESHOOTING

### Common Issues & Solutions

**Issue: PDF text extraction fails**
```
Solution: Some PDFs are scanned (image-based)
→ Install Tesseract OCR for optical character recognition
```

**Issue: OOM during embedding generation**
```
Solution: Use smaller batch size
→ Reduce BATCH_SIZE from 100 to 25
→ Process in smaller chunks
```

**Issue: ChromaDB permission errors**
```
Solution: Check directory permissions
→ mkdir -p data/chromadb
→ chmod 755 data/chromadb
```

---

## 📚 REFERENCES

**Required Libraries:** Already installed ✓
- langchain-core, langchain-community
- chromadb, chroma-hnswlib
- sentence-transformers
- openai
- torch, transformers
- pydantic, fastapi

**Training Resources:**
- Understand RAG: https://python.langchain.com/docs/use_cases/question_answering/
- ChromaDB docs: https://docs.trychroma.com/
- LangChain concepts: https://python.langchain.com/docs/concepts/

---

**Next Step:** Review this plan, confirm approach, and I'll create the 7 scripts for implementation.
