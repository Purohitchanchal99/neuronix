"""
Neuronix RAG (Retrieval-Augmented Generation) Data Ingestion Pipeline
=======================================================================
This script loads medical/psychology PDFs from /docs, chunks them intelligently,
and stores embeddings in a Chroma vector database with rich metadata.

Features:
- DirectoryLoader + PyPDFLoader for PDF extraction
- Intelligent text chunking (1000 chars, 200 char overlap)
- Google Gemini embeddings for vector conversion
- Chroma vector store management
- Metadata enrichment from master_mapping.json
- Comprehensive verification and testing
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# ================================================================
# WINDOWS COMPATIBILITY FIX
# ================================================================
# Windows doesn't have pwd module (Unix-only)
# langchain_community tries to import it, so we create a mock
if sys.platform == "win32":
    import types
    pwd_module = types.ModuleType('pwd')
    sys.modules['pwd'] = pwd_module

# LangChain imports (lazy loaded to avoid heavy dependency chains)
from langchain_core.documents import Document # pyright: ignore[reportMissingImports]

# ================================================================
# LIGHTWEIGHT CUSTOM TEXT SPLITTER (zero dependencies)
# ================================================================
def simple_text_splitter(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    Simple text splitter without langchain overhead.
    
    Args:
        text: Text to split
        chunk_size: Size of each chunk
        overlap: Number of overlapping characters between chunks
        
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    
    return chunks

def _get_loaders():
    """Lazy load document loaders to avoid import time overhead"""
    from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
    return DirectoryLoader, PyPDFLoader

def _get_chroma_and_embeddings():
    """Lazy load Chroma and embeddings to avoid import time overhead"""
    from langchain_chroma import Chroma
    # Use HuggingFace embeddings (MUST MATCH retrieval pipeline)
    from langchain_huggingface import HuggingFaceEmbeddings
    return Chroma, HuggingFaceEmbeddings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'ingest_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / "docs"
DATA_DIR = BASE_DIR / "data"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
MAPPING_FILE = DATA_DIR / "master_mapping.json"

# Text splitting configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
SEPARATORS = [
    "\n\n",
    "\n",
    " ",
    ""
]


class NeuronixRAGPipeline:
    """Main RAG pipeline for Neuronix medical knowledge base"""
    
    def __init__(self, google_api_key: str = None):
        """
        Initialize the RAG pipeline
        
        Args:
            google_api_key: Google API key for Gemini embeddings.
                          If None, will try to read from GOOGLE_API_KEY env variable
        """
        self.docs_dir = DOCS_DIR
        self.vector_db_dir = VECTOR_DB_DIR
        self.mapping_file = MAPPING_FILE
        
        # Initialize embeddings (lazy load to avoid heavy dependency chain)
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        # Note: API key now only used for LLM, not for embeddings
        
        # Lazy load Chroma and HuggingFace embeddings
        ChromaClass, HuggingFaceEmbeddingsClass = _get_chroma_and_embeddings()
        self.chroma_class = ChromaClass  # Store for later use
        
        # Initialize embeddings - MUST MATCH retrieval pipeline (query_rag_system.py)
        self.embeddings = HuggingFaceEmbeddingsClass(model_name="sentence-transformers/all-MiniLM-L6-v2")
        logger.info("[OK] HuggingFace Embeddings initialized (sentence-transformers/all-MiniLM-L6-v2)")
        
        # Store text splitter configuration (using simple_text_splitter function)
        self.chunk_size = CHUNK_SIZE
        self.chunk_overlap = CHUNK_OVERLAP
        logger.info(f"[OK] Text splitter configured (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
        
        # Load mapping
        self.mapping_data = self._load_mapping()
        
        # Vector store (will be initialized later)
        self.vector_store = None
        
        # Statistics
        self.stats = {
            'pdfs_loaded': 0,
            'documents_created': 0,
            'chunks_created': 0,
            'chunks_stored': 0,
            'errors': []
        }
    
    def _load_mapping(self) -> Dict:
        """Load the master_mapping.json file"""
        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            logger.info(f"[OK] Loaded master mapping with {len(mapping.get('countries', {}))} countries")
            return mapping
        except FileNotFoundError:
            logger.error(f"Mapping file not found at {self.mapping_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding mapping JSON: {e}")
            return {}
    
    def _get_country_and_status(self, filename: str) -> Tuple[str, int]:
        """
        Extract country and status information from filename and mapping
        
        Args:
            filename: PDF filename
            
        Returns:
            Tuple of (country_name, status) where status is 0 (free) or 1 (paid)
        """
        # Extract country from directory path
        # e.g., "India/IGNOU_Cognitive_PDF.pdf" -> "India"
        
        for country_code, country_data in self.mapping_data.get('countries', {}).items():
            country_name = country_data.get('full_name', country_code)
            # Check if this file might belong to this country
            # For now, we'll use directory structure
            if country_name.lower() in filename.lower():
                # Try to find matching subject to get status
                for subject_data in country_data.get('subjects', {}).values():
                    if subject_data.get('subject_name', '').lower() in filename.lower():
                        return country_name, subject_data.get('status', 1)
                # Default to status 1 if country match but no subject
                return country_name, 1
        
        # Default values
        return "Unknown", 1
    
    def load_documents(self) -> List[Document]:
        """Load all PDF documents from the docs directory"""
        logger.info("=" * 80)
        logger.info("PHASE 1: Loading Documents")
        logger.info("=" * 80)
        
        # Lazy load document loaders
        DirectoryLoader, PyPDFLoader = _get_loaders()
        
        if not self.docs_dir.exists():
            logger.error(f"Docs directory not found: {self.docs_dir}")
            return []
        
        try:
            documents = []
            
            # Load PDF files
            pdf_loader = DirectoryLoader(
                str(self.docs_dir),
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
                silent_errors=True
            )
            documents.extend(pdf_loader.load())
            
            # Also load text files for testing (when PDFs aren't available)
            if len(documents) == 0:
                logger.info("No PDFs found, checking for text files...")
                from langchain_community.document_loaders import TextLoader
                import glob as glob_module
                
                for txt_file in glob_module.glob(str(self.docs_dir / "**/*.txt"), recursive=True):
                    try:
                        loader = TextLoader(txt_file)
                        docs = loader.load()
                        documents.extend(docs)
                    except Exception as e:
                        logger.warning(f"Could not load {txt_file}: {e}")
            
            self.stats['pdfs_loaded'] = len(documents)
            
            logger.info(f"[OK] Loaded {len(documents)} documents")
            
            # Log document sources
            sources = set()
            for doc in documents:
                source = doc.metadata.get('source', 'unknown')
                sources.add(Path(source).name)
            if sources:
                logger.info(f"  Sources: {', '.join(sorted(sources))}")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            self.stats['errors'].append(f"Document loading error: {e}")
            return []
    
    def create_chunks(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks with metadata
        
        Args:
            documents: List of loaded documents
            
        Returns:
            List of chunked documents with enriched metadata
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: Creating Chunks")
        logger.info("=" * 80)
        
        chunks = []
        
        for doc in documents:
            source_file = Path(doc.metadata.get('source', 'unknown')).name
            
            # Determine country and status from file path
            full_path = doc.metadata.get('source', '')
            country = "Unknown"
            status = 1
            
            # Extract country from path
            for country_name in self.mapping_data.get('countries', {}).values():
                full_name = country_name.get('full_name', '')
                if full_name in full_path:
                    country = full_name
                    # Default status for documents
                    status = 0 if country in ['India', 'Germany', 'France', 'Switzerland'] else 1
                    break
            
            try:
                # Split the document using custom lightweight splitter
                raw_chunks = simple_text_splitter(
                    doc.page_content,
                    chunk_size=self.chunk_size,
                    overlap=self.chunk_overlap
                )
                
                # Convert to Document objects
                doc_chunks = [
                    Document(page_content=chunk, metadata=doc.metadata.copy())
                    for chunk in raw_chunks
                ]
                
                # Enrich metadata for each chunk
                for i, chunk in enumerate(doc_chunks):
                    chunk.metadata.update({
                        'source_file': source_file,
                        'country': country,
                        'status': status,
                        'status_label': 'Free' if status == 0 else 'Paid',
                        'chunk_index': i,
                        'total_chunks': len(doc_chunks)
                    })
                
                chunks.extend(doc_chunks)
                logger.info(f"  [OK] {source_file}: {len(doc_chunks)} chunks created")
                
            except Exception as e:
                logger.error(f"  [ERROR] Error chunking {source_file}: {e}")
                self.stats['errors'].append(f"Chunking error for {source_file}: {e}")
                continue
        
        self.stats['documents_created'] = len(documents)
        self.stats['chunks_created'] = len(chunks)
        logger.info(f"[OK] Created {len(chunks)} total chunks from {len(documents)} documents")
        
        return chunks
    
    def initialize_database(self):
        """Initialize the Chroma vector database"""
        # Lazy load Chroma
        Chroma, _ = _get_chroma_and_embeddings()
        
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3: Initializing Vector Database")
        logger.info("=" * 80)
        
        try:
            # Create vector DB directory if it doesn't exist
            self.vector_db_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize Chroma
            self.vector_store = self.chroma_class(
                collection_name="neuronix_medical_kb",
                persist_directory=str(self.vector_db_dir),
                embedding_function=self.embeddings
            )
            
            # Validate initialization
            if self.vector_store is None:
                raise ValueError("Vector store initialization returned None")
            
            logger.info(f"[OK] Chroma vector database initialized at {self.vector_db_dir}")
            logger.info(f"[DEBUG] Vector store type: {type(self.vector_store)}")
            logger.info(f"  Embedding model: HuggingFace (all-MiniLM-L6-v2)")
            logger.info(f"  Collection: neuronix_medical_kb")
            
        except Exception as e:
            logger.error(f"Error initializing vector database: {e}")
            self.stats['errors'].append(f"Database initialization error: {e}")
            raise
    
    def ingest_chunks(self, chunks: List[Document]) -> bool:
        """
        Store chunks in the vector database
        
        Args:
            chunks: List of chunks to store
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 4: Ingesting Chunks into Vector Store")
        logger.info("=" * 80)
        
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return False
        
        if not chunks:
            logger.warning("No chunks to ingest")
            return False
        
        try:
            # Debug: Verify vector store
            logger.info(f"[DEBUG] Vector store type before ingestion: {type(self.vector_store)}")
            
            # Add chunks in batches
            batch_size = 50
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                
                # Convert to the format Chroma expects
                texts = [chunk.page_content for chunk in batch]
                metadatas = [chunk.metadata for chunk in batch]
                
                # Add to vector store
                ids = self.vector_store.add_texts(
                    texts=texts,
                    metadatas=metadatas
                )
                
                self.stats['chunks_stored'] += len(ids)
                logger.info(f"  [OK] Stored batch {i//batch_size + 1}: {len(ids)} chunks")
            
            logger.info(f"[OK] Total chunks stored: {self.stats['chunks_stored']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting chunks: {e}")
            self.stats['errors'].append(f"Chunk ingestion error: {e}")
            return False
    
    def verify_retrieval(self, query: str = "Depression", k: int = 3) -> bool:
        """
        Test the RAG pipeline by searching for a keyword
        
        Args:
            query: Search query (default: "Depression")
            k: Number of results to retrieve
            
        Returns:
            True if verification successful
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 5: Verification - Testing Retrieval")
        logger.info("=" * 80)
        
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return False
        
        try:
            logger.info(f"\nSearching for: '{query}'")
            logger.info(f"Retrieving top {k} results...\n")
            
            # Search
            results = self.vector_store.similarity_search(query, k=k)
            
            if not results:
                logger.warning("No results found")
                return False
            
            # Display results
            for i, result in enumerate(results, 1):
                metadata = result.metadata
                logger.info(f"\n{'─' * 78}")
                logger.info(f"Result #{i}")
                logger.info(f"{'─' * 78}")
                logger.info(f"Source: {metadata.get('source_file', 'Unknown')}")
                logger.info(f"Country: {metadata.get('country', 'Unknown')}")
                logger.info(f"Status: {metadata.get('status_label', 'Unknown')}")
                logger.info(f"Chunk: {metadata.get('chunk_index', '?')}/{metadata.get('total_chunks', '?')}")
                logger.info(f"\nContent (first 500 chars):")
                logger.info(f"{result.page_content[:500]}...")
            
            logger.info(f"\n{'─' * 78}")
            logger.info(f"[OK] Retrieval verification successful!")
            logger.info(f"  Found {len(results)} relevant documents")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            self.stats['errors'].append(f"Verification error: {e}")
            return False
    
    def print_statistics(self):
        """Print ingestion statistics"""
        logger.info("\n" + "=" * 80)
        logger.info("INGESTION STATISTICS")
        logger.info("=" * 80)
        
        logger.info(f"\nDocuments:")
        logger.info(f"  PDFs Loaded: {self.stats['pdfs_loaded']}")
        logger.info(f"  Documents Created: {self.stats['documents_created']}")
        
        logger.info(f"\nChunking:")
        logger.info(f"  Text Chunks Created: {self.stats['chunks_created']}")
        logger.info(f"  Chunk Size: {CHUNK_SIZE} characters")
        logger.info(f"  Chunk Overlap: {CHUNK_OVERLAP} characters")
        
        logger.info(f"\nVector Store:")
        logger.info(f"  Chunks Stored: {self.stats['chunks_stored']}")
        logger.info(f"  Database Location: {self.vector_db_dir}")
        logger.info(f"  Embedding Model: Google Gemini")
        
        if self.stats['errors']:
            logger.info(f"\nErrors ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                logger.info(f"  [ERROR] {error}")
        else:
            logger.info(f"[OK] No errors encountered")
        
        logger.info("\n" + "=" * 80)
        
        # Summary
        success_rate = (self.stats['chunks_stored'] / max(1, self.stats['chunks_created'])) * 100
        logger.info(f"\n📊 Overall Success Rate: {success_rate:.1f}%")
        logger.info(f"[OK] Ingestion pipeline completed successfully!")
        logger.info("=" * 80)
    
    def run_full_pipeline(self, verify: bool = True) -> Tuple[bool, Dict]:
        """
        Run the complete RAG ingestion pipeline
        
        Args:
            verify: Whether to run verification at the end
            
        Returns:
            Tuple of (success, statistics)
        """
        logger.info("\n")
        logger.info("#" * 80)
        logger.info("# NEURONIX RAG DATA INGESTION PIPELINE")
        logger.info(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("#" * 80)
        
        try:
            # Phase 1: Load documents
            documents = self.load_documents()
            if not documents:
                logger.warning("No documents loaded, exiting")
                return False, self.stats
            
            # Phase 2: Create chunks
            chunks = self.create_chunks(documents)
            if not chunks:
                logger.warning("No chunks created, exiting")
                return False, self.stats
            
            # Phase 3: Initialize database
            self.initialize_database()
            
            # Phase 4: Ingest chunks
            success = self.ingest_chunks(chunks)
            if not success:
                logger.error("Chunk ingestion failed")
                return False, self.stats
            
            # Phase 5: Verify (optional)
            if verify and self.stats['chunks_stored'] > 0:
                self.verify_retrieval()
            
            # Print statistics
            self.print_statistics()
            
            logger.info(f"\n[OK] Pipeline completed successfully!")
            return True, self.stats
            
        except Exception as e:
            logger.error(f"Pipeline failed with error: {e}")
            self.stats['errors'].append(f"Pipeline error: {e}")
            self.print_statistics()
            return False, self.stats
        
        finally:
            logger.info(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


def main():
    """Main entry point"""
    import sys
    
    # Check for Google API key
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        logger.error("\n" + "!" * 80)
        logger.error("ERROR: GOOGLE_API_KEY environment variable not set")
        logger.error("!" * 80)
        logger.error("\nPlease set your Google API key:")
        logger.error("  Windows (PowerShell): $env:GOOGLE_API_KEY = 'your-api-key'")
        logger.error("  Windows (CMD): set GOOGLE_API_KEY=your-api-key")
        logger.error("  Linux/Mac: export GOOGLE_API_KEY='your-api-key'")
        logger.error("\nGet your API key from: https://makersuite.google.com/app/apikey")
        logger.error("!" * 80 + "\n")
        sys.exit(1)
    
    try:
        # Initialize and run pipeline
        pipeline = NeuronixRAGPipeline(google_api_key=google_api_key)
        success, stats = pipeline.run_full_pipeline(verify=True)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\n⚠ Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
