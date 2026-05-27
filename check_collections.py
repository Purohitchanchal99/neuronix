#!/usr/bin/env python3
import os, sys
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['GOOGLE_API_KEY'] = 'AIzaSyCaKeDM8SY0OYpzBMhs1lH8NFSUq_SJ-S4'

sys.path.insert(0, str(Path(__file__).parent))

from backend.chat_engine import NeuronixChatEngine

engine = NeuronixChatEngine()

print("Checking collections...")
try:
    collections = engine.vector_store._client.list_collections()
    print(f"Found {len(collections)} collections:")
    
    for col in collections:
        count = col.count()
        print(f"  - {col.name}: {count} documents")
        
        if count > 0:
            # Get first doc from collection
            items = col.get(limit=1)
            if items and items.get('documents'):
                print(f"    First doc: {items['documents'][0][:100]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
