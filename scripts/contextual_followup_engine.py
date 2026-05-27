#!/usr/bin/env python3
"""
Phase 3C: Contextual Follow-up Engine
======================================
Generates smart, contextual follow-up questions that guide conversation

Replaces generic follow-ups with:
- Context-aware questions
- Guided conversation flow
- Progressive deepening
- Topic-specific follow-ups
"""

from typing import Dict, List, Optional
import random


class ContextualFollowupEngine:
    """
    Generates follow-up questions based on conversation context
    
    Strategy:
    1. Identify topic (anxiety, sleep, depression, etc.)
    2. Detect stage (initial, developing, escalating)
    3. Generate contextual question that guides deeper understanding
    """
    
    # 🔥 TOPIC-SPECIFIC FOLLOW-UPS
    ANXIETY_FOLLOWUPS = [
        # Initial
        "When do you usually feel this the most?",
        "Has something changed recently that might have triggered this?",
        "Do you notice any physical symptoms along with the anxiety?",
        
        # Developing
        "How long does the anxiety typically last when it hits?",
        "Do you have any patterns—times of day or situations that make it worse?",
        "What's the worst part about feeling this way?",
        
        # Escalating
        "This sounds like it's really affecting your daily life. How are you managing?",
        "Have you noticed it getting worse over time?",
        "What would help you feel even a little bit more in control?",
    ]
    
    SLEEP_FOLLOWUPS = [
        # Initial
        "Is this a new problem or has it been going on for a while?",
        "What time do you usually try to sleep?",
        "What kinds of things run through your mind when you can't sleep?",
        
        # Developing
        "Are you falling asleep but waking up, or is it hard to fall asleep?",
        "How many hours are you actually getting?",
        "What have you already tried to help?",
        
        # Escalating
        "How is the lack of sleep affecting your ability to function?",
        "Is this making other problems worse—like anxiety or mood?",
        "Would you be open to some evidence-based sleep techniques?",
    ]
    
    DEPRESSION_FOLLOWUPS = [
        # Initial
        "When did you start noticing this?",
        "Is there anything that makes it feel a bit better, even temporarily?",
        "Have you felt this way before?",
        
        # Developing
        "How is this affecting your ability to do everyday things?",
        "Are there people in your life you feel comfortable talking to about this?",
        "What would a good day look like for you right now?",
        
        # Escalating
        "You've been dealing with this for a while now. Have you considered talking to a professional?",
        "Is there someone close to you who knows what you're going through?",
        "What's one thing that used to matter to you that we could talk about working back toward?",
    ]
    
    STRESS_FOLLOWUPS = [
        # Initial
        "What's the main thing causing you stress right now?",
        "Is this a new situation or an ongoing issue?",
        "How is it affecting your daily life?",
        
        # Developing
        "Are you handling it okay, or is it becoming overwhelming?",
        "Where does most of your stress come from—work, relationships, something else?",
        "If you had to pick one thing to address first, what would it be?",
        
        # Escalating
        "This sounds like a lot to carry. Do you have support?",
        "What would make the biggest difference in reducing this stress?",
        "Would you be open to exploring some stress management techniques?",
    ]
    
    ANGER_FOLLOWUPS = [
        # Initial
        "What usually triggers this anger?",
        "Is this a recent thing or something you've dealt with before?",
        "How do you typically react when you get angry?",
        
        # Developing
        "Are there warning signs before the anger hits?",
        "What's usually happening right before it gets intense?",
        "How does it feel for you physically when you're angry?",
        
        # Escalating
        "This anger seems to be really impacting your life. What's underneath it?",
        "Are there specific people or situations that set it off?",
        "What would help you cool down when it's happening?",
    ]
    
    GENERAL_FOLLOWUPS = [
        "Tell me more about that",
        "When did you first notice this?",
        "How is this affecting your daily life?",
        "Is there anything else you want to share?",
        "What would help right now?",
    ]
    
    # 🔥 ESCALATION-SPECIFIC FOLLOW-UPS
    ESCALATING_FOLLOWUPS = [
        "I've noticed things seem to be getting more difficult for you. How are you holding up?",
        "It sounds like this is intensifying. Do you have support right now?",
        "This pattern concerns me. Have you talked to anyone professional about it?",
        "You're dealing with a lot. What do you think would help most right now?",
    ]
    
    IMPROVING_FOLLOWUPS = [
        "It sounds like you're managing better. What's helping?",
        "Keep going with what's working. What's one thing you could do more of?",
        "That's great progress. What else could support this improvement?",
        "You're doing well. What do you think comes next?",
    ]
    
    CHRONIC_STRESS_FOLLOWUPS = [
        "You've been dealing with this for a while. How are you holding up?",
        "Have you been able to get any breaks or support?",
        "What would genuinely help you right now?",
        "Would professional support be something you'd consider?",
    ]
    
    def __init__(self):
        self.topic_map = {
            'anxiety': self.ANXIETY_FOLLOWUPS,
            'anxious': self.ANXIETY_FOLLOWUPS,
            'worried': self.ANXIETY_FOLLOWUPS,
            'sleep': self.SLEEP_FOLLOWUPS,
            'insomnia': self.SLEEP_FOLLOWUPS,
            'tired': self.SLEEP_FOLLOWUPS,
            'depressed': self.DEPRESSION_FOLLOWUPS,
            'depression': self.DEPRESSION_FOLLOWUPS,
            'sad': self.DEPRESSION_FOLLOWUPS,
            'stress': self.STRESS_FOLLOWUPS,
            'stressed': self.STRESS_FOLLOWUPS,
            'overwhelmed': self.STRESS_FOLLOWUPS,
            'angry': self.ANGER_FOLLOWUPS,
            'anger': self.ANGER_FOLLOWUPS,
            'frustrated': self.ANGER_FOLLOWUPS,
        }
    
    def generate_followup(
        self,
        query: str,
        conversation_count: int = 1,
        distress_trend: str = "stable",
        distress_level: float = 0.5
    ) -> str:
        """
        Generate contextual follow-up
        
        Args:
            query: User's latest query
            conversation_count: How many messages in this conversation
            distress_trend: 'escalating', 'improving', 'stable'
            distress_level: 0.0 to 1.0
        
        Returns:
            Contextual follow-up question
        """
        
        q_lower = query.lower()
        
        # Priority 1: Escalation-specific
        if distress_trend == 'escalating' and conversation_count >= 3:
            return random.choice(self.ESCALATING_FOLLOWUPS)
        
        if distress_trend == 'improving' and conversation_count >= 3:
            return random.choice(self.IMPROVING_FOLLOWUPS)
        
        if distress_level > 0.6 and conversation_count >= 3:
            return random.choice(self.CHRONIC_STRESS_FOLLOWUPS)
        
        # Priority 2: Topic-specific
        for keyword, followups in self.topic_map.items():
            if keyword in q_lower:
                # Return stage-appropriate followup
                if conversation_count <= 1:
                    return random.choice(followups[:3])  # Initial questions
                elif conversation_count <= 3:
                    return random.choice(followups[3:6])  # Developing questions
                else:
                    return random.choice(followups[6:])  # Escalating questions
        
        # Priority 3: Generic
        return random.choice(self.GENERAL_FOLLOWUPS)
    
    def get_guidance_prompt(
        self,
        primary_topic: Optional[str],
        distress_trend: str,
        distress_level: float
    ) -> str:
        """
        Get guidance prompt for system message to guide response generation
        
        Used to instruct LLM about conversation direction
        """
        
        if distress_trend == 'escalating':
            return (
                "The user's distress appears to be escalating. "
                "Show genuine concern. Validate their experience. "
                "Gently suggest they may need additional support. "
                "Make a specific recommendation."
            )
        
        if distress_level > 0.8:
            return (
                "The user is in significant distress right now. "
                "Prioritize safety. Validate deeply. "
                "Be clear about crisis resources. "
                "Do not minimize their experience."
            )
        
        if distress_level > 0.6 and distress_trend == 'stable':
            return (
                "The user has been dealing with high distress for a while. "
                "Acknowledge the effort they're putting in. "
                "Explore what's helped before. "
                "Gently encourage professional support if appropriate."
            )
        
        if primary_topic and primary_topic in ['anxiety', 'anxious']:
            return (
                "The user is dealing with anxiety. "
                "Normalize the experience. "
                "Offer concrete techniques they can use immediately. "
                "Explore triggers if appropriate."
            )
        
        if primary_topic and primary_topic in ['sleep', 'tired']:
            return (
                "The user has sleep issues. "
                "Ask about sleep hygiene. "
                "Explore what's happening at night. "
                "Provide evidence-based suggestions."
            )
        
        return (
            "Respond with empathy. "
            "Ask clarifying questions to understand better. "
            "Provide helpful information. "
            "Guide toward helpful next steps."
        )


# ================================================================
# TESTING & DEMO
# ================================================================

def test_contextual_followups():
    """Test the contextual followup engine"""
    
    print("\n" + "="*80)
    print("PHASE 3C: CONTEXTUAL FOLLOW-UP ENGINE - DEMO")
    print("="*80)
    
    engine = ContextualFollowupEngine()
    
    # Test Case 1: Initial anxiety conversation
    print("\n[Test 1] Initial Anxiety Conversation")
    print("─" * 80)
    followup = engine.generate_followup(
        query="I feel anxious all the time",
        conversation_count=1,
        distress_trend="stable",
        distress_level=0.45
    )
    print(f"Query: 'I feel anxious all the time'")
    print(f"Context: First message, moderate distress")
    print(f"Follow-up: {followup}")
    
    # Test Case 2: Developing conversation, escalating
    print("\n[Test 2] Escalating Pattern")
    print("─" * 80)
    followup = engine.generate_followup(
        query="It's getting worse, I can't sleep",
        conversation_count=3,
        distress_trend="escalating",
        distress_level=0.65
    )
    print(f"Query: 'It's getting worse, I can't sleep'")
    print(f"Context: 3 messages, escalating trend, high distress")
    print(f"Follow-up: {followup}")
    
    # Test Case 3: Sleep issue, early stage
    print("\n[Test 3] Sleep Issue - Early Stage")
    print("─" * 80)
    followup = engine.generate_followup(
        query="I haven't been sleeping well",
        conversation_count=1,
        distress_trend="stable",
        distress_level=0.4
    )
    print(f"Query: 'I haven't been sleeping well'")
    print(f"Context: First message, sleep issue")
    print(f"Follow-up: {followup}")
    
    # Test Case 4: Depression, chronic
    print("\n[Test 4] Chronic High Stress")
    print("─" * 80)
    followup = engine.generate_followup(
        query="I'm struggling with depression",
        conversation_count=4,
        distress_trend="stable",
        distress_level=0.7
    )
    print(f"Query: 'I'm struggling with depression'")
    print(f"Context: 4 messages, chronic high distress")
    print(f"Follow-up: {followup}")
    
    # Test Case 5: Improving pattern
    print("\n[Test 5] Improvement")
    print("─" * 80)
    followup = engine.generate_followup(
        query="Things are getting a bit better",
        conversation_count=5,
        distress_trend="improving",
        distress_level=0.35
    )
    print(f"Query: 'Things are getting a bit better'")
    print(f"Context: 5 messages, improving trend")
    print(f"Follow-up: {followup}")
    
    # Test guidance prompts
    print("\n[Test 6] Guidance Prompts for LLM")
    print("─" * 80)
    
    scenarios = [
        ("anxiety", "escalating", 0.7),
        ("depression", "stable", 0.8),
        ("sleep", "stable", 0.45),
        (None, "stable", 0.35),
    ]
    
    for topic, trend, distress in scenarios:
        guidance = engine.get_guidance_prompt(topic, trend, distress)
        print(f"\nTopic: {topic} | Trend: {trend} | Distress: {distress:.0%}")
        print(f"Guidance: {guidance}")
    
    print("\n" + "="*80)
    print("✅ CONTEXTUAL FOLLOW-UP ENGINE DEMO COMPLETE")
    print("="*80)
    print("\n🎯 Key Features:")
    print("  ✓ Topic-specific follow-ups (anxiety, sleep, depression, stress, anger)")
    print("  ✓ Stage-aware questions (initial, developing, escalating)")
    print("  ✓ Trend-based adaptation (escalating, improving, stable)")
    print("  ✓ Emergency-aware escalation")
    print("  ✓ Guidance prompts for LLM integration")
    print("\n")


if __name__ == "__main__":
    test_contextual_followups()
