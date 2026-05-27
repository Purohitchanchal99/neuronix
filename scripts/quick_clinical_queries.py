"""
🏥 QUICK CLINICAL QUERIES
========================
Test and demonstrate the 7-component context-aware AI system

Handles in-progress ingestion gracefully with intelligent context awareness
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from context_aware_ai_system import (
    ContextAwareAISystem,
    UserExpertiseLevel,
    UserContext
)
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [CLINICAL] - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class ClinicalQueryRunner:
    """Execute clinical queries with full context awareness"""
    
    def __init__(self):
        self.system = ContextAwareAISystem()
        self.query_results = []
        logger.info("🏥 Clinical Query Runner initialized")
    
    def run_clinical_test_suite(self):
        """Run comprehensive clinical query tests"""
        
        logger.info("\n" + "="*70)
        logger.info("🧪 CLINICAL QUERY TEST SUITE")
        logger.info("="*70)
        
        # Test Setup: Register different user types
        self._setup_test_users()
        
        # ====================================================================
        # TEST CASE 1: BEGINNER USER - SIMPLE ANXIETY QUESTION
        # ====================================================================
        logger.info("\n📋 TEST 1: Beginner User - Anxiety Query")
        logger.info("-"*70)
        
        result = self.system.process_query(
            user_id="user_beginner_01",
            question="What is anxiety? I'm experiencing it for the first time.",
            emergency=False
        )
        
        self._print_result(result, test_num=1)
        
        # ====================================================================
        # TEST CASE 2: INTERMEDIATE USER - TREATMENT COMPARISON
        # ====================================================================
        logger.info("\n📋 TEST 2: Intermediate User - Treatment Comparison")
        logger.info("-"*70)
        
        result = self.system.process_query(
            user_id="user_intermediate_01",
            question="What's the difference between CBT and DBT for anxiety disorders?",
            emergency=False
        )
        
        self._print_result(result, test_num=2)
        
        # ====================================================================
        # TEST CASE 3: ADVANCED USER - NEUROBIOLOGICAL QUESTION
        # ====================================================================
        logger.info("\n📋 TEST 3: Advanced User - Neurobiological Query")
        logger.info("-"*70)
        
        result = self.system.process_query(
            user_id="user_advanced_01",
            question="Explain the amygdala-prefrontal cortex dysregulation in generalized anxiety disorder",
            emergency=False
        )
        
        self._print_result(result, test_num=3)
        
        # ====================================================================
        # TEST CASE 4: HINGLISH QUERY
        # ====================================================================
        logger.info("\n📋 TEST 4: Hinglish Query")
        logger.info("-"*70)
        
        result = self.system.process_query(
            user_id="user_hindi_01",
            question="Mujhe depression ho gaya hai. Isse kaise chhutkaara paunga?",
            emergency=False
        )
        
        self._print_result(result, test_num=4)
        
        # ====================================================================
        # TEST CASE 5: CRISIS SCENARIO - EMERGENCY MODE
        # ====================================================================
        logger.info("\n📋 TEST 5: Crisis Scenario - Emergency Mode")
        logger.info("-"*70)
        
        result = self.system.process_query(
            user_id="user_crisis_01",
            question="I'm thinking about harming myself. What should I do?",
            emergency=True
        )
        
        self._print_result(result, test_num=5)
        
        # ====================================================================
        # TEST CASE 6: RESOURCE REQUEST
        # ====================================================================
        logger.info("\n📋 TEST 6: Resource Request")
        logger.info("-"*70)
        
        result = self.system.process_query(
            user_id="user_beginner_02",
            question="How do I find a therapist in my area?",
            emergency=False
        )
        
        self._print_result(result, test_num=6)
        
        # ====================================================================
        # TEST CASE 7: FOLLOW-UP INTERACTION (PERSONALIZATION)
        # ====================================================================
        logger.info("\n📋 TEST 7: Follow-up Query (Personalization Test)")
        logger.info("-"*70)
        
        # First interaction
        result1 = self.system.process_query(
            user_id="user_personalization_01",
            question="What is depression?",
            emergency=False
        )
        
        # Follow-up interaction (should detect interest pattern)
        result2 = self.system.process_query(
            user_id="user_personalization_01",
            question="What are the treatment options?",
            emergency=False
        )
        
        self._print_result(result2, test_num="7 (Follow-up)")
        
        # ====================================================================
        # FINAL REPORT
        # ====================================================================
        self._print_final_report()
    
    def _setup_test_users(self):
        """Register test users with different profiles"""
        
        logger.info("\n👥 Setting up test users...")
        
        # User 1: Beginner
        self.system.register_user(
            user_id="user_beginner_01",
            expertise_level=UserExpertiseLevel.BEGINNER,
            language_preference="english",
            interests=["anxiety", "mental health basics"]
        )
        
        # User 2: Intermediate
        self.system.register_user(
            user_id="user_intermediate_01",
            expertise_level=UserExpertiseLevel.INTERMEDIATE,
            language_preference="english",
            interests=["psychology", "therapy techniques", "clinical research"]
        )
        
        # User 3: Advanced
        self.system.register_user(
            user_id="user_advanced_01",
            expertise_level=UserExpertiseLevel.ADVANCED,
            language_preference="english",
            interests=["neuroscience", "neuropsychology", "neurotransmitter biology"]
        )
        
        # User 4: Hinglish preference
        self.system.register_user(
            user_id="user_hindi_01",
            expertise_level=UserExpertiseLevel.BEGINNER,
            language_preference="hinglish",
            interests=["depression", "mental wellness"]
        )
        
        # User 5: Crisis scenario
        self.system.register_user(
            user_id="user_crisis_01",
            expertise_level=UserExpertiseLevel.BEGINNER,
            language_preference="english",
            interests=[]
        )
        
        # User 6: Resource seeker
        self.system.register_user(
            user_id="user_beginner_02",
            expertise_level=UserExpertiseLevel.BEGINNER,
            language_preference="english",
            interests=["therapy", "finding help"]
        )
        
        # User 7: Personalization test
        self.system.register_user(
            user_id="user_personalization_01",
            expertise_level=UserExpertiseLevel.BEGINNER,
            language_preference="english",
            interests=[]
        )
        
        logger.info("✅ 7 test users registered")
    
    def _print_result(self, result: dict, test_num):
        """Print formatted query result"""
        
        logger.info(f"\n📊 Query Result {test_num}:")
        logger.info(f"   User: {result['user_id']}")
        logger.info(f"   Question: {result['question'][:60]}...")
        logger.info(f"   Detected Expertise: {result['detected_expertise']}")
        logger.info(f"   Detection Confidence: {result['detection_confidence']:.2f}")
        logger.info(f"   Quality Assessment: {result['quality_assessment']['recommendation']}")
        logger.info(f"   Quality Score: {result['quality_assessment']['score']:.2f}")
        
        if result['quality_assessment']['issues']:
            logger.info(f"   Issues: {', '.join(result['quality_assessment']['issues'])}")
        
        if result['quality_assessment']['unsafe_indicators']:
            logger.warning(f"   ⚠️ Safety Flag: {result['quality_assessment']['unsafe_indicators']}")
        
        logger.info(f"   Response Preview: {result['simulated_response'][:100]}...")
        
        self.query_results.append(result)
    
    def _print_final_report(self):
        """Print final test report"""
        
        logger.info("\n" + "="*70)
        logger.info("📊 FINAL TEST REPORT")
        logger.info("="*70)
        
        status = self.system.get_system_status()
        
        logger.info(f"\n✅ System Status:")
        for component, status_text in status['components'].items():
            logger.info(f"   {component}: {status_text}")
        
        logger.info(f"\n📈 Statistics:")
        logger.info(f"   Total Queries Processed: {len(self.query_results)}")
        logger.info(f"   Total Interactions Logged: {status['total_interactions']}")
        logger.info(f"   Registered Users: {status['registered_users']}")
        
        # Quality assessment summary
        passed_count = sum(1 for r in self.query_results if r['quality_assessment']['passed'])
        total_count = len(self.query_results)
        
        logger.info(f"\n🎯 Quality Assessment Summary:")
        logger.info(f"   Passed: {passed_count}/{total_count} ({100*passed_count/total_count:.1f}%)")
        
        # Expertise detection summary
        expertise_counts = {}
        for r in self.query_results:
            exp = r['detected_expertise']
            expertise_counts[exp] = expertise_counts.get(exp, 0) + 1
        
        logger.info(f"\n🧠 Expertise Level Detection Summary:")
        for level, count in expertise_counts.items():
            logger.info(f"   {level}: {count}")
        
        logger.info("\n✅ Test Suite Completed!")
    
    def save_results(self, filename: str = "clinical_queries_results.json"):
        """Save test results to file"""
        
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "test_count": len(self.query_results),
            "system_status": self.system.get_system_status(),
            "results": []
        }
        
        for result in self.query_results:
            # Serialize result
            result_copy = result.copy()
            output_data["results"].append(result_copy)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Results saved to: {filename}")


# ============================================================================
# INTERACTIVE QUERY MODE
# ============================================================================

class InteractiveQueryMode:
    """Interactive mode for testing queries one by one"""
    
    def __init__(self):
        self.system = ContextAwareAISystem()
        self._setup_default_users()
    
    def _setup_default_users(self):
        """Setup default users"""
        
        self.system.register_user(
            user_id="interactive_user",
            expertise_level=UserExpertiseLevel.INTERMEDIATE,
            language_preference="english",
            interests=["mental health"]
        )
    
    def run_interactive(self):
        """Run interactive query session"""
        
        print("\n" + "="*70)
        print("🏥 INTERACTIVE CLINICAL QUERY MODE")
        print("="*70)
        print("\nCommands:")
        print("  Type your question to get a response")
        print("  'level beginner' - Switch to beginner mode")
        print("  'level intermediate' - Switch to intermediate")
        print("  'level advanced' - Switch to advanced")
        print("  'emergency' - Toggle emergency mode")
        print("  'status' - Show system status")
        print("  'quit' - Exit")
        print("-"*70)
        
        emergency_mode = False
        
        while True:
            user_input = input("\n💬 Your query: ").strip()
            
            if not user_input:
                continue
            
            # Commands
            if user_input.lower() == 'quit':
                print("✅ Exiting...")
                break
            
            elif user_input.lower() == 'status':
                status = self.system.get_system_status()
                print(json.dumps(status, indent=2))
                continue
            
            elif user_input.lower().startswith('level'):
                level_str = user_input.split()[1].lower()
                if level_str == 'beginner':
                    self.system.personalization.user_profiles['interactive_user'].expertise_level = UserExpertiseLevel.BEGINNER
                    print("✅ Switched to Beginner level")
                elif level_str == 'intermediate':
                    self.system.personalization.user_profiles['interactive_user'].expertise_level = UserExpertiseLevel.INTERMEDIATE
                    print("✅ Switched to Intermediate level")
                elif level_str == 'advanced':
                    self.system.personalization.user_profiles['interactive_user'].expertise_level = UserExpertiseLevel.ADVANCED
                    print("✅ Switched to Advanced level")
                continue
            
            elif user_input.lower() == 'emergency':
                emergency_mode = not emergency_mode
                status = "ON" if emergency_mode else "OFF"
                print(f"✅ Emergency mode: {status}")
                continue
            
            # Process query
            print("\n⏳ Processing query...")
            result = self.system.process_query(
                user_id="interactive_user",
                question=user_input,
                emergency=emergency_mode
            )
            
            print(f"\n📊 Response:")
            print(f"   Expertise Detected: {result['detected_expertise']} (confidence: {result['detection_confidence']:.2f})")
            print(f"   Quality: {result['quality_assessment']['recommendation']} (score: {result['quality_assessment']['score']:.2f})")
            print(f"\n💬 Response:\n   {result['simulated_response']}")
            
            if result['quality_assessment']['issues']:
                print(f"\n⚠️ Issues: {', '.join(result['quality_assessment']['issues'])}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    
    import sys
    
    # Check for command-line arguments
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        # Interactive mode
        interactive = InteractiveQueryMode()
        interactive.run_interactive()
    
    else:
        # Test suite mode (default)
        runner = ClinicalQueryRunner()
        runner.run_clinical_test_suite()
        runner.save_results()
    
    print("\nDone!")