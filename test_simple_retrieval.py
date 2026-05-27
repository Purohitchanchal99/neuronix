#!/usr/bin/env python3
"""
Simple test to isolate the retrieve_context error
"""
import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

print("=" * 80)
print("SIMPLE RETRIEVAL TEST")
print("=" * 80)

try:
    print("\n1. Initializing NeuronixRAGQuerySystem...")
    from scripts.query_rag_system import NeuronixRAGQuerySystem
    system = NeuronixRAGQuerySystem(num_chunks=5)
    print("   ✓ Initialized successfully")
    
    print("\n2. Testing retrieve_context()...")
    query = "What is depression?"
    print(f"   Query: '{query}'")
    
    results = system.retrieve_context(query, k=3)
    print(f"   ✓ Got {len(results)} results")
    
    if results:
        print(f"\n3. First result:")
        print(f"   {results[0].page_content[:100]}...")
        
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
