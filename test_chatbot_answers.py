#!/usr/bin/env python3
"""
COMPREHENSIVE TEST: Verify Neuronix is retrieving answers
Tests:
1. Vector DB status
2. Document retrieval  
3. Chat response generation
4. End-to-end flow
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.chat_engine import NeuronixChatEngine

print("\n" + "="*80)
print("🧪 NEURONIX TESTING SUITE - Verify Answer Generation")
print("="*80 + "\n")

# Initialize
print("📌 [STEP 1] Initializing Chat Engine...")
try:
    engine = NeuronixChatEngine()
    print("✅ Chat engine initialized successfully\n")
except Exception as e:
    print(f"❌ Failed to initialize: {e}\n")
    sys.exit(1)

# Test 1: Check Vector DB
print("📌 [STEP 2] Checking Vector Database...")
try:
    db_status = engine.get_db_status()
    print(f"✅ DB Status:\n{db_status}\n")
except Exception as e:
    print(f"❌ Error checking DB: {e}\n")

# Test 2: Test Retrieval
print("📌 [STEP 3] Testing Document Retrieval...")
test_queries = [
    "depression symptoms",
    "anxiety treatment",
    "stress management",
    "sleep problems",
    "mental health",
]

for query in test_queries:
    try:
        docs = engine.vector_store.similarity_search(query, k=2)
        if docs:
            print(f"✅ Query '{query}': Retrieved {len(docs)} docs")
            print(f"   Sample: {docs[0].page_content[:100]}...")
        else:
            print(f"⚠️  Query '{query}': NO documents retrieved")
    except Exception as e:
        print(f"❌ Query '{query}': Error - {e}")

print("\n")

# Test 3: Test Chat Responses
print("📌 [STEP 4] Testing Chat Responses...")
test_messages = [
    "i am feeling stressed",
    "mujhe anxiety hai",
    "neend nahi aa rahi",
    "depression se suffering kar raha hoon",
    "kaise feel kar rahe ho?",
]

for msg in test_messages:
    print(f"\n👤 User: {msg}")
    try:
        response = engine.chat(msg)
        print(f"🧠 Neuronix: {response[:200]}...")
        
        # Check if response is empty or generic
        if len(response) < 50:
            print("⚠️  WARNING: Response seems too short!")
        elif "relevant documents" in response.lower() or "nahi mile" in response.lower():
            print("⚠️  WARNING: No documents retrieved (fallback response)")
        else:
            print("✅ Response looks good")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*80)
print("🧪 TEST COMPLETE")
print("="*80 + "\n")
