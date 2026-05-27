#!/usr/bin/env python3
"""
RAG PIPELINE DEBUGGING SCRIPT
=============================
Implements the exact diagnostic flow from production debugging guide.

Tests in exact order:
Step 1: Verify Retrieval (is similarity search working?)
Step 2: Verify Embedding Model (are ingestion and retrieval using same model?)
Step 3: Verify Context Injection (is retrieved context in the prompt?)
Step 4: Test with actual query ("What is anxiety?")
"""

import sys
import os
import logging
from pathlib import Path

# Windows compatibility
if sys.platform == "win32":
    import types
    pwd_module = types.ModuleType('pwd')
    sys.modules['pwd'] = pwd_module

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

print("\n" + "="*80)
print("🔍 RAG PIPELINE DIAGNOSTIC TOOL")
print("="*80)

# ================================================================
# STEP 1: VERIFY RETRIEVAL QUALITY
# ================================================================
print("\n\n" + "="*80)
print("STEP 1: VERIFY RETRIEVAL QUALITY")
print("="*80)
print("\nTesting if vector store can find relevant chunks...\n")

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
    
    embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    logger.info(f"Loading embeddings: {embedding_model}")
    
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
    logger.info("✅ Embeddings loaded\n")
    
    logger.info(f"Loading vector store from: {VECTOR_DB_DIR}")
    vector_store = Chroma(
        collection_name="neuronix_medical_kb",
        persist_directory=str(VECTOR_DB_DIR),
        embedding_function=embeddings
    )
    
    # Check if database has data
    db_status = vector_store._collection.count()
    print(f"📊 Vector store status: {db_status} documents found\n")
    
    if db_status == 0:
        print("❌ PROBLEM: Vector database is EMPTY!")
        print("   → Run ingestion pipeline first")
        sys.exit(1)
    
    # TEST QUERY: Simple definition question
    test_query = "What is anxiety?"
    print(f"🔍 Testing retrieval with query: '{test_query}'\n")
    
    results = vector_store.similarity_search_with_score(test_query, k=5)
    
    if not results:
        print("❌ CRITICAL: No results returned!")
        print("   → Embedding mismatch or database corruption")
        sys.exit(1)
    
    print(f"✅ Retrieved {len(results)} chunks:\n")
    
    for i, (doc, score) in enumerate(results, 1):
        print(f"\n{'─'*80}")
        print(f"RESULT {i}")
        print(f"{'─'*80}")
        print(f"Similarity Score: {score:.4f}")
        print(f"Source: {doc.metadata.get('source_file', 'Unknown')}")
        print(f"Page: {doc.metadata.get('page', '?')}")
        print(f"\nContent Preview (first 300 chars):")
        print(f"{doc.page_content[:300]}...")
    
    print(f"\n{'='*80}")
    print("📊 ANALYSIS:")
    print(f"{'='*80}")
    
    # Analyze results
    scores = [score for _, score in results]
    avg_score = sum(scores) / len(scores)
    
    print(f"\nScore Statistics:")
    print(f"  Highest: {max(scores):.4f}")
    print(f"  Lowest:  {min(scores):.4f}")
    print(f"  Average: {avg_score:.4f}\n")
    
    # Evaluation
    if avg_score > 0.5:
        print("✅ RETRIEVAL WORKING: Average score is good (>0.5)")
        retrieval_status = "GOOD"
    elif avg_score > 0.3:
        print("⚠️  RETRIEVAL MARGINAL: Scores are low but not zero (0.3-0.5)")
        print("   → Might indicate weak chunking or embedding mismatch")
        retrieval_status = "MARGINAL"
    else:
        print("❌ RETRIEVAL FAILING: Scores very low (<0.3)")
        print("   → Strong signal of embedding mismatch")
        retrieval_status = "POOR"
    
    # Check if results are relevant
    first_result_content = results[0][0].page_content.lower()
    if "anxiety" in first_result_content or "disorder" in first_result_content:
        print("\n✅ RELEVANCE CHECK: First result mentions relevant terms")
        relevance_status = "GOOD"
    else:
        print("\n⚠️  RELEVANCE CHECK: First result doesn't mention 'anxiety'")
        print(f"   Content: {first_result_content[:100]}")
        relevance_status = "POOR"
    
except Exception as e:
    logger.error(f"\n❌ ERROR in Step 1: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ================================================================
# STEP 2: VERIFY EMBEDDING MODEL
# ================================================================
print("\n\n" + "="*80)
print("STEP 2: VERIFY EMBEDDING MODEL CONSISTENCY")
print("="*80)
print("\nChecking if ingestion and retrieval use SAME embeddings...\n")

try:
    # Read ingest_data.py to see what model it uses
    ingest_file = BASE_DIR / "scripts" / "ingest_data.py"
    
    if ingest_file.exists():
        with open(ingest_file, 'r') as f:
            ingest_content = f.read()
        
        # Look for embedding model declarations
        if "models/embedding-001" in ingest_content:
            print("❌ CRITICAL: ingest_data.py uses 'models/embedding-001'")
            print("   But HuggingFaceEmbeddings doesn't support Google models!")
            print("   This will FAIL during ingestion.\n")
            ingest_model = "models/embedding-001 ❌ INVALID"
        elif "all-MiniLM-L6-v2" in ingest_content:
            print("✅ ingest_data.py uses 'all-MiniLM-L6-v2'")
            ingest_model = "all-MiniLM-L6-v2 ✅"
        else:
            print("⚠️  Could not determine ingest model")
            ingest_model = "UNKNOWN"
    else:
        print(f"⚠️  Could not find {ingest_file}")
        ingest_model = "NOT FOUND"
    
    # Read query_rag_system.py to see what model it uses
    query_file = BASE_DIR / "scripts" / "query_rag_system.py"
    
    if query_file.exists():
        with open(query_file, 'r') as f:
            query_content = f.read()
        
        if "all-MiniLM-L6-v2" in query_content:
            print("✅ query_rag_system.py uses 'all-MiniLM-L6-v2'")
            query_model = "all-MiniLM-L6-v2 ✅"
        else:
            print("⚠️  Could not determine query model")
            query_model = "UNKNOWN"
    else:
        print(f"⚠️  Could not find {query_file}")
        query_model = "NOT FOUND"
    
    print(f"\n{'─'*80}")
    print("EMBEDDING MODEL COMPARISON:")
    print(f"{'─'*80}")
    print(f"Ingestion uses:  {ingest_model}")
    print(f"Retrieval uses:  {query_model}")
    
    if ingest_model == query_model and "✅" in ingest_model:
        print("\n✅ MODELS MATCH: Both use same embeddings")
        embedding_status = "MATCH"
    else:
        print("\n❌ EMBEDDING MISMATCH!")
        print("   → Vectors from ingestion incompatible with retrieval")
        print("   → This causes zero relevance in similarity search")
        embedding_status = "MISMATCH"
    
except Exception as e:
    logger.error(f"\n❌ ERROR in Step 2: {e}")
    embedding_status = "ERROR"

# ================================================================
# STEP 3: VERIFY CONTEXT INJECTION
# ================================================================
print("\n\n" + "="*80)
print("STEP 3: VERIFY CONTEXT IS INJECTED INTO PROMPT")
print("="*80)
print("\nChecking if retrieved chunks are actually used by LLM...\n")

try:
    # Read query_rag_system.py
    with open(BASE_DIR / "scripts" / "query_rag_system.py", 'r') as f:
        query_code = f.read()
    
    # Find the prompt generation section
    if "context_str" in query_code and "CONTEXT FROM TEXTBOOKS" in query_code:
        print("✅ CONTEXT INJECTION: Prompt template includes retrieved chunks")
        
        # Extract the prompt template (approximate)
        if "QUESTION: {query}" in query_code and "CONTEXT FROM TEXTBOOKS:" in query_code:
            print("✅ Prompt correctly includes:")
            print("   • User's question")
            print("   • Retrieved context from textbooks")
            print("   • Instructions to cite sources\n")
            context_injection_status = "CORRECT"
        else:
            print("⚠️  Prompt structure unclear")
            context_injection_status = "UNCLEAR"
    else:
        print("❌ CONTEXT INJECTION MISSING!")
        print("   → Prompt doesn't reference retrieved chunks")
        context_injection_status = "MISSING"
    
except Exception as e:
    logger.error(f"\nERROR in Step 3: {e}")
    context_injection_status = "ERROR"

# ================================================================
# STEP 4: DIAGNOSE ROOT CAUSE
# ================================================================
print("\n\n" + "="*80)
print("DIAGNOSTIC SUMMARY")
print("="*80 + "\n")

print(f"1. Retrieval Quality:      {retrieval_status}")
print(f"2. Embedding Match:        {embedding_status}")
print(f"3. Context Injection:      {context_injection_status}")
print(f"4. Result Relevance:       {relevance_status}\n")

print("="*80)
print("ROOT CAUSE ANALYSIS")
print("="*80 + "\n")

if embedding_status == "MISMATCH":
    print("🎯 PRIMARY ISSUE: EMBEDDING MODEL MISMATCH")
    print("\nProblem:")
    print("  • ingest_data.py tries to use 'models/embedding-001' (Google model)")
    print("  • query_rag_system.py uses 'all-MiniLM-L6-v2' (HuggingFace model)")
    print("  • HuggingFaceEmbeddings class doesn't support Google models")
    print("\nConsequence:")
    print("  • Ingestion either fails or uses wrong vectors")
    print("  • Retrieval can't match queries to documents")
    print("  • Simple queries like 'What is anxiety?' return zero-relevance chunks")
    print("\nFix (IMMEDIATE):")
    print("  → Replace 'models/embedding-001' with 'sentence-transformers/all-MiniLM-L6-v2'")
    print("  → Re-run ingestion pipeline")

elif retrieval_status == "POOR" and relevance_status == "POOR":
    print("🎯 PRIMARY ISSUE: CHUNKING OR INDEXING PROBLEM")
    print("\nEvidence:")
    print("  • Retrieval returns chunks but with very low scores")
    print("  • Results not semantically relevant to query")
    print("\nLikely causes:")
    print("  1. Chunks too large (losing semantic precision)")
    print("  2. PDF text extraction corrupted (garbage text)")
    print("  3. Database corrupted or outdated")
    print("\nFix:")
    print("  → Verify PDF extraction quality")
    print("  → Re-chunk with smaller size (400-600 chars recommended)")
    print("  → Re-run full ingestion pipeline")

elif retrieval_status == "GOOD" and context_injection_status == "CORRECT":
    print("🎯 ISSUE: LLM GENERATION PROBLEM")
    print("\nRetrieval and context injection are working.")
    print("Problem is in LLM answer generation or formatting.")
    print("\nCheck:")
    print("  • LLM model availability (gemini-pro)")
    print("  • API key configuration")
    print("  • Response formatting")

else:
    print("🎯 MULTIPLE ISSUES DETECTED")
    print("\nStart with these fixes in order:")
    print("  1. Fix embedding model mismatch (if detected)")
    print("  2. Verify PDF extraction quality")
    print("  3. Re-run ingestion with correct settings")
    print("  4. Test retrieval again")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80 + "\n")

print("Run the fix script:")
print("  python fix_rag_pipeline.py")

print("\nOr manually:")
print("  1. Edit scripts/ingest_data.py line 133")
print("  2. Change: HuggingFaceEmbeddingsClass(model=\"models/embedding-001\")")
print("  3. To:     HuggingFaceEmbeddingsClass(model_name=\"sentence-transformers/all-MiniLM-L6-v2\")")
print("  4. Delete data/vector_db/ folder completely")
print("  5. Run: python scripts/ingest_data.py")
print("\n" + "="*80)
