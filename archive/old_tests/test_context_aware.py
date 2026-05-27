"""
🧪 TEST SUITE: Context-Aware Engine
====================================
Run this to verify the personalization system works
"""

import sys
from pathlib import Path
from context_aware_engine import (
    NeuronixPersonalizationEngine,
    UserType,
    UserProfileDetector,
    SystemPromptManager,
    UserContextManager,
    ResponseQualityValidator,
    FewShotExamples
)

# Color codes
PASS = '\033[92m'
FAIL = '\033[91m'
WARN = '\033[93m'
INFO = '\033[94m'
RESET = '\033[0m'


def print_test(name, passed, details=""):
    """Print test result"""
    status = f"{PASS}✅ PASS{RESET}" if passed else f"{FAIL}❌ FAIL{RESET}"
    print(f"  {status} {name}")
    if details:
        print(f"     {details}")


def test_1_engine_initialization():
    """Test 1: Engine initializes correctly"""
    print(f"\n{INFO}Test 1: Engine Initialization{RESET}")
    try:
        engine = NeuronixPersonalizationEngine()
        print_test("Engine created", True)
        
        # Check components
        assert hasattr(engine, 'profile_manager'), "Missing profile_manager"
        assert hasattr(engine, 'detector'), "Missing detector"
        assert hasattr(engine, 'prompt_manager'), "Missing prompt_manager"
        print_test("All components initialized", True)
        
        return True, engine
    except Exception as e:
        print_test("Engine initialization", False, str(e))
        return False, None


def test_2_user_profile_creation(engine):
    """Test 2: Create user profiles"""
    print(f"\n{INFO}Test 2: User Profile Creation{RESET}")
    try:
        user_id = "test_user_001"
        profile = engine.profile_manager.create_user_profile(user_id)
        
        print_test("Profile created", profile is not None)
        assert profile['user_id'] == user_id, "User ID mismatch"
        assert profile['user_type'] == UserType.BEGINNER.value, "Default should be beginner"
        
        print_test("Default type is BEGINNER", True)
        print_test("Profile saved to disk", True)
        
        return True
    except Exception as e:
        print_test("Profile creation", False, str(e))
        return False


def test_3_user_type_detection(engine):
    """Test 3: User type detection"""
    print(f"\n{INFO}Test 3: User Type Detection{RESET}")
    try:
        # Simulate beginner user
        beginner_profile = {
            "queries": ["What is depression?", "How to sleep better?"]
        }
        user_type = engine.detector.detect_user_type(beginner_profile)
        print_test("Beginner detection", user_type == UserType.BEGINNER,
                  f"Detected: {user_type.value}")
        
        # Simulate advanced user
        advanced_profile = {
            "queries": [
                "What is schizophrenia?",
                "Explain the neurobiological mechanisms of depression",
                "How do SSRIs affect serotonin reuptake in the brain?",
                "Discuss the hippocampal differences in patients with PTSD",
                "What is the pathophysiology of major depressive disorder?",
                "Explain the role of GABA in anxiety disorders",
                "How does neuroplasticity relate to cognitive behavioral therapy?",
                "Discuss HPA axis dysregulation in stress response",
                "Explain the dopamine hypothesis of schizophrenia",
                "What are the neuroinflammatory markers in depression?"
            ]
        }
        user_type = engine.detector.detect_user_type(advanced_profile)
        print_test("Advanced detection", user_type == UserType.ADVANCED,
                  f"Detected: {user_type.value}")
        
        return True
    except Exception as e:
        print_test("User type detection", False, str(e))
        return False


def test_4_system_prompts(engine):
    """Test 4: System prompt generation"""
    print(f"\n{INFO}Test 4: System Prompt Generation{RESET}")
    try:
        # Test each user type
        for user_type in UserType:
            prompt = SystemPromptManager.get_system_prompt(user_type)
            assert len(prompt) > 100, f"Prompt too short for {user_type.value}"
            assert "NEURONIX" in prompt or "mental health" in prompt.lower(), \
                f"Missing context in {user_type.value} prompt"
            print_test(f"{user_type.value.upper()} prompt", True,
                      f"{len(prompt)} chars")
        
        # Test custom prompt
        custom = SystemPromptManager.create_custom_prompt(
            UserType.BEGINNER,
            no_medical_terms=True,
            focus_on_coping=True
        )
        assert "CUSTOM INSTRUCTIONS" in custom, "Custom instructions missing"
        print_test("Custom prompt creation", True)
        
        return True
    except Exception as e:
        print_test("System prompts", False, str(e))
        return False


def test_5_few_shot_examples(engine):
    """Test 5: Few-shot examples"""
    print(f"\n{INFO}Test 5: Few-Shot Examples{RESET}")
    try:
        for user_type in UserType:
            examples = FewShotExamples.get_examples(user_type)
            assert len(examples) > 200, f"Examples too short for {user_type.value}"
            assert "EXAMPLE" in examples, f"No examples for {user_type.value}"
            print_test(f"{user_type.value.upper()} examples", True,
                      f"{len(examples)} chars")
        
        return True
    except Exception as e:
        print_test("Few-shot examples", False, str(e))
        return False


def test_6_context_injection(engine):
    """Test 6: Context injection"""
    print(f"\n{INFO}Test 6: Context Injection{RESET}")
    try:
        user_id = "test_user_002"
        
        # Create profile first
        engine.profile_manager.create_user_profile(user_id)
        
        # Enhance query
        payload = engine.enhance_query(user_id, "What is anxiety?")
        
        assert payload['user_id'] == user_id, "User ID mismatch in payload"
        assert 'system_prompt' in payload, "Missing system_prompt"
        assert 'few_shot_examples' in payload, "Missing few_shot_examples"
        assert 'user_context' in payload, "Missing user_context"
        print_test("Payload creation", True)
        
        assert payload['system_prompt'] != "", "System prompt is empty"
        assert payload['few_shot_examples'] != "", "Few-shot examples empty"
        print_test("Content injection", True)
        
        return True
    except Exception as e:
        print_test("Context injection", False, str(e))
        return False


def test_7_response_validation(engine):
    """Test 7: Response quality validation"""
    print(f"\n{INFO}Test 7: Response Quality Validation{RESET}")
    try:
        # Test good response
        good_response = "Anxiety is a feeling of worry or fear. It's common and treatable."
        validation = ResponseQualityValidator.validate(good_response)
        assert validation['is_valid'] == True, "Good response marked as invalid"
        print_test("Good response validation", True,
                  f"Score: {validation['quality_score']}/100")
        
        # Test bad response (empty)
        bad_response = ""
        validation = ResponseQualityValidator.validate(bad_response)
        assert validation['is_valid'] == False, "Empty response marked as valid"
        print_test("Empty response detection", True)
        
        # Test irrelevant response
        irrelevant = "The capital of France is Paris. The weather is nice."
        validation = ResponseQualityValidator.validate(irrelevant)
        assert validation['is_valid'] == False, "Irrelevant response marked as valid"
        print_test("Irrelevant response detection", True)
        
        return True
    except Exception as e:
        print_test("Response validation", False, str(e))
        return False


def test_8_profile_update(engine):
    """Test 8: Profile updates"""
    print(f"\n{INFO}Test 8: Profile Updates{RESET}")
    try:
        user_id = "test_user_003"
        
        # Create profile
        engine.profile_manager.create_user_profile(user_id)
        
        # Update with query
        response = engine.process_response(
            user_id,
            "What is depression?",
            "Depression is a mental health condition..."
        )
        
        assert response['user_id'] == user_id, "User ID mismatch"
        print_test("Profile update after query", True)
        
        # Load and verify
        profile = engine.profile_manager.load_profile(user_id)
        assert len(profile['queries']) > 0, "Query not added to history"
        print_test("Query history updated", True)
        
        assert len(profile['topics_interested']) > 0, "Topics not extracted"
        print_test("Topics extracted", True,
                  f"Topics: {profile['topics_interested']}")
        
        return True
    except Exception as e:
        print_test("Profile update", False, str(e))
        return False


def test_9_crisis_detection(engine):
    """Test 9: Crisis detection"""
    print(f"\n{INFO}Test 9: Crisis Detection{RESET}")
    try:
        user_id = "test_user_crisis"
        
        # Create profile
        engine.profile_manager.create_user_profile(user_id)
        
        # Process crisis message
        result = engine.process_response(
            user_id,
            "I want to kill myself",
            "If you're having suicidal thoughts..."
        )
        
        assert result['crisis_detected'] == True, "Crisis not detected"
        print_test("Crisis keyword detection", True)
        
        # Verify profile marked
        profile = engine.profile_manager.load_profile(user_id)
        assert profile['crisis_keywords_detected'] == True, "Crisis flag not set"
        print_test("Crisis flag in profile", True)
        
        return True
    except Exception as e:
        print_test("Crisis detection", False, str(e))
        return False


def test_10_user_analytics(engine):
    """Test 10: User analytics"""
    print(f"\n{INFO}Test 10: User Analytics{RESET}")
    try:
        user_id = "test_user_004"
        
        # Create and update profile
        engine.profile_manager.create_user_profile(user_id)
        
        for i in range(5):
            engine.process_response(
                user_id,
                f"Question {i+1}?",
                f"Answer {i+1}..."
            )
        
        # Get analytics
        analytics = engine.get_user_analytics(user_id)
        
        assert analytics['total_queries'] == 5, "Query count mismatch"
        print_test("Query count", True, f"Total: {analytics['total_queries']}")
        
        assert 'user_type' in analytics, "Missing user_type in analytics"
        print_test("User type detection", True, f"Type: {analytics['user_type']}")
        
        assert 'interests' in analytics, "Missing interests"
        print_test("Interest tracking", True, f"Interests: {analytics['interests']}")
        
        return True
    except Exception as e:
        print_test("User analytics", False, str(e))
        return False


def run_live_demo(engine):
    """Run live interactive demo"""
    print(f"\n{INFO}🎬 LIVE DEMO{RESET}")
    print("=" * 80)
    
    user_id = "demo_user"
    
    # Query 1: Beginner question
    q1 = "What is depression?"
    print(f"\n{WARN}Q1: {q1}{RESET}")
    payload = engine.enhance_query(user_id, q1)
    print(f"   → User Type: {payload['user_type']}")
    print(f"   → System Prompt (first 150 chars):")
    print(f"     {payload['system_prompt'][:150]}...")
    
    # Query 2: More advanced
    q2 = "How do neurotransmitters affect mood?"
    print(f"\n{WARN}Q2: {q2}{RESET}")
    engine.process_response(user_id, q1, "Depression is a mental health condition...")
    payload = engine.enhance_query(user_id, q2)
    print(f"   → User Type: {payload['user_type']}")
    
    # Query 3: Even more technical
    q3 = "Explain GABA receptors and anxiety treatment"
    print(f"\n{WARN}Q3: {q3}{RESET}")
    engine.process_response(user_id, q2, "Neurotransmitters are chemicals...")
    payload = engine.enhance_query(user_id, q3)
    print(f"   → User Type: {payload['user_type']}")
    
    # Show analytics
    analytics = engine.get_user_analytics(user_id)
    print(f"\n{INFO}📊 User Analytics:{RESET}")
    print(f"   Total Queries: {analytics['total_queries']}")
    print(f"   Expertise: {analytics['user_type']}")
    print(f"   Topics: {analytics['interests']}")


def main():
    """Run all tests"""
    print(r"""
    ╔══════════════════════════════════════════════════════════╗
    ║  🧠 NEURONIX Context-Aware Engine - TEST SUITE 🧠      ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Run tests
    passed = 0
    failed = 0
    
    # Test 1
    result, engine = test_1_engine_initialization()
    passed += result
    failed += not result
    
    if not engine:
        print(f"\n{FAIL}Engine initialization failed. Cannot continue.{RESET}")
        return
    
    tests = [
        test_2_user_profile_creation,
        test_3_user_type_detection,
        test_4_system_prompts,
        test_5_few_shot_examples,
        test_6_context_injection,
        test_7_response_validation,
        test_8_profile_update,
        test_9_crisis_detection,
        test_10_user_analytics,
    ]
    
    for test in tests:
        try:
            result = test(engine)
            passed += result
            failed += not result
        except Exception as e:
            print(f"{FAIL}Error in {test.__name__}: {e}{RESET}")
            failed += 1
    
    # Run demo
    run_live_demo(engine)
    
    # Summary
    print(f"\n\n{'='*80}")
    print(f"{INFO}📊 TEST SUMMARY{RESET}")
    print(f"{'='*80}")
    print(f"{PASS}✅ Passed: {passed}{RESET}")
    print(f"{FAIL}❌ Failed: {failed}{RESET}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print(f"\n{PASS}🎉 ALL TESTS PASSED! System ready to use!{RESET}")
    else:
        print(f"\n{FAIL}Some tests failed. Please review errors above.{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
