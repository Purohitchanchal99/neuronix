"""
🧠 NEURONIX CONTEXT-AWARE AI SYSTEM
==================================
7-core components for intelligent, personalized, and safe AI responses

Components:
1. System Prompt Manager - Master behavior control
2. Context Utilization - Active context usage
3. Context Injection Flow - Combining system + user + query
4. User-Type Detection - Expertise level detection
5. Response Quality Filter - Output validation
6. Few-Shot Training - Example-based learning
7. Personalization Layer - User preferences & history
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 1. SYSTEM PROMPT MANAGER - BRAIN OF AI
# ============================================================================

class SystemPromptManager:
    """
    Master system prompt that controls AI behavior
    
    Rules included:
    - Empathetic tone (especially for mental health)
    - Safety disclaimers
    - Personalization awareness
    - Context-aware responses
    """
    
    BASE_SYSTEM_PROMPT = """
You are NEURONIX, an empathetic and clinically-informed AI assistant specialized in mental health.

CORE PRINCIPLES:
1. EMPATHY: Always respond with empathy and respect for user's mental health journey
2. SAFETY: Include appropriate disclaimers for serious conditions
3. EVIDENCE-BASED: Reference clinical guidelines (DSM-5, ICD-11) when relevant
4. PERSONALIZATION: Adapt complexity level to user expertise
5. DISCLAIMERS: For serious concerns, suggest professional help
6. CLARITY: Avoid medical jargon unless user is advanced
7. CONTEXT-AWARE: Reference user preferences and history

SAFETY PROTOCOL:
- If user mentions suicidal ideation → Immediate disclaimer + crisis resources
- If condition seems serious → Recommend professional evaluation
- If uncertain about diagnosis → Say "consult a professional"
- Never prescribe medications
- Never replace real therapy

LANGUAGE ADAPTATION:
- Beginner: Simple language, examples, step-by-step
- Intermediate: Balanced detail, some technical terms
- Advanced: Concise, technical depth, research-backed
"""

    CLINICAL_RULES = """
CLINICAL MENTAL HEALTH CONTEXT:
- DSM-5 and ICD-11 are reference frameworks
- Symptoms vary significantly between individuals
- Treatment should be personalized
- Therapy + medication often work best together
- Mental health is NOT a moral failing
- Recovery is possible with proper support
"""

    def __init__(self):
        self.base_prompt = self.BASE_SYSTEM_PROMPT
        self.clinical_rules = self.CLINICAL_RULES
        logger.info("✅ System Prompt Manager initialized")
    
    def get_system_prompt(self, 
                         user_context: Dict = None,
                         emergency_mode: bool = False) -> str:
        """
        Get system prompt adjusted for user context
        
        Args:
            user_context: User's stored preferences/history
            emergency_mode: Stricter disclaimers if True
        
        Returns:
            Injected system prompt
        """
        
        prompt = self.base_prompt
        
        # Add clinical rules
        prompt += "\n" + self.clinical_rules
        
        # Add emergency protocol if needed
        if emergency_mode:
            prompt += """
EMERGENCY MODE - STRICT DISCLAIMERS:
- This is AI-generated information only
- NOT a substitute for professional mental health care
- For crisis: Contact emergency services immediately
- User's safety is paramount
"""
        
        # Add user-specific instructions
        if user_context:
            if user_context.get("language_preference") == "hinglish":
                prompt += "\n- Use Hinglish (Hindi-English) when appropriate"
            
            if user_context.get("sensitivity_level") == "high":
                prompt += "\n- Extra care with sensitive mental health topics"
                prompt += "\n- Never minimize user experiences"
        
        return prompt
    
    def add_custom_rule(self, rule: str) -> None:
        """Add custom behavioral rule"""
        self.base_prompt += f"\n- {rule}"
        logger.info(f"✅ Rule added: {rule}")


# ============================================================================
# 2. CONTEXT UTILIZATION ENGINE
# ============================================================================

class UserExpertiseLevel(Enum):
    """User expertise levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class UserContext:
    """User's stored context for personalization"""
    user_id: str
    expertise_level: UserExpertiseLevel
    language_preference: str = "english"  # english, hindi, hinglish
    mental_health_background: bool = False
    sensitivity_level: str = "normal"  # low, normal, high
    has_clinical_training: bool = False
    interests: List[str] = None
    past_interactions: List[Dict] = None
    interaction_history_count: int = 0
    
    def __post_init__(self):
        if self.interests is None:
            self.interests = []
        if self.past_interactions is None:
            self.past_interactions = []


class ContextUtilizationEngine:
    """
    Actively uses stored context to personalize responses
    
    Logic:
    - Beginner → Simple, step-by-step answers
    - Intermediate → Balanced detail
    - Advanced → Technical, concise, research-backed
    """
    
    # Response style templates
    RESPONSE_STYLES = {
        UserExpertiseLevel.BEGINNER: {
            "complexity": "simple",
            "use_examples": True,
            "include_definitions": True,
            "max_technical_terms": 2,
            "tone": "friendly and supportive",
            "structure": "step-by-step explanation with examples"
        },
        UserExpertiseLevel.INTERMEDIATE: {
            "complexity": "moderate",
            "use_examples": True,
            "include_definitions": False,
            "max_technical_terms": 5,
            "tone": "professional and informative",
            "structure": "balanced explanation with context"
        },
        UserExpertiseLevel.ADVANCED: {
            "complexity": "technical",
            "use_examples": False,
            "include_definitions": False,
            "max_technical_terms": 10,
            "tone": "concise and evidence-based",
            "structure": "direct answer with research references"
        }
    }
    
    def __init__(self):
        self.user_contexts: Dict[str, UserContext] = {}
        logger.info("✅ Context Utilization Engine initialized")
    
    def register_user(self, user_context: UserContext) -> None:
        """Register or update user context"""
        self.user_contexts[user_context.user_id] = user_context
        logger.info(f"✅ User registered: {user_context.user_id} ({user_context.expertise_level.value})")
    
    def get_response_style_prompt(self, user_id: str) -> str:
        """Get response style instructions for user"""
        
        user = self.user_contexts.get(user_id)
        if not user:
            logger.warning(f"⚠️ User {user_id} not found, using beginner style")
            user = UserContext(user_id=user_id, expertise_level=UserExpertiseLevel.BEGINNER)
        
        style = self.RESPONSE_STYLES[user.expertise_level]
        
        prompt = f"""
RESPOND WITH {user.expertise_level.value.upper()} LEVEL:
- Complexity: {style['complexity']}
- Use examples: {style['use_examples']}
- Include definitions: {style['include_definitions']}
- Max technical terms: {style['max_technical_terms']}
- Tone: {style['tone']}
- Structure: {style['structure']}
"""
        return prompt
    
    def get_user_interests_context(self, user_id: str) -> str:
        """Build context based on user interests"""
        
        user = self.user_contexts.get(user_id)
        if not user or not user.interests:
            return ""
        
        return f"\nUser's interests: {', '.join(user.interests)}"
    
    def get_history_context(self, user_id: str, max_items: int = 3) -> str:
        """Build context from recent interactions"""
        
        user = self.user_contexts.get(user_id)
        if not user or not user.past_interactions:
            return ""
        
        # Get last N interactions
        recent = user.past_interactions[-max_items:]
        
        history_text = "\nRecent interaction context:"
        for i, interaction in enumerate(recent, 1):
            topic = interaction.get("topic", "Unknown")
            date = interaction.get("date", "")
            history_text += f"\n{i}. {topic} ({date})"
        
        return history_text


# ============================================================================
# 3. CONTEXT INJECTION FLOW
# ============================================================================

@dataclass
class ContextualizedPrompt:
    """
    Complete injected prompt combining:
    1. System prompt (behavior rules)
    2. User context (stored data)
    3. Current question
    """
    system_prompt: str
    response_style: str
    user_interests: str
    user_history: str
    current_question: str
    
    def get_full_prompt(self) -> str:
        """Assemble complete prompt for API"""
        full = self.system_prompt
        full += self.response_style
        full += self.user_interests
        full += self.user_history
        full += f"\nUser Question: {self.current_question}"
        return full


class ContextInjectionFlow:
    """
    Orchestrates context injection:
    System Prompt + User Context + Current Question → Full Prompt
    """
    
    def __init__(self, 
                 system_manager: SystemPromptManager,
                 context_engine: ContextUtilizationEngine):
        self.system_manager = system_manager
        self.context_engine = context_engine
        logger.info("✅ Context Injection Flow initialized")
    
    def build_contextualized_prompt(self,
                                   user_id: str,
                                   question: str,
                                   emergency: bool = False) -> ContextualizedPrompt:
        """
        Build complete contextualized prompt
        
        Flow:
        1. Get system prompt (with emergency rules if needed)
        2. Get response style for user level
        3. Get user interests context
        4. Get interaction history context
        5. Combine with current question
        """
        
        user_context = self.context_engine.user_contexts.get(user_id)
        
        # Step 1: System prompt
        system_prompt = self.system_manager.get_system_prompt(
            user_context=asdict(user_context) if user_context else None,
            emergency_mode=emergency
        )
        
        # Step 2: Response style
        response_style = self.context_engine.get_response_style_prompt(user_id)
        
        # Step 3: User interests
        user_interests = self.context_engine.get_user_interests_context(user_id)
        
        # Step 4: Interaction history
        user_history = self.context_engine.get_history_context(user_id)
        
        # Step 5: Combine
        contextualized_prompt = ContextualizedPrompt(
            system_prompt=system_prompt,
            response_style=response_style,
            user_interests=user_interests,
            user_history=user_history,
            current_question=question
        )
        
        logger.info(f"✅ Contextualized prompt built for user: {user_id}")
        
        return contextualized_prompt


# ============================================================================
# 4. USER-TYPE DETECTION
# ============================================================================

class UserTypeDetector:
    """
    Detects user expertise level based on question complexity
    
    Logic:
    - Simple questions → Beginner
    - Medium complexity → Intermediate
    - Technical/advanced → Advanced
    """
    
    BEGINNER_KEYWORDS = [
        "what is", "explain", "how do i", "i don't understand",
        "can you explain", "what does", "simple", "basics", "intro",
        "beginner", "confused", "help me", "don't know"
    ]
    
    INTERMEDIATE_KEYWORDS = [
        "how does", "why does", "what are the", "effectiveness of",
        "comparison", "when should", "difference between", "techniques",
        "methods", "approach", "research shows"
    ]
    
    ADVANCED_KEYWORDS = [
        "neurotransmitter", "neural pathway", "cerebral", "cortex",
        "pharmacokinetics", "dsm-5 criteria", "icd-11", "etiology",
        "neurobiological", "pathophysiology", "meta-analysis",
        "randomized controlled trial", "regression analysis"
    ]
    
    def __init__(self):
        self.detection_history: List[Dict] = []
        logger.info("✅ User Type Detector initialized")
    
    def detect_expertise_level(self, question: str) -> UserExpertiseLevel:
        """
        Detect user expertise from question
        
        Returns:
            UserExpertiseLevel based on question complexity
        """
        
        question_lower = question.lower()
        
        # Count keyword matches
        advanced_count = sum(1 for kw in self.ADVANCED_KEYWORDS if kw in question_lower)
        intermediate_count = sum(1 for kw in self.INTERMEDIATE_KEYWORDS if kw in question_lower)
        beginner_count = sum(1 for kw in self.BEGINNER_KEYWORDS if kw in question_lower)
        
        # Determine level
        if advanced_count >= intermediate_count and advanced_count > beginner_count:
            level = UserExpertiseLevel.ADVANCED
        elif intermediate_count > beginner_count:
            level = UserExpertiseLevel.INTERMEDIATE
        else:
            level = UserExpertiseLevel.BEGINNER
        
        logger.info(f"🔍 Detected expertise level: {level.value} (adv:{advanced_count}, int:{intermediate_count}, beg:{beginner_count})")
        
        return level
    
    def estimate_confidence(self, question: str) -> float:
        """Estimate confidence of detection (0-1)"""
        
        question_lower = question.lower()
        word_count = len(question.split())
        
        # Simple heuristic: more technical terms = higher confidence
        technical_count = (
            sum(1 for kw in self.ADVANCED_KEYWORDS if kw in question_lower) +
            sum(1 for kw in self.INTERMEDIATE_KEYWORDS if kw in question_lower)
        )
        
        confidence = min(technical_count / max(word_count / 2, 1), 1.0)
        return confidence


# ============================================================================
# 5. RESPONSE QUALITY FILTER
# ============================================================================

class ResponseQualityFilter:
    """
    Validates AI response quality
    
    Checks:
    ❌ Empty responses
    ❌ Random characters
    ❌ Irrelevant answers
    ❌ Unsafe/harmful content
    ✅ All passed → Send
    ❌ Failed → Regenerate signal
    """
    
    class QualityMetrics:
        """Quality assessment metrics"""
        MIN_LENGTH = 50  # Minimum response length
        MAX_LENGTH = 2000  # Maximum response length
        QUALITY_SCORE_THRESHOLD = 0.7  # 70% quality minimum
    
    def __init__(self):
        self.UNSAFE_KEYWORDS = [
            "suicide", "overdose", "self-harm", "kill myself",
            "dangerous", "illegal", "drug deal",
            # Still includes context indicators but for flagging only
        ]
        logger.info("✅ Response Quality Filter initialized")
    
    def assess_quality(self, response: str) -> Dict:
        """
        Comprehensive quality assessment
        
        Returns:
            {
                "passed": bool,
                "score": float (0-1),
                "issues": List[str],
                "recommendation": str
            }
        """
        
        issues = []
        quality_score = 1.0
        
        # Check 1: Empty or too short
        if not response or len(response.strip()) < self.QualityMetrics.MIN_LENGTH:
            issues.append("⚠️ Response too short")
            quality_score -= 0.4
        
        # Check 2: Too long
        if len(response) > self.QualityMetrics.MAX_LENGTH:
            issues.append("⚠️ Response too long")
            quality_score -= 0.2
        
        # Check 3: Random characters/gibberish
        if self._has_gibberish(response):
            issues.append("⚠️ Contains gibberish/random characters")
            quality_score -= 0.5
        
        # Check 4: Relevance (basic heuristic)
        if not self._appears_relevant(response):
            issues.append("⚠️ Response may be irrelevant")
            quality_score -= 0.3
        
        # Check 5: Safety flag (for emergencies)
        unsafe_indicators = [kw for kw in self.UNSAFE_KEYWORDS if kw.lower() in response.lower()]
        if unsafe_indicators:
            issues.append(f"🚨 Safety trigger detected: {unsafe_indicators}")
            quality_score -= 0.2  # Still passable but flagged
        
        # Check 6: Coherence
        if not self._is_coherent(response):
            issues.append("⚠️ Response lacks coherence")
            quality_score -= 0.3
        
        quality_score = max(quality_score, 0.0)
        passed = quality_score >= self.QualityMetrics.QUALITY_SCORE_THRESHOLD
        
        recommendation = (
            "✅ PASS" if passed else "❌ REGENERATE"
        )
        
        if unsafe_indicators:
            recommendation = "🚨 NEEDS REVIEW"
        
        logger.info(f"Quality Assessment: Score={quality_score:.2f}, {recommendation}")
        
        return {
            "passed": passed,
            "score": quality_score,
            "issues": issues,
            "recommendation": recommendation,
            "unsafe_indicators": unsafe_indicators if unsafe_indicators else None
        }
    
    @staticmethod
    def _has_gibberish(text: str) -> bool:
        """Check for random characters/gibberish"""
        # Simple heuristic: high ratio of special characters
        special_chars = sum(1 for c in text if not c.isalnum() and c.isascii() and c not in ' .,!?-:')
        ratio = special_chars / len(text) if len(text) > 0 else 0
        return ratio > 0.3
    
    @staticmethod
    def _appears_relevant(text: str) -> bool:
        """Check if response appears to address mental health"""
        # Simple heuristic: word length average
        words = text.split()
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        return avg_word_length > 3  # Average word > 3 chars
    
    @staticmethod
    def _is_coherent(text: str) -> bool:
        """Check for basic coherence"""
        # Simple heuristic: has meaningful sentences
        sentences = text.split('. ')
        return len(sentences) >= 2


# ============================================================================
# 6. FEW-SHOT TRAINING EXAMPLES
# ============================================================================

@dataclass
class FewShotExample:
    """Single few-shot training example"""
    user_question: str
    context: str  # User expertise level, etc.
    expected_response: str
    response_style: str
    clinical_accuracy: bool = True


class FewShotTrainingLibrary:
    """
    Training examples to guide AI behavior
    Prevents hallucinations, unsafe responses, irrelevance
    """
    
    def __init__(self):
        self.examples: List[FewShotExample] = []
        self._build_default_examples()
        logger.info(f"✅ Few-Shot Training Library initialized with {len(self.examples)} examples")
    
    def _build_default_examples(self):
        """Build default training examples"""
        
        # Example 1: Honest uncertainty
        self.examples.append(FewShotExample(
            user_question="Who am I? What's my purpose?",
            context="Beginner, existential question",
            expected_response="I'm an AI and don't have personal information about you. I can help you explore questions about mental wellness, identity, and purpose through conversation. What aspects of yourself are you curious about?",
            response_style="Honest, acknowledges limitation, redirects helpfully",
            clinical_accuracy=True
        ))
        
        # Example 2: Simple explanation
        self.examples.append(FewShotExample(
            user_question="What is anxiety?",
            context="Beginner",
            expected_response="Anxiety is your body's response to stress. It's like an alarm system that activates when you perceive danger or uncertainty. Some anxiety is normal, but when it becomes excessive and prevents daily activities, professional help can be beneficial.",
            response_style="Simple language, uses analogy, acknowledges when help is needed",
            clinical_accuracy=True
        ))
        
        # Example 3: Technical response
        self.examples.append(FewShotExample(
            user_question="Explain the neurobiological basis of anxiety disorders",
            context="Advanced, researcher/clinician",
            expected_response="Anxiety disorders involve dysregulation of the amygdala-prefrontal cortex circuit. Hyperactivity in the amygdala (threat detection) combined with reduced ventromedial prefrontal cortex activity (fear inhibition) characterizes conditions like GAD and PTSD. Neurochemical involvement includes GABA, glutamate, and serotonin dysregulation.",
            response_style="Technical, evidence-based, concise",
            clinical_accuracy=True
        ))
        
        # Example 4: Safety protocol
        self.examples.append(FewShotExample(
            user_question="I'm thinking about ending my life",
            context="Crisis situation",
            expected_response="🚨 I'm concerned about your wellbeing. This is important and requires immediate professional support. Please contact emergency services (911 in US) or a crisis helpline. National Suicide Prevention Lifeline: 988 (call or text). Your life has value and there is help available.",
            response_style="Empathetic, action-oriented, immediate resources",
            clinical_accuracy=True
        ))
        
        # Example 5: Resource suggestion
        self.examples.append(FewShotExample(
            user_question="How do I find a therapist?",
            context="Intermediate",
            expected_response="Good step! Here are evidence-based approaches:\n1. Ask your primary care doctor for referrals\n2. Check insurance provider list\n3. Try directories like Psychology Today or TherapyDen\n4. Ensure therapist is licensed (LCSW, psychologist, etc.)\n5. Many offer free consultations to find the right fit.",
            response_style="Practical guidance, step-by-step, emphasizes clinical credentials",
            clinical_accuracy=True
        ))
    
    def get_relevant_examples(self, question: str, expertise_level: UserExpertiseLevel, max_examples: int = 2) -> List[FewShotExample]:
        """Get most relevant examples for prompt injection"""
        
        # Simple matching: return examples at similar expertise level
        relevant = []
        
        for ex in self.examples:
            # Match complexity
            if expertise_level.value in ex.context.lower():
                relevant.append(ex)
        
        return relevant[:max_examples]
    
    def get_examples_prompt(self, question: str, expertise_level: UserExpertiseLevel) -> str:
        """Build prompt section with few-shot examples"""
        
        examples = self.get_relevant_examples(question, expertise_level)
        
        if not examples:
            return ""
        
        prompt = "\nREFERENCE EXAMPLES (similar context):"
        
        for i, ex in enumerate(examples, 1):
            prompt += f"\n\nExample {i}:"
            prompt += f"\nUser: {ex.user_question}"
            prompt += f"\nContext: {ex.context}"
            prompt += f"\nResponse: {ex.expected_response}"
            prompt += f"\nStyle: {ex.response_style}"
        
        return prompt


# ============================================================================
# 7. PERSONALIZATION LAYER
# ============================================================================

class PersonalizationLayer:
    """
    Uses user history and preferences to personalize responses
    
    Tracks:
    - Past interactions
    - Preferences (language, tone, detail level)
    - Topics of interest
    - Response effectiveness (implicit)
    """
    
    def __init__(self):
        self.user_profiles: Dict[str, UserContext] = {}
        self.interaction_logs: Dict[str, List[Dict]] = {}
        logger.info("✅ Personalization Layer initialized")
    
    def record_interaction(self,
                          user_id: str,
                          question: str,
                          response: str,
                          expertise_detected: UserExpertiseLevel,
                          quality_score: float) -> None:
        """
        Record user interaction for personalization
        """
        
        if user_id not in self.interaction_logs:
            self.interaction_logs[user_id] = []
        
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "question": question[:100],  # Truncate for privacy
            "response_length": len(response),
            "expertise_detected": expertise_detected.value,
            "quality_score": quality_score,
            "topic": self._extract_topic(question)
        }
        
        self.interaction_logs[user_id].append(interaction)
        logger.info(f"✅ Interaction recorded for {user_id}")
    
    def update_user_expertise(self,
                             user_id: str,
                             detected_level: UserExpertiseLevel) -> None:
        """
        Update user expertise based on detection
        (Can be overridden by explicit user setting)
        """
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserContext(
                user_id=user_id,
                expertise_level=detected_level
            )
        
        # Update if new detection seems consistent
        current = self.user_profiles[user_id].expertise_level
        
        if current != detected_level:
            logger.info(f"🔄 Updating user expertise: {current.value} → {detected_level.value}")
            self.user_profiles[user_id].expertise_level = detected_level
    
    def get_personalization_prompt(self, user_id: str) -> str:
        """Generate personalization-based prompt"""
        
        if user_id not in self.interaction_logs:
            return ""
        
        logs = self.interaction_logs[user_id]
        
        # Extract patterns
        topics = [log.get("topic") for log in logs[-5:]]  # Last 5 interactions
        topics = [t for t in topics if t]  # Remove None
        
        prompt = ""
        
        if topics:
            unique_topics = list(set(topics))
            prompt += f"\nUser's recent interests: {', '.join(unique_topics)}"
        
        if len(logs) > 10:
            avg_response_length = sum(log.get("response_length", 0) for log in logs[-5:]) / min(5, len(logs))
            if avg_response_length < 300:
                prompt += "\n- User prefers concise responses"
            elif avg_response_length > 800:
                prompt += "\n- User appreciates detailed responses"
        
        return prompt
    
    @staticmethod
    def _extract_topic(question: str) -> str:
        """Extract topic from question"""
        
        topics = {
            "anxiety": ["anxiety", "panic", "worry", "nervous"],
            "depression": ["depression", "sad", "hopeless", "empty"],
            "sleep": ["sleep", "insomnia", "dream", "rest"],
            "stress": ["stress", "overwhelm", "pressure"],
            "relationship": ["relationship", "partner", "family", "love"],
            "work": ["work", "job", "career", "boss"],
            "medication": ["medication", "pill", "drug", "prescription"],
            "therapy": ["therapy", "therapist", "counseling", "cbt"],
        }
        
        q_lower = question.lower()
        
        for topic, keywords in topics.items():
            if any(kw in q_lower for kw in keywords):
                return topic
        
        return "general"


# ============================================================================
# MASTER ORCHESTRATOR
# ============================================================================

class ContextAwareAISystem:
    """
    Master system combining all 7 components
    
    Workflow:
    User Input → Detect Type → Build Context → Inject → Filter → Respond
    """
    
    def __init__(self):
        # Initialize all 7 components
        self.system_manager = SystemPromptManager()
        self.context_engine = ContextUtilizationEngine()
        self.context_injection = ContextInjectionFlow(self.system_manager, self.context_engine)
        self.user_detector = UserTypeDetector()
        self.quality_filter = ResponseQualityFilter()
        self.few_shot_library = FewShotTrainingLibrary()
        self.personalization = PersonalizationLayer()
        
        logger.info("🚀 Context-Aware AI System fully initialized (7 components)")
    
    def register_user(self, 
                     user_id: str,
                     expertise_level: UserExpertiseLevel = UserExpertiseLevel.BEGINNER,
                     language_preference: str = "english",
                     interests: List[str] = None) -> UserContext:
        """Register a new user"""
        
        user_context = UserContext(
            user_id=user_id,
            expertise_level=expertise_level,
            language_preference=language_preference,
            interests=interests or []
        )
        
        self.context_engine.register_user(user_context)
        self.personalization.user_profiles[user_id] = user_context
        
        logger.info(f"✅ User registered: {user_id}")
        
        return user_context
    
    def process_query(self,
                     user_id: str,
                     question: str,
                     emergency: bool = False) -> Dict:
        """
        Complete pipeline: Detect → Build Context → Inject → Generate → Filter
        
        Returns:
            {
                "user_id": str,
                "question": str,
                "detected_expertise": str,
                "full_prompt": str,
                "quality_assessment": Dict,
                "metadata": Dict
            }
        """
        
        logger.info(f"\n📋 Processing query from {user_id}")
        
        # Step 1: Detect user expertise
        detected_expertise = self.user_detector.detect_expertise_level(question)
        confidence = self.user_detector.estimate_confidence(question)
        
        logger.info(f"✅ Expertise detected: {detected_expertise.value} (confidence: {confidence:.2f})")
        
        # Step 2: Update user profile
        self.personalization.update_user_expertise(user_id, detected_expertise)
        
        # Step 3: Build contextualized prompt
        contextualized_prompt = self.context_injection.build_contextualized_prompt(
            user_id=user_id,
            question=question,
            emergency=emergency
        )
        
        full_prompt = contextualized_prompt.get_full_prompt()
        
        logger.info(f"✅ Full prompt built ({len(full_prompt)} characters)")
        
        # Step 4: Add few-shot examples
        few_shot_prompt = self.few_shot_library.get_examples_prompt(question, detected_expertise)
        if few_shot_prompt:
            full_prompt += few_shot_prompt
            logger.info("✅ Few-shot examples added")
        
        # Step 5: Add personalization
        personalization_prompt = self.personalization.get_personalization_prompt(user_id)
        if personalization_prompt:
            full_prompt += personalization_prompt
            logger.info("✅ Personalization injected")
        
        # Note: Step 6 (Generate) would call actual LLM (Gemini, etc)
        # For now we simulate it
        simulated_response = self._simulate_llm_response(question, detected_expertise)
        
        # Step 7: Quality check
        quality_assessment = self.quality_filter.assess_quality(simulated_response)
        
        logger.info(f"✅ Quality check: {quality_assessment['recommendation']}")
        
        # Log interaction
        self.personalization.record_interaction(
            user_id=user_id,
            question=question,
            response=simulated_response,
            expertise_detected=detected_expertise,
            quality_score=quality_assessment['score']
        )
        
        return {
            "user_id": user_id,
            "question": question,
            "detected_expertise": detected_expertise.value,
            "detection_confidence": confidence,
            "full_prompt": full_prompt,
            "simulated_response": simulated_response,
            "quality_assessment": quality_assessment,
            "metadata": {
                "emergency_mode": emergency,
                "personality_tags": [],
                "timestamp": datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def _simulate_llm_response(question: str, expertise_level: UserExpertiseLevel) -> str:
        """Simulate LLM response (would call Gemini/GPT in production)"""
        
        if expertise_level == UserExpertiseLevel.BEGINNER:
            return f"I understand you're asking about '{question}'. Let me break this down simply for you. [Beginner-level explanation would go here with examples and definitions.]"
        
        elif expertise_level == UserExpertiseLevel.INTERMEDIATE:
            return f"Regarding your question about '{question}': [Intermediate-level technical explanation with context and research background would go here.]"
        
        else:  # ADVANCED
            return f"Your inquiry into '{question}' relates to several evidence-based mechanisms. [Advanced technical response with research citations and neurobiological framework would go here.]"
    
    def get_system_status(self) -> Dict:
        """Get complete system status"""
        
        return {
            "components": {
                "system_prompt_manager": "✅ Active",
                "context_utilization": f"✅ {len(self.context_engine.user_contexts)} users registered",
                "context_injection": "✅ Active",
                "user_type_detector": "✅ Active",
                "quality_filter": "✅ Active",
                "few_shot_library": f"✅ {len(self.few_shot_library.examples)} examples",
                "personalization_layer": f"✅ {len(self.personalization.user_profiles)} profiles"
            },
            "total_interactions": sum(len(logs) for logs in self.personalization.interaction_logs.values()),
            "registered_users": len(self.context_engine.user_contexts)
        }
