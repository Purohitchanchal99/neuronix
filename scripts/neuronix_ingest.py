"""
Neuronix Ingestion Pipeline
===========================
Production-grade PDF ingestion with HuggingFace embeddings

Features:
- HuggingFace embeddings (sentence-transformers/all-MiniLM-L6-v2)
- Batch processing (size: 10 PDFs)
- Checkpoint saving after each batch
- Automatic corruption handling (skip on error)
- Real-time monitoring (2-minute intervals)
- Incremental storage in ChromaDB
"""

import sys
import os
import json
import logging
import time
import tempfile
import shutil
import gc
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set
from threading import Thread, Event

# Windows compatibility
if sys.platform == "win32":
    import types
    pwd_module = types.ModuleType('pwd')
    sys.modules['pwd'] = pwd_module

from langchain_core.documents import Document
from dotenv import load_dotenv
load_dotenv()

from neuronix_constants import (
    EMBEDDING_MODEL, COLLECTION_NAME, CHROMA_PERSIST_DIRECTORY,
    INGESTION_BATCH_SIZE, CHUNK_SIZE, CHUNK_OVERLAP, DOCS_DIR,
    VECTOR_DB_DIR, CHECKPOINT_FILE, MONITORING_INTERVAL_SECONDS,
    LOG_FORMAT, MAX_RETRIES_PDF, SKIP_ON_ERROR, MAPPING_FILE,
    MONITORING_LOG, FAILED_FILES_FILE, FAILED_PDFS_DIR,
    MIN_TEXT_LENGTH, ENRICH_METADATA, METADATA_FIELDS,
    USE_HYBRID_COLLECTIONS, COLLECTION_STRATEGY, HYBRID_COLLECTIONS,
    USE_PARALLEL_PROCESSING, MAX_WORKERS, DOC_TYPE_MAPPING
)

# ================================================================
# LOGGING CONFIGURATION
# ================================================================
BASE_DIR = Path(__file__).parent.parent  # Parent of scripts/ dir

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'neuronix_ingest.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

monitoring_logger = logging.getLogger('neuronix_monitor')
monitoring_logger.addHandler(logging.FileHandler(MONITORING_LOG, encoding='utf-8'))
monitoring_logger.addHandler(logging.StreamHandler())
monitoring_logger.setLevel(logging.INFO)


def simple_text_split(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP, min_length: int = MIN_TEXT_LENGTH) -> List[str]:
    """
    🔥 OPTIMIZED: Split text into overlapping chunks with filtering
    
    Args:
        text: Text to split
        chunk_size: Size of each chunk (default 1500)
        overlap: Overlap between chunks (default 100)
        min_length: Skip pages < 200 chars (filters index, refs, blanks)
    
    Returns:
        List of valid chunks (useless pages removed)
    """
    if not text or not text.strip():
        return []
    
    # 🔥 FILTER: Skip short pages (index, references, blank pages, etc)
    if len(text.strip()) < min_length:
        logger.debug(f"⏭️  Skipping short text ({len(text)} chars < {min_length})")
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        
        # 🔥 FILTER: Only add chunks with meaningful content
        if len(chunk) >= min_length:
            chunks.append(chunk)
        
        start += chunk_size - overlap
    
    return chunks


def detect_document_type(pdf_name: str) -> str:
    """
    🔥 DETECT: Identify document type from filename
    
    Returns: Type like 'medical', 'psychology', 'neurology', 'india', 'general'
    """
    from neuronix_constants import DOC_TYPE_MAPPING
    
    name_lower = pdf_name.lower()
    
    for doc_type, keywords in DOC_TYPE_MAPPING.items():
        for keyword in keywords:
            if keyword in name_lower:
                return doc_type
    
    return "general"


def create_enhanced_metadata(pdf_path: Path, chunk_index: int, total_chunks: int, page_number: int = 0) -> Dict:
    """
    🔥 METADATA: Create enriched metadata for advanced RAG
    
    Enables:
    - Future filtering by document type
    - Country-wise knowledge queries  
    - Smart RAG with metadata-aware retrieval
    """
    doc_type = detect_document_type(pdf_path.name)
    
    return {
        'source': pdf_path.name,
        'file_path': str(pdf_path),
        'chunk_index': chunk_index,
        'total_chunks': total_chunks,
        'page': page_number,
        'doc_type': doc_type,
        'country': _extract_country(pdf_path),
        'ingestion_time': datetime.now().isoformat(),
        'chunk_size': CHUNK_SIZE,
        'overlap': CHUNK_OVERLAP
    }


def _extract_country(pdf_path: Path) -> str:
    """Extract country from file path"""
    try:
        parts = pdf_path.parts
        if 'docs' in parts:
            idx = parts.index('docs')
            if idx + 1 < len(parts):
                return parts[idx + 1].replace('_', ' ').title()
    except:
        pass
    return "Unknown"


def retry_with_exponential_backoff(func, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 30.0):
    """
    🔥 PRODUCTION RETRY: Retry with exponential backoff
    
    Args:
        func: Callable to retry
        max_retries: Maximum retry attempts
        base_delay: Starting delay in seconds
        max_delay: Maximum delay cap
    
    Returns:
        Result of func() if successful
        
    Raises:
        Exception: If all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(f"  ⚠️  Attempt {attempt + 1} failed, retrying in {delay:.1f}s... ({type(e).__name__}: {str(e)[:50]})")
                time.sleep(delay)
            else:
                logger.error(f"  ❌ All {max_retries + 1} attempts failed for DB operation")
    
    raise last_exception


class NeuronixIngestion:
    """Neuronix ingestion pipeline with HuggingFace embeddings"""
    
    def __init__(self):
        """Initialize with HuggingFace embeddings"""
        logger.info("🚀 Initializing Neuronix Ingestion Engine...")
        
        try:
            # Import and initialize HuggingFace embeddings
            from langchain_huggingface import HuggingFaceEmbeddings
            from langchain_chroma import Chroma
            
            self.HuggingFaceEmbeddings = HuggingFaceEmbeddings
            self.Chroma = Chroma
            
            # Set up cache folder for HuggingFace models
            cache_folder = BASE_DIR / "hf_cache"
            cache_folder.mkdir(parents=True, exist_ok=True)
            
            # Initialize embeddings - CRITICAL: Same model for query system
            logger.info(f"📦 Loading HuggingFace model: {EMBEDDING_MODEL}")
            logger.info(f"   Cache folder: {cache_folder}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                cache_folder=str(cache_folder),
                model_kwargs={"device": "cpu", "trust_remote_code": True}  # or "cuda" if GPU available
            )
            logger.info(f"✅ HuggingFace Embeddings ready (384-dim, cached)")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
        
        # Statistics for monitoring
        self.stats = {
            'pdfs_processed': 0,
            'pdfs_failed': 0,
            'chunks_created': 0,
            'embeddings_stored': 0,
            'errors': [],
            'start_time': None,
            'batch_times': []
        }
        
        self.vector_store = None
        self.monitoring_stop_event = None
    
    def get_all_pdfs(self) -> List[Path]:
        """Get all PDF files from docs directory"""
        if not DOCS_DIR.exists():
            logger.error(f"📁 Docs directory not found: {DOCS_DIR}")
            return []
        
        pdfs = list(DOCS_DIR.rglob("*.pdf"))
        logger.info(f"📚 Found {len(pdfs)} PDFs to process")
        
        return sorted(pdfs)
    
    def load_pdf_text(self, pdf_path: Path, retry_count: int = 0) -> Optional[str]:
        """
        Load text from PDF with retry mechanism
        
        Args:
            pdf_path: Path to PDF file
            retry_count: Current retry attempt
            
        Returns:
            Extracted text or None if failed
        """
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(str(pdf_path))
            text = ""
            
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
            
            if not text or not text.strip():
                logger.warning(f"⚠️  {pdf_path.name}: No text extracted")
                return None
            
            return text
            
        except Exception as e:
            if retry_count < MAX_RETRIES_PDF:
                logger.warning(f"⚠️  Retry {retry_count + 1}/{MAX_RETRIES_PDF} for {pdf_path.name}")
                return self.load_pdf_text(pdf_path, retry_count + 1)
            
            logger.error(f"❌ Failed to read {pdf_path.name}: {e}")
            self.stats['errors'].append(f"PDF read error: {pdf_path.name} - {str(e)[:50]}")
            self.stats['pdfs_failed'] += 1
            
            return None if SKIP_ON_ERROR else False
    
    def initialize_vector_store(self):
        """Initialize ChromaDB vector store"""
        try:
            logger.info(f"🗄️  Initializing ChromaDB vector store...")
            logger.info(f"   Model: {EMBEDDING_MODEL}")
            logger.info(f"   Collection: {COLLECTION_NAME}")
            logger.info(f"   Location: {VECTOR_DB_DIR}")
            
            VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
            
            self.vector_store = self.Chroma(
                collection_name=COLLECTION_NAME,
                persist_directory=str(VECTOR_DB_DIR),
                embedding_function=self.embeddings
            )
            
            logger.info(f"✅ ChromaDB initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Vector store initialization failed: {e}")
            raise
    
    def load_checkpoint(self) -> Dict:
        """Load progress checkpoint with batch and PDF-level tracking"""
        try:
            if CHECKPOINT_FILE.exists():
                with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                logger.info(f"📥 Checkpoint loaded: Batch {checkpoint.get('last_completed_batch', 0)} | {len(checkpoint.get('processed_files', []))} PDFs already processed")
                return checkpoint
        except Exception as e:
            logger.warning(f"⚠️  Could not load checkpoint: {e}")
        
        # Return default checkpoint structure
        return {
            "last_completed_batch": 0,
            "processed_files": [],
            "pdfs_processed": 0,
            "chunks_created": 0,
            "embeddings_stored": 0,
            "pdfs_failed": 0
        }

    def load_checkpoint_safe(self) -> Dict:
        """
        PRODUCTION SAFE: Load checkpoint with guaranteed safe defaults
        
        Ensures ALL keys exist with proper defaults — no KeyError possible
        ✅ Handles corrupted checkpoints
        ✅ Handles old format migration
        ✅ Handles missing keys
        """
        checkpoint = self.load_checkpoint()
        
        # 🧠 FULL SAFE DEFAULT STRUCTURE
        safe_checkpoint = {
            "last_completed_batch": 0,
            "processed_files": [],
            "pdfs_processed": 0,
            "chunks_created": 0,
            "embeddings_stored": 0,
            "pdfs_failed": 0
        }
        
        if not checkpoint:
            logger.info("📋 Using fresh checkpoint defaults")
            return safe_checkpoint
        
        # 🔥 Merge old + new safely — only take valid values
        for key in safe_checkpoint:
            value = checkpoint.get(key, safe_checkpoint[key])
            # Validate types
            if key == "processed_files":
                if isinstance(value, list):
                    safe_checkpoint[key] = value
                else:
                    safe_checkpoint[key] = []
            elif key in ["last_completed_batch", "pdfs_processed", "chunks_created", "embeddings_stored", "pdfs_failed"]:
                if isinstance(value, int):
                    safe_checkpoint[key] = value
                else:
                    safe_checkpoint[key] = safe_checkpoint[key]
            else:
                safe_checkpoint[key] = value
        
        return safe_checkpoint

    def load_failed_files(self) -> Dict[str, dict]:
        """Load dict of PDFs that failed to process with error details and retry count"""
        try:
            if FAILED_FILES_FILE.exists():
                with open(FAILED_FILES_FILE, 'r', encoding='utf-8') as f:
                    failed = json.load(f)
                    
                    # Handle backward compatibility: convert old list format to dict
                    if isinstance(failed, list):
                        failed_dict = {}
                        for item in failed:
                            if isinstance(item, dict):
                                # Already new format
                                failed_dict[item.get('file')] = item
                            else:
                                # Old format (string)
                                failed_dict[item] = {
                                    'file': item,
                                    'error': 'unknown',
                                    'time': datetime.now().isoformat(),
                                    'retries': 0
                                }
                        failed = failed_dict
                    
                    count = len(failed)
                    if count > 0:
                        logger.info(f"⚠️  Loaded {count} previously failed PDFs")
                    return failed
        except Exception as e:
            logger.warning(f"⚠️  Could not load failed files: {e}")
        return {}

    def save_failed_files(self, failed_files: Dict[str, dict]):
        """Save dict of failed PDFs with error tracking and retry counter (atomic write)"""
        try:
            # Sort by file name for consistent output
            failed_list = [failed_files[key] for key in sorted(failed_files.keys())]
            
            FAILED_FILES_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Atomic write
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=FAILED_FILES_FILE.parent,
                delete=False,
                suffix='.tmp',
                encoding='utf-8'
            ) as tmp_file:
                json.dump(failed_list, tmp_file, indent=2)
                temp_name = tmp_file.name
            
            os.replace(temp_name, FAILED_FILES_FILE)
            
            if len(failed_list) > 0:
                logger.info(f"⚠️  Saved {len(failed_list)} failed PDFs to tracking file")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not save failed files: {e}")
            try:
                if 'temp_name' in locals() and os.path.exists(temp_name):
                    os.remove(temp_name)
            except:
                pass

    def copy_failed_pdf_to_debug_folder(self, pdf_path: Path):
        """Copy failed PDF to debug folder for inspection"""
        try:
            if not FAILED_PDFS_DIR.exists():
                FAILED_PDFS_DIR.mkdir(parents=True, exist_ok=True)
            
            dest_path = FAILED_PDFS_DIR / pdf_path.name
            shutil.copy2(pdf_path, dest_path)
            logger.info(f"  📋 Copied to: {dest_path}")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not copy failed PDF: {e}")

    def save_checkpoint(self, batch_num: int, total_batches: int, processed_files: List[str]):
        """Save progress checkpoint with PDF tracking (2-layer resume, atomic writes)"""
        try:
            checkpoint_data = {
                'timestamp': datetime.now().isoformat(),
                'last_completed_batch': batch_num,
                'total_batches': total_batches,
                'processed_files': processed_files,  # 🔥 Layer 2: Track individual PDFs
                'pdfs_processed': self.stats['pdfs_processed'],
                'chunks_created': self.stats['chunks_created'],
                'embeddings_stored': self.stats['embeddings_stored'],
                'pdfs_failed': self.stats['pdfs_failed']
            }
            
            # 🔥 ATOMIC WRITE: Use tempfile + atomic rename
            checkpoint_dir = CHECKPOINT_FILE.parent
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file in same directory
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=checkpoint_dir,
                delete=False,
                suffix='.tmp',
                encoding='utf-8'
            ) as tmp_file:
                json.dump(checkpoint_data, tmp_file, indent=2)
                temp_name = tmp_file.name
            
            # Atomic rename
            os.replace(temp_name, CHECKPOINT_FILE)
            
            logger.info(f"💾 Checkpoint saved (atomic): Batch {batch_num}/{total_batches} | {len(processed_files)} PDFs tracked")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not save checkpoint: {e}")
            # Clean up temp file if it exists
            try:
                if 'temp_name' in locals() and os.path.exists(temp_name):
                    os.remove(temp_name)
            except:
                pass
    
    def process_pdf_batch(self, pdf_paths: List[Path], batch_num: int, processed_files: set, failed_files: Dict[str, dict] = None) -> tuple:
        """
        Process a batch of PDFs with PDF-level checkpoint saving and failure tracking
        
        Args:
            pdf_paths: List of PDF paths to process
            batch_num: Current batch number
            processed_files: Set of already-processed PDF paths
            failed_files: Dict of PDFs that failed to process with error details
        
        Returns:
            Tuple of (docs_added, updated_processed_files_set, updated_failed_files_dict)
        """
        if failed_files is None:
            failed_files = {}
        
        batch_start = time.time()
        skipped_in_batch = 0
        batch_successful = 0
        docs_added = 0
        logger.info(f"\n📦 BATCH {batch_num}: Processing {len(pdf_paths)} PDFs...")
        
        for pdf_path in pdf_paths:
            pdf_str = str(pdf_path)
            
            # 🔥 RETRY LIMIT: Skip if already retried 3+ times
            if pdf_str in failed_files:
                retry_count = failed_files[pdf_str].get('retries', 0)
                if retry_count >= MAX_RETRIES_PDF:
                    logger.info(f"  🚫 SKIP: {pdf_path.name} (max retries reached: {retry_count})")
                    skipped_in_batch += 1
                    continue
            
            # 🔥 LAYER 2: Skip already-processed PDFs
            if pdf_str in processed_files:
                logger.info(f"  ⏭️  SKIP: {pdf_path.name} (already processed)")
                skipped_in_batch += 1
                continue
            
            try:
                # Load PDF text
                text = self.load_pdf_text(pdf_path)
                if not text:
                    logger.warning(f"  ⚠️  {pdf_path.name}: Failed to extract text")
                    self.stats['pdfs_failed'] += 1
                    failed_files[pdf_str] = {
                        'file': pdf_path.name,
                        'error': 'text extraction failed',
                        'time': datetime.now().isoformat(),
                        'retries': failed_files.get(pdf_str, {}).get('retries', 0) + 1
                    }
                    self.copy_failed_pdf_to_debug_folder(pdf_path)
                    continue
                
                # Create chunks
                chunks = simple_text_split(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
                
                if not chunks:
                    logger.warning(f"  ⚠️  {pdf_path.name}: No chunks created")
                    failed_files[pdf_str] = {
                        'file': pdf_path.name,
                        'error': 'no chunks created',
                        'time': datetime.now().isoformat(),
                        'retries': failed_files.get(pdf_str, {}).get('retries', 0) + 1
                    }
                    self.copy_failed_pdf_to_debug_folder(pdf_path)
                    continue
                
                # Track statistics
                self.stats['pdfs_processed'] += 1
                self.stats['chunks_created'] += len(chunks)
                batch_successful += 1
                
                # Create Document objects with metadata and unique IDs
                documents = []
                chunk_ids = []
                for i, chunk in enumerate(chunks):
                    # 🔥 UNIQUE CHUNK ID: Prevents duplicates on crash mid-insert
                    chunk_id = f"{pdf_path.stem}_{i}_{hash(chunk[:50]) % 100000}"
                    chunk_ids.append(chunk_id)
                    
                    # 🔥 ENHANCED METADATA: Rich metadata for advanced RAG
                    enhanced_metadata = create_enhanced_metadata(
                        pdf_path, 
                        chunk_index=i,
                        total_chunks=len(chunks),
                        page_number=0  # Can be enhanced to track actual page numbers
                    )
                    
                    doc = Document(
                        page_content=chunk,
                        metadata=enhanced_metadata
                    )
                    documents.append(doc)
                
                # Store this PDF's chunks in ChromaDB
                try:
                    logger.info(f"  💾 Storing {len(documents)} chunks for {pdf_path.name}...")
                    
                    # Process in 500-chunk sub-batches with unique IDs
                    CHUNK_BATCH_SIZE = 500
                    for i in range(0, len(documents), CHUNK_BATCH_SIZE):
                        chunk_batch = documents[i:i+CHUNK_BATCH_SIZE]
                        batch_ids = chunk_ids[i:i+CHUNK_BATCH_SIZE]
                        
                        # 🔥 PRODUCTION RETRY: Retry with exponential backoff on DB failure
                        def store_batch():
                            self.vector_store.add_documents(chunk_batch, ids=batch_ids)
                        
                        try:
                            retry_with_exponential_backoff(store_batch, max_retries=3)
                            docs_added += len(chunk_batch)
                            self.stats['embeddings_stored'] += len(chunk_batch)
                        except Exception as db_error:
                            logger.error(f"  ❌ DB storage failed for batch {i//CHUNK_BATCH_SIZE + 1}: {db_error}")
                            raise
                        
                        # 🔥 MEMORY: Clean up garbage after each sub-batch
                        gc.collect()
                    
                    # 🔥 CRITICAL: Persist DB after each PDF (prevents corruption on crash)
                    try:
                        logger.info(f"  💾 Persisting DB after {pdf_path.name}...")
                        self.vector_store._client.persist() if hasattr(self.vector_store, '_client') else None
                    except Exception as persist_err:
                        logger.warning(f"  ⚠️  Persist warning (non-critical): {persist_err}")
                    
                    # 🔥 HARDENED: Mark as processed ONLY after successful storage
                    processed_files.add(pdf_str)
                    
                    # 🔥 Remove from failed list if it was there
                    if pdf_str in failed_files:
                        failed_files.pop(pdf_str)
                    
                    logger.info(f"  ✅ Done: {pdf_path.name} ({len(chunks)} chunks)")
                    
                    # 🔥 SAVE CHECKPOINT AFTER EACH PDF (atomic write!)
                    checkpoint_files = [str(p) for p in sorted(processed_files)]
                    total_batches = getattr(self, 'total_batches', batch_num)
                    self._save_checkpoint_atomic(batch_num, total_batches, checkpoint_files)
                    self.save_failed_files(failed_files)
                    
                    # 🔥 CPU COOLING: Small delay to prevent overheating
                    time.sleep(0.05)
                
                except Exception as e:
                    logger.error(f"  ❌ Storage error for {pdf_path.name}: {e}")
                    self.stats['errors'].append(f"Storage error: {pdf_path.name}")
                    failed_files[pdf_str] = {
                        'file': pdf_path.name,
                        'error': f'storage error: {str(e)[:50]}',
                        'time': datetime.now().isoformat(),
                        'retries': failed_files.get(pdf_str, {}).get('retries', 0) + 1
                    }
                    self.copy_failed_pdf_to_debug_folder(pdf_path)
                    self.save_failed_files(failed_files)
                    # DO NOT mark as processed on storage failure
                    if not SKIP_ON_ERROR:
                        raise
                    # Still sleep on error
                    time.sleep(0.05)
                
            except Exception as e:
                logger.error(f"  ❌ Error processing {pdf_path.name}: {e}")
                self.stats['errors'].append(f"PDF error: {pdf_path.name}")
                self.stats['pdfs_failed'] += 1
                failed_files[pdf_str] = {
                    'file': pdf_path.name,
                    'error': f'processing error: {str(e)[:50]}',
                    'time': datetime.now().isoformat(),
                    'retries': failed_files.get(pdf_str, {}).get('retries', 0) + 1
                }
                self.copy_failed_pdf_to_debug_folder(pdf_path)
                self.save_failed_files(failed_files)
                if not SKIP_ON_ERROR:
                    raise
                # Still sleep on error
                time.sleep(0.05)
        
        # Measure batch time
        batch_time = time.time() - batch_start
        self.stats['batch_times'].append(batch_time)
        
        logger.info(f"  📊 Batch {batch_num} summary: {batch_successful} processed, {skipped_in_batch} skipped, {docs_added} chunks stored, {len(failed_files)} failed")
        
        return docs_added, processed_files, failed_files
    
    def _save_checkpoint_atomic(self, batch_num: int, total_batches: int, processed_files: List[str]):
        """
        Atomic checkpoint save using temporary file (HARDENED)
        
        This prevents checkpoint corruption if write fails midway.
        Uses atomic rename to ensure consistency.
        """
        try:
            checkpoint_data = {
                'timestamp': datetime.now().isoformat(),
                'last_completed_batch': batch_num,
                'total_batches': total_batches if total_batches > 0 else batch_num,
                'processed_files': processed_files,
                'pdfs_processed': self.stats['pdfs_processed'],
                'chunks_created': self.stats['chunks_created'],
                'embeddings_stored': self.stats['embeddings_stored'],
                'pdfs_failed': self.stats['pdfs_failed']
            }
            
            # 🔥 ATOMIC WRITE: Use tempfile + atomic rename
            checkpoint_dir = CHECKPOINT_FILE.parent
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file in same directory (same filesystem for atomic rename)
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=checkpoint_dir,
                delete=False,
                suffix='.tmp',
                encoding='utf-8'
            ) as tmp_file:
                json.dump(checkpoint_data, tmp_file, indent=2)
                temp_name = tmp_file.name
            
            # Atomic rename (no corruption possible now)
            os.replace(temp_name, CHECKPOINT_FILE)
            
        except Exception as e:
            logger.warning(f"⚠️  Could not save checkpoint atomically: {e}")
            # Clean up temp file if it exists
            try:
                if 'temp_name' in locals() and os.path.exists(temp_name):
                    os.remove(temp_name)
            except:
                pass
    
    def _save_checkpoint_internal(self, batch_num: int, total_batches: int, processed_files: List[str]):
        """Deprecated: Use _save_checkpoint_atomic instead"""
        self._save_checkpoint_atomic(batch_num, total_batches, processed_files)
    
    def monitoring_thread(self, stop_event: Event):
        """Monitor and report progress every 2 minutes"""
        logger.info("📊 Monitoring thread started (reports every 2 minutes)")
        
        while not stop_event.is_set():
            try:
                elapsed = time.time() - self.stats['start_time']
                
                # 🔥 MEMORY: Force garbage collection every 2 minutes
                gc.collect()
                
                monitoring_logger.info(
                    f"PDFs: {self.stats['pdfs_processed']} | "
                    f"Chunks: {self.stats['chunks_created']:,} | "
                    f"Embeddings: {self.stats['embeddings_stored']:,} | "
                    f"Failed: {self.stats['pdfs_failed']} | "
                    f"Time: {elapsed:.0f}s"
                )
                
                # Wait 2 minutes or until stop event
                stop_event.wait(MONITORING_INTERVAL_SECONDS)
                
            except Exception as e:
                logger.warning(f"⚠️  Monitoring error: {e}")
    
    def run(self):
        """Run the complete ingestion pipeline with 2-layer resume"""
        logger.info("\n" + "="*80)
        logger.info("🧠 NEURONIX INGESTION PIPELINE (2-Layer Resume System)")
        logger.info("="*80)
        logger.info(f"   Embedding Model: {EMBEDDING_MODEL}")
        logger.info(f"   Batch Size: {INGESTION_BATCH_SIZE} PDFs")
        logger.info(f"   Chunk Size: {CHUNK_SIZE} chars (🔥 optimized), Overlap: {CHUNK_OVERLAP}")
        logger.info(f"   Min Text Length: {MIN_TEXT_LENGTH} chars (filters index/refs/blanks)")
        logger.info(f"   Enhanced Metadata: {ENRICH_METADATA} (doc_type, country, page)")
        logger.info(f"   Parallel Processing: {USE_PARALLEL_PROCESSING} (workers: {MAX_WORKERS})")
        logger.info("="*80 + "\n")
        
        self.stats['start_time'] = time.time()
        
        try:
            # Get PDFs
            pdf_list = self.get_all_pdfs()
            if not pdf_list:
                logger.error("❌ No PDFs found in docs directory")
                return False
            
            # Initialize vector store
            self.initialize_vector_store()
            
            # Start monitoring thread
            self.monitoring_stop_event = Event()
            monitor = Thread(target=self.monitoring_thread, args=(self.monitoring_stop_event,), daemon=True)
            monitor.start()
            
            # Process PDFs in batches
            total_batches = (len(pdf_list) + INGESTION_BATCH_SIZE - 1) // INGESTION_BATCH_SIZE
            
            # Load checkpoint with 2-layer resume (PRODUCTION SAFE VERSION)
            checkpoint = self.load_checkpoint_safe()
            
            # 🔥 DEBUG PRINT: Verify checkpoint_safe is actually being used
            print(f"\n[DEBUG] CHECKPOINT: {checkpoint}\n")
            
            # 🔥 SAFE EXTRACTION: All keys guaranteed to exist with proper types
            last_batch = checkpoint.get("last_completed_batch", 0)
            processed_files = set(checkpoint.get("processed_files", []))
            start_batch = last_batch + 1
            
            # Log checkpoint status
            logger.info(f"📥 Checkpoint loaded: Batch {last_batch} | {len(processed_files)} PDFs already processed")
            
            # 🔥 Load failed files tracking
            failed_files = self.load_failed_files()
            
            if start_batch > total_batches:
                logger.info(f"✅ All batches already completed! (Total: {total_batches})")
                self.monitoring_stop_event.set()
                monitor.join(timeout=1)
                return True
            
            if start_batch > 1:
                logger.info(f"▶️  Resuming from Batch {start_batch}/{total_batches}")
            
            # Process batches
            for batch_num in range(start_batch, total_batches + 1):
                start_idx = (batch_num - 1) * INGESTION_BATCH_SIZE
                end_idx = min(start_idx + INGESTION_BATCH_SIZE, len(pdf_list))
                batch = pdf_list[start_idx:end_idx]
                
                # Update total_batches in instance for checkpoint saving
                self.total_batches = total_batches
                
                try:
                    logger.info(f"\n📦 BATCH {batch_num}: Processing {len(batch)} PDFs...")
                    # Process batch with PDF-level tracking (Layer 2) and failed files
                    docs_added, processed_files, failed_files = self.process_pdf_batch(batch, batch_num, processed_files, failed_files)
                    
                    # Save checkpoint after each batch with processed files list
                    checkpoint_files = [str(p) for p in sorted(processed_files)]
                    self.save_checkpoint(batch_num, total_batches, checkpoint_files)
                    self.save_failed_files(failed_files)
                    
                except Exception as batch_error:
                    logger.error(f"[ERROR] Batch {batch_num} failed: {batch_error}")
                    print(f"[ERROR] BATCH ERROR TRACEBACK:", batch_error)
                    import traceback
                    traceback.print_exc()
                    raise
            
            # Stop monitoring
            self.monitoring_stop_event.set()
            monitor.join(timeout=1)
            
            # 🔥 CRITICAL: Final persistence flush (atomic snapshot)
            try:
                logger.info("💾 Final DB persistence flush...")
                self.vector_store._client.persist() if hasattr(self.vector_store, '_client') else None
                logger.info("✅ Final persistence complete")
            except Exception as persist_err:
                logger.warning(f"⚠️  Final persist warning (non-critical): {persist_err}")
            
            # 🔥 FINAL MEMORY CLEANUP
            gc.collect()
            
            # Final report
            elapsed = time.time() - self.stats['start_time']
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            avg_batch_time = sum(self.stats['batch_times']) / len(self.stats['batch_times']) if self.stats['batch_times'] else 0
            
            logger.info("\n" + "="*80)
            logger.info("✅ INGESTION COMPLETE!")
            logger.info("="*80)
            logger.info(f"\n📊 FINAL STATISTICS:")
            logger.info(f"   PDFs Processed:     {self.stats['pdfs_processed']}/{len(pdf_list)}")
            logger.info(f"   PDFs Failed:        {self.stats['pdfs_failed']}")
            logger.info(f"   Total Chunks:       {self.stats['chunks_created']:,}")
            logger.info(f"   Embeddings Stored:  {self.stats['embeddings_stored']:,}")
            logger.info(f"   Total Time:         {minutes}m {seconds}s")
            logger.info(f"   Avg Batch Time:     {avg_batch_time:.2f}s")
            
            if self.stats['errors']:
                logger.info(f"\n⚠️  Errors ({len(self.stats['errors'])}):")
                for error in self.stats['errors'][:10]:
                    logger.info(f"      • {error}")
                if len(self.stats['errors']) > 10:
                    logger.info(f"      ... and {len(self.stats['errors']) - 10} more")
            
            logger.info(f"\n✅ {self.stats['embeddings_stored']:,} embeddings generated.")
            logger.info(f"✅ Vector database ready for queries!")
            logger.info("="*80 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"\n[ERROR] Pipeline failed: {e}")
            print(f"\n[ERROR] FULL ERROR TRACEBACK:")
            import traceback
            traceback.print_exc()
            if self.monitoring_stop_event:
                self.monitoring_stop_event.set()
            return False
    
    def retry_failed_pdfs(self):
        """
        Retry processing of previously failed PDFs (RECOVERY SYSTEM)
        
        🔁 Filters out already-processed files and retries only failed ones
        """
        logger.info("\n" + "="*80)
        logger.info("🔁 RETRY SYSTEM: Processing previously failed PDFs")
        logger.info("="*80 + "\n")
        
        self.stats['start_time'] = time.time()
        
        try:
            # Load current state (PRODUCTION SAFE)
            checkpoint = self.load_checkpoint_safe()
            processed_files = set(checkpoint.get('processed_files', []))
            failed_files = self.load_failed_files()
            
            if not failed_files:
                logger.info("✅ No failed PDFs to retry!")
                return True
            
            logger.info(f"🔁 Retrying {len(failed_files)} failed PDFs")
            logger.info(f"   (Already processed: {len(processed_files)})\n")
            
            # Initialize vector store
            self.initialize_vector_store()
            
            # Process failed PDFs one by one
            recovered = 0
            still_failing = 0
            skipped_retry_limit = 0
            
            for pdf_str, fail_info in list(failed_files.items()):
                pdf_path = Path(pdf_str)
                retry_count = fail_info.get('retries', 0)
                
                # 🔥 RETRY LIMIT: Skip if already retried 3+ times
                if retry_count >= MAX_RETRIES_PDF:
                    logger.warning(f"🚫 SKIP: {pdf_path.name} (max retries {retry_count} reached)")
                    skipped_retry_limit += 1
                    continue
                
                if not pdf_path.exists():
                    logger.warning(f"⚠️  File no longer exists: {pdf_path.name}")
                    failed_files.pop(pdf_str, None)
                    continue
                
                try:
                    logger.info(f"🔄 Retrying: {pdf_path.name} (attempt {retry_count + 1})...")
                    
                    # Load PDF text
                    text = self.load_pdf_text(pdf_path)
                    if not text:
                        logger.warning(f"  ⚠️  Still failing to extract text: {pdf_path.name}")
                        fail_info['retries'] = retry_count + 1
                        fail_info['time'] = datetime.now().isoformat()
                        still_failing += 1
                        continue
                    
                    # Create chunks
                    chunks = simple_text_split(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
                    
                    if not chunks:
                        logger.warning(f"  ⚠️  Still no chunks: {pdf_path.name}")
                        fail_info['retries'] = retry_count + 1
                        fail_info['time'] = datetime.now().isoformat()
                        still_failing += 1
                        continue
                    
                    # Create and store documents with unique chunk IDs
                    documents = []
                    chunk_ids = []
                    for i, chunk in enumerate(chunks):
                        # 🔥 UNIQUE CHUNK ID: Prevents duplicates on crash mid-insert
                        chunk_id = f"{pdf_path.stem}_{i}_{hash(chunk[:50]) % 100000}"
                        chunk_ids.append(chunk_id)
                        
                        # 🔥 ENHANCED METADATA: In retry system too
                        enhanced_metadata = create_enhanced_metadata(
                            pdf_path,
                            chunk_index=i,
                            total_chunks=len(chunks),
                            page_number=0
                        )
                        
                        doc = Document(
                            page_content=chunk,
                            metadata=enhanced_metadata
                        )
                        documents.append(doc)
                    
                    # Store in ChromaDB with unique IDs
                    CHUNK_BATCH_SIZE = 500
                    for i in range(0, len(documents), CHUNK_BATCH_SIZE):
                        chunk_batch = documents[i:i+CHUNK_BATCH_SIZE]
                        batch_ids = chunk_ids[i:i+CHUNK_BATCH_SIZE]
                        
                        # 🔥 PRODUCTION RETRY: Retry with exponential backoff on DB failure
                        def store_batch_recovery():
                            self.vector_store.add_documents(chunk_batch, ids=batch_ids)
                        
                        try:
                            retry_with_exponential_backoff(store_batch_recovery, max_retries=3)
                            self.stats['embeddings_stored'] += len(chunk_batch)
                        except Exception as db_error:
                            logger.error(f"  ❌ DB storage failed in recovery for batch {i//CHUNK_BATCH_SIZE + 1}: {db_error}")
                            raise
                        
                        # 🔥 MEMORY: Clean up garbage after each sub-batch
                        gc.collect()
                    
                    # 🔥 CRITICAL: Persist DB after each PDF
                    try:
                        self.vector_store._client.persist() if hasattr(self.vector_store, '_client') else None
                    except Exception as persist_err:
                        logger.warning(f"  ⚠️  Persist warning (non-critical): {persist_err}")
                    
                    # ✅ Success - move from failed to processed
                    failed_files.pop(pdf_str, None)
                    processed_files.add(pdf_str)
                    recovered += 1
                    
                    logger.info(f"  ✅ Recovered: {pdf_path.name} ({len(chunks)} chunks)")
                    
                    # Save progress
                    self.save_failed_files(failed_files)
                    time.sleep(0.05)
                    
                except Exception as e:
                    logger.error(f"  ❌ Still failing: {pdf_path.name} - {e}")
                    fail_info['retries'] = retry_count + 1
                    fail_info['error'] = str(e)[:100]
                    fail_info['time'] = datetime.now().isoformat()
                    still_failing += 1
            
            # 🔥 Final DB persistence (atomic snapshot)
            try:
                logger.info("💾 Final DB persistence flush (recovery)...")
                self.vector_store._client.persist() if hasattr(self.vector_store, '_client') else None
                logger.info("✅ Final persistence complete (recovery)")
            except Exception as persist_err:
                logger.warning(f"⚠️  Final persist warning (non-critical): {persist_err}")
            
            # 🔥 FINAL MEMORY CLEANUP
            gc.collect()
            
            # Final report
            elapsed = time.time() - self.stats['start_time']
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            
            logger.info("\n" + "="*80)
            logger.info("🔁 RETRY COMPLETE!")
            logger.info("="*80)
            logger.info(f"\n📊 RETRY STATISTICS:")
            logger.info(f"   PDFs Recovered:     {recovered}")
            logger.info(f"   Still Failing:      {still_failing}")
            logger.info(f"   Hit Retry Limit:    {skipped_retry_limit}")
            logger.info(f"   Total Time:         {minutes}m {seconds}s")
            logger.info(f"\n✅ {recovered} PDFs recovered to database!")
            logger.info("="*80 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"\n❌ Retry system failed: {e}")
            return False
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """
        🔧 HELPER: Extract text from PDF file
        
        Wrapper around load_pdf_text for clarity when integrating with
        external cleaning pipelines.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text or None if failed
        """
        return self.load_pdf_text(pdf_path)
    
    def store_chunk_in_vector_db(self, content: str, metadata: dict, chunk_id: Optional[str] = None):
        """
        🔧 HELPER: Store a single cleaned chunk in vector database
        
        Used when integrating with external cleaning pipelines that
        produce pre-cleaned, pre-chunked content.
        
        Args:
            content: Chunk content (cleaned text)
            metadata: Metadata dictionary with doc info, topics, etc.
            chunk_id: Optional unique ID for the chunk (auto-generated if None)
            
        Returns:
            None (stores directly in vector_store)
            
        Raises:
            Exception if storage fails
        """
        if not self.vector_store:
            raise RuntimeError("Vector store not initialized! Call initialize_vector_store() first.")
        
        # Generate chunk ID if not provided
        if not chunk_id:
            chunk_id = f"chunk_{hash(content[:50]) % 1000000}"
        
        # Create Document object compatible with ChromaDB
        doc = Document(
            page_content=content,
            metadata=metadata
        )
        
        # Store in vector database
        try:
            self.vector_store.add_documents([doc], ids=[chunk_id])
            self.stats['embeddings_stored'] += 1
            logger.debug(f"✅ Stored chunk: {chunk_id}")
        except Exception as e:
            logger.error(f"❌ Failed to store chunk {chunk_id}: {e}")
            raise


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Neuronix PDF Ingestion Pipeline")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    # Print startup message (visible even in non-verbose mode)
    print("\n" + "="*80)
    print("[START] INGESTION PIPELINE STARTED")
    print("="*80)
    print()
    
    try:
        ingester = NeuronixIngestion()
        success = ingester.run()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ INGESTION FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
