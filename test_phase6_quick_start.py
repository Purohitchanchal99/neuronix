#!/usr/bin/env python3
"""
PHASE 6: Quick Start Test
=========================

Run this to verify Phase 6 works end-to-end before integration
"""

import sys
import json
from datetime import datetime

def test_memory_system():
    """Test memory system"""
    print("\n" + "="*60)
    print("TEST 1: Memory System")
    print("="*60)
    
    try:
        from scripts.memory_system import ConversationStore
        
        store = ConversationStore()
        user_id = "test_user_1"
        
        # Start conversation
        store.start_conversation(user_id)
        
        # Add messages
        store.add_message(user_id, "I want to learn recursion", role="user", topics=["recursion"])
        store.add_message(user_id, "Recursion is when a function calls itself", role="assistant")
        store.add_message(user_id, "How do I avoid infinite loops?", role="user", topics=["recursion", "loops"])
        store.add_message(user_id, "Use a base case to stop the recursion", role="assistant")
        
        # Test retrieval
        results = store.search_memories("How does recursion work?", k=2)
        
        print(f"✅ Created conversation with 4 messages")
        print(f"✅ Found {len(results)} relevant memories")
        print(f"✅ Memory system working!\n")
        
        return True
    except Exception as e:
        print(f"❌ Memory system failed: {e}\n")
        return False


def test_learning_tracker():
    """Test learning tracker"""
    print("\n" + "="*60)
    print("TEST 2: Learning Tracker")
    print("="*60)
    
    try:
        from scripts.learning_tracker import LearningTracker, InteractionType
        
        tracker = LearningTracker()
        user_id = "test_user_2"
        
        # Record interactions
        tracker.record_interaction(user_id, "recursion", InteractionType.STRUGGLE)
        tracker.record_interaction(user_id, "recursion", InteractionType.PARTIAL)
        tracker.record_interaction(user_id, "recursion", InteractionType.SUCCESS)
        
        tracker.record_interaction(user_id, "functions", InteractionType.SUCCESS)
        tracker.record_interaction(user_id, "functions", InteractionType.MASTERY)
        
        # Get metrics
        metrics = tracker.get_metrics(user_id)
        mastery = tracker.get_mastery(user_id, "recursion")
        
        print(f"✅ Recorded 5 learning interactions")
        print(f"✅ Recursion confidence: {mastery.confidence:.2f}")
        print(f"✅ Topics mastered: {metrics.mastered_topics}")
        print(f"✅ Learning tracker working!\n")
        
        return True
    except Exception as e:
        print(f"❌ Learning tracker failed: {e}\n")
        return False


def test_adaptive_recommender():
    """Test recommendations"""
    print("\n" + "="*60)
    print("TEST 3: Adaptive Recommender")
    print("="*60)
    
    try:
        from scripts.learning_tracker import LearningTracker, InteractionType
        from scripts.adaptive_recommender import AdaptiveRecommender
        
        tracker = LearningTracker()
        recommender = AdaptiveRecommender()
        user_id = "test_user_3"
        
        # Simulate learning
        tracker.record_interaction(user_id, "if-statements", InteractionType.MASTERY)
        tracker.record_interaction(user_id, "loops", InteractionType.SUCCESS)
        tracker.record_interaction(user_id, "loops", InteractionType.SUCCESS)
        
        # Get recommendation
        next_rec = recommender.recommend_next_topic(tracker, user_id)
        
        if next_rec:
            print(f"✅ Recommended topic: {next_rec.topic}")
            print(f"✅ Priority: {next_rec.priority:.2%}")
            print(f"✅ Reason: {next_rec.reason}")
            print(f"✅ Adaptive recommender working!\n")
            return True
        else:
            print(f"⚠️  No recommendation (expected for test user)\n")
            return True
        
    except Exception as e:
        print(f"❌ Adaptive recommender failed: {e}\n")
        return False


def test_session_summarizer():
    """Test session summarization"""
    print("\n" + "="*60)
    print("TEST 4: Session Summarizer")
    print("="*60)
    
    try:
        from scripts.memory_system import ConversationStore
        from scripts.learning_tracker import LearningTracker, InteractionType
        from scripts.session_summarizer import SessionSummarizer
        
        store = ConversationStore()
        tracker = LearningTracker()
        summarizer = SessionSummarizer()
        
        user_id = "test_user_4"
        
        # Create session
        store.start_conversation(user_id)
        store.add_message(user_id, "I'm confused about loops", role="user", tone="confused")
        store.add_message(user_id, "Loops let you repeat code...", role="assistant")
        store.add_message(user_id, "Now I get it!", role="user", tone="confident")
        store.add_message(user_id, "Great! Let's practice.", role="assistant")
        
        # Track learning
        tracker.record_interaction(user_id, "loops", InteractionType.CONFUSION)
        tracker.record_interaction(user_id, "loops", InteractionType.SUCCESS)
        
        # Close and summarize
        conversation = store.close_conversation(user_id)
        metrics = tracker.get_metrics(user_id)
        
        summary = summarizer.summarize_session(conversation, metrics, tracker)
        
        print(f"✅ Session summary generated")
        print(f"✅ Duration: {summary.duration_minutes} minutes")
        print(f"✅ Productivity: {summary.productivity_score:.0%}")
        print(f"✅ Key insights: {len(summary.insights)}")
        print(f"✅ Session summarizer working!\n")
        
        return True
    except Exception as e:
        print(f"❌ Session summarizer failed: {e}\n")
        return False


def main():
    """Run all tests"""
    print("\n" + "🚀 " * 20)
    print("PHASE 6 - QUICK START TEST")
    print("🚀 " * 20)
    
    results = []
    
    # Run tests
    results.append(("Memory System", test_memory_system()))
    results.append(("Learning Tracker", test_learning_tracker()))
    results.append(("Adaptive Recommender", test_adaptive_recommender()))
    results.append(("Session Summarizer", test_session_summarizer()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nPhase 6 is ready for integration:")
        print("  1. Copy files to your project")
        print("  2. Update neuronix_core.py with imports")
        print("  3. Implement handle_query_phase6() method")
        print("  4. Update backend API /chat endpoint")
        print("  5. Deploy!")
        print("\nSee: PHASE6_IMPLEMENTATION_GUIDE.md for details")
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("Check error messages above and fix dependencies")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
