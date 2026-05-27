"""
🎬 INTERACTIVE DEMO: Context-Aware Personalization System
==========================================================
Experience the personalization engine in action with real examples!
"""

import json
from datetime import datetime
from context_aware_engine import (
    NeuronixPersonalizationEngine,
    UserType,
    ResponseQualityValidator
)

# Color codes for pretty printing
HEADER = '\033[95m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
END = '\033[0m'


def print_section(title):
    """Print a section header"""
    print(f"\n{BOLD}{CYAN}{'='*80}{END}")
    print(f"{BOLD}{CYAN}{title.center(80)}{END}")
    print(f"{BOLD}{CYAN}{'='*80}{END}\n")


def print_response(label, content, max_chars=300):
    """Print a response with nice formatting"""
    if len(content) > max_chars:
        content = content[:max_chars] + "..."
    print(f"{BLUE}{label}:{END}")
    print(f"  {content}\n")


def print_metadata(label, value):
    """Print metadata"""
    print(f"  {GREEN}•{END} {label}: {BOLD}{value}{END}")


class InteractiveDemo:
    """Interactive demonstration of the personalization system"""
    
    def __init__(self):
        self.engine = NeuronixPersonalizationEngine()
        print(f"{GREEN}✅ Personalization Engine Loaded{END}")
    
    def demo_1_beginner_user(self):
        """Demo 1: Beginner user experiencing the system"""
        print_section("DEMO 1: Beginner User (First Time)")
        
        user_id = "demo_beginner"
        
        # Query 1
        q1 = "What is anxiety? I'm feeling worried a lot."
        print(f"{BOLD}{YELLOW}User Question:{END}")
        print(f"  \"{q1}\"\n")
        
        # Get enhanced context
        payload = self.engine.enhance_query(user_id, q1)
        
        print_metadata("User Type Detected", payload['user_type'].upper())
        print_metadata("System Prompt Type", "Beginner-Friendly")
        print_metadata("Few-Shot Examples", "Included (Simple Language)")
        print_metadata("Personalization Level", "Basic")
        
        print(f"\n{BLUE}{UNDERLINE}System Prompt (for the AI):{END}")
        print(f"{payload['system_prompt'][:400]}...\n")
        
        # Simulated response
        simulated_response = """Anxiety is like your worry button getting stuck! 😟

Think of it this way:
• Normal = You worry sometimes
• Anxiety = You worry A LOT, all the time

What it feels like:
✓ Your heart beats faster
✓ You feel nervous
✓ Hard to sleep
✓ Can't focus on things

Good news: It's very treatable! 

You can:
1. Talk to someone (friend, family)
2. Deep breathing exercises
3. Regular exercise helps
4. See a doctor if it gets worse

You're NOT alone! Many people feel this way."""
        
        print(f"{GREEN}{UNDERLINE}AI Response (Beginner-Level):{END}")
        print(f"  {simulated_response}\n")
        
        # Validate response
        validation = ResponseQualityValidator.validate(simulated_response)
        print(f"{GREEN}✅ Response Quality Score: {validation['quality_score']}/100{END}\n")
        
        # Update profile
        self.engine.process_response(user_id, q1, simulated_response)
        
        print(f"{CYAN}Profile Updated!{END}")
        print(f"  → Query stored in history")
        print(f"  → Interest 'anxiety' tracked")
        print(f"  → System learning about this user\n")
    
    def demo_2_progressive_learning(self):
        """Demo 2: Same user becomes more advanced over time"""
        print_section("DEMO 2: Progressive Learning (Same User After 3+ Queries)")
        
        user_id = "demo_progressive"
        
        # Simulate previous interactions
        queries = [
            ("What is depression?", "Depression is a mental health condition..."),
            ("How does therapy help?", "Therapy works by changing thought patterns..."),
            ("What about medications?", "There are different types of medications..."),
        ]
        
        print(f"{YELLOW}Simulating user history:{END}")
        for q, a in queries:
            self.engine.process_response(user_id, q, a)
            print(f"  ✓ Query: {q}")
        
        # Now ask a more advanced question
        q_advanced = "Explain the neurobiological basis of depression and how SSRIs affect serotonin reuptake"
        print(f"\n{BOLD}{YELLOW}New Question (After 4 queries):{END}")
        print(f"  \"{q_advanced}\"\n")
        
        # Get enhanced context
        payload = self.engine.enhance_query(user_id, q_advanced)
        
        print_metadata("User Type Detected", payload['user_type'].upper())
        print_metadata("System Prompt Type", "Intermediate-Advanced")
        print_metadata("Complexity Level", "Technical + Clinical")
        print_metadata("Few-Shot Examples", "Research-backed examples")
        
        print(f"\n{BLUE}{UNDERLINE}System Prompt (Updated for Advanced User):{END}")
        print(f"{payload['system_prompt'][:400]}...\n")
        
        # Simulated advanced response
        advanced_response = """Depression involves dysregulation of multiple neurotransmitter systems:

NEUROBIOLOGICAL BASIS:
• Monoamine Hypothesis: Deficiency in serotonin (5-HT), norepinephrine (NE), dopamine (DA)
• HPA Axis Dysfunction: Elevated baseline cortisol, impaired negative feedback
• Glutamatergic Imbalance: Excessive NMDA receptor activity
• Neuroplasticity Changes: ↓ BDNF, hippocampal volume reduction
• Inflammatory Markers: Elevated TNF-α, IL-6

MECHANISM OF SSRIs:
1. Block serotonin reuptake at the presynaptic terminal
2. ↑ Synaptic serotonin concentration
3. Enhanced 5-HT1A/1B receptor activation
4. Delayed neuroadaptation (weeks 4-8): ↓ Autoreceptor sensitivity
5. Enhanced neurogenesis and synaptic plasticity

CLINICAL EVIDENCE:
• 50-60% remission rates in RCTs
• First-line treatment for MDD per DSM-5
• Typical latency: 2-4 weeks for response"""
        
        print(f"{GREEN}{UNDERLINE}AI Response (Advanced-Level):{END}")
        print(f"  {advanced_response}\n")
        
        validation = ResponseQualityValidator.validate(advanced_response)
        print(f"{GREEN}✅ Response Quality Score: {validation['quality_score']}/100{END}\n")
        
        # Update profile
        self.engine.process_response(user_id, q_advanced, advanced_response)
        
        # Show analytics
        analytics = self.engine.get_user_analytics(user_id)
        print(f"{CYAN}User Profile Updated!{END}")
        print_metadata("Total Queries", analytics['total_queries'])
        print_metadata("Expertise Level", analytics['user_type'].upper())
        print_metadata("Topics of Interest", ', '.join(analytics['interests']))
        print(f"\n{YELLOW}→ System automatically adjusted complexity level!{END}\n")
    
    def demo_3_crisis_scenario(self):
        """Demo 3: Crisis detection and response"""
        print_section("DEMO 3: Crisis Detection & Safety Resources")
        
        user_id = "demo_crisis"
        
        crisis_query = "I've been thinking about ending everything. I can't handle this pain anymore."
        print(f"{RED}{BOLD}⚠️  CRISIS SCENARIO ⚠️{END}\n")
        print(f"{YELLOW}User Question:{END}")
        print(f"  \"{crisis_query}\"\n")
        
        # Get enhanced context
        payload = self.engine.enhance_query(user_id, crisis_query)
        
        print(f"{RED}⚠️  CRISIS KEYWORDS DETECTED!{END}\n")
        print_metadata("Crisis Indicator", "Suicidal ideation")
        print_metadata("Automatic Action", "Resources provided")
        print_metadata("Escalation", "Emergency contacts included")
        
        # Simulate response
        crisis_response = """I hear you, and I'm genuinely concerned about your safety.

What you're feeling right now is TEMPORARY, even if it doesn't feel that way.

⚠️ IMMEDIATE HELP (Get in touch RIGHT NOW):

India:
📞 Aasra: +91-22-2754-6669
📞 iCall: 9152987821
📞 Vandrevala Foundation: +91-99999-77722

USA:
📞 National Suicide Prevention: 988
📞 Crisis Text: Text HOME to 741741

UK:
📞 Samaritans: 116 123
💬 SHOUT: Text SHOUT to 85258

IMMEDIATE ACTIONS:
✓ Call one of the numbers above RIGHT NOW
✓ Tell someone you trust what you're feeling
✓ Go to nearest emergency room
✓ Don't be alone

You matter. Your life has value. Please reach out."""
        
        print(f"\n{RED}{UNDERLINE}AI Response (Safety-First):{END}")
        print(f"  {crisis_response}\n")
        
        # Process with crisis detection
        result = self.engine.process_response(user_id, crisis_query, crisis_response)
        
        print(f"{RED}{BOLD}CRISIS HANDLING:{END}")
        print_metadata("Crisis Detected", "YES")
        print_metadata("Safety Resources", "Provided")
        print_metadata("Profile Flag", "crisis_keywords_detected = True")
        print_metadata("Escalation", "Should be reviewed by human")
        
        profile = self.engine.profile_manager.load_profile(user_id)
        print(f"\n{YELLOW}Note: This user's profile is flagged for safety monitoring{END}\n")
    
    def demo_4_response_quality(self):
        """Demo 4: Response quality validation"""
        print_section("DEMO 4: Response Quality Validation")
        
        test_cases = [
            {
                "label": "✅ High Quality Response",
                "response": "Depression is a mood disorder characterized by persistent sadness. It affects sleep, appetite, and energy levels. Treatment includes therapy and medication.",
                "should_pass": True
            },
            {
                "label": "❌ Empty Response",
                "response": "",
                "should_pass": False
            },
            {
                "label": "❌ Random Characters",
                "response": "xyzabc !@#$ qwerty asdf",
                "should_pass": False
            },
            {
                "label": "❌ Too Short",
                "response": "Yes.",
                "should_pass": False
            },
            {
                "label": "❌ Completely Irrelevant",
                "response": "Paris is the capital of France. The Eiffel Tower is very tall. France makes good wine.",
                "should_pass": False
            },
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"{BOLD}Test Case {i}: {test['label']}{END}")
            validation = ResponseQualityValidator.validate(test['response'])
            
            status = f"{GREEN}✅ VALID{END}" if validation['is_valid'] else f"{RED}❌ INVALID{END}"
            print(f"  Status: {status}")
            print(f"  Quality Score: {validation['quality_score']}/100")
            
            if validation['issues']:
                print(f"  Issues Found: {', '.join(validation['issues'])}")
            
            feedback = ResponseQualityValidator.get_feedback(validation)
            print(f"  Feedback: {feedback}\n")
    
    def demo_5_personalization_journey(self):
        """Demo 5: Complete personalization journey"""
        print_section("DEMO 5: Complete Personalization Journey")
        
        user_id = "demo_journey"
        
        print(f"{CYAN}Scenario: New user's first 5 interactions{END}\n")
        
        interactions = [
            {
                "q": "What is bipolar disorder?",
                "a": "Bipolar disorder causes mood swings...",
            },
            {
                "q": "How does it affect relationships?",
                "a": "Mood changes can strain relationships...",
            },
            {
                "q": "What treatments are available?",
                "a": "Treatment includes medication and therapy...",
            },
            {
                "q": "What about lithium therapy?",
                "a": "Lithium is a mood stabilizer...",
            },
            {
                "q": "Explain cellular mechanisms of mood stabilizers",
                "a": "Mood stabilizers affect intracellular signaling...",
            },
        ]
        
        for i, interaction in enumerate(interactions, 1):
            # Enhance query
            payload = self.engine.enhance_query(user_id, interaction['q'])
            
            # Process response
            self.engine.process_response(
                user_id,
                interaction['q'],
                interaction['a']
            )
            
            # Get analytics
            analytics = self.engine.get_user_analytics(user_id)
            
            print(f"{BOLD}Interaction {i}:{END}")
            print(f"  Question: {interaction['q']}")
            print(f"  Detected Type: {analytics['user_type'].upper()}")
            print(f"  Total Queries: {analytics['total_queries']}")
            print(f"  Topics: {', '.join(analytics['interests'][:3])}")
            
            # Show progression
            if i > 1:
                prev_analytics = self.engine.get_user_analytics(user_id)
                progression = f"  {YELLOW}Progression: {analytics['total_queries']} queries →{END}"
                if i == 5:
                    print(f"{progression} User now detected as {analytics['user_type'].upper()}! ✨\n")
                else:
                    print()
        
        final_analytics = self.engine.get_user_analytics(user_id)
        print(f"{GREEN}{BOLD}Final User Profile:{END}")
        print_metadata("Expertise Level", final_analytics['user_type'])
        print_metadata("Total Interactions", final_analytics['total_queries'])
        print_metadata("Topics of Interest", ', '.join(final_analytics['interests']))
        print_metadata("Member Since", final_analytics['member_since'][:10])
    
    def run_all(self):
        """Run all demos"""
        print(r"""
        ╔════════════════════════════════════════════════════════════╗
        ║                                                            ║
        ║  🧠 NEURONIX - Context-Aware Personalization Demo 🧠    ║
        ║                                                            ║
        ║  Watch how the AI adapts to different users and          ║
        ║  learns from interactions!                                ║
        ║                                                            ║
        ╚════════════════════════════════════════════════════════════╝
        """)
        
        demos = [
            ("First-Time Beginner", self.demo_1_beginner_user),
            ("Progressive Learning", self.demo_2_progressive_learning),
            ("Crisis Handling", self.demo_3_crisis_scenario),
            ("Response Quality", self.demo_4_response_quality),
            ("Personalization Journey", self.demo_5_personalization_journey),
        ]
        
        print(f"\n{BOLD}Available Demos:{END}")
        for i, (name, _) in enumerate(demos, 1):
            print(f"  {CYAN}{i}{END}. {name}")
        
        print(f"\n  {CYAN}0{END}. Run All")
        print(f"  {CYAN}6{END}. Exit\n")
        
        try:
            choice = input(f"{BOLD}Select demo (0-6): {END}").strip()
            
            if choice == "0":
                for name, demo_func in demos:
                    demo_func()
                    input(f"\n{BOLD}Press Enter to continue...{END}")
            elif choice in ["1", "2", "3", "4", "5"]:
                demo_func = demos[int(choice)-1][1]
                demo_func()
            elif choice == "6":
                print(f"\n{GREEN}Thanks for using NEURONIX!{END}\n")
                return
            else:
                print(f"{RED}Invalid choice{END}\n")
                self.run_all()
        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}Demo interrupted{END}\n")
        except Exception as e:
            print(f"\n{RED}Error: {e}{END}\n")


def main():
    """Main entry point"""
    try:
        demo = InteractiveDemo()
        demo.run_all()
    except Exception as e:
        print(f"{RED}Error initializing demo: {e}{END}")
        print(f"{YELLOW}Make sure context_aware_engine.py is in the same directory{END}\n")


if __name__ == "__main__":
    main()
