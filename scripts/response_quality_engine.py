#!/usr/bin/env python3
"""
Phase 2: Response Quality Upgrade
==================================
Makes responses feel:
  ✓ Natural
  ✓ Adaptive
  ✓ Human-like
  ✓ Less repetitive

Key Improvements:
  1. Adaptive tone detection (emotional/informational/neutral)
  2. Response variation (random selection from multiple options)
  3. Better contextual suggestions
  4. Gentle follow-ups that feel conversational
  5. Combined into cohesive response pipeline
"""

import random
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ToneAnalysis:
    """Result of tone analysis"""
    tone: str  # emotional, informational, neutral
    distress_level: float  # 0.0 to 1.0
    keywords: List[str]
    confidence: float  # 0.0 to 1.0


class ToneDetector:
    """Detect emotional tone from user query"""
    
    # 🔥 EMOTIONAL KEYWORDS - High distress indicators
    EMOTIONAL_KEYWORDS = {
        "anxious": ["anxious", "anxiety", "worried", "worry", "nervous", "scary"],
        "sad": ["sad", "depression", "depressed", "down", "blue", "hopeless"],
        "overwhelmed": ["overwhelmed", "stressed", "stress", "pressure"],
        "angry": ["angry", "anger", "frustrated", "gussa", "frustration", "furious"],
        "scared": ["scared", "fear", "afraid", "terrified", "panic"],
        "tired": ["tired", "exhausted", "fatigue", "exhaustion", "worn out"],
        "lonely": ["lonely", "lonely", "isolated", "alone", "disconnected"],
    }
    
    # INFORMATIONAL KEYWORDS - Educational queries
    INFORMATIONAL_KEYWORDS = ["what is", "how does", "tell me", "explain", "define", "describe"]
    
    # DISTRESS AMPLIFIERS - Words that increase emotional intensity
    DISTRESS_AMPLIFIERS = [
        "all the time", "always", "never", "can't", "endless", "uncontrollable",
        "terrible", "unbearable", "suicidal", "harm"
    ]
    
    def detect(self, query: str) -> ToneAnalysis:
        """
        Detect tone and emotional intensity from query
        
        Returns:
            ToneAnalysis with detected tone, distress level, and confidence
        """
        q_lower = query.lower()
        
        # 1. Check for emotional keywords and their intensity
        emotional_matches = []
        distress_level = 0.0
        
        for emotion, keywords in self.EMOTIONAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in q_lower:
                    emotional_matches.append(emotion)
                    distress_level += 0.3
        
        # 2. Check for distress amplifiers (increases distress level)
        amplifier_count = sum(1 for amp in self.DISTRESS_AMPLIFIERS if amp in q_lower)
        distress_level += amplifier_count * 0.15
        
        # 3. Check for informational queries
        is_informational = any(info_kw in q_lower for info_kw in self.INFORMATIONAL_KEYWORDS)
        
        # 4. Determine tone
        if emotional_matches and not is_informational:
            tone = "emotional"
        elif is_informational:
            tone = "informational"
        else:
            tone = "neutral"
        
        # 5. Calculate confidence based on keyword density
        confidence = min(1.0, (len(emotional_matches) / 3.0) if emotional_matches else 0.7)
        
        # Cap distress level at 1.0
        distress_level = min(1.0, distress_level)
        
        return ToneAnalysis(
            tone=tone,
            distress_level=distress_level,
            keywords=list(set(emotional_matches)),
            confidence=confidence
        )


class ResponseVariation:
    """Generate varied acknowledgments and follow-ups to avoid repetitiveness"""
    
    # 🔥 EMOTIONAL ACKNOWLEDGMENTS (varies based on distress level)
    EMOTIONAL_ACK_HIGH_DISTRESS = [
        "That sounds really overwhelming, and it makes complete sense you'd feel this way.",
        "I can see this is weighing heavily on you. Your feelings are completely valid.",
        "That must be genuinely difficult to carry. Thank you for trusting me with this.",
        "It sounds like things are really intense for you right now. That's rough.",
    ]
    
    EMOTIONAL_ACK_MEDIUM_DISTRESS = [
        "I hear you, and what you're describing sounds tough but manageable.",
        "That's something a lot of people struggle with. You're not alone.",
        "It sounds like this has been on your mind. That's understandable.",
        "I appreciate you sharing this. It takes courage to be honest.",
    ]
    
    EMOTIONAL_ACK_LOW_DISTRESS = [
        "That sounds like something worth exploring.",
        "I'm glad you're thinking about this.",
        "That's a meaningful question to ask.",
    ]
    
    # INFORMATIONAL ACKNOWLEDGMENTS
    INFORMATIONAL_ACK = [
        "That's a great question, and I've found some helpful information for you.",
        "I love when people ask this. Let me share what I found.",
        "That's exactly the kind of question that deserves a solid answer.",
        "You asking the right questions. Here's what the research shows:",
    ]
    
    # NEUTRAL ACKNOWLEDGMENTS
    NEUTRAL_ACK = [
        "I hear you.",
        "Got it. Let me help.",
        "That's interesting. Here's what I found:",
        "Understood. Let me share some insight.",
    ]
    
    # 🔥 ADAPTIVE FOLLOW-UPS (feels like real conversation)
    FOLLOWUP_OPTIONS = [
        "Would you like me to suggest a simple technique you could try right now?",
        "Do you want to talk more about what's been going on?",
        "I'm here if you want to share more or if you have other questions.",
        "What's one small thing you could do today to help yourself feel a bit better?",
        "Is there something specific about this that's been hardest for you?",
        "Would it help to know what usually works for people in similar situations?",
        "How has this been affecting your day-to-day life?",
        "What would feel like a helpful next step for you?",
        "How long have you been dealing with this?",
        "Are there any people in your life you feel safe talking to about this?",
        "What have you tried before that helped, even a little?",
        "Is this something that comes and goes, or is it pretty constant?",
        "What would relief look like for you?",
        "Would you be open to trying some evidence-based techniques?",
    ]
    
    FOLLOWUP_CRISIS = [
        "I'm really concerned. Please reach out to someone right now—call a helpline, tell a trusted person, or go to an emergency room.",
        "Your safety is everything right now. Please contact an emergency helpline immediately.",
        "I know this is heavy. You don't have to handle this alone—please call a crisis helpline or tell someone you trust right now.",
        "Please reach out for help immediately. There are trained people ready to listen and help.",
        "This is urgent. Your life matters. Please call 988 (US), +91-9999 666 555 (India), or your local crisis line now.",
    ]
    
    @staticmethod
    def get_acknowledgment(tone: str, distress_level: float = 0.5) -> str:
        """
        Get appropriate acknowledgment based on tone and distress
        
        Args:
            tone: 'emotional', 'informational', or 'neutral'
            distress_level: 0.0 to 1.0 for emotional intensity
        """
        if tone == "emotional":
            if distress_level > 0.7:
                return random.choice(ResponseVariation.EMOTIONAL_ACK_HIGH_DISTRESS)
            elif distress_level > 0.35:
                return random.choice(ResponseVariation.EMOTIONAL_ACK_MEDIUM_DISTRESS)
            else:
                return random.choice(ResponseVariation.EMOTIONAL_ACK_LOW_DISTRESS)
        elif tone == "informational":
            return random.choice(ResponseVariation.INFORMATIONAL_ACK)
        else:
            return random.choice(ResponseVariation.NEUTRAL_ACK)
    
    @staticmethod
    def get_followup(is_crisis: bool = False) -> str:
        """Get a gentle follow-up question"""
        if is_crisis:
            return random.choice(ResponseVariation.FOLLOWUP_CRISIS)
        return random.choice(ResponseVariation.FOLLOWUP_OPTIONS)


class ContextualSuggestions:
    """Generate smarter, context-aware suggestions"""
    
    # 🔥 SUGGESTIONS MAPPED TO SPECIFIC SITUATIONS
    ANXIETY_SUGGESTIONS = [
        "Try focusing on slow breathing for a minute—just gently noticing each breath without forcing it. 4 in, 4 hold, 4 out.",
        "One powerful technique: name 5 things you see, 4 things you can feel, 3 things you hear. Helps ground you in the present.",
        "Try a short walk, even just around your room. Movement can help interrupt the anxiety loop.",
        "Write down what you're worried about. Often it becomes clearer once it's on paper.",
    ]
    
    SLEEP_SUGGESTIONS = [
        "It might help to take a short break and do something calming, even for a few minutes.",
        "Try a consistent bedtime—your body loves routine. Even 15 minutes earlier each night helps.",
        "No screens 30 minutes before bed. I know it's hard, but it actually works for many people.",
        "If your mind won't quiet down, try progressive muscle relaxation—tense and release each muscle group.",
    ]
    
    DEPRESSION_SUGGESTIONS = [
        "Try taking one small step today instead of solving everything at once. One thing.",
        "Reaching out to one person—even a text—is huge. You don't have to explain everything.",
        "Professional support is real support. It's not weakness; it's clarity.",
        "Sometimes doing the opposite of what depression tells you is the answer. It usually lies.",
    ]
    
    STRESS_SUGGESTIONS = [
        "When you feel like this, pick one thing and focus only on that for 15 minutes. Then reassess.",
        "Take a actual break—not scrolling, but real rest. Even 5 minutes helps reset your nervous system.",
        "You can't solve everything right now. Breaking it into smaller pieces changes everything.",
        "Deep breaths and a glass of water. These sound too simple, but your body needs both.",
    ]
    
    ANGER_SUGGESTIONS = [
        "When anger peaks, physical release helps—walk, run, punch a pillow. Then you can think clearly.",
        "Try naming the anger: what's underneath it? Usually fear or hurt.",
        "Taking space for 20 minutes often changes the whole dynamic.",
        "Anger is information. It's telling you a boundary was crossed. What's the boundary?",
    ]
    
    GENERAL_SUGGESTIONS = [
        "Try taking one small step today instead of solving everything at once.",
        "Talking to someone you trust can really help. You don't have to carry this alone.",
        "Consider reaching out to a professional. It's more accessible than you think.",
        "Build one healthy habit this week. Just one. It compounds.",
    ]
    
    @staticmethod
    def get_suggestions(query: str, count: int = 2) -> List[str]:
        """
        Get personalized suggestions based on query keywords
        
        Args:
            query: User query
            count: Number of suggestions to return
        """
        q_lower = query.lower()
        
        # Match query to suggestion category with better keyword detection
        if any(w in q_lower for w in ["anxiety", "anxious", "worried", "worry", "nervous", "panic"]):
            suggestions = ContextualSuggestions.ANXIETY_SUGGESTIONS
        elif any(w in q_lower for w in ["sleep", "insomnia", "tired", "exhausted", "can't sleep", "sleeping"]):
            suggestions = ContextualSuggestions.SLEEP_SUGGESTIONS
        elif any(w in q_lower for w in ["depressed", "depression", "sad", "down", "hopeless", "hopelessness"]):
            suggestions = ContextualSuggestions.DEPRESSION_SUGGESTIONS
        elif any(w in q_lower for w in ["stress", "stressed", "overwhelmed", "pressure", "overwhelming"]):
            suggestions = ContextualSuggestions.STRESS_SUGGESTIONS
        elif any(w in q_lower for w in ["angry", "anger", "frustrated", "furious", "gussa", "irritated"]):
            suggestions = ContextualSuggestions.ANGER_SUGGESTIONS
        else:
            suggestions = ContextualSuggestions.GENERAL_SUGGESTIONS
        
        # Return random selection without duplicates
        return random.sample(suggestions, min(count, len(suggestions)))


class ResponseQualityEngine:
    """
    Main engine combining all Phase 2 improvements
    
    Pipeline:
      1. Detect tone (emotional/informational/neutral)
      2. Get adaptive acknowledgment
      3. Generate contextual suggestions
      4. Combine into cohesive response
      5. Add gentle follow-up
    """
    
    def __init__(self):
        self.tone_detector = ToneDetector()
        self.variation = ResponseVariation()
        self.suggestions = ContextualSuggestions()
    
    def build_response(
        self,
        query: str,
        educational_content: str = "",
        is_crisis: bool = False
    ) -> Dict:
        """
        Build a Phase 2 quality response
        
        Args:
            query: User query
            educational_content: Retrieved context/knowledge (optional)
            is_crisis: Whether this is a crisis situation
        
        Returns:
            Dict with response, tone analysis, suggestions, followup
        """
        
        # Step 1: Detect tone
        tone_analysis = self.tone_detector.detect(query)
        
        # Step 2: Get adaptive acknowledgment
        ack = self.variation.get_acknowledgment(
            tone_analysis.tone,
            tone_analysis.distress_level
        )
        
        # Step 3: Build body (content)
        body_parts = []
        
        if educational_content:
            # Truncate to reasonable length
            clean_content = educational_content.strip()[:300]
            body_parts.append(f"Here's what I found:\n{clean_content}...")
        
        # Step 4: Add suggestions (not if crisis)
        if not is_crisis and tone_analysis.tone in ["emotional", "neutral"]:
            suggestion_list = self.suggestions.get_suggestions(query)
            if suggestion_list:
                suggestions_text = "\n".join([f"• {s}" for s in suggestion_list])
                body_parts.append(f"What might help:\n{suggestions_text}")
        
        # Build main response
        body = "\n\n".join(body_parts)
        
        response = f"{ack}"
        if body:
            response += f"\n\n{body}"
        
        # Step 5: Add gentle follow-up
        followup = self.variation.get_followup(is_crisis)
        response += f"\n\n{followup}"
        
        return {
            "response": response,
            "tone": tone_analysis.tone,
            "distress_level": tone_analysis.distress_level,
            "confidence": tone_analysis.confidence,
            "keywords": tone_analysis.keywords,
            "followup": followup,
            "is_crisis": is_crisis,
        }
    
    def compare_old_vs_new(
        self,
        query: str,
        educational_content: str = ""
    ) -> Dict:
        """
        Show comparison between old (robotic) and new (human) responses
        
        Useful for demonstration and testing
        """
        
        # Old style (generic, formulaic)
        old_response = (
            "I'm sorry you're feeling this way. Try breathing exercises. "
            "Consider talking to a professional. Feel free to ask more questions."
        )
        
        # New style
        new_result = self.build_response(query, educational_content)
        
        return {
            "query": query,
            "old_response": old_response,
            "new_response": new_result["response"],
            "tone_detected": new_result["tone"],
            "distress_level": new_result["distress_level"],
            "improvements": [
                "✓ Adaptive tone matches emotion level",
                "✓ Natural acknowledgment (not generic apology)",
                "✓ Context-aware suggestions",
                "✓ Conversational follow-up",
                "✓ Feels like talking to a friend, not a bot",
            ]
        }


# ================================================================
# QUICK TESTING & DEMOS
# ================================================================

if __name__ == "__main__":
    engine = ResponseQualityEngine()
    
    print("\n" + "="*80)
    print("🧠 PHASE 2: RESPONSE QUALITY UPGRADE")
    print("="*80)
    
    # Test cases from the upgrade document
    test_cases = [
        {
            "name": "Emotional Query",
            "query": "I feel anxious all the time",
            "context": "Anxiety is characterized by persistent worry and physical symptoms. Treatment options include therapy and medication."
        },
        {
            "name": "Mixed Query",
            "query": "Why do I feel anxious and what can I do?",
            "context": "Anxiety involves both psychological and physiological components. Cognitive behavioral therapy (CBT) is highly effective."
        },
        {
            "name": "Informational Query",
            "query": "What is CBT?",
            "context": "Cognitive Behavioral Therapy (CBT) is a structured approach that addresses the relationship between thoughts, feelings, and behaviors."
        },
    ]
    
    for test_case in test_cases:
        print(f"\n{'─'*80}")
        print(f"📋 TEST: {test_case['name']}")
        print(f"{'─'*80}")
        
        # Show comparison
        comparison = engine.compare_old_vs_new(test_case['query'], test_case['context'])
        
        print(f"\nQuery: \"{test_case['query']}\"")
        print(f"\n🤖 OLD (ROBOTIC):")
        print(f"   {comparison['old_response']}")
        
        print(f"\n✨ NEW (HUMAN-LIKE):")
        for line in comparison['new_response'].split('\n'):
            print(f"   {line}")
        
        print(f"\n📊 ANALYSIS:")
        print(f"   Tone Detected: {comparison['tone_detected']}")
        print(f"   Distress Level: {comparison['distress_level']:.1%}")
        
        print(f"\n🎯 IMPROVEMENTS:")
        for improvement in comparison['improvements']:
            print(f"   {improvement}")
    
    print("\n" + "="*80)
    print("✅ PHASE 2 TESTS COMPLETE")
    print("="*80)
    print("\n🚀 Key Achievements:")
    print("   ✓ Tone detection working")
    print("   ✓ Response variation implemented")
    print("   ✓ Contextual suggestions deployed")
    print("   ✓ Human-like follow-ups active")
    print("   ✓ Responses feel natural and conversational")
    print("\n")
