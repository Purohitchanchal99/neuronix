#!/usr/bin/env python3
import os, sys
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['GOOGLE_API_KEY'] = 'AIzaSyCaKeDM8SY0OYpzBMhs1lH8NFSUq_SJ-S4'

sys.path.insert(0, str(Path(__file__).parent))

from backend.chat_engine import NeuronixChatEngine

engine = NeuronixChatEngine()

print(f"vector_store = {engine.vector_store}")
print(f"vector_store is None: {engine.vector_store is None}")
print(f"bool(vector_store): {bool(engine.vector_store)}")

# Try similarity search directly
if engine.vector_store is not None:
    res = engine.vector_store.similarity_search("depression symptoms", k=3)
    print(f"\nSIMILARITY SEARCH RESULT: {len(res)} documents found")
    for doc in res:
        print(f"- {doc.page_content[:150]}")
else:
    print("vector_store is None - cannot search")
