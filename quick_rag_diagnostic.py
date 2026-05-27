#!/usr/bin/env python3
"""
QUICK RAG DIAGNOSTIC - File-based analysis
Check embedding model configuration without loading heavy dependencies
"""

import sys
from pathlib import Path
import re

BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "scripts"

print("\n" + "="*80)
print("⚡ RAG PIPELINE QUICK DIAGNOSTIC (File Analysis)")
print("="*80 + "\n")

# ================================================================
# CHECK 1: Vector Store Exists
# ================================================================
print("CHECK 1: Vector Store Status")
print("─" * 80)

vector_db_dir = BASE_DIR / "data" / "vector_db"
if vector_db_dir.exists():
    files = list(vector_db_dir.iterdir())
    print(f"✅ Vector DB directory exists: {vector_db_dir}")
    print(f"   Contains {len(files)} items")
    
    # Check for important files
    if (vector_db_dir / "chroma.sqlite3").exists():
        print(f"   ✅ chroma.sqlite3 found (vectors are stored)")
    else:
        print(f"   ⚠️  chroma.sqlite3 NOT found (likely empty)")
else:
    print(f"❌ Vector DB directory NOT found: {vector_db_dir}")
    print("   → Ingestion pipeline not run yet")

# ================================================================
# CHECK 2: Embedding Model Mismatch (CRITICAL)
# ================================================================
print("\n\nCHECK 2: Embedding Model Consistency")
print("─" * 80)

ingest_file = SCRIPTS_DIR / "ingest_data.py"
query_file = SCRIPTS_DIR / "query_rag_system.py"

ingest_model = "NOT FOUND"
query_model = "NOT FOUND"
ingest_issue = None

if ingest_file.exists():
    with open(ingest_file, 'r', encoding='utf-8') as f:
        ingest_content = f.read()
    
    # Check for embedding model
    if 'model="models/embedding-001"' in ingest_content:
        ingest_model = "models/embedding-001"
        ingest_issue = "INVALID - HuggingFaceEmbeddings doesn't support Google models!"
    elif "all-MiniLM-L6-v2" in ingest_content:
        ingest_model = "all-MiniLM-L6-v2"
    elif "GoogleGenerativeAIEmbeddings" in ingest_content:
        ingest_model = "GoogleGenerativeAIEmbeddings"
    else:
        # Try to find what embeddings class is used
        match = re.search(r'HuggingFaceEmbeddingsClass\(model[_name]*="([^"]+)"', ingest_content)
        if match:
            ingest_model = match.group(1)
            if "google" in ingest_model.lower() or "models/" in ingest_model:
                ingest_issue = "INVALID - HuggingFaceEmbeddings incompatible!"

if query_file.exists():
    with open(query_file, 'r', encoding='utf-8') as f:
        query_content = f.read()
    
    if "all-MiniLM-L6-v2" in query_content:
        query_model = "all-MiniLM-L6-v2"
    elif "sentence-transformers" in query_content:
        match = re.search(r'"(sentence-transformers/[^"]+)"', query_content)
        if match:
            query_model = match.group(1)

print(f"\nIngestion Pipeline (ingest_data.py):")
print(f"  Model: {ingest_model}")
if ingest_issue:
    print(f"  Status: ❌ {ingest_issue}")
else:
    print(f"  Status: ✅")

print(f"\nRetrieval Pipeline (query_rag_system.py):")
print(f"  Model: {query_model}")
if query_model == "all-MiniLM-L6-v2":
    print(f"  Status: ✅")
else:
    print(f"  Status: ⚠️  ")

if ingest_model == query_model and not ingest_issue:
    print(f"\n✅ EMBEDDING MODELS MATCH")
else:
    print(f"\n❌ EMBEDDING MISMATCH DETECTED!")
    print(f"   Ingestion: {ingest_model}")
    print(f"   Retrieval: {query_model}")
    if ingest_issue:
        print(f"   Issue: {ingest_issue}")

# ================================================================
# CHECK 3: Chunking Configuration
# ================================================================
print("\n\nCHECK 3: Chunking Configuration")
print("─" * 80)

if ingest_file.exists():
    with open(ingest_file, 'r', encoding='utf-8') as f:
        ingest_content = f.read()
    
    # Find chunk configuration
    chunk_size_match = re.search(r'CHUNK_SIZE\s*=\s*(\d+)', ingest_content)
    chunk_overlap_match = re.search(r'CHUNK_OVERLAP\s*=\s*(\d+)', ingest_content)
    
    if chunk_size_match:
        chunk_size = chunk_size_match.group(1)
        print(f"Chunk Size: {chunk_size} characters")
        if int(chunk_size) > 800:
            print("  ⚠️  Large chunks (>800) may lose semantic precision")
        elif int(chunk_size) < 300:
            print("  ⚠️  Small chunks (<300) may be too granular")
        else:
            print("  ✅ Good chunk size")
    
    if chunk_overlap_match:
        chunk_overlap = chunk_overlap_match.group(1)
        overlap_pct = (int(chunk_overlap) / int(chunk_size if chunk_size_match else 1000)) * 100
        print(f"Chunk Overlap: {chunk_overlap} characters ({overlap_pct:.0f}%)")

# ================================================================
# CHECK 4: Prompt Template
# ================================================================
print("\n\nCHECK 4: Context Injection in Prompt")
print("─" * 80)

if query_file.exists():
    with open(query_file, 'r', encoding='utf-8') as f:
        query_content = f.read()
    
    if "context_str" in query_content and "CONTEXT FROM TEXTBOOKS" in query_content:
        print("✅ Prompt template includes retrieved context")
        print("✅ Context is injected before LLM call")
    else:
        print("❌ Context might not be injected into prompt")

# ================================================================
# DIAGNOSIS
# ================================================================
print("\n\n" + "="*80)
print("🎯 DIAGNOSIS")
print("="*80 + "\n")

issues = []

if ingest_issue:
    issues.append("EMBEDDING_MISMATCH")
if ingest_model != query_model:
    issues.append("MODEL_MISMATCH")
if not (vector_db_dir / "chroma.sqlite3").exists():
    issues.append("EMPTY_VECTOR_DB")

if not issues:
    print("✅ Configuration looks correct!")
    print("   Likely issue: Vector DB might be empty or outdated")
    print("\n   → Run ingestion: python scripts/ingest_data.py")
else:
    print(f"Found {len(issues)} issues:\n")
    
    for i, issue in enumerate(issues, 1):
        if issue == "EMBEDDING_MISMATCH":
            print(f"{i}. ❌ EMBEDDING MISMATCH (CRITICAL)")
            print(f"   Location: ingest_data.py line ~133")
            print(f"   Problem: HuggingFaceEmbeddings(model=\"models/embedding-001\")")
            print(f"   Fix: Change to HuggingFaceEmbeddings(model_name=\"sentence-transformers/all-MiniLM-L6-v2\")")
            
        elif issue == "MODEL_MISMATCH":
            print(f"{i}. ❌ EMBEDDING MODEL MISMATCH")
            print(f"   Ingestion uses: {ingest_model}")
            print(f"   Retrieval uses: {query_model}")
            print(f"   Fix: Make them match, then re-index")
            
        elif issue == "EMPTY_VECTOR_DB":
            print(f"{i}. ⚠️  EMPTY VECTOR DATABASE")
            print(f"   No chroma.sqlite3 found")
            print(f"   Fix: Run ingestion pipeline first")

# ================================================================
# ACTION PLAN
# ================================================================
print("\n\n" + "="*80)
print("📋 RECOMMENDED ACTION PLAN")
print("="*80 + "\n")

if "EMBEDDING_MISMATCH" in issues:
    print("1️⃣  FIX EMBEDDING MISMATCH (Critical)")
    print("   Edit: scripts/ingest_data.py")
    print("   Line: ~133")
    print("   Find: HuggingFaceEmbeddingsClass(model=\"models/embedding-001\")")
    print("   Replace: HuggingFaceEmbeddings(model_name=\"sentence-transformers/all-MiniLM-L6-v2\")")
    print()

if "EMPTY_VECTOR_DB" in issues or "MODEL_MISMATCH" in issues:
    print(f"2️⃣  DELETE OLD VECTOR DATABASE")
    print(f"   Delete folder: {vector_db_dir}")
    print()

print("3️⃣  RE-RUN INGESTION")
print("   python scripts/ingest_data.py")
print()

print("4️⃣  TEST RETRIEVAL")
print("   python scripts/query_rag_system.py")
print("   Or: python neuronix_query.py \"What is anxiety?\"")
print("\n" + "="*80)
