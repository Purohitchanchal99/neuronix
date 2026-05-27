"""
Neuronix Constants and Configuration
====================================
Centralized configuration for Neuronix clinical AI system
- Embedding model consistency
- ChromaDB settings
- Ingestion parameters
- Monitoring thresholds
"""

from pathlib import Path

# ================================================================
# PATHS & DIRECTORIES
# ================================================================
BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / "docs"
DATA_DIR = BASE_DIR / "data"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
SCRIPTS_DIR = BASE_DIR / "scripts"
CHECKPOINTS_DIR = DATA_DIR / "checkpoints"

# Ensure directories exist
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

MAPPING_FILE = DATA_DIR / "master_mapping.json"
CHECKPOINT_FILE = DATA_DIR / "progress.txt"
MONITORING_LOG = SCRIPTS_DIR / "neuronix_monitoring.log"

# 🔥 FAILED FILES TRACKING (NEW)
FAILED_FILES_FILE = CHECKPOINTS_DIR / "failed_files.json"
FAILED_PDFS_DIR = DATA_DIR / "failed_pdfs"
FAILED_PDFS_DIR.mkdir(parents=True, exist_ok=True)

# ================================================================
# EMBEDDING MODEL (HUGGINGFACE) - CRITICAL: SAME FOR INGESTION & QUERY
# ================================================================
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 produces 384-dim embeddings

# ================================================================
# CHROMADB SETTINGS
# ================================================================
COLLECTION_NAME = "neuronix_medical_kb"
CHROMA_PERSIST_DIRECTORY = str(VECTOR_DB_DIR)

# ================================================================
# INGESTION PARAMETERS
# ================================================================
INGESTION_BATCH_SIZE = 10  # Process 10 PDFs at a time
CHUNK_SIZE = 1500  # 🔥 OPTIMIZED: Increased from 1000 → chunks ~40% less
CHUNK_OVERLAP = 100  # 🔥 OPTIMIZED: Reduced from 200 → faster processing
MIN_TEXT_LENGTH = 200  # 🔥 NEW: Skip pages < 200 chars (index, refs, blanks)
PDF_EXTENSIONS = [".pdf", ".PDF"]

# 🔥 METADATA ENRICHMENT (for future AI)
ENRICH_METADATA = True  # Enable enhanced metadata (page #, doc type, etc)
METADATA_FIELDS = ["source", "page", "doc_type", "country", "chunk_index", "total_chunks", "ingestion_time"]

# 🔥 HYBRID STORAGE (scalable architecture)
USE_HYBRID_COLLECTIONS = False  # Enable separate collections per category
COLLECTION_STRATEGY = "single"  # "single" or "hybrid"
# Hybrid collections: psychology_books, medical_books, india_specific, etc
HYBRID_COLLECTIONS = {
    "medical_books": "neuronix_medical_kb",
    "psychology": "neuronix_psychology_kb",
    "india_specific": "neuronix_india_kb",
    "other": "neuronix_general_kb"
}

# 🔥 PARALLEL PROCESSING (future upgrade)
USE_PARALLEL_PROCESSING = False  # Enable multi-threaded PDF processing
MAX_WORKERS = 4  # Number of threads for parallel processing

# ================================================================
# QUERY PARAMETERS
# ================================================================
RETRIEVAL_K_MIN = 5  # Minimum chunks to retrieve
RETRIEVAL_K_MAX = 8  # Maximum chunks to retrieve
QUERY_DEFAULT_K = 6  # Default: retrieve 6 chunks

# ================================================================
# LLM SETTINGS (GEMINI)
# ================================================================
LLM_MODEL = "gemini-pro"
LLM_TEMPERATURE = 0.7
LLM_TOP_P = 0.8
LLM_TOP_K = 40

# ================================================================
# MONITORING & LOGGING
# ================================================================
MONITORING_INTERVAL_SECONDS = 120  # Report every 2 minutes
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ================================================================
# FALLBACK MESSAGES (HINGLISH)
# ================================================================
INSUFFICIENT_CONTEXT_MSG = "Yeh information abhi mere paas complete nahi hai."
NO_RESULTS_MSG = "Maaf kijiye, main is prashna ka jawab nahi de pa raha hoon."
ERROR_MSG = "Kuch problem aayi. Baad mein koshish kijiye."

# ================================================================
# DATABASE PARAMETERS
# ================================================================
MAX_RETRIES_PDF = 3  # Retry corrupted PDFs up to 3 times
SKIP_ON_ERROR = True  # Skip corrupted PDFs instead of failing

# 🔥 DOCUMENT TYPE DETECTION
DOC_TYPE_MAPPING = {
    "psychology": ["psychology", "behavioral", "mental"],
    "medical": ["medicine", "medical", "clinical", "disease", "treatment"],
    "neurology": ["neurology", "brain", "nervous", "seizure"],
    "india": ["india", "indian", "hindi"],
    "general": []  # Fallback
}
