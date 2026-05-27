#!/usr/bin/env python3
"""
Retry Only Failed PDFs
======================
Re-ingest ONLY the PDFs that failed before (sirf failed PDFs ko retry karo)
NOT all PDFs - only those in failed_files.json
"""

import sys
import os

# Add scripts to path
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), "scripts")))

from scripts.neuronix_ingest import NeuronixIngestion

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔁 FAILED PDF RETRY SYSTEM")
    print("="*80)
    print("\n📋 This will retry ONLY the PDFs that failed previously.")
    print("   All already-processed PDFs will be SKIPPED.\n")
    
    ingestion = NeuronixIngestion()
    
    # Run ONLY the retry system (NOT the full ingestion)
    success = ingestion.retry_failed_pdfs()
    
    if success:
        print("\n✅ Retry complete!")
    else:
        print("\n❌ Retry failed!")
        sys.exit(1)
