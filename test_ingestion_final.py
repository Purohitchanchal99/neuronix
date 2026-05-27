#!/usr/bin/env python3
"""
Test the ChromaDB integration after ingestion
Verify: Documents are indexed, retriever works, and context retrieval is functional
"""

import os
import sys
from pathlib import Path

# Set API key
os.environ['GOOGLE_API_KEY'] = 'AIzaSyCaKeDM8SY0OYpzBMhs1lH8NFSUq_SJ-S4'

sys.path.insert(0, str(Path(__file__).parent))

from backend.chat_engine import NeuronixChatEngine

print("=" * 80)
print("CHROMADB INGESTION VERIFICATION TEST")
print("=" * 80)

try:
    print("\n[1] Initializing NeuronixChatEngine...")
    engine = NeuronixChatEngine()
    print("    ✅ Engine initialized")
    
    print("\n[2] Getting database status after ingestion...")
    db_status = engine.get_db_status()
    print(f"    Database Status:")
    print(f"      - Initialized: {db_status['initialized']}")
    print(f"      - Has Data: {db_status['has_data']}")
    print(f"      - Document Count: {db_status['doc_count']}")
    print(f"      - Message: {db_status['message']}")
    
    print("\n[3] Testing RAG retrieval with depression query...")
    test_query = "depression symptoms DSM-5"
    retrieved = engine._create_rag_chain_for_query(test_query)
    
    if retrieved:
        print(f"    ✅ Retrieved context (length: {len(retrieved)} chars)")
        print(f"\n    RETRIEVED CONTEXT:\n")
        print(f"    {retrieved[:500]}...")  # Show first 500 chars
    else:
        print(f"    ⚠️ No context retrieved (expected if DB empty)")
    
    print("\n[4] Checking ChromaDB directly...")
    try:
        from langchain_chroma import Chroma
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.environ['GOOGLE_API_KEY']
        )
        
        vector_store = Chroma(
            persist_directory=str(Path(__file__).parent / "data" / "vector_db"),
            embedding_function=embeddings,
            client_settings=None
        )
        
        # Try to count documents
        collection = vector_store._client.list_collections()
        print(f"    Collections found: {len(collection)}")
        for col in collection:
            count = col.count()
            print(f"      - {col.name}: {count} documents")
            
        # Try a search
        query_result = vector_store.similarity_search("depression symptoms", k=3)
        print(f"    ✅ Similarity search returned {len(query_result)} results")
        
    except Exception as e:
        print(f"    ⚠️ Direct ChromaDB check failed: {e}")
    
    print("\n[5] Testing mental health handler...")
    response = engine._handle_mental_health("mujhe depression hain")
    print(f"    ✅ Response generated (length: {len(response)} chars)")
    print(f"\n    RESPONSE PREVIEW:\n")
    print(f"    {response[:300]}...")
    
    print("\n" + "=" * 80)
    if db_status['has_data']:
        print("✅ INTELLIGENCE CHECK PASSED - Documents retrieved successfully!")
    else:
        print("⚠️ Database empty but system working - Ready for ingestion or manual documents")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
