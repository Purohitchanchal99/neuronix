#!/usr/bin/env python3
import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

BASE_DIR = Path(__file__).parent
VECTOR_DB_DIR = BASE_DIR / "data" / "vector_db"

print("Loading embeddings...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

print("Loading ChromaDB...")
vector_store = Chroma(
    collection_name="neuronix_medical_kb",
    persist_directory=str(VECTOR_DB_DIR),
    embedding_function=embeddings
)

print(f"Vector store loaded")

# Simple test
print("Performing similarity_search...")
try:
    results = vector_store.similarity_search("What is depression?", k=5)
    print(f"✓ Got {len(results)} results")
    if results:
        print(f"  First: {results[0].page_content[:80]}...")
except Exception as e:
    print(f"✗ Error: {e}")
