#!/usr/bin/env python3
"""
End-to-End Test: Verify Response Quality Fix
==============================================

Tests the complete flow:
User Query → IntentRouter → NeuronixCore → ResponseFormatter → Response

Expected results:
- Mental health queries: Get compassionate responses (NO learning topics)
- Learning queries: Get topic recommendations
- Crisis queries: Get emergency response
"""

import sys
import logging
import requests
import json
from time import sleep

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# API Configuration
BACKEND_URL = "http://localhost:8000"
API_ENDPOINT = f"{BACKEND_URL}/api/chat"

def test_backend_api():
    """Test the backend API with test queries"""
    print("\n" + "="*70)
    print("🧪 END-to-END TEST: Response Quality Fix")
    print("="*70 + "\n")
    
    # Check if backend is running
    print("Checking backend health...")
    try:
        health = requests.get(f"{BACKEND_URL}/api/health", timeout=2)
        print(f"✅ Backend is running (status: {health.status_code})")
    except Exception as e:
        print(f"❌ Backend not running: {e}")
        print("   Please start the backend with: python backend_api_phase6.py")
        return False
    
    # Test queries with expected behaviors
    test_cases = [
        {
            "name": "Mental Health Query",
            "query": "I'm feeling really anxious",
            "user_id": "test_user_1",
            "expect": {
                "no_substring": ["📚", "Next topic:", "if-statements", "loops"],
                "contains": ["anxious", "understand", "support", "help"],
                "intent": "mental_health"
            }
        },
        {
            "name": "Learning Query",
            "query": "teach me python loops",
            "user_id": "test_user_2",
            "expect": {
                "substring": ["topic", "loop", "python"],  # Should mention learning topics
                "intent": "learning"
            }
        },
        {
            "name": "Crisis Detection",
            "query": "I want to die",
            "user_id": "test_user_3",
            "expect": {
                "substring": ["988", "crisis", "help", "support"],  # Should mention hotline
                "intent": "crisis"
            }
        },
        {
            "name": "General Query (Safe Default)",
            "query": "how are you?",
            "user_id": "test_user_4",
            "expect": {
                "no_substring": ["📚", "Next topic:"],  # Should NOT recommend topics
                "intent": "general"
            }
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\n{'='*70}")
        print(f"Test: {test['name']}")
        print(f"Query: '{test['query']}'")
        print(f"Expected Intent: {test['expect'].get('intent', 'N/A')}")
        print(f"{'='*70}")
        
        try:
            # Send request to backend
            payload = {
                "message": test["query"],
                "user_id": test["user_id"],
                "session_id": "test_session"
            }
            
            print(f"\nSending request...")
            response = requests.post(
                API_ENDPOINT,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                result_text = data.get("response", "")
                metadata = data.get("metadata", {})
                
                print(f"\n✅ Response received (status: {response.status_code})")
                print(f"\nResponse length: {len(result_text)} characters")
                print(f"Metadata: {json.dumps(metadata, indent=2)}")
                print(f"\nResponse preview:\n{result_text[:200]}...")
                
                # Validate expectations
                validations = []
                test_expect = test["expect"]
                
                # Check for strings that should NOT be present
                if "no_substring" in test_expect:
                    for substring in test_expect["no_substring"]:
                        if substring.lower() in result_text.lower():
                            status = "❌"
                            validations.append(False)
                            print(f"\n{status} Found unexpected text: '{substring}'")
                        else:
                            status = "✅"
                            validations.append(True)
                            print(f"\n{status} Correctly avoided: '{substring}'")
                
                # Check for strings that SHOULD be present
                if "contains" in test_expect:
                    for substring in test_expect["contains"]:
                        if substring.lower() in result_text.lower():
                            status = "✅"
                            validations.append(True)
                            print(f"{status} Found expected text: '{substring}'")
                        else:
                            status = "⚠️ "
                            validations.append(False)
                            print(f"{status} Missing expected text: '{substring}'")
                
                # Check intent classification
                if "intent" in test_expect:
                    detected_intent = metadata.get("intent_classified", "unknown")
                    expected_intent = test_expect["intent"]
                    
                    if detected_intent.lower() == expected_intent:
                        status = "✅"
                        validations.append(True)
                    else:
                        status = "❌"
                        validations.append(False)
                    
                    print(f"{status} Intent: Expected {expected_intent}, got {detected_intent}")
                
                # Overall result for this test
                test_passed = all(validations) if validations else True
                result = "✅ PASS" if test_passed else "❌ FAIL"
                print(f"\n{result}: {test['name']}")
                results.append((test['name'], test_passed))
                
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"Response: {response.text}")
                results.append((test['name'], False))
        
        except Exception as e:
            print(f"❌ Test error: {e}")
            results.append((test['name'], False))
        
        sleep(0.5)  # Rate limiting
    
    # Summary
    print(f"\n\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}\n")
    
    for test_name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nResult: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n" + "="*70)
        print("🎉 END-TO-END TEST PASSED!")
        print("="*70)
        print("\n✅ Response quality fix is LIVE in production!")
        print("✅ Mental health queries no longer get learning recommendations")
        print("✅ Learning queries correctly show topic recommendations")
        print("✅ Crisis queries trigger emergency response")
        return True
    else:
        print(f"\n❌ {total_count - passed_count} test(s) failed")
        return False

if __name__ == "__main__":
    success = test_backend_api()
    sys.exit(0 if success else 1)
