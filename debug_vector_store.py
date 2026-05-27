#!/usr/bin/env python3
"""
Debug the vector store initialization
"""

import os
import sys
from pathlib import Path

# Fix encoding for Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['GOOGLE_API_KEY'] = 'AIzaSyCaKeDM8SY0OYpzBMhs1lH8NFSUq_SJ-S4'

sys.path.insert(0, str(Path(__file__).parent))

from backend.chat_engine import NeuronixChatEngine

print("=" * 80)
print("VECTOR STORE DEBUG TEST")
print("=" * 80)

engine = NeuronixChatEngine()

print("\n[DEBUG] After initialization:")
print(f"  engine.embeddings: {type(engine.embeddings).__name__}")
print(f"  engine.vector_store: {type(engine.vector_store).__name__}")
print(f"  engine.retriever: {type(engine.retriever).__name__}")

# Safely print db_status
try:
    status = engine.db_status
    print(f"  db_status initialized: {status.get('initialized')}")
    print(f"  db_status has_data: {status.get('has_data')}")
    print(f"  db_status doc_count: {status.get('doc_count')}")
    print(f"  db_status message: {status.get('message')}")
except Exception as e:
    print(f"  db_status error: {e}")

if engine.vector_store:
    print("\nVECTOR STORE INITIALIZED!")
    print(f"  Type: {type(engine.vector_store).__name__}")
    print(f"  Has _client: {hasattr(engine.vector_store, '_client')}")
    
    # Try direct similarity search
    try:
        result = engine.vector_store.similarity_search("depression", k=2)
        print(f"\nSIMILARITY SEARCH WORKS! Found {len(result)} documents")
        for i, doc in enumerate(result):
            preview = doc.page_content[:100].replace('\n', ' ')
            print(f"  {i+1}. {preview}...")
    except Exception as e:
        print(f"\nSIMILARITY SEARCH FAILED: {e}")
else:
    print("\nVECTOR STORE NOT INITIALIZED")

if engine.retriever:
    print(f"\nRETRIEVER INITIALIZED!")
else:
    print(f"\nRETRIEVER NOT INITIALIZED")
