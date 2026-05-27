"""
Neuronix RAG Demo - Local Testing Without Google API Key

This demo version shows the RAG pipeline working with sample documents,
useful for testing the chunking and vector database logic without
requiring a Google API key.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List

# ================================================================
# WINDOWS COMPATIBILITY FIX
# ================================================================
if sys.platform == "win32":
    import types
    pwd_module = types.ModuleType('pwd')
    sys.modules['pwd'] = pwd_module

from langchain_core.documents import Document # type: ignore

# ================================================================
# LIGHTWEIGHT CUSTOM TEXT SPLITTER (zero dependencies)
# ================================================================
def simple_text_splitter(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
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

# ================================================================
# LIGHTWEIGHT CUSTOM DOCUMENT LOADERS (no heavy dependencies)
# ================================================================
import os
import glob as glob_module

def load_text_files(folder_path: str) -> list:
    """Load .txt files with simple file I/O (no langchain overhead)"""
    docs = []
    txt_files = glob_module.glob(os.path.join(folder_path, "**/*.txt"), recursive=True)
    
    for file_path in txt_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():  # Only add non-empty files
                    docs.append({
                        'content': content,
                        'metadata': {'source': os.path.basename(file_path), 'path': file_path}
                    })
        except Exception as e:
            logger.warning(f"Could not load {file_path}: {e}")
    
    return docs

def load_pdf_files(folder_path: str) -> list:
    """Load .pdf files - uses langchain's PyPDFLoader only if PDFs exist"""
    try:
        from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
        
        pdf_loader = DirectoryLoader(
            str(folder_path),
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            silent_errors=True
        )
        docs = pdf_loader.load()
        return docs
    except Exception as e:
        logger.debug(f"PDF loading not available: {e}")
        return []

# Lazy imports - loaded when needed to avoid heavy dependency chains

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'demo_ingest_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / "docs"
DATA_DIR = BASE_DIR / "data"
MAPPING_FILE = DATA_DIR / "master_mapping.json"

# Text splitting configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


class DemoRAGIngester:
    """Demo RAG ingester for local testing without API"""
    
    def __init__(self):
        """Initialize the demo ingester"""
        self.docs_dir = DOCS_DIR
        self.mapping_file = MAPPING_FILE
        
        # Store text splitting configuration (using simple_text_splitter function)
        self.chunk_size = CHUNK_SIZE
        self.chunk_overlap = CHUNK_OVERLAP
        
        # Load mapping
        self.mapping_data = self._load_mapping()
        
        # Statistics
        self.stats = {
            'documents_loaded': 0,
            'chunks_created': 0,
            'errors': []
        }
    
    def _load_mapping(self) -> dict:
        """Load the master_mapping.json file"""
        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            logger.info(f"[OK] Loaded master mapping")
            return mapping
        except Exception as e:
            logger.error(f"Error loading mapping: {e}")
            return {}
    
    def load_documents(self) -> List[Document]:
        """Load PDF and text documents from docs directory"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: Loading Documents")
        logger.info("=" * 80)
        
        documents = []
        
        # Try PDF files first (lightweight - only loads PyPDFLoader if PDFs exist)
        pdf_docs = load_pdf_files(str(self.docs_dir))
        if pdf_docs:
            documents.extend(pdf_docs)
            logger.info(f"[OK] Loaded {len(pdf_docs)} PDF documents")
        
        # If no PDFs, try text files for demo
        if len(documents) == 0:
            logger.info("No PDF files found, loading text files for demo...")
            txt_docs = load_text_files(str(self.docs_dir))
            
            if txt_docs:
                for doc in txt_docs:
                    documents.append(Document(
                        page_content=doc['content'],
                        metadata=doc['metadata']
                    ))
                logger.info(f"[OK] Loaded {len(txt_docs)} text documents")
            else:
                logger.warning("No documents found in docs folder")
        
        self.stats['documents_loaded'] = len(documents)
        logger.info(f"[OK] Total documents loaded: {len(documents)}")
        
        return documents
    
    def create_chunks(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks using custom simple splitter"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: Creating Chunks")
        logger.info("=" * 80)
        
        chunks = []
        
        for doc in documents:
            try:
                # Use simple_text_splitter function
                raw_chunks = simple_text_splitter(
                    doc.page_content,
                    chunk_size=self.chunk_size,
                    overlap=self.chunk_overlap
                )
                
                # Convert to Document objects
                doc_chunks = [
                    Document(
                        page_content=chunk,
                        metadata=doc.metadata
                    )
                    for chunk in raw_chunks
                ]
                
                chunks.extend(doc_chunks)
                logger.info(f"  [OK] Created {len(doc_chunks)} chunks from {Path(doc.metadata.get('source', 'unknown')).name}")
            except Exception as e:
                logger.error(f"  [ERROR] Error chunking: {e}")
                self.stats['errors'].append(str(e))
        
        self.stats['chunks_created'] = len(chunks)
        logger.info(f"[OK] Total chunks created: {len(chunks)}")
        
        return chunks
    
    def display_sample_chunks(self, chunks: List[Document], count: int = 3):
        """Display sample chunks for inspection"""
        logger.info("\n" + "=" * 80)
        logger.info(f"SAMPLE CHUNKS (showing {min(count, len(chunks))} of {len(chunks)})")
        logger.info("=" * 80)
        
        for i, chunk in enumerate(chunks[:count], 1):
            logger.info(f"\nChunk #{i}")
            logger.info("-" * 80)
            logger.info(f"Source: {chunk.metadata.get('source', 'unknown')}")
            logger.info(f"Content preview: {chunk.page_content[:200]}...")
    
    def print_statistics(self):
        """Print ingestion statistics"""
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"\nDocuments: {self.stats['documents_loaded']}")
        logger.info(f"Chunks Created: {self.stats['chunks_created']}")
        logger.info(f"Chunk Size: {CHUNK_SIZE} characters")
        logger.info(f"Chunk Overlap: {CHUNK_OVERLAP} characters")
        
        if self.stats['errors']:
            logger.info(f"\nErrors: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                logger.info(f"  - {error}")
        else:
            logger.info(f"\n[OK] No errors encountered")
        
        logger.info("\n" + "=" * 80)
    
    def run_demo(self):
        """Run the demo ingestion pipeline"""
        logger.info("\n")
        logger.info("#" * 80)
        logger.info("# NEURONIX RAG DEMO - LOCAL TESTING")
        logger.info(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("#" * 80)
        
        try:
            # Phase 1: Load documents
            documents = self.load_documents()
            if not documents:
                logger.warning("\n[ERROR] No documents found!")
                logger.info("\nTo test the pipeline, create sample files in /docs/India/:")
                logger.info("  - Sample text files (.txt)")
                logger.info("  - Or actual PDF files (.pdf)")
                return False
            
            # Phase 2: Create chunks
            chunks = self.create_chunks(documents)
            if not chunks:
                logger.warning("[ERROR] Failed to create chunks")
                return False
            
            # Phase 3: Display samples
            self.display_sample_chunks(chunks, count=3)
            
            # Phase 4: Statistics
            self.print_statistics()
            
            logger.info(f"\n[OK] Demo completed successfully!")
            logger.info("\nNext steps:")
            logger.info("  1. Set GOOGLE_API_KEY environment variable")
            logger.info("  2. Run: python scripts/ingest_data.py")
            logger.info("     (This will create the searchable vector database)")
            logger.info("  3. Search with: python scripts/query_rag.py 'your query'")
            
            return True
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            return False
        
        finally:
            logger.info(f"\nEnded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# Module-level convenience functions for direct imports
def load_documents():
    """Load documents from the test directory. Module-level wrapper for DemoRAGIngester."""
    ingester = DemoRAGIngester()
    return ingester.load_documents()


def create_chunks():
    """Create chunks from loaded documents. Module-level wrapper for DemoRAGIngester."""
    ingester = DemoRAGIngester()
    documents = ingester.load_documents()
    return ingester.create_chunks(documents)


def run_demo():
    """Run the demo RAG ingestion. Module-level wrapper for DemoRAGIngester."""
    ingester = DemoRAGIngester()
    return ingester.run_demo()


def main():
    """Main entry point"""
    demo = DemoRAGIngester()
    success = demo.run_demo()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
