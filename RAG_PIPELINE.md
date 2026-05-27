# Neuronix RAG (Retrieval-Augmented Generation) Pipeline

## Overview

The `ingest_data.py` script implements a complete RAG pipeline for building Neuronix's medical knowledge base. It transforms downloaded PDFs into a searchable vector database using Google Gemini embeddings.

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           PHASE 1: Document Loading                         │
│  Scan /docs → Load PDFs with DirectoryLoader + PyPDFLoader  │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         PHASE 2: Intelligent Text Chunking                  │
│  Split with RecursiveCharacterTextSplitter                  │
│  Chunk Size: 1000 chars | Overlap: 200 chars                │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│     PHASE 3: Vector Database Initialization                 │
│           Initialize Chroma Vector Store                    │
│       Location: /data/vector_db                             │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│     PHASE 4: Chunk Ingestion with Metadata                  │
│  Convert text → vectors via Google Gemini Embeddings        │
│  Add metadata: source_file, country, status, chunk_index    │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│       PHASE 5: Verification & Testing                       │
│  Search for test queries (e.g., "Depression", "CBT")        │
│  Print top retrieval results to confirm working             │
└─────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### 1. Install Dependencies

Install all RAG pipeline dependencies:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install langchain-community==0.0.20
pip install langchain-google-genai==0.0.8
pip install google-generativeai==0.3.0
pip install pypdf==3.17.1
```

### 2. Get Google Gemini API Key

The pipeline uses Google Gemini embeddings. You need an API key:

1. **Go to** [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Click** "Create new API key"
3. **Copy** your API key

### 3. Set Environment Variable

Set your Google API key before running the script:

**Windows (PowerShell):**
```powershell
$env:GOOGLE_API_KEY = "your-api-key-here"
```

**Windows (Command Prompt):**
```cmd
set GOOGLE_API_KEY=your-api-key-here
```

**Linux/macOS:**
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

**Alternative: Create a `.env` file** (in root directory)
```
GOOGLE_API_KEY=your-api-key-here
```

Then load it in PowerShell:
```powershell
Get-Content .env | ForEach-Object {
    if ($_ -notmatch "^\s*$" -and $_ -notmatch "^#") {
        $name, $value = $_ -split "=", 2
        [System.Environment]::SetEnvironmentVariable($name, $value)
    }
}
```

## Running the Pipeline

### Basic Usage

```bash
cd scripts
python ingest_data.py
```

### Expected Output

The script produces comprehensive logs showing each phase:

```
################################################################################
# NEURONIX RAG DATA INGESTION PIPELINE
# Started: 2026-04-15 10:30:45
################################################################################

================================================================================
PHASE 1: Loading Documents
================================================================================
✓ Google Gemini Embeddings initialized
✓ Text splitter initialized (chunk_size=1000, overlap=200)
✓ Loaded master mapping with 15 countries
✓ Loaded 12 documents
  Sources: cognitive_psychology.pdf, depression_handbook.pdf, ...

================================================================================
PHASE 2: Creating Chunks
================================================================================
  ✓ cognitive_psychology.pdf: 45 chunks created
  ✓ depression_handbook.pdf: 38 chunks created
✓ Created 523 total chunks from 12 documents

================================================================================
PHASE 3: Initializing Vector Database
================================================================================
✓ Chroma vector database initialized at data/vector_db
  Embedding model: Google Gemini (embedding-001)
  Collection: neuronix_medical_kb

================================================================================
PHASE 4: Ingesting Chunks into Vector Store
================================================================================
  ✓ Stored batch 1: 50 chunks
  ✓ Stored batch 2: 50 chunks
  ...
✓ Total chunks stored: 523

================================================================================
PHASE 5: Verification - Testing Retrieval
================================================================================
Searching for: 'Depression'
Retrieving top 3 results...

──────────────────────────────────────────────────────────────────────────────
Result #1
──────────────────────────────────────────────────────────────────────────────
Source: depression_handbook.pdf
Country: Germany
Status: Free
Chunk: 2/38

Content (first 500 chars):
Depression is a complex mental health disorder characterized by persistent 
sadness, loss of interest in activities, and inability to perform daily tasks...

──────────────────────────────────────────────────────────────────────────────

✓ Retrieval verification successful!
  Found 3 relevant documents

================================================================================
INGESTION STATISTICS
================================================================================

Documents:
  PDFs Loaded: 12
  Documents Created: 12

Chunking:
  Text Chunks Created: 523
  Chunk Size: 1000 characters
  Chunk Overlap: 200 characters

Vector Store:
  Chunks Stored: 523
  Database Location: data/vector_db
  Embedding Model: Google Gemini

✓ No errors encountered

================================================================================
✓ Pipeline completed successfully!
================================================================================
```

### Log Files

The script creates detailed logging:

- **`scripts/ingest_log.txt`**: Complete pipeline execution log with debug information
- **`scripts/ingest_data.py`**: Returns exit code 0 on success, 1 on failure

## Data Flow Details

### Input Structure

```
/docs
├── India/
│   ├── cognitive_psychology.pdf
│   └── depression_handbook.pdf
├── Germany/
│   ├── modern_psychology.pdf
│   └── clinical_psychology.pdf
└── ... (other countries)
```

### Vector Store Output

```
/data/vector_db
├── chroma.sqlite
└── index/
│   └── (Chroma internal files)
```

### Metadata per Chunk

Each chunk stored includes:

```python
{
    "source_file": "depression_handbook.pdf",
    "country": "Germany",
    "status": 0,  # 0 = Free, 1 = Paid alternative
    "status_label": "Free",
    "chunk_index": 2,  # Which chunk in this document
    "total_chunks": 38,
    "page": 15,  # From PDF metadata
    "source": "path/to/depression_handbook.pdf"
}
```

## Code Structure

### NeuronixRAGPipeline Class

Main pipeline orchestrator with methods:

| Method | Purpose |
|--------|---------|
| `__init__()` | Initialize embeddings, text splitter, load mapping |
| `load_documents()` | Load PDFs from /docs directory |
| `create_chunks()` | Split documents with metadata enrichment |
| `initialize_database()` | Set up Chroma vector store |
| `ingest_chunks()` | Store vectors in database |
| `verify_retrieval()` | Test search functionality |
| `run_full_pipeline()` | Execute all phases end-to-end |

### Configuration Constants

```python
CHUNK_SIZE = 1000          # Characters per chunk
CHUNK_OVERLAP = 200        # Overlap between chunks
SEPARATORS = [             # Split on these boundaries first
    "\n\n",   # Paragraph breaks
    "\n",     # Line breaks
    " ",      # Word boundaries
    ""        # Character level
]
```

## Using the Vector Database

### Querying from Python

```python
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Initialize
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vector_store = Chroma(
    embedding_function=embeddings,
    persist_directory="data/vector_db",
    collection_name="neuronix_medical_kb"
)

# Search
query = "cognitive behavioral therapy for depression"
results = vector_store.similarity_search(query, k=5)

# Process results
for result in results:
    print(f"Country: {result.metadata['country']}")
    print(f"Source: {result.metadata['source_file']}")
    print(f"Content: {result.page_content}\n")
```

### Filtering by Metadata

```python
# Find only free resources from India
from langchain_community.vectorstores.chroma import Chroma

retriever = vector_store.as_retriever(
    search_kwargs={
        "k": 5,
        "filter": {
            "$and": [
                {"country": {"$eq": "India"}},
                {"status": {"$eq": 0}}
            ]
        }
    }
)

results = retriever.get_relevant_documents("Depression treatment")
```

## Chunking Strategy Explanation

### Why 1000 Characters?

- **Optimal length** for medical/psychology content
- **Preserves context**: Full paragraphs, complete concepts
- **GPU efficient**: Fits within Gemini embedding token limits
- **Granular enough**: Allows precise relevance matching

### Why 200 Character Overlap?

- **Maintains continuity**: Ensures sentence/concept completeness across chunk boundaries
- **Preserves relationships**: Clinical context spans across chunk boundaries
- **Improves search**: Overlapping regions increase chance of capturing relevant content
- **Reduces fragmentation**: Key medical concepts won't be split awkwardly

### Text Split Logic

Uses `RecursiveCharacterTextSplitter` which respects document structure:

1. **First attempt**: Split on `\n\n` (paragraphs)
2. **If too large**: Split on `\n` (lines)
3. **If still large**: Split on spaces (words)
4. **Last resort**: Split on characters

This preserves document structure and semantic meaning.

## Troubleshooting

### API Key Issues

**Error**: `ValueError: Google API key not found`

**Solution**: Ensure `GOOGLE_API_KEY` environment variable is set:
```powershell
$env:GOOGLE_API_KEY = "your-key"
Write-Host $env:GOOGLE_API_KEY  # Verify it's set
```

### PDF Loading Errors

**Error**: PDFs not found in /docs

**Solution**: Ensure PDFs are downloaded first:
```bash
python scripts/downloader.py
```

### Database Initialization Fails

**Error**: `sqlite3.OperationalError` or permission issues

**Solution**: 
1. Delete `/data/vector_db` folder
2. Ensure write permissions in `/data`
3. Run pipeline again

### Memory Issues with Large PDFs

**Error**: `MemoryError` or timeout during embedding

**Solution**:
1. Reduce `CHUNK_SIZE` to 500 characters
2. Process PDFs in smaller batches
3. Ensure sufficient system RAM

### Embedding Rate Limiting

**Error**: `google.api_core.exceptions.ResourceExhausted`

**Solution**: 
1. Add delay between chunks
2. Use smaller batch size
3. Check Google API quota

## Next Steps

1. **RAG Query System**: Create [scripts/query_rag.py](#) to search the vector database
2. **API Integration**: Expose RAG as FastAPI endpoint in [backend/](#)
3. **WebUI**: Build search interface in [frontend/](#)
4. **Evaluation**: Measure retrieval quality metrics
5. **Fine-tuning**: Adjust chunking strategy based on query performance

## Performance Metrics

Expected performance on standard hardware:

| Metric | Expected Value |
|--------|-----------------|
| Documents loaded/minute | 5-10 PDFs |
| Chunks created/second | 100-200 chunks |
| Embeddings generated/minute | 500-1000 chunks |
| Database query latency | 100-500ms |
| Search results retrieved | 0.5-2 seconds |

## Security Considerations

1. **API Key**: Never commit `.env` file or hardcode keys
2. **File Permissions**: Ensure `/data/vector_db` is not publicly accessible
3. **Content Filtering**: Implement access control for paid resources
4. **Data Retention**: Plan archival/deletion strategy for vector database

## References

- [LangChain Documentation](https://python.langchain.com/)
- [Chroma Vector Database](https://www.trychroma.com/)
- [Google Gemini API](https://ai.google.dev/)
- [RecursiveCharacterTextSplitter](https://python.langchain.com/en/latest/modules/indexes/text_splitters/examples/recursive_character_splitter.html)

---

**Last Updated**: April 15, 2026  
**Version**: 1.0  
**Status**: ✓ Production Ready
