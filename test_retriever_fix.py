#!/usr/bin/env python3
"""
Test retriever after clean RustBindings reset
Verify: Documents counted correctly, similarity search works, RAG chain returns context
"""

import os
import sys
from pathlib import Path

# Set API key
os.environ['GOOGLE_API_KEY'] = 'AIzaSyCaKeDM8SY0OYpzBMhs1lH8NFSUq_SJ-S4'

sys.path.insert(0, str(Path(__file__).parent))

from backend.chat_engine import NeuronixChatEngine

print("=" * 80)
print("RETRIEVER & SIMILARITY SEARCH TEST (AFTER CLEAN RESET)")
print("=" * 80)

try:
    print("\n[1] Initializing NeuronixChatEngine with fresh ChromaDB...")
    engine = NeuronixChatEngine()
    print("    ✅ Engine initialized")
    
    print("\n[2] Getting database status...")
    db_status = engine.get_db_status()
    print(f"    Database Status:")
    print(f"      ✓ Initialized: {db_status['initialized']}")
    print(f"      ✓ Has Data: {db_status['has_data']}")
    print(f"      ✓ Document Count: {db_status['doc_count']}")
    print(f"      ✓ Message: {db_status['message']}")
    
    if db_status['doc_count'] == 0:
        print("\n    ⚠️ WARNING: No documents found!")
        print("    This suggests the re-ingestion may have failed or collection is empty.")
    else:
        print(f"\n    🎉 SUCCESS: Database has {db_status['doc_count']} documents!")
    
    print("\n[3] Testing direct similarity search...")
    if engine.vector_store:
        try:
            # Test with simple query
            test_queries = [
                "depression symptoms",
                "anxiety disorder",
                "sleep insomnia",
            ]
            
            for test_q in test_queries:
                print(f"\n    Query: '{test_q}'")
                results = engine.vector_store.similarity_search(test_q, k=2)
                
                if results:
                    print(f"      ✅ Retrieved {len(results)} documents")
                    for i, doc in enumerate(results, 1):
                        print(f"        {i}. {doc.metadata.get('source', 'unknown')[:50]}")
                        print(f"           {doc.page_content[:80]}...")
                else:
                    print(f"      ❌ No results returned")
        except Exception as e:
            print(f"      ❌ Similarity search failed: {e}")
    else:
        print("      ❌ Vector store not initialized!")
    
    print("\n[4] Testing RAG chain retrieval...")
    test_query = "depression treatment approaches"
    retrieved = engine._create_rag_chain_for_query(test_query)
    
    if retrieved and len(retrieved) > 0:
        print(f"    ✅ RAG chain returned context ({len(retrieved)} chars)")
        print(f"\n    Retrieved content preview:")
        print(f"    {retrieved[:300]}...")
    else:
        print(f"    ⚠️ RAG chain returned empty string")
        print(f"    Possible reasons:")
        print(f"     - Retriever not initialized")
        print(f"     - No matches found in database")
        print(f"     - Query too specific or embeddings mismatch")
    
    print("\n[5] Testing query-to-response pipeline...")
    test_user_query = "mujhe depression hai"
    
    print(f"\n    Input: '{test_user_query}'")
    response = engine._handle_mental_health(test_user_query)
    
    print(f"    ✅ Response generated ({len(response)} chars)")
    print(f"\n    Response preview:")
    print(f"    {response[:250]}...")
    
    # Check if response includes retrieved context (look for 📚 Source marker)
    if "Source:" in response or "📚" in response:
        print(f"\n    🎉 Response includes retrieved context!")
    else:
        print(f"\n    ℹ️ Response using fallback knowledge (no retrieved context)")
    
    print("\n" + "=" * 80)
    print("✅ RETRIEVER TEST COMPLETE")
    print("=" * 80)
    
    # Summary
    print("\nSummary:")
    print(f"  - ChromaDB Initialized: {db_status['initialized']}")
    print(f"  - Documents Available: {db_status['doc_count']}")
    print(f"  - Similarity Search: {'Working' if retrieved else 'Needs investigation'}")
    print(f"  - RAG Chain: {'Returns context' if retrieved and len(retrieved) > 0 else 'Returns empty'}")
    
except Exception as e:
    print(f"\n❌ FATAL ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
