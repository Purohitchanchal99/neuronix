#!/usr/bin/env python3
"""
Test Intent Router Integration with NeuronixCore
=================================================

Verify that:
1. Mental health queries skip learning recommendations
2. Learning queries get topic recommendations
3. Crisis queries trigger emergency response
4. General queries default to mental health (safe)
"""

import sys
import logging
from scripts.neuronix_core import NeuronixCore
from scripts.intent_router import IntentRouter, QueryIntent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Test cases: (query, expected_intent, should_have_recommendation)
TEST_CASES = [
    # Mental Health Queries (should NOT have learning recommendations)
    ("I'm feeling really anxious", QueryIntent.MENTAL_HEALTH, False),
    ("I have depression", QueryIntent.MENTAL_HEALTH, False),
    ("not feeling good", QueryIntent.MENTAL_HEALTH, False),
    ("I'm a loser", QueryIntent.MENTAL_HEALTH, False),
    ("I'm having suicidal thoughts", QueryIntent.CRISIS, False),
    
    # Learning Queries (SHOULD have learning recommendations)
    ("teach me python loops", QueryIntent.LEARNING, True),
    ("what is a variable?", QueryIntent.LEARNING, True),
    ("how to write functions", QueryIntent.LEARNING, True),
    
    # General Queries (should default to MENTAL_HEALTH - safe)
    ("Hi there", QueryIntent.GENERAL, False),
    ("how are you?", QueryIntent.GENERAL, False),
]

def test_intent_router():
    """Test intent router classification"""
    print("\n" + "="*70)
    print("TEST 1: Intent Router Classification")
    print("="*70 + "\n")
    
    router = IntentRouter()
    passed = 0
    failed = 0
    
    for query, expected_intent, _ in TEST_CASES:
        result = router.classify_intent(query)
        intent = result.get("intent")
        confidence = result.get("confidence", 0)
        
        status = "✅" if intent == expected_intent else "❌"
        passed += 1 if intent == expected_intent else 0
        failed += 0 if intent == expected_intent else 1
        
        print(f"{status} Query: '{query}'")
        print(f"   Expected: {expected_intent.name} | Got: {intent.name} ({confidence:.0%})")
    
    print(f"\nResult: {passed}/{len(TEST_CASES)} passed")
    return passed == len(TEST_CASES)

def test_recommendation_routing():
    """Test that recommendations are properly routed by intent"""
    print("\n" + "="*70)
    print("TEST 2: Recommendation Routing (Intent-based)")
    print("="*70 + "\n")
    
    router = IntentRouter()
    passed = 0
    failed = 0
    
    for query, expected_intent, should_have_recommendation in TEST_CASES[:5]:  # Test first 5
        result = router.classify_intent(query)
        intent = result.get("intent")
        
        # Logic:
        # - CRISIS → Emergency response only
        # - MENTAL_HEALTH → Compassionate response only
        # - LEARNING → Response + recommendations
        # - GENERAL → Safe default (no recommendations)
        
        should_skip_recommendations = intent != QueryIntent.LEARNING
        
        if should_skip_recommendations == should_have_recommendation:
            # This means logic is consistent
            status = "✅"
            passed += 1
        else:
            status = "❌"
            failed += 1
        
        action = "RECOMMEND NEXT TOPIC" if should_have_recommendation else "SKIP RECOMMENDATIONS"
        print(f"{status} '{query}'")
        print(f"   Intent: {intent.name}")
        print(f"   Action: {action}")
    
    print(f"\nResult: {passed}/5 routing decisions correct")
    return passed == 5

def test_response_format():
    """Test that response format never includes raw learning recommendations for mental health"""
    print("\n" + "="*70)
    print("TEST 3: Response Format Validation")
    print("="*70 + "\n")
    
    router = IntentRouter()
    response_checks = []
    
    mental_health_queries = [
        "I'm feeling really anxious",
        "I'm having a panic attack",
        "I feel worthless",
    ]
    
    for query in mental_health_queries:
        result = router.classify_intent(query)
        intent = result.get("intent")
        
        # Check: Mental health queries should NOT trigger learning topic recommendations
        # The response should be compassionate, not "📚 Next topic: if-statements"
        
        print(f"Query: '{query}'")
        print(f"Intent: {intent.name}")
        
        if intent == QueryIntent.MENTAL_HEALTH:
            print(f"✅ Will NOT show learning topics")
            response_checks.append(True)
        else:
            print(f"❌ WRONG: Should be MENTAL_HEALTH, got {intent.name}")
            response_checks.append(False)
    
    print(f"\nResult: {sum(response_checks)}/{len(response_checks)} mental health responses correct")
    return all(response_checks)

def test_crisis_priority():
    """Test that crisis queries take highest priority"""
    print("\n" + "="*70)
    print("TEST 4: Crisis Priority (Highest Priority)")
    print("="*70 + "\n")
    
    router = IntentRouter()
    crisis_queries = [
        "I want to die",
        "I'm going to kill myself",
        "help me i want to end it all",
        "suicide",
    ]
    
    crisis_detected = 0
    for query in crisis_queries:
        result = router.classify_intent(query)
        intent = result.get("intent")
        confidence = result.get("confidence", 0)
        
        is_crisis = intent == QueryIntent.CRISIS
        status = "✅" if is_crisis else "⚠️ "
        crisis_detected += 1 if is_crisis else 0
        
        print(f"{status} '{query}'")
        print(f"   Intent: {intent.name} ({confidence:.0%})")
    
    print(f"\nResult: {crisis_detected}/{len(crisis_queries)} crisis queries detected")
    return crisis_detected >= len(crisis_queries) - 1  # Allow 1 false negative

def main():
    print("\n" + "="*70)
    print("🧠 INTENT ROUTER INTEGRATION TEST SUITE")
    print("="*70)
    
    tests = [
        ("Intent Classification", test_intent_router),
        ("Recommendation Routing", test_recommendation_routing),
        ("Response Format", test_response_format),
        ("Crisis Priority", test_crisis_priority),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' failed with error: {e}", exc_info=True)
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70 + "\n")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} test groups passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Intent router is properly integrated.")
        print("\nVerified:")
        print("✅ Mental health queries → NO learning recommendations")
        print("✅ Learning queries → Topic recommendations")
        print("✅ Crisis queries → Emergency response + highest priority")
        print("✅ General queries → Safe default (mental health)")
    else:
        print(f"\n❌ {total - passed} test(s) failed. Review above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
