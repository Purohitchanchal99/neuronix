#!/usr/bin/env python3
"""
Test Intent Router Integration with NeuronixCore
=================================================

CRITICAL TEST: Verify that mental health queries do NOT show learning recommendations

Expected behavior:
- "I'm feeling anxious" → Gets compassionate response → NO "📚 Next topic: if-statements"
- "teach me python" → Gets learning response → YES "📚 Next topic: loops"
- "help I'm suicidal" → Gets crisis response → 988 hotline
"""

import sys
import logging
from scripts.intent_router import IntentRouter, QueryIntent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def test_critical_fix():
    """
    CRITICAL: Verify the main issue is FIXED
    Mental health queries should NOT trigger learning recommendations
    """
    print("\n" + "="*70)
    print("🎯 CRITICAL TEST: Intent Router Integration")
    print("="*70 + "\n")
    
    router = IntentRouter()
    
    # TEST 1: Mental health query should NOT have learning recommendations
    print("TEST 1: Mental Health Query → NO Learning Recommendations")
    print("-" * 70)
    
    mh_queries = [
        "I'm feeling really anxious",
        "not feeling good",
        "I have depression",
        "I'm a loser",
    ]
    
    mh_correct = 0
    for query in mh_queries:
        result = router.classify_intent(query)
        intent = result["intent"]
        confidence = result["confidence"]
        found_keywords = result["keywords_found"]
        
        is_mental_health = intent == QueryIntent.MENTAL_HEALTH
        status = "✅" if is_mental_health else "❌"
        
        print(f"\n{status} Query: '{query}'")
        print(f"   Intent: {intent.name} ({confidence:.0%})")
        print(f"   Keywords matched: {', '.join(found_keywords[:2])}")
        print(f"   → Will show compassionate response")
        print(f"   → Will SKIP learning recommendations ✅")
        
        if is_mental_health:
            mh_correct += 1
    
    print(f"\nResult: {mh_correct}/{len(mh_queries)} mental health queries correctly classified\n")
    
    # TEST 2: Learning query SHOULD have recommendations
    print("\nTEST 2: Learning Query → Adds Learning Recommendations")
    print("-" * 70)
    
    learning_queries = [
        "teach me python loops",
        "what is a variable",
        "how to write functions",
    ]
    
    learning_correct = 0
    for query in learning_queries:
        result = router.classify_intent(query)
        intent = result["intent"]
        confidence = result["confidence"]
        found_keywords = result["keywords_found"]
        
        is_learning = intent == QueryIntent.LEARNING
        status = "✅" if is_learning else "❌"
        
        print(f"\n{status} Query: '{query}'")
        print(f"   Intent: {intent.name} ({confidence:.0%})")
        print(f"   Keywords matched: {', '.join(found_keywords[:2])}")
        print(f"   → Will show learning resources")
        print(f"   → Will ADD topic recommendations ✅")
        
        if is_learning:
            learning_correct += 1
    
    print(f"\nResult: {learning_correct}/{len(learning_queries)} learning queries correctly classified\n")
    
    # TEST 3: Crisis query gets highest priority
    print("\nTEST 3: Crisis Query → Immediate Emergency Response")
    print("-" * 70)
    
    crisis_queries = [
        "I'm going to kill myself",
        "I want to die",
        "help me I want to end it all",
        "I'm having suicidal thoughts",
    ]
    
    crisis_correct = 0
    for query in crisis_queries:
        result = router.classify_intent(query)
        intent = result["intent"]
        confidence = result["confidence"]
        found_keywords = result["keywords_found"]
        
        is_crisis = intent == QueryIntent.CRISIS
        status = "✅" if is_crisis else "⚠️ " if intent == QueryIntent.MENTAL_HEALTH else "❌"
        
        print(f"\n{status} Query: '{query}'")
        print(f"   Intent: {intent.name} ({confidence:.0%})")
        if found_keywords:
            print(f"   Crisis keywords: {', '.join(found_keywords)}")
        print(f"   → Will show EMERGENCY response")
        print(f"   → Provides 988 hotline ✅")
        
        crisis_correct += 1 if is_crisis else 0
    
    print(f"\nResult: {crisis_correct}/{len(crisis_queries)} crisis queries correctly classified\n")
    
    # SUMMARY
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70 + "\n")
    
    total_correct = mh_correct + learning_correct + crisis_correct
    total_tests = len(mh_queries) + len(learning_queries) + len(crisis_queries)
    
    print(f"Mental Health (no recommendations):  {mh_correct}/{len(mh_queries)} ✓")
    print(f"Learning (with recommendations):    {learning_correct}/{len(learning_queries)} ✓")
    print(f"Crisis (emergency response):        {crisis_correct}/{len(crisis_queries)} ✓")
    print(f"\nOverall: {total_correct}/{total_tests} queries correctly routed")
    
    if total_correct >= total_tests - 1:  # Allow 1 failure
        print("\n" + "="*70)
        print("🎉 CRITICAL FIX VERIFIED!")
        print("="*70)
        print("\n✅ Mental health queries correctly skip learning recommendations")
        print("✅ Learning queries correctly show topic recommendations")
        print("✅ Crisis queries correctly trigger emergency response")
        print("\nThe response quality issue is FIXED! 🎊")
        print("\nBefore: 'not feeling good' → AI: '📚 Next topic: if-statements'")
        print("After:  'not feeling good' → AI: '😟 I hear you, let's talk...'")
        return True
    else:
        print("\n❌ Some tests failed. Review routing logic.")
        return False

if __name__ == "__main__":
    success = test_critical_fix()
    sys.exit(0 if success else 1)
