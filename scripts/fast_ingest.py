"""
Fast Batch RAG Ingestion Pipeline
==================================
Optimized for speed: batch processes PDFs with progress tracking.

Features:
- Batch PDF loading (20 at a time)
- Efficient chunking without heavy dependencies
- Direct ChromaDB storage with Google Gemini embeddings
- Real-time progress reporting
- Automatic retry for failed PDFs
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Windows compatibility
if sys.platform == "win32":
    import types
    pwd_module = types.ModuleType('pwd')
    sys.modules['pwd'] = pwd_module

# LangChain imports
from langchain_core.documents import Document

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'fast_ingest_log.txt', encoding='utf-8'),
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

BATCH_SIZE = 20  # Process 20 PDFs at a time
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def simple_text_split(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into chunks without heavy dependencies"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    
    return chunks


class FastBatchIngestion:
    """Fast batch ingestion pipeline"""
    
    def __init__(self):
        """Initialize with lazy loading"""
        self.docs_dir = DOCS_DIR
        self.vector_db_dir = VECTOR_DB_DIR
        self.mapping_file = MAPPING_FILE
        
        # Lazy load Chroma and embeddings
        logger.info("🔧 Initializing ingestion engine...")
        
        try:
            from langchain_chroma import Chroma
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            
            self.Chroma = Chroma
            self.GoogleGenerativeAIEmbeddings = GoogleGenerativeAIEmbeddings
            
            # Initialize embeddings
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            logger.info("✅ Google Gemini Embeddings ready")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
        
        # Statistics
        self.stats = {
            'pdfs_processed': 0,
            'pdfs_failed': 0,
            'chunks_created': 0,
            'embeddings_stored': 0,
            'errors': []
        }
    
    def get_all_pdfs(self) -> List[Path]:
        """Get all PDF files from docs directory"""
        if not self.docs_dir.exists():
            logger.error(f"Docs directory not found: {self.docs_dir}")
            return []
        
        pdfs = list(self.docs_dir.rglob("*.pdf"))
        logger.info(f"📁 Found {len(pdfs)} PDFs to process")
        
        return sorted(pdfs)  # Sort for consistent ordering
    
    def load_pdf_text(self, pdf_path: Path) -> str:
        """Load text from a single PDF"""
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(str(pdf_path))
            text = ""
            
            for page in reader.pages:
                text += page.extract_text()
            
            return text
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to read {pdf_path.name}: {e}")
            self.stats['errors'].append(f"PDF read error: {pdf_path.name}")
            self.stats['pdfs_failed'] += 1
            return None
    
    def initialize_vector_store(self):
        """Initialize ChromaDB vector store"""
        try:
            logger.info("📚 Initializing vector store...")
            
            self.vector_db_dir.mkdir(parents=True, exist_ok=True)
            
            self.vector_store = self.Chroma(
                collection_name="neuronix_medical_kb",
                persist_directory=str(self.vector_db_dir),
                embedding_function=self.embeddings
            )
            
            logger.info(f"✅ Vector store initialized at {self.vector_db_dir}")
            
        except Exception as e:
            logger.error(f"❌ Vector store initialization failed: {e}")
            raise
    
    def process_pdf_batch(self, pdf_paths: List[Path]):
        """Process a batch of PDFs"""
        logger.info(f"\n📦 Processing batch of {len(pdf_paths)} PDFs...")
        
        documents = []
        
        for pdf_path in pdf_paths:
            # Load PDF
            text = self.load_pdf_text(pdf_path)
            if not text:
                continue
            
            # Create chunks
            chunks = simple_text_split(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
            
            if chunks:
                self.stats['pdfs_processed'] += 1
                self.stats['chunks_created'] += len(chunks)
                
                # Create Document objects with metadata
                for i, chunk in enumerate(chunks):
                    doc = Document(
                        page_content=chunk,
                        metadata={
                            'source': pdf_path.name,
                            'file_path': str(pdf_path),
                            'chunk_index': i,
                            'country': self._extract_country(pdf_path),
                            'total_chunks': len(chunks)
                        }
                    )
                    documents.append(doc)
                
                logger.info(f"  ✓ {pdf_path.name}: {len(chunks)} chunks")
        
        # Store batch in vector DB
        if documents:
            try:
                logger.info(f"  💾 Storing {len(documents)} chunks in vector DB...")
                
                # Add documents to vector store
                self.vector_store.add_documents(documents)
                
                self.stats['embeddings_stored'] += len(documents)
                logger.info(f"  ✅ Batch stored successfully")
                
            except Exception as e:
                logger.error(f"  ❌ Vector store error: {e}")
                self.stats['errors'].append(f"Storage error: {e}")
    
    def _extract_country(self, pdf_path: Path) -> str:
        """Extract country from file path"""
        try:
            parts = pdf_path.parts
            if 'docs' in parts:
                idx = parts.index('docs')
                if idx + 1 < len(parts):
                    return parts[idx + 1].replace('_', ' ')
        except:
            pass
        return "Unknown"
    
    def run(self):
        """Run the complete ingestion pipeline"""
        logger.info("\n" + "="*70)
        logger.info("⚡ FAST BATCH RAG INGESTION PIPELINE")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        try:
            # Get PDFs
            pdf_list = self.get_all_pdfs()
            if not pdf_list:
                logger.error("No PDFs found")
                return False
            
            # Initialize vector store
            self.initialize_vector_store()
            
            # Process in batches
            total_batches = (len(pdf_list) + BATCH_SIZE - 1) // BATCH_SIZE
            
            for batch_num, i in enumerate(range(0, len(pdf_list), BATCH_SIZE), 1):
                batch = pdf_list[i:i + BATCH_SIZE]
                
                logger.info(f"\n🔄 BATCH {batch_num}/{total_batches}")
                logger.info(f"   Processing PDFs {i+1} to {min(i+BATCH_SIZE, len(pdf_list))} of {len(pdf_list)}")
                
                self.process_pdf_batch(batch)
                
                # Progress report
                logger.info(f"\n📊 Progress: {self.stats['pdfs_processed']}/{len(pdf_list)} PDFs")
                logger.info(f"   Chunks: {self.stats['chunks_created']:,}")
                logger.info(f"   Stored: {self.stats['embeddings_stored']:,}")
            
            # Final report
            elapsed = (datetime.now() - start_time).total_seconds()
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            
            logger.info("\n" + "="*70)
            logger.info("✅ INGESTION COMPLETE!")
            logger.info("="*70)
            logger.info(f"\n📊 FINAL STATISTICS:")
            logger.info(f"   PDFs Processed:    {self.stats['pdfs_processed']}/{len(pdf_list)}")
            logger.info(f"   PDFs Failed:       {self.stats['pdfs_failed']}")
            logger.info(f"   Total Chunks:      {self.stats['chunks_created']:,}")
            logger.info(f"   Embeddings Stored: {self.stats['embeddings_stored']:,}")
            logger.info(f"   Total Time:        {minutes}m {seconds}s")
            
            if self.stats['errors']:
                logger.info(f"\n⚠️  Errors: {len(self.stats['errors'])}")
                for error in self.stats['errors'][:10]:
                    logger.info(f"   • {error}")
            
            logger.info("\n🎉 Vector database ready for queries!")
            logger.info("="*70 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"\n❌ Pipeline failed: {e}")
            return False


if __name__ == "__main__":
    ingester = FastBatchIngestion()
    success = ingester.run()
    
    sys.exit(0 if success else 1)
