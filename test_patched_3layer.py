"""
Test Suite: PATCHED 3-Layer Normalization with Critical Word Protection
=========================================================================

Tests the production-grade normalization pipeline:
- Layer 1: Dictionary (fast fixes)
- Layer 2: Pattern normalization (STRICTER regex)
- Layer 3: Fuzzy word correction (WITH CRITICAL WORD PROTECTION)

Key Fix: Critical words like "neend", "gussa", "tension" NEVER get fuzzy-corrected

Usage: python test_patched_3layer.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from chat_engine import NeuronixChatEngine

def test_critical_word_protection():
    """Test that CRITICAL WORDS are protected from fuzzy correction"""
    print("\n" + "="*70)
    print("TEST 1: CRITICAL WORD PROTECTION (Never fuzzy-correct)")
    print("="*70)
    
    engine = NeuronixChatEngine()
    
    test_cases = [
        # (input, should_contain, reason)
        ("neend", "neend", "Sleep word protected from fuzzy"),
        ("gussa", "gussa", "Anger word protected from fuzzy"),
        ("tension", "tension", "Tension word protected from fuzzy"),
        ("depression", "depression", "Depression word protected from fuzzy"),
        ("anxiety", "anxiety", "Anxiety word protected from fuzzy"),
        ("stress", "stress", "Stress word protected from fuzzy"),
        ("thak", "thak", "Tiredness word protected from fuzzy"),
        ("nahi", "nahi", "Negation word protected from fuzzy"),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected, reason in test_cases:
        result = engine._normalize_text_rule_based(input_text)
        status = "✅ PASS" if expected in result else "❌ FAIL"
        
        print(f"\n  {status} | Input: '{input_text}'")
        print(f"         Result: '{result}'")
        print(f"         Reason: {reason}")
        
        if expected in result:
            passed += 1
        else:
            failed += 1
            print(f"         ❌ ERROR: Expected '{expected}' in result")
    
    print(f"\n  Critical Word Protection: {passed} passed, {failed} failed\n")
    return passed, failed


def test_stricter_regex_patterns():
    """Test stricter regex patterns (no character class issues)"""
    print("\n" + "="*70)
    print("TEST 2: STRICTER REGEX PATTERNS")
    print("="*70)
    
    engine = NeuronixChatEngine()
    
    test_cases = [
        # (input, expected, reason)
        ("neend nai", "neend nahi", "Sleep + negation (nai→nhi)"),
        ("neend nhi", "neend nahi", "Sleep + negation (nhi variant)"),
        ("neend ni", "neend nahi", "Sleep + negation (ni variant)"),
        
        ("thak gya", "thak gaya", "Tiredness (gya→gaya)"),
        ("thak gayi", "tired", "Tiredness (gayi→tired)"),
        
        ("gussa a rha", "gussa aa raha", "Anger with spacing (a rha)"),
        ("gussa aa rha", "gussa aa raha", "Anger with spacing (aa rha)"),
        ("gussa arha", "gussa aa raha", "Anger with spacing (arha)"),
        
        ("tensio", "tension", "Tension typo (tensio→tension)"),
        ("depresun", "depression", "Depression typo (depresun→depression)"),
        ("komsi", "kaunsi", "Books question (komsi→kaunsi)"),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected, reason in test_cases:
        result = engine._normalize_text_rule_based(input_text)
        status = "✅ PASS" if expected in result else "❌ FAIL"
        
        print(f"\n  {status} | Input: '{input_text}'")
        print(f"         Result: '{result}'")
        print(f"         Expected: '{expected}'")
        print(f"         Reason: {reason}")
        
        if expected in result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n  Stricter Regex Patterns: {passed} passed, {failed} failed\n")
    return passed, failed


def test_dictionary_priority():
    """Test that dictionary replacements happen BEFORE fuzzy"""
    print("\n" + "="*70)
    print("TEST 3: DICTIONARY PRIORITY (Dict replaces before fuzzy)")
    print("="*70)
    
    engine = NeuronixChatEngine()
    
    test_cases = [
        # Multi-word dictionary entries should be replaced first
        ("gussa a rha", "gussa", "Multi-word dict entry for anger spacing"),
        ("neend nai", "neend nahi", "Multi-word dict entry for sleep negation"),
        ("depresun", "depression", "Single-word dict entry for depression typo"),
        ("tensio", "tension", "Single-word dict entry for tension typo"),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, should_contain, reason in test_cases:
        result = engine._normalize_text_rule_based(input_text)
        
        # Check if result contains any form of the expected output
        status = "✅ PASS" if should_contain in result else "❌ FAIL"
        
        print(f"\n  {status} | Input: '{input_text}'")
        print(f"         Result: '{result}'")
        print(f"         Should contain: '{should_contain}'")
        print(f"         Reason: {reason}")
        
        if should_contain in result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n  Dictionary Priority: {passed} passed, {failed} failed\n")
    return passed, failed


def test_full_pipeline_complex():
    """Test full pipeline with complex real-world inputs"""
    print("\n" + "="*70)
    print("TEST 4: FULL PIPELINE WITH COMPLEX INPUTS")
    print("="*70)
    
    engine = NeuronixChatEngine()
    
    test_cases = [
        (
            "mujhe tensio aur gussa a rha tha",
            ["tension", "gussa"],
            "Hinglish with typos and anger spacing"
        ),
        (
            "neend nai aa rahi aur thak gya hoon",
            ["neend nahi", "thak gaya"],
            "Sleep negation + tiredness"
        ),
        (
            "depresun ke wajah se stress aur anxeity",
            ["depression", "stress"],
            "Medical terms with typos"
        ),
        (
            "gussa aa raha aur neend nahi aa rahi",
            ["gussa aa raha", "neend nahi"],
            "Two critical patterns together"
        ),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected_list, reason in test_cases:
        result = engine._normalize_text_rule_based(input_text)
        
        all_found = all(exp in result for exp in expected_list)
        status = "✅ PASS" if all_found else "❌ FAIL"
        
        print(f"\n  {status} | Input: '{input_text}'")
        print(f"         Result: '{result}'")
        print(f"         Expected: {expected_list}")
        print(f"         Reason: {reason}")
        
        if all_found:
            passed += 1
        else:
            failed += 1
            for exp in expected_list:
                if exp not in result:
                    print(f"         ❌ Missing: '{exp}'")
    
    print(f"\n  Complex Pipeline: {passed} passed, {failed} failed\n")
    return passed, failed


def test_fuzzy_fallback():
    """Test that fuzzy matching still works for unknown typos"""
    print("\n" + "="*70)
    print("TEST 5: FUZZY FALLBACK (For unseen typos)")
    print("="*70)
    
    engine = NeuronixChatEngine()
    
    test_cases = [
        ("stres", "stress", "Close typo (missing s)"),
        ("depresion", "depression", "Missing second e/s"),
        ("ankiety", "anxiety", "Misspelling (ankiety→anxiety)"),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected, reason in test_cases:
        result = engine._normalize_text_rule_based(input_text)
        # Fuzzy is lenient, just check if result contains expected or is close
        contains_expected = expected in result
        
        status = "✅ PASS" if contains_expected else "⚠️  NOTE"
        
        print(f"\n  {status} | Input: '{input_text}'")
        print(f"         Result: '{result}'")
        print(f"         Expected: '{expected}'")
        print(f"         Reason: {reason}")
        
        if contains_expected:
            passed += 1
        else:
            failed += 1
            print(f"         (Fuzzy may not match. Check threshold)")
    
    print(f"\n  Fuzzy Fallback: {passed} passed, {failed} failed\n")
    return passed, failed


def main():
    """Run all test suites"""
    print("\n" + "🧪 "+"="*66)
    print("PATCHED 3-LAYER NORMALIZATION TEST SUITE")
    print("="*70)
    
    total_passed = 0
    total_failed = 0
    
    # Run all tests
    p1, f1 = test_critical_word_protection()
    p2, f2 = test_stricter_regex_patterns()
    p3, f3 = test_dictionary_priority()
    p4, f4 = test_full_pipeline_complex()
    p5, f5 = test_fuzzy_fallback()
    
    total_passed = p1 + p2 + p3 + p4 + p5
    total_failed = f1 + f2 + f3 + f4 + f5
    
    # Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"✅ PASSED: {total_passed}")
    print(f"❌ FAILED: {total_failed}")
    print(f"📊 Total Tests: {total_passed + total_failed}")
    print(f"📈 Pass Rate: {total_passed}/{total_passed + total_failed} ({100*total_passed/(total_passed+total_failed):.1f}%)")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED! Patched 3-layer normalization is working perfectly.")
    else:
        print(f"\n⚠️  {total_failed} tests failed. Review above for details.")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
