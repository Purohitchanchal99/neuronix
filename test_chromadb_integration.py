#!/usr/bin/env python
"""Quick test of ChromaDB integration"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set dummy API key for testing
os.environ['GOOGLE_API_KEY'] = 'test-key'

try:
    from backend.chat_engine import NeuronixChatEngine
    
    print("\n" + "="*80)
    print("TESTING CHROMADB INTEGRATION")
    print("="*80 + "\n")
    
    print("[1] Initializing NeuronixChatEngine...")
    engine = NeuronixChatEngine()
    
    print("[2] Getting database status...")
    status = engine.get_db_status()
    
    print("\n✅ Database Status:")
    print(f"   - Initialized: {status.get('initialized', False)}")
    print(f"   - Has Data: {status.get('has_data', False)}")
    print(f"   - Document Count: {status.get('doc_count', 0)}")
    print(f"   - Message: {status.get('message', 'No message')}")
    
    print("\n[3] Checking retriever...")
    if engine.retriever:
        print("   ✅ Retriever is available")
    else:
        print("   ⚠️ Retriever is None (database likely empty)")
    
    print("\n" + "="*80)
    print("Integration test completed successfully!")
    print("="*80 + "\n")
    
except Exception as e:
    print(f"\n❌ ERROR during initialization: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
