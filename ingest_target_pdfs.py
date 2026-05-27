#!/usr/bin/env python3
"""
Targeted PDF Ingest with Text Cleaning Pipeline
================================================
Process ONLY 2 Failed PDFs with FULL TEXT CLEANING

🔥 Key Difference:
  Before: PDF → raw ingestion → embeddings
  After:  PDF → clean → chunk → metadata → Q&A → safety → embeddings
  
This is where the TextProcessingPipeline is actually used!
"""

import sys
import os
from pathlib import Path
import hashlib
from langchain_core.documents import Document

# Add scripts to path
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), "scripts")))

from scripts.neuronix_ingest import NeuronixIngestion
from scripts.neuronix_constants import DOCS_DIR
from scripts.text_cleaner_pipeline import TextProcessingPipeline
import logging

logger = logging.getLogger('neuronix_ingest')


def ingest_target_pdfs():
    """Ingest 2 target PDFs through cleaning pipeline"""
    
    # The 2 PDFs to ingest
    target_pdfs = [
        "Abnormal Psychology_Psychology2e_WEB.pdf",
        "Applied Statistics_IntroductoryStatistics-OP.pdf"
    ]
    
    print("\n" + "="*80)
    print("[INGESTION] TARGETED INGESTION: 2 PDFs with TEXT CLEANING PIPELINE")
    print("="*80)
    print("\nPipeline Flow:")
    print("   1. Extract raw text from PDF")
    print("   2. TextCleaner: Smart header/footer removal")
    print("   3. SmartChunker: Semantic heading-aware chunking")
    print("   4. MetadataGenerator: Frequency-based topic extraction")
    print("   5. QAGenerator: Contextual Q&A generation")
    print("   6. SafetyChecker: Pattern-based crisis detection")
    print("   7. Store cleaned chunks + embeddings in ChromaDB")
    print("\nTarget PDFs:")
    for pdf_name in target_pdfs:
        pdf_path = DOCS_DIR / pdf_name
        exists = "[OK]" if pdf_path.exists() else "[MISSING]"
        size = f"({pdf_path.stat().st_size / 1024 / 1024:.1f} MB)" if pdf_path.exists() else ""
        print(f"   {exists} {pdf_name} {size}")
    print()
    
    # Initialize ingestion engine
    ingestion = NeuronixIngestion()
    
    # Initialize cleaning pipeline
    print("[INIT] Initializing Text Cleaning Pipeline...")
    pipeline = TextProcessingPipeline()
    print("[OK] Pipeline ready!\n")
    
    # Get the PDFs
    pdf_paths = []
    for pdf_name in target_pdfs:
        pdf_path = DOCS_DIR / pdf_name
        if pdf_path.exists():
            pdf_paths.append(pdf_path)
        else:
            print(f"❌ NOT FOUND: {pdf_name}")
    
    if not pdf_paths:
        print("\n❌ No target PDFs found!")
        return False
    
    print(f"📦 Processing {len(pdf_paths)} PDFs with cleaning pipeline...\n")
    
    # Initialize vector store
    ingestion.initialize_vector_store()
    
    # Process the 2 PDFs through the pipeline
    processed = set()
    failed = {}
    total_chunks = 0
    total_qa_pairs = 0
    safety_flags = 0
    
    for pdf_path in pdf_paths:
        try:
            print(f"\n📄 Processing: {pdf_path.name}")
            print("─" * 80)
            
            # Step 1: Extract raw text from PDF
            print("   [1/7] Extracting text from PDF...")
            raw_text = ingestion.extract_text_from_pdf(pdf_path)
            
            if not raw_text:
                raise Exception("Failed to extract text from PDF")
            
            print(f"        ✅ Extracted {len(raw_text):,} characters")
            
            # Step 2-6: Run through cleaning pipeline
            print("   [2-6/7] Running cleaning pipeline...")
            result = pipeline.process(raw_text, pdf_path.name)
            
            if result['status'] != 'success':
                raise Exception(result.get('message', 'Pipeline processing failed'))
            
            chunks = result['chunks']
            
            if not chunks:
                raise Exception("Pipeline produced no chunks")
            
            print(f"        ✅ Cleaned & chunked: {len(chunks)} chunks")
            
            # Step 7: Store in vector database
            print(f"   [7/7] Storing {len(chunks)} chunks in ChromaDB...")
            
            stored_count = 0
            for i, chunk_data in enumerate(chunks):
                try:
                    # Extract chunk information
                    content = chunk_data['content']
                    metadata = chunk_data['metadata']
                    chunk_hash = chunk_data.get('chunk_hash')
                    
                    # 🔥 ENHANCE METADATA with pipeline & source info
                    metadata['source_file'] = pdf_path.name
                    metadata['cleaned'] = True  # Mark as cleaned
                    metadata['file_size_mb'] = pdf_path.stat().st_size / 1024 / 1024
                    
                    if chunk_hash:
                        metadata['chunk_hash'] = chunk_hash
                    
                    # Generate unique chunk ID
                    chunk_id = f"{pdf_path.stem}_cleaned_{i}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
                    
                    # Store in vector DB
                    ingestion.store_chunk_in_vector_db(
                        content=content,
                        metadata=metadata,
                        chunk_id=chunk_id
                    )
                    
                    stored_count += 1
                    total_chunks += 1
                    
                except Exception as chunk_err:
                    logger.error(f"        ⚠️  Failed to store chunk {i}: {chunk_err}")
                    continue
            
            print(f"        ✅ Stored {stored_count}/{len(chunks)} chunks")
            
            # Extract statistics from result
            if 'statistics' in result:
                stats = result['statistics']
                
                # Count Q&A pairs
                qa_count = stats.get('qa_pairs_generated', 0)
                if qa_count:
                    total_qa_pairs += qa_count
                    print(f"        📝 Q&A pairs: {qa_count}")
                
                # Check for safety flags
                safety_info = stats.get('safety_check', {})
                if safety_info.get('has_crisis_content'):
                    safety_flags += 1
                    print(f"        🚨 Safety flag: {safety_info.get('crisis_type', 'UNKNOWN')}")
                    logger.warning(f"SAFETY: Crisis content detected in {pdf_path.name}")
            
            # Mark as successfully processed
            processed.add(pdf_path.name)
            
            print(f"\n   ✅ Successfully processed: {pdf_path.name}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n   ❌ Failed: {error_msg}")
            failed[pdf_path.name] = {
                'file': pdf_path.name,
                'error': error_msg[:100]
            }
            logger.error(f"ERROR processing {pdf_path.name}: {error_msg}")
    
    # Final report
    print("\n" + "="*80)
    print("✅ INGESTION WITH CLEANING PIPELINE COMPLETE")
    print("="*80)
    print(f"\n📊 Results:")
    print(f"   ✅ Successfully processed: {len(processed)} PDFs")
    print(f"   ❌ Failed: {len(failed)} PDFs")
    print(f"\n📈 Statistics:")
    print(f"   Total chunks created: {total_chunks:,}")
    print(f"   Total Q&A pairs: {total_qa_pairs:,}")
    print(f"   Safety flags: {safety_flags}")
    print(f"   Vector DB embeddings: {ingestion.stats['embeddings_stored']:,}")
    
    if failed:
        print(f"\n⚠️  Failed PDFs:")
        for pdf_name, error_info in failed.items():
            print(f"   • {pdf_name}: {error_info['error']}")
        return False
    else:
        print("\n✅ All target PDFs successfully ingested with cleaning pipeline!")
        print("\n🎉 IMPROVEMENT SUMMARY:")
        print(f"   ✅ PDF noise removed: Headers/footers filtered via Counter")
        print(f"   ✅ Chunk quality improved: Semantic heading-aware splitting")
        print(f"   ✅ Metadata enriched: Frequency-based topics extracted")
        print(f"   ✅ Q&A generated: {total_qa_pairs:,} contextual pairs for RAG")
        print(f"   ✅ Safety checked: {safety_flags} flag(s) if any crisis detected")
        print("\n🚀 Ready for production queries!")
        return True

if __name__ == "__main__":
    success = ingest_target_pdfs()
    sys.exit(0 if success else 1)
