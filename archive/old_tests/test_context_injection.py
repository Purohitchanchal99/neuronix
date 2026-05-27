#!/usr/bin/env python3
"""
Direct test of context injection and LLM call
Bypasses Streamlit to see actual output
"""

import sys
import os
from pathlib import Path

# Add paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from backend.chat_engine import NeuronixChatEngine
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("[TEST] Starting Context Injection Diagnostic")
print("=" * 80)

# Initialize chat engine
try:
    print("\n[1] Initializing NeuronixChatEngine...")
    engine = NeuronixChatEngine()
    print("✅ Engine initialized")
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    sys.exit(1)

# Test query
test_query = "anxiety symptoms DSM-5"
print(f"\n[2] Test Query: '{test_query}'")

# Run the query
print("\n[3] Running chat query...")
print("=" * 80)
try:
    response = engine.chat(test_query)
    print("=" * 80)
    print(f"\n[4] Response Received:\n{response}")
except Exception as e:
    print(f"❌ Error during chat: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("[TEST] Complete")
print("=" * 80)
