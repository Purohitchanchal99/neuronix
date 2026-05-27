"""
🧠 Context-Aware Personalization Engine for NEURONIX
========================================================
Implements:
1. System Prompt Management (AI Behavior Control)
2. User Context Storage & Retrieval
3. Context Injection into API calls
4. User-type Detection (Beginner/Intermediate/Advanced)
5. Response Quality Filtering
6. Few-shot Training Examples
7. Smart Personalization
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 1️⃣ USER TYPE DETECTION
# ============================================================================

class UserType(Enum):
    """User expertise levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class UserProfileDetector:
    """Automatically detect user type from interaction patterns"""
    
    def __init__(self):
        self.questions_asked = 0
        self.technical_keywords = {
            "api", "database", "algorithm", "code", "function",
            "neural", "embedding", "vector", "model", "training",
            "schema", "query", "optimization", "performance",
            "deploy", "production", "pipeline", "architecture"
        }
    
    def detect_user_type(self, user_history: Dict) -> UserType:
        """
        Detect user type from:
        - Question complexity
        - Technical keywords used
        - Follow-up depth
        - Previous queries
        """
        
        queries = user_history.get("queries", [])
        if not queries:
            return UserType.BEGINNER
        
        # Score calculation
        score = 0
        
        for query in queries[-10:]:  # Last 10 queries
            text = query.lower()
            
            # Technical keyword count
            keywords_found = sum(1 for kw in self.technical_keywords if kw in text)
            score += keywords_found * 5
            
            # Question length (longer = more detailed)
            if len(text) > 100:
                score += 2
            if len(text) > 200:
                score += 3
            
            # Follow-up indicators
            if any(word in text for word in ["why", "how", "explain", "details"]):
                score += 1
        
        # Determine type
        if score >= 20:
            return UserType.ADVANCED
        elif score >= 8:
            return UserType.INTERMEDIATE
        else:
            return UserType.BEGINNER
    
    def get_complexity_indicators(self, user_history: Dict) -> Dict:
        """Get detailed complexity analysis"""
        queries = user_history.get("queries", [])
        avg_length = sum(len(q) for q in queries) / len(queries) if queries else 0
        
        return {
            "total_queries": len(queries),
            "avg_query_length": avg_length,
            "user_type": self.detect_user_type(user_history).value,
            "technical_depth": min(10, len(queries) if queries else 0)
        }


# ============================================================================
# 2️⃣ SYSTEM PROMPT MANAGEMENT
# ============================================================================

class SystemPromptManager:
    """Control AI behavior with context-aware system prompts"""
    
    # Base system prompts for different user types
    BASE_PROMPTS = {
        UserType.BEGINNER: """You are NEURONIX, a friendly clinical mental health assistant.
        
YOUR ROLE:
- Explain mental health concepts in SIMPLE language
- Use analogies to explain complex ideas
- Break down answers into small, easy steps
- Avoid technical jargon (explain if necessary)
- Be encouraging and supportive

TONE: 
- Friendly and approachable
- Use Hinglish (Hindi + English mix)
- Answer like a caring friend who knows medicine

ALWAYS:
- Start with what you know about the person (from context)
- Ask clarifying questions if needed
- Provide examples they can relate to
- Suggest when professional help is needed""",
        
        UserType.INTERMEDIATE: """You are NEURONIX, a clinical mental health AI assistant.

YOUR ROLE:
- Provide balanced clinical and practical information
- Reference research where relevant
- Explain mechanisms and processes
- Support informed decision-making

TONE:
- Professional but approachable
- Hinglish communication
- Evidence-based explanations

FOCUS:
- Bridge understanding of clinical concepts
- Provide context and background
- Offer different perspectives
- Include safety considerations""",
        
        UserType.ADVANCED: """You are NEURONIX, an advanced clinical mental health knowledge system.

YOUR ROLE:
- Provide comprehensive, research-backed information
- Deep dive into clinical mechanisms
- Discuss evidence-based interventions
- Engage with complex clinical scenarios

TONE:
- Clinical but accessible
- Hinglish preferred
- Intellectually rigorous

CAPABILITIES:
- Detailed diagnostic information
- Pathophysiology discussions
- Treatment options analysis
- Research citations and evidence levels""",
    }
    
    @staticmethod
    def get_system_prompt(user_type: UserType, context: Optional[str] = None) -> str:
        """Get system prompt for user type + optional extra context"""
        base = SystemPromptManager.BASE_PROMPTS[user_type]
        
        if context:
            base += f"\n\nUSER CONTEXT:\n{context}"
        
        return base
    
    @staticmethod
    def create_custom_prompt(user_type: UserType, **kwargs) -> str:
        """Create custom prompt with specific instructions"""
        base = SystemPromptManager.BASE_PROMPTS[user_type]
        custom = "\n\nCUSTOM INSTRUCTIONS:\n"
        
        if kwargs.get("no_medical_terms"):
            custom += "- Avoid medical terminology, use simple words\n"
        
        if kwargs.get("focus_on_coping"):
            custom += "- Focus on practical coping strategies\n"
        
        if kwargs.get("crisis_mode"):
            custom += "- Include crisis resources and immediate help options\n"
        
        if kwargs.get("quick_answers"):
            custom += "- Keep answers brief (2-3 sentences max)\n"
        
        return base + custom


# ============================================================================
# 3️⃣ USER CONTEXT STORAGE & RETRIEVAL
# ============================================================================

class UserContextManager:
    """Store and retrieve user context for personalization"""
    
    def __init__(self, storage_dir: str = "user_contexts"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def create_user_profile(self, user_id: str) -> Dict:
        """Create new user profile"""
        profile = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "user_type": UserType.BEGINNER.value,
            "preferences": {
                "language": "hinglish",
                "explanation_style": "beginner",
                "tone": "friendly",
                "max_response_length": "medium"
            },
            "queries": [],
            "topics_interested": [],
            "crisis_keywords_detected": False,
            "last_updated": datetime.now().isoformat()
        }
        self.save_profile(user_id, profile)
        return profile
    
    def save_profile(self, user_id: str, profile: Dict):
        """Save user profile to disk"""
        file_path = self.storage_dir / f"{user_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
    
    def load_profile(self, user_id: str) -> Optional[Dict]:
        """Load user profile from disk"""
        file_path = self.storage_dir / f"{user_id}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def update_profile(self, user_id: str, query: str, response: str, 
                      detected_crisis: bool = False):
        """Update profile after interaction"""
        profile = self.load_profile(user_id)
        if not profile:
            profile = self.create_user_profile(user_id)
        
        # Add to query history
        profile["queries"].append({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "response_length": len(response)
        })
        
        # Track topics
        topics = self._extract_topics(query)
        profile["topics_interested"].extend(topics)
        profile["topics_interested"] = list(set(profile["topics_interested"]))
        
        # Update crisis flag
        if detected_crisis:
            profile["crisis_keywords_detected"] = True
        
        profile["last_updated"] = datetime.now().isoformat()
        self.save_profile(user_id, profile)
        
        return profile
    
    @staticmethod
    def _extract_topics(query: str) -> List[str]:
        """Extract topics from query"""
        topics = []
        topic_keywords = {
            "depression": ["depression", "sad", "unhappy", "blue"],
            "anxiety": ["anxiety", "panic", "worry", "nervous"],
            "stress": ["stress", "stressed", "pressure"],
            "sleep": ["sleep", "insomnia", "nightmare", "sleepless"],
            "relationships": ["relationship", "partner", "friend", "family"],
            "work": ["work", "job", "career", "boss"],
            "medication": ["medicine", "drug", "pill", "treatment"],
            "therapy": ["therapy", "counseling", "therapist", "psychologist"]
        }
        
        query_lower = query.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in query_lower for kw in keywords):
                topics.append(topic)
        
        return topics


# ============================================================================
# 4️⃣ FEW-SHOT TRAINING EXAMPLES
# ============================================================================

class FewShotExamples:
    """Provide examples to guide AI response quality"""
    
    @staticmethod
    def get_examples(user_type: UserType) -> str:
        """Get few-shot examples for user type"""
        
        examples = {
            UserType.BEGINNER: """
EXAMPLE 1:
Q: What is depression?
A: Depression is like your mood taking a long vacation and forgetting to come back! 😢
- You feel sad most of the time
- Things you enjoyed become boring
- You have less energy than usual
- Sleep gets affected

Think of it like a phone with a low battery - everything feels slow.

It's very treatable! A doctor can help. Talk to someone you trust first.

EXAMPLE 2:
Q: Should I take medication?
A: This is a great question! Only a doctor can decide this for you.
- Medicines can help, but so can therapy or lifestyle changes
- It depends on YOUR situation, not someone else's
- Talk to a medical professional (doctor/psychiatrist)
- There's no shame in any choice

IMPORTANT: I'm here to inform you, not replace medical advice!
""",
            
            UserType.INTERMEDIATE: """
EXAMPLE 1:
Q: How does cognitive behavioral therapy work?
A: CBT operates on the principle that thoughts → feelings → behaviors are interconnected.

MECHANISM:
- Identifies negative thought patterns
- Examines evidence for/against these thoughts
- Develops alternative thinking strategies
- Changes behavioral responses

EFFICACY:
- Research-backed for depression, anxiety, PTSD
- 50-60% remission rates in clinical trials
- Typically 12-20 sessions for effectiveness

APPLICATION:
- Individual therapy most common
- Group interventions available
- Self-guided CBT online tools show promise

EVIDENCE LEVEL: Strong (Grade A)

EXAMPLE 2:
Q: What about SSRIs vs SNRIs?
A: Different mechanisms, similar efficacy:

SSRI (Selective Serotonin Reuptake Inhibitors):
- Block serotonin reuptake only
- First-line for depression/anxiety
- Side effects: Sexual dysfunction, weight gain

SNRI (Serotonin-Norepinephrine Reuptake Inhibitors):
- Affect serotonin AND norepinephrine
- Better for some anxiety disorders
- Different side effect profile

CHOICE: Depends on individual response, medical history
""",
            
            UserType.ADVANCED: """
EXAMPLE 1:
Q: Discuss the neurobiological basis of major depressive disorder.
A: MDD involves dysregulation of multiple neurotransmitter systems:

MONOAMINE HYPOTHESIS (Classical):
- Serotonin (5-HT): Platelet aggregation ↓, CSF 5-HIAA ↓
- Norepinephrine (NE): MHPG levels abnormal
- Dopamine (DA): Anhedonia pathway involvement
- Limitations: Doesn't explain all symptoms or treatment lag

GLUTAMATERGIC SYSTEM:
- Excitatory/Inhibitory imbalance
- NMDA receptor hyperactivity
- Ketamine's rapid effects support this model
- Emerging therapeutic target

INFLAMMATORY PATHWAY:
- TNF-α, IL-6, CRP elevations in subset
- Psychoneuroimmunological mechanisms
- 30% "inflammatory depression" phenotype

NEUROPLASTICITY:
- HPA axis dysregulation: Elevated baseline cortisol
- Brain-derived neurotrophic factor (BDNF) ↓
- Hippocampal volume reduction (stress-mediated)
- SSRI-induced neurogenesis (weeks 4-8)

GENETICS & ENVIRONMENT:
- Polygenic risk scores (PRSs) emerging
- EpigeneticModification of stress-responsive genes
- 5-HTTLPR polymorphism interaction with stress

TREATMENT IMPLICATIONS:
- Polypharmacy rationale (target multiple systems)
- Personalized medicine approaches warranted
- Biomarker-guided treatment development ongoing
"""
        }
        
        return examples.get(user_type, examples[UserType.BEGINNER])


# ============================================================================
# 5️⃣ RESPONSE QUALITY VALIDATOR
# ============================================================================

class ResponseQualityValidator:
    """Ensure response quality and relevance"""
    
    QUALITY_CHECKS = {
        "empty_response": lambda r: len(r.strip()) == 0,
        "random_characters": lambda r: not any(c.isalpha() for c in r),
        "too_short": lambda r: len(r.strip()) < 20,
        "irrelevant": lambda r: not any(word in r.lower() for word in [
            "depression", "anxiety", "mental", "health", "therapy", "treatment",
            "sleep", "stress", "relationship", "emotion", "support", "help",
            "symptom", "feel", "care", "doctor", "medicine"
        ]),
    }
    
    @staticmethod
    def validate(response: str) -> Dict:
        """Validate response quality"""
        issues = []
        
        for check_name, check_func in ResponseQualityValidator.QUALITY_CHECKS.items():
            try:
                if check_func(response):
                    issues.append(check_name)
            except:
                pass
        
        is_valid = len(issues) == 0
        
        return {
            "is_valid": is_valid,
            "issues": issues,
            "quality_score": max(0, 100 - (len(issues) * 25)),
            "requires_regeneration": len(issues) > 0
        }
    
    @staticmethod
    def get_feedback(validation_result: Dict) -> str:
        """Get human-readable feedback"""
        if validation_result["is_valid"]:
            return "✅ Response quality: Excellent"
        else:
            return f"⚠️ Issues detected: {', '.join(validation_result['issues'])}"


# ============================================================================
# 6️⃣ CONTEXT INJECTOR (FOR API CALLS)
# ============================================================================

class ContextInjector:
    """Inject user context into API calls"""
    
    def __init__(self, profile_manager: UserContextManager, 
                 detector: UserProfileDetector,
                 prompt_manager: SystemPromptManager):
        self.profile_manager = profile_manager
        self.detector = detector
        self.prompt_manager = prompt_manager
    
    def create_injection_payload(self, user_id: str, query: str) -> Dict:
        """Create enhanced payload with context"""
        
        # Load user profile
        profile = self.profile_manager.load_profile(user_id)
        if not profile:
            profile = self.profile_manager.create_user_profile(user_id)
        
        # Detect user type
        user_type = UserType(self.detector.detect_user_type(profile))
        profile["user_type"] = user_type.value
        
        # Build context string
        context_parts = []
        
        if profile.get("topics_interested"):
            context_parts.append(f"User interests: {', '.join(profile['topics_interested'][:5])}")
        
        if len(profile.get("queries", [])) > 0:
            context_parts.append(f"User experience level: {user_type.value}")
        
        context_string = "\n".join(context_parts)
        
        # Get system prompt
        system_prompt = self.prompt_manager.get_system_prompt(user_type, context_string)
        
        # Get few-shot examples
        few_shots = FewShotExamples.get_examples(user_type)
        
        # Build injection payload
        return {
            "user_id": user_id,
            "user_type": user_type.value,
            "query": query,
            "system_prompt": system_prompt,
            "few_shot_examples": few_shots,
            "user_context": {
                "query_count": len(profile.get("queries", [])),
                "topics_interested": profile.get("topics_interested", []),
                "preferences": profile.get("preferences", {}),
            },
            "quality_validator": True,  # Enable validation on response
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# 7️⃣ COMPLETE PERSONALIZATION ENGINE
# ============================================================================

class NeuronixPersonalizationEngine:
    """Main personalization engine combining all components"""
    
    def __init__(self, storage_dir: str = "user_contexts"):
        self.profile_manager = UserContextManager(storage_dir)
        self.detector = UserProfileDetector()
        self.prompt_manager = SystemPromptManager()
        self.injector = ContextInjector(
            self.profile_manager,
            self.detector,
            self.prompt_manager
        )
        logger.info("✅ Personalization Engine Initialized")
    
    def enhance_query(self, user_id: str, query: str) -> Dict:
        """
        Enhanced query with full context:
        - System prompt
        - User context
        - Few-shot examples
        - Quality validation enabled
        """
        return self.injector.create_injection_payload(user_id, query)
    
    def process_response(self, user_id: str, query: str, response: str) -> Dict:
        """Process and validate response, update user profile"""
        
        # Check response quality
        validation = ResponseQualityValidator.validate(response)
        
        # Check for crisis indicators
        crisis_keywords = ["suicide", "self-harm", "kill myself", "harm myself"]
        detected_crisis = any(kw in response.lower() or kw in query.lower() 
                            for kw in crisis_keywords)
        
        # Update profile
        profile = self.profile_manager.update_profile(
            user_id, query, response, detected_crisis
        )
        
        return {
            "user_id": user_id,
            "validation": validation,
            "crisis_detected": detected_crisis,
            "profile_updated": True,
            "user_type": profile["user_type"],
            "quality_feedback": ResponseQualityValidator.get_feedback(validation)
        }
    
    def get_user_analytics(self, user_id: str) -> Dict:
        """Get user analytics and insights"""
        profile = self.profile_manager.load_profile(user_id)
        if not profile:
            return {"error": "User not found"}
        
        user_type = self.detector.detect_user_type(profile)
        
        return {
            "user_id": user_id,
            "total_queries": len(profile.get("queries", [])),
            "user_type": user_type.value,
            "complexity_indicators": self.detector.get_complexity_indicators(profile),
            "interests": profile.get("topics_interested", []),
            "preferences": profile.get("preferences", {}),
            "crisis_risk": profile.get("crisis_keywords_detected", False),
            "member_since": profile.get("created_at"),
            "last_active": profile.get("last_updated")
        }


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Initialize engine
    engine = NeuronixPersonalizationEngine()
    
    # Example: User 1 - Beginner
    user_id_1 = "user_001_beginner"
    query_1 = "What is anxiety?"
    
    payload_1 = engine.enhance_query(user_id_1, query_1)
    print("\n📋 BEGINNER USER PAYLOAD:")
    print(f"User Type: {payload_1['user_type']}")
    print(f"System Prompt (first 200 chars):\n{payload_1['system_prompt'][:200]}...")
    
    # Example: User 2 - Advanced
    user_id_2 = "user_002_advanced"
    query_2 = "Explain the neurobiological mechanisms of depression and current treatment approaches"
    
    # First query (beginner level)
    engine.enhance_query(user_id_2, "What helps with stress?")
    
    # Second query (more advanced)
    payload_2 = engine.enhance_query(user_id_2, query_2)
    print("\n📋 ADVANCED USER PAYLOAD:")
    print(f"User Type: {payload_2['user_type']}")
    print(f"Few-shot examples (first 300 chars):\n{payload_2['few_shot_examples'][:300]}...")
    
    # Simulate response
    sample_response = "Depression involves complex neurobiological mechanisms..."
    result = engine.process_response(user_id_2, query_2, sample_response)
    print("\n✅ RESPONSE PROCESSING:")
    print(f"Quality: {result['quality_feedback']}")
    print(f"Crisis Detected: {result['crisis_detected']}")
    
    # Get analytics
    analytics = engine.get_user_analytics(user_id_2)
    print("\n📊 USER ANALYTICS:")
    print(f"Total Queries: {analytics['total_queries']}")
    print(f"User Type: {analytics['user_type']}")
    print(f"Interests: {analytics['interests']}")
