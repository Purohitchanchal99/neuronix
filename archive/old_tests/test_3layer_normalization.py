"""
Test Suite: 3-Layer Normalization System
=========================================

Tests the production-grade normalization pipeline:
- Layer 1: Dictionary (fast fixes)
- Layer 2: Pattern normalization (regex)
- Layer 3: Fuzzy word correction

Usage: python test_3layer_normalization.py
"""

import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from chat_engine import NeuronixChatEngine

def test_layer1_dictionary():
    """Test Layer 1: Dictionary fast fixes"""
    print("\n" + "="*60)
    print("LAYER 1: DICTIONARY REPLACEMENTS (FAST)")
    print("="*60)
    
    engine = NeuronixChatEngine()
    
    test_cases = [
        ("tensio", "tension"),
        ("komsi", "kaunsi"),
        ("komssi", "kaunsi"),
        ("neend nai", "neend nahi"),
        ("neend nhi", "neend nahi"),
        ("thak gya", "thak gaya"),
        ("depresun", "depression"),
        ("depreshun", "depression"),
        ("gussa a rha", "gussa aa raha"),
        ("mook", "book"),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected in test_cases:
        result = engine._normalize_text_rule_based(input_text)
        status = "✅ PASS" if expected in result else "❌ FAIL"
        
        print(f"  {status} | '{input_text}' → '{result}'")
        if expected in result:
            passed += 1
        else:
            failed += 1
            print(f"         Expected to contain: '{expected}'")
    
    print(f"\nLayer 1 Results: {passed} passed, {failed} failed")
    return passed, failed


def test_layer2_pattern():
    """Test Layer 2: Regex pattern normalization"""
    print("\n" + "="*60)
    print("LAYER 2: PATTERN NORMALIZATION (REGEX)")
    print("="*60)
    
    engine = NeuronixChatEngine()
    
    # Test cases with spacing variations and pattern matches
    test_cases = [
        ("neend  nai", "neend nahi"),          # Extra space
        ("thak    gya", "thak gaya"),          # Multiple spaces
        ("gussa  a  rha", "gussa aa raha"),    # Multiple spaces
        ("tensio", "tension"),                 # Pattern
        ("depresun", "depression"),            # Pattern
        ("komssi", "kaunsi"),                  # Pattern
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected in test_cases:
        result = engine._normalize_text_rule_based(input_text)
        status = "✅ PASS" if expected in result else "❌ FAIL"
        
        print(f"  {status} | '{input_text}' → '{result}'")
        if expected in result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nLayer 2 Results: {passed} passed, {failed} failed")
    return passed, failed


def test_layer3_fuzzy():
    """Test Layer 3: Fuzzy word correction"""
    print("\n" + "="*60)
    print("LAYER 3: FUZZY WORD CORRECTION")
    print("="*60)
    
    engine = NeuronixChatEngine()
    
    # Words that should be corrected by fuzzy matching
    test_cases = [
        ("stres", "stress"),        # Minor typo: missing s
        ("anxeity", "anxiety"),     # Common misspelling
        ("depresion", "depression"), # Missing 's'
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected in test_cases:
        result = engine._normalize_text_rule_based(input_text)
        status = "✅ PASS" if expected in result else "❌ FAIL"
        
        print(f"  {status} | '{input_text}' → '{result}'")
        if expected in result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nLayer 3 Results: {passed} passed, {failed} failed")
    return passed, failed


def test_full_pipeline():
    """Test full 3-layer pipeline with complex inputs"""
    print("\n" + "="*60)
    print("FULL PIPELINE: COMPLEX REAL-WORLD INPUTS")
    print("="*60)
    
    engine = NeuronixChatEngine()
    
    complex_cases = [
        (
            "mujhe tensio aur gussa a rha tha",
            ["tension", "gussa aa raha"],
            "Hinglish with typos and spacing"
        ),
        (
            "neend nai aa rahi aur thak gya hoon",
            ["neend nahi", "thak gaya"],
            "Sleep and tiredness with variants"
        ),
        (
            "depresun ke wajah se stress aur anxeity",
            ["depression", "stress", "anxiety"],
            "Medical terms with typos"
        ),
        (
            "kaunsi book padhu self help ke liye",
            ["kaunsi", "book", "self help"],
            "Book recommendation question"
        ),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected_terms, description in complex_cases:
        result = engine._normalize_text_rule_based(input_text)
        
        # Check if all expected terms are in result
        all_match = all(term in result for term in expected_terms)
        status = "✅ PASS" if all_match else "❌ FAIL"
        
        print(f"\n  {status} | {description}")
        print(f"         Input:  '{input_text}'")
        print(f"         Output: '{result}'")
        print(f"         Looking for: {expected_terms}")
        
        if all_match:
            passed += 1
        else:
            failed += 1
            for term in expected_terms:
                if term not in result:
                    print(f"         Missing: '{term}'")
    
    print(f"\nFull Pipeline Results: {passed} passed, {failed} failed")
    return passed, failed


def test_unknown_logging():
    """Test unknown input logging (for auto-learning)"""
    print("\n" + "="*60)
    print("BONUS: UNKNOWN INPUT LOGGING (AUTO-LEARNING PREP)")
    print("="*60)
    
    engine = NeuronixChatEngine()
    
    # These inputs should be logged if no changes were made
    test_inputs = [
        "normal english text",
        "already normalized hinglish",
        "hello world",
    ]
    
    print(f"  Initial unknown log size: {len(engine.UNKNOWN_LOG)}")
    
    for text in test_inputs:
        result = engine._normalize_text_rule_based(text)
        print(f"  Processed: '{text}'")
    
    print(f"  Final unknown log size: {len(engine.UNKNOWN_LOG)}")
    print(f"  Logged inputs (potential patterns to learn): {engine.UNKNOWN_LOG[:5]}")
    
    if len(engine.UNKNOWN_LOG) > 0:
        print("  ✅ Auto-learning logging working (foundation ready)")
    else:
        print("  ℹ️  No unknown inputs logged yet")


def run_all_tests():
    """Run complete test suite"""
    print("\n")
    print("████████████████████████████████████████████████████████")
    print("  3-LAYER NORMALIZATION TEST SUITE")
    print("  Production-Grade Hinglish NLP System")
    print("████████████████████████████████████████████████████████")
    
    total_passed = 0
    total_failed = 0
    
    try:
        # Layer 1 Tests
        p, f = test_layer1_dictionary()
        total_passed += p
        total_failed += f
        
        # Layer 2 Tests
        p, f = test_layer2_pattern()
        total_passed += p
        total_failed += f
        
        # Layer 3 Tests
        p, f = test_layer3_fuzzy()
        total_passed += p
        total_failed += f
        
        # Full Pipeline Tests
        p, f = test_full_pipeline()
        total_passed += p
        total_failed += f
        
        # Unknown Logging (Bonus)
        test_unknown_logging()
        
    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Total Passed: ✅ {total_passed}")
    print(f"Total Failed: ❌ {total_failed}")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED! System is production-ready.")
        return True
    else:
        print(f"\n⚠️  {total_failed} tests failed. Review above for details.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
