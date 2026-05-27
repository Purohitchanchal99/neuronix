"""
🧠 CONTEXT-AWARE AI EXAMPLES & DEMONSTRATIONS
==============================================
Comprehensive examples of all 7 components in action
"""

import logging
from context_aware_ai_system import (
    ContextAwareAISystem,
    SystemPromptManager,
    ContextUtilizationEngine,
    UserTypeDetector,
    ResponseQualityFilter,
    FewShotTrainingLibrary,
    PersonalizationLayer,
    ContextInjectionFlow,
    UserExpertiseLevel,
    UserContext
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# COMPONENT 1: SYSTEM PROMPT MANAGER EXAMPLES
# ============================================================================

def example_1_system_prompt_manager():
    """Demonstrate system prompt management"""
    
    print("\n" + "="*70)
    print("EXAMPLE 1: SYSTEM PROMPT MANAGER")
    print("="*70)
    
    manager = SystemPromptManager()
    
    # Example 1a: Base system prompt
    print("\n1️⃣ Base System Prompt:")
    print("-"*70)
    base_prompt = manager.get_system_prompt()
    print(base_prompt[:500] + "...")
    
    # Example 1b: Emergency mode
    print("\n2️⃣ Emergency Mode Prompt (with stricter disclaimers):")
    print("-"*70)
    emergency_prompt = manager.get_system_prompt(emergency_mode=True)
    print(emergency_prompt[-300:])
    
    # Example 1c: With user context
    print("\n3️⃣ Personalized Prompt (Hinglish preference):")
    print("-"*70)
    user_context = {"language_preference": "hinglish", "sensitivity_level": "high"}
    personalized_prompt = manager.get_system_prompt(user_context=user_context)
    print(personalized_prompt[-300:])
    
    # Example 1d: Add custom rule
    print("\n4️⃣ Adding Custom Rule:")
    print("-"*70)
    manager.add_custom_rule("Always include a confidence level in responses")
    print("✅ Rule added: 'Always include a confidence level in responses'")


# ============================================================================
# COMPONENT 2: CONTEXT UTILIZATION ENGINE EXAMPLES
# ============================================================================

def example_2_context_utilization():
    """Demonstrate context-based response styling"""
    
    print("\n" + "="*70)
    print("EXAMPLE 2: CONTEXT UTILIZATION ENGINE")
    print("="*70)
    
    engine = ContextUtilizationEngine()
    
    # Create users at different levels
    users = [
        UserContext(user_id="alice", expertise_level=UserExpertiseLevel.BEGINNER),
        UserContext(user_id="bob", expertise_level=UserExpertiseLevel.INTERMEDIATE, 
                   interests=["psychology", "research"]),
        UserContext(user_id="charlie", expertise_level=UserExpertiseLevel.ADVANCED,
                   interests=["neuroscience", "therapy"])
    ]
    
    for user in users:
        engine.register_user(user)
    
    # Show different response styles
    print("\n1️⃣ Response Styles by Expertise Level:")
    print("-"*70)
    
    for user in users:
        style = engine.RESPONSE_STYLES[user.expertise_level]
        print(f"\n{user.user_id.upper()} ({user.expertise_level.value}):")
        print(f"  - Complexity: {style['complexity']}")
        print(f"  - Use examples: {style['use_examples']}")
        print(f"  - Tone: {style['tone']}")
        print(f"  - Structure: {style['structure']}")
    
    # Show personalized prompts
    print("\n2️⃣ Personalized Response Style Prompts:")
    print("-"*70)
    
    for user in users:
        style_prompt = engine.get_response_style_prompt(user.user_id)
        print(f"\nFor {user.user_id}:")
        print(style_prompt[:200])


# ============================================================================
# COMPONENT 3: CONTEXT INJECTION FLOW EXAMPLES
# ============================================================================

def example_3_context_injection():
    """Demonstrate context injection pipeline"""
    
    print("\n" + "="*70)
    print("EXAMPLE 3: CONTEXT INJECTION FLOW")
    print("="*70)
    
    system_manager = SystemPromptManager()
    context_engine = ContextUtilizationEngine()
    injection_flow = ContextInjectionFlow(system_manager, context_engine)
    
    # Register a user
    user = UserContext(
        user_id="test_user",
        expertise_level=UserExpertiseLevel.INTERMEDIATE,
        interests=["anxiety", "therapy"],
        language_preference="english"
    )
    context_engine.register_user(user)
    
    # Build contextualized prompt
    print("\n1️⃣ Building Contextualized Prompt:")
    print("-"*70)
    
    question = "What is cognitive behavioral therapy?"
    contextual_prompt = injection_flow.build_contextualized_prompt(
        user_id="test_user",
        question=question
    )
    
    print(f"Question: {question}")
    print(f"\nFull Prompt Components:")
    print(f"  - System Prompt: {len(contextual_prompt.system_prompt)} chars")
    print(f"  - Response Style: {len(contextual_prompt.response_style)} chars")
    print(f"  - User Interests: {len(contextual_prompt.user_interests)} chars")
    print(f"  - User History: {len(contextual_prompt.user_history)} chars")
    print(f"  - Question: {len(contextual_prompt.current_question)} chars")
    
    print(f"\nTotal Prompt Length: {len(contextual_prompt.get_full_prompt())} characters")
    
    # Show emergency mode
    print("\n2️⃣ Emergency Mode Contextualized Prompt:")
    print("-"*70)
    
    emergency_prompt = injection_flow.build_contextualized_prompt(
        user_id="test_user",
        question="I'm having suicidal thoughts",
        emergency=True
    )
    
    print(f"Emergency prompt includes stricter disclaimers: ", end="")
    if "EMERGENCY MODE" in emergency_prompt.get_full_prompt():
        print("✅ YES")
    else:
        print("❌ NO")


# ============================================================================
# COMPONENT 4: USER-TYPE DETECTION EXAMPLES
# ============================================================================

def example_4_user_type_detection():
    """Demonstrate user expertise detection"""
    
    print("\n" + "="*70)
    print("EXAMPLE 4: USER-TYPE DETECTION")
    print("="*70)
    
    detector = UserTypeDetector()
    
    # Test questions at different levels
    test_questions = [
        ("What is anxiety?", "Should be BEGINNER"),
        ("What is the difference between anxiety and panic disorder?", "Should be INTERMEDIATE"),
        ("Explain the amygdala-prefrontal cortex dysregulation in GAD", "Should be ADVANCED"),
        ("How do I manage my stress?", "Should be BEGINNER"),
        ("Neurobiological mechanisms of selective serotonin reuptake inhibitors", "Should be ADVANCED"),
        ("I don't understand what depression is", "Should be BEGINNER"),
    ]
    
    print("\n📊 Expertise Detection Results:")
    print("-"*70)
    
    for question, expected in test_questions:
        detected = detector.detect_expertise_level(question)
        confidence = detector.estimate_confidence(question)
        
        marker = "✅" if expected.split("BEGINNER")[0] == "" and detected == UserExpertiseLevel.BEGINNER \
                 or expected.split("INTERMEDIATE")[0] == "" and detected == UserExpertiseLevel.INTERMEDIATE \
                 or expected.split("ADVANCED")[0] == "" and detected == UserExpertiseLevel.ADVANCED \
                 else "❓"
        
        print(f"\n{marker} Question: {question}")
        print(f"   Detected: {detected.value} (confidence: {confidence:.2f})")
        print(f"   Expected: {expected}")


# ============================================================================
# COMPONENT 5: RESPONSE QUALITY FILTER EXAMPLES
# ============================================================================

def example_5_quality_filter():
    """Demonstrate response quality assessment"""
    
    print("\n" + "="*70)
    print("EXAMPLE 5: RESPONSE QUALITY FILTER")
    print("="*70)
    
    filter = ResponseQualityFilter()
    
    test_responses = [
        ("Depression is a mental health condition characterized by persistent sadness and loss of interest.", "Good response"),
        ("xyz abc def 123 !@#$", "Gibberish"),
        ("", "Empty response"),
        ("ok", "Too short"),
        ("I'm concerned about your wellbeing. Please contact emergency services (911) or a crisis helpline.", "Safety flagged"),
        ("Depression is characterized by persistent depressed mood, anhedonia, changes in appetite and sleep, fatigue, feelings of worthlessness, difficulty concentrating, and recurrent thoughts of death. It affects millions globally and is highly treatable with therapy and/or medication.", "Excellent response"),
    ]
    
    print("\n📋 Response Quality Assessment:")
    print("-"*70)
    
    for response, description in test_responses:
        assessment = filter.assess_quality(response)
        
        print(f"\n📝 {description}:")
        print(f"   Response: {response[:50]}{'...' if len(response) > 50 else ''}")
        print(f"   Recommendation: {assessment['recommendation']}")
        print(f"   Quality Score: {assessment['score']:.2f}")
        
        if assessment['issues']:
            print(f"   Issues: {', '.join(assessment['issues'])}")


# ============================================================================
# COMPONENT 6: FEW-SHOT TRAINING EXAMPLES
# ============================================================================

def example_6_few_shot_training():
    """Demonstrate few-shot training library"""
    
    print("\n" + "="*70)
    print("EXAMPLE 6: FEW-SHOT TRAINING LIBRARY")
    print("="*70)
    
    library = FewShotTrainingLibrary()
    
    print(f"\n📚 Total Training Examples: {len(library.examples)}")
    print("-"*70)
    
    # Show each example
    for i, example in enumerate(library.examples, 1):
        print(f"\n{i}. {example.response_style}")
        print(f"   User: {example.user_question[:60]}")
        print(f"   Context: {example.context}")
        print(f"   Expected Response: {example.expected_response[:80]}...")
        print(f"   Clinically Accurate: {'✅' if example.clinical_accuracy else '❌'}")
    
    # Show relevant examples selection
    print("\n" + "-"*70)
    print("\n🎯 Example Selection for BEGINNER Difficulty:")
    print("-"*70)
    
    query = "What is anxiety?"
    relevant = library.get_relevant_examples(query, UserExpertiseLevel.BEGINNER)
    
    for ex in relevant:
        print(f"\n✅ Relevant Example:")
        print(f"   Q: {ex.user_question}")
        print(f"   A: {ex.expected_response[:100]}...")


# ============================================================================
# COMPONENT 7: PERSONALIZATION LAYER EXAMPLES
# ============================================================================

def example_7_personalization():
    """Demonstrate personalization layer"""
    
    print("\n" + "="*70)
    print("EXAMPLE 7: PERSONALIZATION LAYER")
    print("="*70)
    
    personalizer = PersonalizationLayer()
    
    # Simulate user interactions
    print("\n1️⃣ Recording User Interactions:")
    print("-"*70)
    
    user_id = "test_user_personalization"
    
    interactions = [
        ("What is anxiety?", 0.85, UserExpertiseLevel.BEGINNER),
        ("How does CBT work?", 0.90, UserExpertiseLevel.INTERMEDIATE),
        ("Can anxiety be cured?", 0.88, UserExpertiseLevel.BEGINNER),
        ("What is the role of serotonin in depression?", 0.92, UserExpertiseLevel.ADVANCED),
    ]
    
    for question, quality, expertise in interactions:
        response = f"Response to: {question}"
        personalizer.record_interaction(
            user_id=user_id,
            question=question,
            response=response,
            expertise_detected=expertise,
            quality_score=quality
        )
        print(f"✅ Recorded: {question[:40]}... ({expertise.value})")
    
    # Show personalization prompt
    print("\n2️⃣ Personalization-Based Prompt:")
    print("-"*70)
    
    personalizer.user_profiles[user_id] = UserContext(
        user_id=user_id,
        expertise_level=UserExpertiseLevel.INTERMEDIATE
    )
    
    personal_prompt = personalizer.get_personalization_prompt(user_id)
    print(f"Generated Prompt:\n{personal_prompt}")
    
    # Show expertise update
    print("\n3️⃣ Expertise Update Based on Interactions:")
    print("-"*70)
    
    old_level = personalizer.user_profiles[user_id].expertise_level
    personalizer.update_user_expertise(user_id, UserExpertiseLevel.ADVANCED)
    new_level = personalizer.user_profiles[user_id].expertise_level
    
    print(f"Updated: {old_level.value} → {new_level.value}")


# ============================================================================
# FULL SYSTEM INTEGRATION EXAMPLE
# ============================================================================

def example_8_full_system_integration():
    """Demonstrate complete system in action"""
    
    print("\n" + "="*70)
    print("EXAMPLE 8: FULL SYSTEM INTEGRATION")
    print("="*70)
    
    system = ContextAwareAISystem()
    
    # Register diverse users
    system.register_user(
        user_id="patient_john",
        expertise_level=UserExpertiseLevel.BEGINNER,
        language_preference="english",
        interests=["anxiety", "therapy"]
    )
    
    system.register_user(
        user_id="therapist_sarah",
        expertise_level=UserExpertiseLevel.ADVANCED,
        language_preference="english",
        interests=["research", "evidence-based treatment"]
    )
    
    # Process queries from different users
    queries = [
        ("patient_john", "I keep feeling worried about everything", False),
        ("therapist_sarah", "What neurobiological changes occur with psychotherapy?", False),
        ("patient_john", "I'm having a crisis. Please help!", True),  # Emergency mode
    ]
    
    print("\n📊 Processing Diverse Queries:")
    print("-"*70)
    
    for user_id, question, emergency in queries:
        result = system.process_query(user_id, question, emergency)
        
        print(f"\n👤 User: {user_id}")
        print(f"   Question: {question}")
        print(f"   Expertise Detected: {result['detected_expertise']}")
        print(f"   Quality: {result['quality_assessment']['recommendation']}")
        print(f"   Emergency Mode: {'🚨 YES' if emergency else '❌ NO'}")
    
    # Show system status
    print("\n" + "-"*70)
    print("\n🖥️ System Status:")
    status = system.get_system_status()
    
    for component, info in status['components'].items():
        print(f"   {component}: {info}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    
    print("""
    🧠 CONTEXT-AWARE AI SYSTEM - COMPREHENSIVE EXAMPLES
    =========================================
    
    This script demonstrates all 7 components:
    1. System Prompt Manager - Master behavior control
    2. Context Utilization Engine - Response style adaptation
    3. Context Injection Flow - Complete prompt assembly
    4. User-Type Detection - Expertise level detection
    5. Response Quality Filter - Output validation
    6. Few-Shot Training - Example-based learning
    7. Personalization Layer - User history & preferences
    """)
    
    # Run all examples
    try:
        example_1_system_prompt_manager()
        example_2_context_utilization()
        example_3_context_injection()
        example_4_user_type_detection()
        example_5_quality_filter()
        example_6_few_shot_training()
        example_7_personalization()
        example_8_full_system_integration()
        
        print("\n" + "="*70)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*70)
    
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
