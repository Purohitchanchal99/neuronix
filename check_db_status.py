#!/usr/bin/env python3
"""Check vector DB status and document count"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.chat_engine import NeuronixChatEngine

print("\n" + "="*80)
print("[DB CHECK] Analyzing Vector Store Status")
print("="*80 + "\n")

try:
    engine = NeuronixChatEngine()
    
    # Check DB status
    status = engine.get_db_status()
    print(f"📊 DB Status:\n{status}\n")
    
    # Check vector store
    db = engine.vector_store
    all_docs = db.get()
    
    if all_docs:
        doc_count = len(all_docs.get('ids', []))
        print(f"✅ Total documents in vector store: {doc_count}")
        if doc_count > 0:
            print(f"   Sample IDs: {all_docs['ids'][:3]}")
    else:
        print("❌ Vector store is EMPTY!")
        
    # Test a retrieval
    print("\n🔍 Testing retrieval with 'depression'...")
    results = db.similarity_search("depression", k=3)
    if results:
        print(f"✅ Retrieved {len(results)} documents:")
        for i, doc in enumerate(results[:2], 1):
            print(f"   [{i}] {doc.page_content[:100]}...")
    else:
        print("❌ Retrieval returned NO documents")
        print("\n   ACTION NEEDED: Run ingestion script to populate vector DB")
        print("   Command: python ingest_target_pdfs.py")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
