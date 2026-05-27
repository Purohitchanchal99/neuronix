"""
🎯 Intent Router
================
Routes queries to correct handler: Mental Health vs Learning

CRITICAL: Must classify BEFORE retrieval/recommendations
"""

import logging
from typing import Dict, Literal
from enum import Enum

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """Query intent types"""
    MENTAL_HEALTH = "mental_health"      # Emotional/crisis/wellbeing
    LEARNING = "learning"                # Educational/skill-building
    CRISIS = "crisis"                    # Immediate danger
    GENERAL = "general"                  # Neutral/unclear


class IntentRouter:
    """Classify query intent and route to appropriate handler"""
    
    # Mental health keywords (emotional/wellbeing)
    MENTAL_HEALTH_KEYWORDS = {
        # Emotional states
        "anxiety", "anxious", "nervous", "worried", "panic",
        "depressed", "depression", "sad", "sadness", "down",
        "lonely", "loneliness", "isolated", "alone",
        "stressed", "stress", "overwhelmed", "overwhelm",
        "angry", "anger", "furious", "irritated",
        "confused", "confused", "lost", "uncertain",
        "worthless", "loser", "failure", "failed",
        "guilty", "guilt", "ashamed", "ashame",
        "scared", "fear", "afraid", "frightened",
        "tired", "exhausted", "burned out", "burnout",
        "hopeless", "hope", "hopeful",
        
        # Symptoms/conditions
        "insomnia", "sleep", "sleeping", "sleep hygiene",
        "headache", "pain", "ache", "sick", "illness",
        "eating", "food", "appetite", "weight",
        "concentration", "focus", "attention",
        
        # Wellbeing
        "self-care", "selfcare", "mindfulness", "meditation",
        "breathing", "exercise", "workout", "yoga",
        "therapy", "therapist", "counseling", "counselor",
        "mental health", "wellness", "wellbeing",
        "relationship", "partner", "spouse", "family",
        "work", "job", "career", "boss",
        "school", "college", "exam", "test",
        
        # Suicidal/crisis
        "suicide", "suicidal", "kill", "kill myself", "die",
        "self-harm", "harm", "hurt myself", "cut",
        "overdose", "pills", "drug",
        "end it", "can't take it", "give up",
        "not feeling good", "not feel good", "not okay",
        "help", "in crisis", "emergency",
        "suicidal thoughts", "suicidal ideation", "suicidal thinking",
        "want to die", "wanna die", "i want to die",
        "have suicidal", "having suicidal",
    }
    
    # Learning keywords (educational/skill-building)
    LEARNING_KEYWORDS = {
        # Programming
        "python", "loop", "function", "variable", "if statement",
        "javascript", "java", "c++", "sql", "html", "css",
        "code", "coding", "program", "programming",
        "algorithm", "data structure", "recursion",
        "debug", "error", "bug", "test",
        "if", "else", "for", "while", "array", "list",
        
        # General learning
        "learn", "teach", "lesson", "tutorial", "course",
        "study", "practice", "exercise", "problem",
        "math", "science", "history", "english",
        "read", "write", "vocabulary", "grammar",
        "how to", "explain", "what is", "define",
    }
    
    def __init__(self):
        """Initialize router"""
        self.mental_health_keywords = self.MENTAL_HEALTH_KEYWORDS
        self.learning_keywords = self.LEARNING_KEYWORDS
    
    def classify_intent(self, query: str) -> Dict:
        """
        Classify query intent with confidence scores
        
        Args:
            query: User query
            
        Returns:
            {
                "intent": QueryIntent,
                "confidence": 0.0-1.0,
                "keywords_found": List[str],
                "reason": str
            }
        """
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # ⭐ CHECK FOR CRISIS FIRST (highest priority - 95% confidence)
        # Look for crisis keywords in the full query OR as patterns with high specificity
        crisis_keywords = [
            "suicide", "suicidal", "kill myself", "kill myself", "self-harm",
            "end it all", "want to die", "wanna die", "i want to die",
            "going to kill", "gonna kill", "will kill", "to kill myself",
            "overdose", "jump off", "cut myself", "hurt myself",
            "can't take it", "can't go on", "too much",
        ]
        
        # Also check for specific crisis phrases
        crisis_present = False
        matched_crisis_keywords = []
        
        for kw in crisis_keywords:
            if kw in query_lower:
                crisis_present = True
                matched_crisis_keywords.append(kw)
        
        # Pattern matching for "suicidal thoughts", "having suicidal ideation" etc.
        if "suicidal" in query_lower and ("thought" in query_lower or "ideation" in query_lower or "having" in query_lower):
            crisis_present = True
            matched_crisis_keywords.append("suicidal thoughts/ideation")
        
        if crisis_present:
            return {
                "intent": QueryIntent.CRISIS,
                "confidence": 0.95,
                "keywords_found": matched_crisis_keywords,
                "reason": "CRISIS: Immediate danger keywords detected"
            }
        
        # Count keyword matches for both categories
        mental_health_matches = []
        for keyword in self.mental_health_keywords:
            if keyword in query_lower:
                mental_health_matches.append(keyword)
        
        learning_matches = []
        for keyword in self.learning_keywords:
            if keyword in query_lower:
                learning_matches.append(keyword)
        
        # Determine primary intent
        if len(mental_health_matches) > len(learning_matches):
            confidence = min(0.95, 0.5 + (len(mental_health_matches) * 0.2))
            return {
                "intent": QueryIntent.MENTAL_HEALTH,
                "confidence": confidence,
                "keywords_found": mental_health_matches,
                "reason": f"Mental health keywords: {', '.join(mental_health_matches[:3])}"
            }
        
        elif len(learning_matches) > len(mental_health_matches):
            confidence = min(0.95, 0.5 + (len(learning_matches) * 0.2))
            return {
                "intent": QueryIntent.LEARNING,
                "confidence": confidence,
                "keywords_found": learning_matches,
                "reason": f"Learning keywords: {', '.join(learning_matches[:3])}"
            }
        
        # If equal or no matches, return GENERAL (default to mental health for safety)
        else:
            return {
                "intent": QueryIntent.GENERAL,
                "confidence": 0.3,
                "keywords_found": [],
                "reason": "No strong intent detected - defaulting to conversational"
            }
    
    def should_use_mental_health_handler(self, query: str) -> bool:
        """Quick check: route to mental health handler?"""
        classification = self.classify_intent(query)
        intent = classification["intent"]
        confidence = classification["confidence"]
        
        # Route to mental health for:
        # - Crisis (100% sure)
        # - Mental health with >60% confidence
        # - General/unclear (default to mental health for safety)
        
        if intent == QueryIntent.CRISIS:
            return True
        
        if intent == QueryIntent.MENTAL_HEALTH and confidence > 0.6:
            return True
        
        if intent == QueryIntent.GENERAL:
            # Default to mental health for safety
            return True
        
        return False
    
    def get_vector_store_filter(self, query: str) -> Dict:
        """
        Get filter for vector store retrieval
        (only retrieve from appropriate domain)
        """
        classification = self.classify_intent(query)
        intent = classification["intent"]
        
        if intent == QueryIntent.MENTAL_HEALTH or intent == QueryIntent.CRISIS:
            return {
                "domain": "mental_health",
                "categories": ["anxiety", "depression", "wellness", "crisis", "therapy"]
            }
        
        elif intent == QueryIntent.LEARNING:
            return {
                "domain": "learning",
                "categories": ["programming", "education", "tutorial", "coding"]
            }
        
        else:
            # General - retrieve from both but weight mental health
            return {
                "domain": "mixed",
                "categories": ["*"],
                "weight_mental_health": True
            }


# ================================================================
# EXAMPLE USAGE
# ================================================================

if __name__ == "__main__":
    router = IntentRouter()
    
    test_queries = [
        # Mental health queries
        "I'm feeling really anxious",
        "I have depression",
        "not feeling good",
        "I'm a loser",
        "I want to die",  # Crisis
        
        # Learning queries
        "teach me python loops",
        "what is a variable?",
        "how to write functions",
        
        # Mixed/unclear
        "Hi there",
        "how are you?",
    ]
    
    print("\n" + "=" * 70)
    print("🎯 INTENT ROUTER TEST")
    print("=" * 70)
    
    for query in test_queries:
        result = router.classify_intent(query)
        handler = "MENTAL HEALTH" if router.should_use_mental_health_handler(query) else "LEARNING"
        
        print(f"\nQuery: '{query}'")
        print(f"Intent: {result['intent'].value}")
        print(f"Confidence: {result['confidence']:.0%}")
        print(f"Keywords: {', '.join(result['keywords_found'][:3]) if result['keywords_found'] else 'None'}")
        print(f"Handler: ➜ {handler}")
        print(f"Reason: {result['reason']}")
    
    print("\n" + "=" * 70)
    print("✅ Intent routing test complete!")
