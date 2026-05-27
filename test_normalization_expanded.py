#!/usr/bin/env python3
"""
Test expanded normalization dictionary
Quick validation of all new Hinglish variants
"""

import sys
sys.path.insert(0, 'backend')

from chat_engine import NeuronixChatEngine

# Initialize engine (API key loaded from environment)
engine = NeuronixChatEngine()

# Test cases for new normalization variants
test_cases = {
    # User's explicit requests
    "neend nai aa rahi hai": ["neend nahi", "aa rahi"],  # neend nai → neend nahi
    "mujhe thak gya hoon": ["thak gaya"],                # thak gya → thak gaya
    "ye kaunsii baat hai?": ["kaunsi"],                  # komsi → kaunsi (approx)
    "gussa a rha hai bilkul": ["gussa aa raha"],         # gussa a rha → gussa aa raha
    
    # Original variants (should still work)
    "tensio aur depression": ["tension", "depression"],
    "depresun aur anxiety": ["depression", "anxiety"],
    "neend nahi aur thak gaayi": ["neend nahi", "thak gaya", "tired"],
    
    # Real-world complex strings
    "mujhe thak gya hai neend nai aa rahi gussa bhi aa rha": [
        "thak gaya", "neend nahi", "gussa aa raha"
    ],
}

print("=" * 60)
print("NORMALIZATION EXTENDED TEST")
print("=" * 60)

passed = 0
failed = 0

for query, expected_keywords in test_cases.items():
    normalized = engine._normalize_text_rule_based(query)
    
    # Check if all expected keywords are in normalized text
    found_all = all(kw in normalized for kw in expected_keywords)
    
    status = "✅ PASS" if found_all else "❌ FAIL"
    passed += found_all
    failed += not found_all
    
    print(f"\n{status}")
    print(f"  Input:      {query}")
    print(f"  Normalized: {normalized}")
    print(f"  Expected:   {expected_keywords}")
    print(f"  Found:      {[kw for kw in expected_keywords if kw in normalized]}")

print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)}")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
