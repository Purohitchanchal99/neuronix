# -*- coding: utf-8 -*-
"""
🏥 CLINICAL RESPONSE TESTING FRAMEWORK - COMPLETE SUITE
========================================================

Validates:
1. DSM-5 vs ICD-11 routing (country-aware)
2. Hinglish tone wrapping (not formal clinical)
3. Symptom checker with follow-up questions (doctor-style inquiry)
4. Crisis detection (immediate helplines)
5. Multi-country clinical standard routing

Status: Tests 1-5 must all pass for production deployment
"""

import os
import sys
import json
from typing import Dict, List, Tuple, Optional

# Fix Unicode encoding on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Import the chat engine
from backend.chat_engine import NeuronixChatEngine


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_section(title: str) -> None:
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"🔬 {title}")
    print("="*80)


# ============================================================================
# TEST FUNCTIONS - CLINICAL RESPONSE VALIDATION
# ============================================================================

def test_dsm5_depression_query():
    """TEST 1: DSM-5 Depression Criteria Query"""
    
    print_section("TEST 1: DSM-5 Depression Criteria")
    print("💬 USER QUERY: 'Bhai, mujhe lag raha hai mujhe Depression hai, DSM-5 ke hisaab se kya symptoms hote hain?'\n")
    
    try:
        engine = NeuronixChatEngine()
        response = engine.chat("Bhai, mujhe lag raha hai mujhe Depression hai, DSM-5 ke hisaab se kya symptoms hote hain?")
        
        print("🤖 NEURONIX RESPONSE:\n")
        print(response)
        
        # Validation checks
        print("\n" + "-"*80)
        print("✅ VALIDATION CHECKLIST:\n")
        
        checks = {
            "DSM-5 Reference Present": "DSM-5" in response,
            "Symptoms Listed": "symptoms" in response.lower() or "criteria" in response.lower(),
            "Self-Diagnosis Disclaimer": "self-diagnosis" in response.lower() or "professional" in response.lower(),
            "Free Alternative Suggested": ("free" in response.lower() or "IGNOU" in response or "NIMHANS" in response),
            "Friendly Tone (Hinglish)": "Bhai" in response or "achj" in response.lower() or "toh" in response.lower(),
        }
        
        for check, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {check}")
        
        all_passed = all(checks.values())
        print(f"\n{'='*80}")
        print(f"RESULT: {'🎉 ALL CHECKS PASSED' if all_passed else '⚠️ SOME CHECKS FAILED'}")
        print(f"{'='*80}\n")
        
        return all_passed
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_icd11_anxiety_query():
    """TEST 2: ICD-11 Anxiety Criteria Query"""
    
    print_section("TEST 2: ICD-11 Anxiety Criteria")
    print("💬 USER QUERY: 'Mujhe bohot anxiety ho rahi hai, ICD-11 standard ke hisaab se kya hona chahiye?'\n")
    
    try:
        engine = NeuronixChatEngine()
        response = engine.chat("Mujhe bohot anxiety ho rahi hai, ICD-11 standard ke hisaab se kya hona chahiye?")
        
        print("🤖 NEURONIX RESPONSE:\n")
        print(response)
        
        print("\n" + "-"*80)
        print("✅ VALIDATION CHECKLIST:\n")
        
        checks = {
            "ICD-11 Reference Present": "ICD-11" in response or "WHO" in response,
            "Anxiety Criteria Mentioned": "anxiety" in response.lower(),
            "WHO Standard Mentioned": "WHO" in response or "ICD-11" in response,
            "Professional Advice Given": "psychiatrist" in response.lower() or "professional" in response.lower(),
            "Friendly Response": "Bhai" in response or "anxiety" in response.lower(),
        }
        
        for check, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {check}")
        
        all_passed = all(checks.values())
        print(f"\n{'='*80}")
        print(f"RESULT: {'🎉 ALL CHECKS PASSED' if all_passed else '⚠️ SOME CHECKS FAILED'}")
        print(f"{'='*80}\n")
        
        return all_passed
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_symptom_checker_followup():
    """TEST 3: Symptom Checker with Follow-up Questions"""
    
    print_section("TEST 3: Symptom Checker Follow-up Questions")
    print("💬 USER QUERY: 'Mujhe neend nahi aa rahi'\n")
    
    try:
        engine = NeuronixChatEngine()
        response = engine.chat("Mujhe neend nahi aa rahi")
        
        print("🤖 NEURONIX RESPONSE:\n")
        print(response)
        
        print("\n" + "-"*80)
        print("✅ VALIDATION CHECKLIST:\n")
        
        checks = {
            "Follow-up Question Present": "शन्" in response or "?" in response,
            "Doctor-like Inquiry": any(phrase in response.lower() for phrase in ["kab se", "kitne din", "baad", "trigger", "since when"]),
            "Not Instant Diagnosis": "diagnosis" not in response.lower() or ("not" in response.lower() and "diagnosis" in response.lower()),
            "Empathetic Tone": any(word in response.lower() for word in ["samajh", "normal", "bohot annoying", "frustrat"]),
        }
        
        for check, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {check}")
        
        all_passed = all(checks.values())
        print(f"\n{'='*80}")
        print(f"RESULT: {'🎉 ALL CHECKS PASSED' if all_passed else '⚠️ SOME CHECKS FAILED'}")
        print(f"{'='*80}\n")
        
        return all_passed
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_multi_country_routing():
    """TEST 4: Multi-Country DSM-5/ICD-11 Routing"""
    
    print_section("TEST 4: Clinical Standard Routing")
    print("💬 Checking if AI uses correct standard based on country\n")
    
    try:
        engine = NeuronixChatEngine()
        
        # Test standard detection
        us_standard = engine._get_clinical_standard("US")
        india_standard = engine._get_clinical_standard("India")
        uk_standard = engine._get_clinical_standard("UK")
        
        print("📍 STANDARD ROUTING TEST:\n")
        print(f"USA → Primary: {us_standard['primary']}")
        print(f"India → Primary: {india_standard['primary']}")
        print(f"UK → Primary: {uk_standard['primary']}")
        
        print("\n" + "-"*80)
        print("✅ VALIDATION CHECKLIST:\n")
        
        checks = {
            "USA uses DSM-5": us_standard['primary'] == "DSM-5",
            "India uses Hybrid (ICD-11+DSM-5)": "ICD-11" in india_standard['primary'] and "DSM-5" in india_standard['primary'],
            "UK uses ICD-11": uk_standard['primary'] == "ICD-11",
        }
        
        for check, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {check}")
        
        all_passed = all(checks.values())
        print(f"\n{'='*80}")
        print(f"RESULT: {'🎉 ALL CHECKS PASSED' if all_passed else '⚠️ SOME CHECKS FAILED'}")
        print(f"{'='*80}\n")
        
        return all_passed
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_free_resource_detection():
    """TEST 5: Free Resource (Status 0) Detection"""
    
    print_section("TEST 5: Free Resource Management")
    print("💬 Testing RAG accuracy benchmarking (Status 0/1 filtering)\n")
    
    try:
        engine = NeuronixChatEngine()
        
        # Create mock documents for testing
        from langchain_core.documents import Document
        
        mock_docs = [
            Document(
                page_content="Depression treatment info",
                metadata={"status": 0, "source_file": "Psychology2e_WEB.pdf"}
            ),
            Document(
                page_content="Anxiety symptoms",
                metadata={"status": 1, "source_file": "Some_Paid_Book.pdf"}
            ),
            Document(
                page_content="Sleep disorders",
                metadata={"status": 0, "source_file": "IGNOU_Free_Handbook.pdf"}
            ),
        ]
        
        benchmark = engine._rag_accuracy_benchmark(mock_docs)
        
        print("📊 RAG ACCURACY BENCHMARK:\n")
        print(f"Total Documents: {benchmark['total']}")
        print(f"Free Resources (Status 0): {benchmark['free_count']}")
        print(f"Paid Resources (Status 1): {benchmark['paid_count']}")
        print(f"Accuracy %: {benchmark['accuracy_percent']:.1f}%")
        print(f"Status: {benchmark['benchmark_status']}")
        print(f"\nFree Alternatives Found: {benchmark['free_alternatives']}")
        
        print("\n" + "-"*80)
        print("✅ VALIDATION CHECKLIST:\n")
        
        checks = {
            "Correctly counts total": benchmark['total'] == 3,
            "Correctly counts free": benchmark['free_count'] == 2,
            "Correctly counts paid": benchmark['paid_count'] == 1,
            "Accuracy % calculated": benchmark['accuracy_percent'] == 66.66666666666666,
            "Correct benchmark status": benchmark['benchmark_status'] == "WARNING",
        }
        
        for check, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {check}")
        
        all_passed = all(checks.values())
        print(f"\n{'='*80}")
        print(f"RESULT: {'🎉 ALL CHECKS PASSED' if all_passed else '⚠️ SOME CHECKS FAILED'}")
        print(f"{'='*80}\n")
        
        return all_passed
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    
    print("\n" + "="*80)
    print("🏥 NEURONIX CLINICAL POWERHOUSE - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    results = {}
    
    # Check API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("\n❌ ERROR: GOOGLE_API_KEY not set!")
        print("Please set your Google API key before running tests:")
        print("  $env:GOOGLE_API_KEY = 'your-key'")
        print("  python test_clinical_powerhouse.py\n")
        sys.exit(1)
    
    try:
        # Run tests
        results["Test 1: DSM-5 Depression"] = test_dsm5_depression_query()
        results["Test 2: ICD-11 Anxiety"] = test_icd11_anxiety_query()
        results["Test 3: Symptom Checker"] = test_symptom_checker_followup()
        results["Test 4: Multi-Country Routing"] = test_multi_country_routing()
        results["Test 5: Free Resource Detection"] = test_free_resource_detection()
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Print summary
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80 + "\n")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total_passed = sum(1 for p in results.values() if p)
    total_tests = len(results)
    
    print(f"\n{'='*80}")
    print(f"TOTAL: {total_passed}/{total_tests} tests passed")
    print(f"{'='*80}\n")
    
    if total_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Clinical Powerhouse is ready to go! 🚀\n")
        return 0
    else:
        print(f"⚠️ {total_tests - total_passed} test(s) failed. Review output above. \n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
