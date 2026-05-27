"""
🔗 NEURONIX + TEXT PIPELINE INTEGRATION
========================================
Connects text cleaning pipeline with existing ingestion system

Workflow:
  Raw PDF → Extract Text → Clean + Process → Store in ChromaDB
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.text_cleaner_pipeline import TextProcessingPipeline
from scripts.neuronix_ingest import NeuronixIngestion
from scripts.neuronix_constants import DOCS_DIR, CHROMA_PERSIST_DIRECTORY

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [NEURONIX_PIPELINE_INTEGRATION] - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class NeuronixCleaningIntegration:
    """
    Integrate text cleaning with existing Neuronix ingestion
    
    Before:
      Raw PDF Text → Segment → Store (loses metadata, quality issues)
    
    After:
      Raw PDF Text → CLEAN → CHUNK → METADATA → Q&A → SAFETY → Store
    """
    
    def __init__(self):
        self.pipeline = TextProcessingPipeline()
        self.ingestion = NeuronixIngestion()
        self.logger = logging.getLogger(__name__)
        
        # Create output directories
        self.cleaned_text_dir = Path(__file__).parent.parent / "cleaned_text"
        self.chunks_dir = Path(__file__).parent.parent / "chunks"
        self.qa_pairs_dir = Path(__file__).parent.parent / "qa_pairs"
        self.safety_logs_dir = Path(__file__).parent.parent / "safety_logs"
        
        for dir_path in [self.cleaned_text_dir, self.chunks_dir, self.qa_pairs_dir, self.safety_logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def process_and_ingest(self, pdf_path: Path, doc_type: str = "psychology") -> Dict:
        """
        Full workflow: Clean → Process → Ingest
        
        Returns:
            {
                'status': 'success' or 'error',
                'chunks_ingested': int,
                'safety_concerns': int,
                'chromadb_ids': List[str],
                'qa_pairs_generated': int,
            }
        """
        
        try:
            self.logger.info(f"🔄 Processing: {pdf_path.name}")
            
            # Step 1: Extract text from PDF
            text = self._extract_pdf_text(pdf_path)
            if not text:
                return {'status': 'error', 'message': 'Failed to extract text'}
            
            # Step 2: Process through cleaning pipeline
            result = self.pipeline.process(text, pdf_path.name, doc_type)
            
            if result['status'] != 'success':
                return result
            
            processed_chunks = result['chunks']
            
            # Step 3: Save cleaned text
            self._save_cleaned_text(text, pdf_path.name)
            
            # Step 4: Save chunks and metadata
            chromadb_ids = self._ingest_to_chromadb(processed_chunks, pdf_path.name)
            
            # Step 5: Save Q&A pairs
            qa_count = self._save_qa_pairs(processed_chunks, pdf_path.name)
            
            # Step 6: Log safety concerns
            safety_summary = result.get('safety_summary', {})
            if safety_summary.get('total_concerns', 0) > 0:
                self._log_safety_concerns(processed_chunks, pdf_path.name)
            
            return {
                'status': 'success',
                'file': pdf_path.name,
                'chunks_ingested': len(chromadb_ids),
                'safety_concerns': safety_summary.get('total_concerns', 0),
                'chromadb_ids': chromadb_ids,
                'qa_pairs_generated': qa_count,
                'processing_time': result['statistics'].get('processing_time', 0),
                'cleaning_stats': result['statistics'].get('cleaning_stats', {}),
            }
        
        except Exception as e:
            self.logger.error(f"❌ Error processing {pdf_path.name}: {e}")
            return {
                'status': 'error',
                'file': pdf_path.name,
                'message': str(e),
            }
    
    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF using PyPDF2 or pdfplumber"""
        try:
            # Try pdfplumber first (better for modern PDFs)
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    text = "\n\n".join(page.extract_text() or "" for page in pdf.pages)
                    return text
            except ImportError:
                pass
            
            # Fallback to PyPDF2
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(pdf_path)
                text = "\n\n".join(page.extract_text() for page in reader.pages)
                return text
            except:
                pass
            
            # Last resort: pypdf
            try:
                from pypdf import PdfReader
                reader = PdfReader(pdf_path)
                text = "\n\n".join(page.extract_text() for page in reader.pages)
                return text
            except:
                pass
            
            self.logger.warning(f"⚠️  Could not extract text from {pdf_path.name}")
            return ""
        
        except Exception as e:
            self.logger.error(f"PDF extraction error: {e}")
            return ""
    
    def _save_cleaned_text(self, text: str, source_name: str) -> Path:
        """Save cleaned text for reference"""
        output_file = self.cleaned_text_dir / f"{source_name}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        self.logger.debug(f"📝 Saved cleaned text: {output_file}")
        return output_file
    
    def _ingest_to_chromadb(self, processed_chunks: List[Dict], source_name: str) -> List[str]:
        """
        Store chunks in ChromaDB with rich metadata
        
        Returns:
            List of ChromaDB IDs for the chunks
        """
        chromadb_ids = []
        
        self.ingestion.initialize_vector_store()
        
        for chunk_data in processed_chunks:
            chunk_id = chunk_data['metadata']['chunk_id']
            content = chunk_data['content']
            metadata = {
                **chunk_data['metadata'],
                'has_safety_concerns': not chunk_data['safety']['is_safe'],
                'crisis_type': chunk_data['safety'].get('crisis_type'),
                'needs_disclaimer': chunk_data['safety']['needs_disclaimer'],
                'qa_pairs_count': len(chunk_data.get('qa_pairs', [])),
            }
            
            # Add to ChromaDB
            try:
                ids = self.ingestion.add_documents(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[chunk_id]
                )
                chromadb_ids.extend(ids)
            except Exception as e:
                self.logger.warning(f"Failed to add chunk {chunk_id}: {e}")
        
        return chromadb_ids
    
    def _save_qa_pairs(self, processed_chunks: List[Dict], source_name: str) -> int:
        """Save Q&A pairs to JSON files"""
        import json
        
        base_name = source_name.replace('.pdf', '').replace(' ', '_')
        qa_file = self.qa_pairs_dir / f"{base_name}_qa.json"
        
        all_qa = []
        for chunk_idx, chunk_data in enumerate(processed_chunks):
            for qa_idx, qa in enumerate(chunk_data.get('qa_pairs', [])):
                all_qa.append({
                    'id': f"{base_name}_q{chunk_idx}_{qa_idx}",
                    'chunk_id': chunk_data['metadata']['chunk_id'],
                    **qa
                })
        
        with open(qa_file, 'w', encoding='utf-8') as f:
            json.dump(all_qa, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"❓ Saved {len(all_qa)} Q&A pairs to {qa_file}")
        return len(all_qa)
    
    def _log_safety_concerns(self, processed_chunks: List[Dict], source_name: str) -> None:
        """Log chunks with safety concerns"""
        import json
        
        concerns = []
        for idx, chunk_data in enumerate(processed_chunks):
            if not chunk_data['safety']['is_safe']:
                concerns.append({
                    'chunk_id': chunk_data['metadata']['chunk_id'],
                    'crisis_type': chunk_data['safety']['crisis_type'],
                    'content_preview': chunk_data['content'][:200],
                    'hotlines': chunk_data['safety']['hotline_resources'],
                })
        
        if concerns:
            base_name = source_name.replace('.pdf', '').replace(' ', '_')
            safety_file = self.safety_logs_dir / f"{base_name}_safety.json"
            
            with open(safety_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'source': source_name,
                    'total_concerns': len(concerns),
                    'concerns': concerns,
                }, f, indent=2, ensure_ascii=False)
            
            self.logger.warning(f"⚠️  Safety concerns logged: {safety_file}")


def process_multiple_pdfs(pdf_paths: List[Path]) -> Dict:
    """
    Process multiple PDFs through the pipeline
    
    Returns:
        Summary of all results
    """
    integration = NeuronixCleaningIntegration()
    results = []
    
    print("\n" + "="*80)
    print("🔄 NEURONIX TEXT CLEANING PIPELINE")
    print("="*80)
    print(f"Processing {len(pdf_paths)} PDFs...\n")
    
    total_chunks = 0
    total_qa = 0
    total_concerns = 0
    
    for pdf_path in pdf_paths:
        if not pdf_path.exists():
            print(f"❌ File not found: {pdf_path}")
            continue
        
        result = integration.process_and_ingest(pdf_path)
        results.append(result)
        
        if result['status'] == 'success':
            chunks = result['chunks_ingested']
            qa = result['qa_pairs_generated']
            concerns = result['safety_concerns']
            
            total_chunks += chunks
            total_qa += qa
            total_concerns += concerns
            
            print(f"✅ {result['file']}")
            print(f"   • Chunks: {chunks}")
            print(f"   • Q&A Pairs: {qa}")
            print(f"   • Safety Concerns: {concerns}")
            if result['cleaning_stats']:
                print(f"   • Page Numbers Removed: {result['cleaning_stats'].get('page_numbers_removed', 0)}")
                print(f"   • Broken Words Fixed: {result['cleaning_stats'].get('broken_words_fixed', 0)}")
        else:
            print(f"❌ {result['file']}: {result.get('message', 'Unknown error')}")
    
    print("\n" + "="*80)
    print("📊 PIPELINE SUMMARY")
    print("="*80)
    print(f"Files Processed: {len(results)}")
    print(f"Total Chunks Created: {total_chunks}")
    print(f"Total Q&A Pairs: {total_qa}")
    print(f"Safety Concerns Found: {total_concerns}")
    print("\n✅ Processing complete! Data ready for ChromaDB queries.")
    print("="*80 + "\n")
    
    return {
        'files': len(results),
        'chunks': total_chunks,
        'qa_pairs': total_qa,
        'safety_concerns': total_concerns,
        'results': results,
    }


if __name__ == "__main__":
    # Example: Process target PDFs
    from neuronix_constants import DOCS_DIR
    
    target_pdfs = [
        "Abnormal Psychology_Psychology2e_WEB.pdf",
        "Applied Statistics_IntroductoryStatistics-OP.pdf"
    ]
    
    pdf_paths = [DOCS_DIR / name for name in target_pdfs if (DOCS_DIR / name).exists()]
    
    if pdf_paths:
        summary = process_multiple_pdfs(pdf_paths)
    else:
        print("❌ No PDFs found!")
