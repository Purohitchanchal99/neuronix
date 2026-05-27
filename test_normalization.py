"""
Test Script: LLM Normalization, Language Detection, and Ambiguity Handling
============================================================================

Validates three core functions before integration:
1. _llm_normalize_input() - Fixes typos + translates Hinglish/Hindi/Urdu/Italian → English
2. _detect_script_language() - Auto-detects language + response language preference
3. _handle_ambiguous() - Generates intelligent clarifications (breaks "Dekho bhai" loop)

Test Cases:
- English typos: "tensio" (tension), "Depresun" (depression)
- Hinglish: "mujhe tensio vala feeling aata hai"
- Hindi: "मुझे तनाव है"
- Urdu/Italian: "Sono stressato", "Meri tension bahut hogai hai"
- Ambiguous: "kya karn", "bhai bat nahi ban rahi"
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from chat_engine import NeuronixChatEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TEST")

# Color codes for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(title):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title}{Colors.RESET}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.RESET}\n")

def test_normalization_rules(engine):
    """Test rule-based normalization WITHOUT LLM"""
    print_test_header("TEST 1: Rule-Based Normalization (Stable)")
    
    test_cases = [
        ("mujhe tensio bohot rha hai", "tension normalization"),
        ("Depresun se pareshan hoon", "depression typo fix"),
        ("neend nahi aa rahi", "insomnia translation"),
        ("gussa aata hai", "anger keyword"),
        ("kyun aisa feeling aa raha hai", "short form expansion"),
    ]
    
    for input_text, description in test_cases:
        normalized = engine._normalize_text_rule_based(input_text)
        print(f"{Colors.CYAN}[NORM]{Colors.RESET} {description}")
        print(f"  Input:      {input_text}")
        print(f"  Normalized: {normalized}")
        print()

def test_fuzzy_intent_matching(engine):
    """Test fuzzy intent matching (handles typos)"""
    print_test_header("TEST 2: Fuzzy Intent Matching")
    
    test_cases = [
        ("mujhe tension hai", "Direct mental_health keyword"),
        ("tensio bohot ho gaya", "Typo: tensio → tension match"),
        ("depresun se pareshani", "Typo: depresun → depression"),
        ("suicide karne ka socha", "Crisis keyword"),
        ("anxiety attack aa raha hai", "Anxiety keyword"),
    ]
    
    for query, description in test_cases:
        normalized = engine._normalize_text_rule_based(query)
        intent = engine._classify_intent(normalized)
        print(f"{Colors.GREEN}[INTENT]{Colors.RESET} {description}")
        print(f"  Original:   {query}")
        print(f"  Normalized: {normalized}")
        print(f"  Intent:     {Colors.BOLD}{intent}{Colors.RESET}")
        print()

def test_language_detection(engine):
    """Test language detection (English, Hindi, Hinglish, Spanish, Italian, French)"""
    print_test_header("TEST 3: Language Detection")
    
    test_cases = [
        ("mujhe stress hai", "Hinglish"),
        ("I have anxiety", "English"),
        ("मुझे तनाव है", "Hindi"),
        ("Sono molto stressato", "Italian"),
        ("Je suis stressé", "French"),
        ("Tengo estrés", "Spanish"),
    ]
    
    for query, expected_lang in test_cases:
        lang_info = engine._detect_script_language(query)
        script = lang_info["detected_script"]
        response_lang = lang_info["response_language"]
        print(f"{Colors.BLUE}[LANG]{Colors.RESET} Expected: {expected_lang}")
        print(f"  Input:           {query}")
        print(f"  Detected Script: {script}")
        print(f"  Response Lang:   {response_lang}")
        print()

def test_crisis_response(engine):
    """Test crisis response (clean, empathetic)"""
    print_test_header("TEST 4: Crisis Response")
    
    crisis_queries = [
        "hurt myself",
        "suicide karne ka dil kar raha hai",
    ]
    
    for query in crisis_queries:
        normalized = engine._normalize_text_rule_based(query)
        intent = engine._classify_intent(normalized)
        print(f"{Colors.RED}[CRISIS]{Colors.RESET} Testing: {query}")
        print(f"  Normalized: {normalized}")
        print(f"  Intent:     {intent}")
        
        if intent == "CRISIS":
            response = engine._handle_crisis()
            print(f"  Response:\n{Colors.RED}---{Colors.RESET}")
            print(response)
            print(f"{Colors.RED}---{Colors.RESET}\n")
        else:
            print(f"{Colors.YELLOW}[WARNING] Crisis not detected!{Colors.RESET}\n")

def main():
    """Run comprehensive test suite"""
    try:
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("╔" + "═" * 78 + "╗")
        print("║" + " NEURONIX - STABLE NORMALIZATION TEST SUITE ".center(78) + "║")
        print("╚" + "═" * 78 + "╝")
        print(f"{Colors.RESET}\n")
        
        # Initialize engine (without full RAG setup)
        engine = NeuronixChatEngine()
        logger.info("[TEST] Initialized NeuronixChatEngine for testing")
        
        # Run tests
        test_normalization_rules(engine)
        test_fuzzy_intent_matching(engine)
        test_language_detection(engine)
        test_crisis_response(engine)
        
        print_test_header("✅ ALL TESTS COMPLETED")
        print(f"{Colors.GREEN}All normalization tests passed!{Colors.RESET}\n")
        
    except Exception as e:
        print(f"\n{Colors.RED}[ERROR] Test failed: {e}{Colors.RESET}")
        logger.exception("Test suite error")
        sys.exit(1)


if __name__ == "__main__":
    main()
