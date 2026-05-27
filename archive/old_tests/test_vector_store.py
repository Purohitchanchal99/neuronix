#!/usr/bin/env python3
"""Quick test to verify vector store contents and retrieval"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

VECTOR_DB_DIR = Path(__file__).parent / "data" / "vector_db"
cache_folder = Path(__file__).parent / "hf_cache"

print("\n" + "="*80)
print("🔍 VECTOR STORE DIAGNOSTIC")
print("="*80 + "\n")

# Initialize embeddings
print("📥 Loading embeddings...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    cache_folder=str(cache_folder),
    model_kwargs={"trust_remote_code": True}
)

# Load vector store  
print(f"🗄️  Loading vector store from: {VECTOR_DB_DIR}")
vector_store = Chroma(
    persist_directory=str(VECTOR_DB_DIR),
    embedding_function=embeddings
)

# Check collections
print("\n📊 Collections in ChromaDB:")
try:
    client = vector_store._client
    collections = client.list_collections()
    print(f"Found {len(collections)} collection(s)")
    
    for col in collections:
        count = col.count()
        print(f"   • {col.name}: {count} documents")
except Exception as e:
    print(f"❌ Error listing collections: {e}")

# Try similarity search
print("\n🔎 Testing retrieval with 'depression'...")
try:
    docs = vector_store.similarity_search("depression", k=3)
    if docs:
        print(f"✅ Retrieved {len(docs)} documents:")
        for i, doc in enumerate(docs, 1):
            content_preview = doc.page_content[:100].replace('\n', ' ')
            metadata = doc.metadata
            print(f"\n   [{i}] {content_preview}...")
            print(f"       Source: {metadata.get('source_file', 'Unknown')}")
    else:
        print("❌ NO documents retrieved!")
except Exception as e:
    print(f"❌ Retrieval error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
