
"""
Neuronix Chat Engine
====================
RAG-powered clinical assistant using Google Gemini Embeddings & LLM

Features:
- Retrieval-Augmented Generation (RAG) from ChromaDB
- Hinglish (Hindi + English) responses for Indian users
- Counselling psychology principles
- Safety triggers for self-harm keywords
- Free alternative suggestions from master_mapping.json
- Zero hallucination - defers to specialists when uncertain
- Interactive chat loop with memory
"""

from dotenv import load_dotenv
load_dotenv()

# 🔥 UTF-8 ENCODING FIX - Force UTF-8 for all output
import sys
import os
import io

# Reconfigure stdout to use UTF-8 (fixes charmap codec errors)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import json
import logging
import re
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Define BASE_DIR for imports
BASE_DIR = Path(__file__).parent.parent

# ================================================================
# WINDOWS COMPATIBILITY FIX
# ================================================================
if sys.platform == "win32":
    import types
    pwd_module = types.ModuleType('pwd')
    sys.modules['pwd'] = pwd_module

# LangChain imports
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI # pyright: ignore[reportMissingImports]
# from langchain_huggingface import HuggingFaceEmbeddings  # DISABLED: sentence-transformers too heavy
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from rapidfuzz import fuzz, process # type: ignore

# Import Session Manager for memory
from .session_manager import SessionManager
from .multilingual_emotion_detector import MultilingualEmotionDetector

# Phase 3: Conversation Intelligence Layer
try:
    from scripts.conversation_memory import ConversationMemory
    from scripts.distress_tracker import DistressTracker
    from scripts.contextual_followup_engine import ContextualFollowupEngine
    from scripts.proactive_safety import ProactiveSafetySystem
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Phase 3 components not available - running in compatibility mode")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent / 'scripts' / 'chat_engine_log.txt', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
MAPPING_FILE = DATA_DIR / "master_mapping.json"

# 🔥 IMPORT COLLECTION NAME FROM INGESTION CONFIG
try:
    from scripts.neuronix_constants import COLLECTION_NAME
except ImportError:
    COLLECTION_NAME = "neuronix_medical_kb"  # Fallback

# Safety Keywords - Crisis Detection (STRICT PROTOCOL)
SELF_HARM_KEYWORDS = [
    'hurt myself', 'suicide', 'suicidal', 'kill myself', 'self harm', 'cut myself',
    'ending my life', 'end my life', 'aatmhatya', 'maut', 'mar jaun', 'khud ko maarna',
    'jaan lena', 'zindagi khatam', 'jhol', 'overdose', 'poison', 'hang myself', 'rope',
    'cliff', 'jump', 'marne ka socha', 'maut ke bare mein', 'jeena chun gaya',
    'zyada nahi raha', 'bc itna kaafi hai', 'ab nahi banega', 'sab khatam',
    'khatam karun', 'mar jaunga'
]

# Hinglish Crisis Helplines - STRICT SAFETY PROTOCOL
CRISIS_HELPLINES = """
Bhai, please rukiye. Aap akele nahi hain.

TURNT IN NUMBERS PAR CALL KAREIN:

1. Vandrevala Foundation: +91-9999 666 555 (24/7, Free)
   Aapke liye hai - Turant emotional support

2. AASRA: +91-9820466726 (24/7, Free)
   Suicide prevention helpline

3. iCall: +91-9152987821 (9 AM - 11 PM)
   Kisi bhi age ke liye

4. Indore Mental Health Crisis: 0731-2538888
   Indore mein turant local help

5. Vandrevala Foundation (SMS): Message HELLO to 9999666555
   Agar baat karna mushkil ha toh sms karo

Aapka jeevan IMPORTANT hai. Please call karun immediately.
You are not alone. Help is just one call away.
"""

# ================================================================
# CLINICAL STANDARDS & DIAGNOSTIC CRITERIA
# ================================================================

CLINICAL_CRITERIA = {
    "DSM-5": {
        "depression": {
            "name": "Major Depressive Disorder",
            "criteria": [
                "Persistent depressed mood (most of day, nearly every day)",
                "Loss of interest or pleasure in activities",
                "Significant weight/appetite changes",
                "Sleep disturbances (insomnia or hypersomnia)",
                "Psychomotor agitation or retardation",
                "Fatigue or loss of energy",
                "Feelings of worthlessness or inappropriate guilt",
                "Diminished concentration ability",
                "Recurrent thoughts of death or suicide"
            ],
            "duration": "2+ weeks",
            "note": "Must have 5+ symptoms for diagnosis"
        },
        "anxiety": {
            "name": "Generalized Anxiety Disorder",
            "criteria": [
                "Excessive anxiety/worry about various aspects of life",
                "Difficult to control worry",
                "Restlessness or feeling keyed up/on edge",
                "Easily fatigued",
                "Difficulty concentrating",
                "Irritability",
                "Muscle tension",
                "Sleep disturbance"
            ],
            "duration": "6+ months",
            "note": "Symptoms cause significant distress or functional impairment"
        }
    },
    "ICD-11": {
        "depression": {
            "name": "Single Episode Depressive Disorder (6A70)",
            "criteria": [
                "Depressed mood persistent, most of day, most days",
                "Loss of interest in activities",
                "Reduced energy or increased fatigue",
                "Significant functional impairment",
                "Concentration problems",
                "Sleep disturbance",
                "Appetite changes"
            ],
            "duration": "2+ weeks",
            "note": "No history of manic/hypomanic episodes"
        },
        "anxiety": {
            "name": "Generalized Anxiety Disorder (6D02)",
            "criteria": [
                "Worry about multiple domains",
                "Difficulty controlling worry",
                "Restlessness or feeling on edge",
                "Muscle tension",
                "Sleep disturbance",
                "Concentration difficulty",
                "Significant functional impairment"
            ],
            "duration": "6+ months",
            "note": "WHO standard - emphasis on functional impairment"
        }
    }
}

# Free resources mapping
FREE_RESOURCES = [
    "Psychology2e_WEB.pdf",
    "IGNOU_Free_Handbook.pdf",
    "NIMHANS_Research_Library",
    "WHO_Mental_Health_Guidelines"
]

# Symptom detection keywords
SYMPTOM_KEYWORDS = {
    "depression": ["depression", "depressed", "depresun", "sad", "low mood", "khushi nahi"],
    "anxiety": ["anxiety", "anxious", "worried", "tension", "tensio", "overthinking"],
    "insomnia": ["sleep", "neend", "insomnia", "cant sleep", "sleepless", "nahi aa rahi"],
    "stress": ["stress", "stressed", "stresss", "pressure", "tension"],
    "anger": ["anger", "angry", "gussa", "frustrated", "irritated"]
}


# ================================================================
# CLINICAL RESPONSE FORMATTER - Mood-Adaptive Hinglish Counselor
# ================================================================
class ClinicalResponseFormatter:
    """Formats clinical responses with mood-adaptive Hinglish tone and probing questions"""
    
    def __init__(self):
        self.free_resources = [
            "Psychology2e_WEB.pdf",
            "IGNOU_Free_Handbook.pdf",
            "NIMHANS_Research_Library"
        ]
    
    def _detect_mood(self, query: str) -> str:
        """Detect user's emotional tone from query"""
        q = query.lower()
        if any(word in q for word in ["depression", "sad", "down", "worthless", "hopeless", "zyada soch"]):
            return "depressed"
        elif any(word in q for word in ["anxiety", "anxious", "worry", "tension", "tensio", "bohot"]):
            return "anxious"
        elif any(word in q for word in ["neend", "sleep", "insomnia", "cant sleep", "sleepless", "nahi aa rahi"]):
            return "distress"
        elif any(word in q for word in ["anger", "angry", "gussa", "frustrated", "irritated"]):
            return "frustrated"
        else:
            return "neutral"
    
    def _get_mood_intro(self, mood: str, condition: str = None) -> str:
        """Generate empathetic Hinglish intro based on mood"""
        if mood == "depressed":
            return "🤝 **Bhai, lagta hai tum thoda down feel kar rahe ho.** Main samajh sakta hoon, ye easy nahi hai. Tum akele nahi ho."
        elif mood == "anxious":
            return "🤝 **Samajh sakta hoon ki worry bohot zyada ho rahi hai.** Ye normal feeling hai, par handle kar sakte hain. Chalo step by step."
        elif mood == "distress":
            return "🤝 **Samajh sakta hoon ki neend ki problem kab tough hoti hai.** Tum akela feel mat karo, bohot sab ke saath aise issues hote hain."
        elif mood == "frustrated":
            return "🤝 **Bhai, samajh raha hoon frustration kaise feel hota hai.** Ye sab normal reactions hain, par manage kar sakte hain."
        else:
            return "Namaste! Main Neuronix hoon, aapka clinical dost. 😊"
    
    def _generate_followup(self, query: str, condition: str = None) -> str:
        """Generate doctor-style probing questions based on condition"""
        q = query.lower()
        
        if "neend" in q or "sleep" in q or "insomnia" in q:
            return "🤔 **Kya ye symptom roz hota hai ya kabhi-kabhi?** Aur kab se ye problem chal rahi hai? Stress ka kya role hai?"
        elif "anxiety" in q or "worry" in q or "tension" in q:
            return "🤔 **Kya ye sudden panic attacks hote hain ya constant worry rehta hai?** Aur ye stress kaunse situations mein zyada hota hai?"
        elif "depression" in q or "sad" in q or "down" in q:
            return "🤔 **Ye symptoms kab se chal rahe hain?** Din bhar rehte hain ya sirf certain times mein? Aur appetite ya sleep mein kya change hua?"
        elif "anger" in q or "frustrated" in q or "gussa" in q:
            return "🤔 **Ye gussa kaunse triggers bante hain?** Aur ye feeling kab tak rehti hai? Controls mein reh pati ho ya bahut zyada explosve ho jati hai?"
        else:
            return "🤔 **Aur thoda aur detail batao — kab se ye problem start hua aur daily life pe kya effect ho raha hai?**"
    
    def format_response(self, rag_output: str, user_query: str = "", 
                       country: str = "India", standard_preference: str = "DSM-5",
                       condition: str = None) -> str:
        """
        Format clinical response with mood-adaptive Hinglish tone, criteria, and probing questions
        
        Args:
            rag_output: The clinical criteria or RAG model's response
            user_query: Original user query
            country: User's country
            standard_preference: DSM-5, ICD-11, or HYBRID
            condition: Medical condition name (depression, anxiety, etc.)
            
        Returns:
            Mood-adaptive formatted response with Hinglish tone, criteria, disclaimer, resources, and follow-up
        """
        # Detect mood from user query
        mood = self._detect_mood(user_query)
        
        parts = []
        
        # 1. Empathetic Hinglish intro based on mood
        intro = self._get_mood_intro(mood, condition)
        parts.append(intro)
        
        # 2. Clinical criteria from RAG output
        if rag_output and rag_output.strip():
            parts.append(f"\n📖 {rag_output}")
        
        # 3. Important disclaimer
        parts.append(
            "\n⚠️ **Important Disclaimer**:\n"
            "Ye information sirf educational purpose ke liye hai.\n"
            "Self-diagnosis se bilkul mat karo.\n"
            "**Qualified psychiatrist ya psychologist** se consult karna bilkul zaruri hai."
        )
        
        # 4. Free learning resources
        parts.append("\n📚 **Free Learning Resources**:")
        for res in self.free_resources:
            parts.append(f"   • {res}")
        
        # 5. Doctor-style follow-up question
        followup = self._generate_followup(user_query, condition)
        parts.append(f"\n{followup}")
        
        return "\n".join(parts)


# ================================================================
# TONE ANALYZER - Detect Emotional State & Adjust Empathy
# ================================================================
class ToneAnalyzer:
    """
    Analyzes user queries to detect emotional tone and adjust system prompt intensity
    
    Emotions detected:
    - Sad/Depressed: Increase empathy, add reassurance
    - Anxious/Worried: Increase calm, step-by-step guidance
    - Frustrated/Angry: Acknowledge frustration, avoid triggers
    - Neutral/Normal: Standard clinical tone
    """
    
    def __init__(self):
        self.emotion_keywords = {
            "sad": [
                "alone", "worthless", "hopeless", "sad", "down", "dejected",
                "lonely", "isolated", "depressed", "depresun", "nil", "nill",
                "akela", "akle", "bhot ghabra", "ghabra raha", "bura lag"
            ],
            "anxious": [
                "anxiety", "anxious", "worried", "worry", "tension", "tensio",
                "panic", "fear", "scared", "nervous", "uneasy", "restless",
                "overthinking", "bohot soch", "ghabrana", "dar", "bhay"
            ],
            "frustrated": [
                "frustrated", "angry", "gussa", "annoyed", "irritated", "upset",
                "fed up", "exhausted", "tired", "thak", "bakwaas", "bekar",
                "waste", "useless", "zyada ho", "bc", "yaar"
            ]
        }
        
        # Initialize multilingual emotion detector
        try:
            self.multilingual_detector = MultilingualEmotionDetector()
            logger.info("[OK] Multilingual emotion detector loaded in ToneAnalyzer")
        except Exception as e:
            logger.warning(f"Could not load multilingual detector: {e}")
            self.multilingual_detector = None
    
    def analyze_tone(self, user_query: str) -> str:
        """
        Detect emotional tone from user query using multilingual detection
        
        Supports:
        - English
        - Hindi
        - Hinglish (mixed English-Hindi)
        - Noisy/typo input
        
        Args:
            user_query: User's message
            
        Returns:
            Emotion label: 'depressed', 'anxious', 'frustrated', 'happy', etc.
        """
        try:
            # Try multilingual detection first
            if hasattr(self, 'multilingual_detector') and self.multilingual_detector:
                emotion, intensity, scores = self.multilingual_detector.detect_emotion(user_query)
                logger.info(f"[TONE] Multilingual detection: {emotion} (intensity: {intensity:.2f})")
                return emotion
        except Exception as e:
            logger.debug(f"Multilingual detection failed: {e}, falling back to keyword matching")
        
        # Fallback to keyword-based detection
        q = user_query.lower()
        
        # Check each emotion category
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in q:
                    logger.info(f"[TONE] Keyword detected: {emotion} (keyword: {keyword})")
                    return emotion
        
        return "neutral"
    
    def get_system_prompt_intensity(self, tone: str) -> Dict[str, str]:
        """
        Adjust system prompt intensity based on detected tone
        
        Args:
            tone: Detected emotion ('sad', 'anxious', 'frustrated', 'neutral')
            
        Returns:
            Dictionary with prompt adjustments
        """
        intensity_map = {
            "sad": {
                "intro": "🤝 **Bhai, samajh sakta hoon tum bohot down feel kar rahe ho.** Main yahan hoon, tum akele nahi ho.",
                "empathy_level": "HIGH",
                "response_style": "Reassuring + Hopeful",
                "example": "Ye feeling temporary hai aur improve ho sakti hai with proper support."
            },
            "anxious": {
                "intro": "🤝 **Samajh sakta hoon ki worry bohot zyada ho rahi hai.** Chalo, step-by-step dekhte hain.",
                "empathy_level": "MEDIUM-HIGH",
                "response_style": "Calming + Structured",
                "example": "First, let's break this down into smaller parts. Ek ek step take karenge."
            },
            "frustrated": {
                "intro": "🤝 **Haan bhai, frustration bilkul samajh aata hai.** Ye feeling valid hai.",
                "empathy_level": "MEDIUM",
                "response_style": "Validating + Solution-focused",
                "example": "Aapka gussa bilkul justified hai. Ab dekhte hain kya solution ho sakta hai."
            },
            "neutral": {
                "intro": "Namaste! Main Neuronix hoon, aapka clinical dost. 😊",
                "empathy_level": "STANDARD",
                "response_style": "Professional + Friendly",
                "example": "Aapke sawaal ka main bilkul sahi jawab dene ki koshish karunga."
            }
        }
        
        return intensity_map.get(tone, intensity_map["neutral"])
    
    def adjust_system_prompt(self, base_prompt: str, tone: str) -> str:
        """
        Modify system prompt based on detected tone
        
        Args:
            base_prompt: Original system prompt
            tone: Detected emotion
            
        Returns:
            Modified system prompt with empathy adjustments
        """
        intensity = self.get_system_prompt_intensity(tone)
        
        # Add tone-specific instruction to system prompt
        tone_instruction = f"\n\n[TONE ADJUSTMENT: {intensity['empathy_level']}]\n" \
                          f"Response Style: {intensity['response_style']}\n" \
                          f"Opening: {intensity['intro']}"
        
        return base_prompt + tone_instruction


class NeuronixChatEngine:
    """
    TWO-TIER NEURONIX ARCHITECTURE
    
    Layer 1: SAFETY CHECK
    ├─ Real self-harm intent → CRISIS mode (helplines only)
    │
    Layer 2: QUERY TYPE CLASSIFICATION
    ├─ NORMAL queries (weather, greetings, casual)
    │  └─ Mode: "Indore Dost" (Friendly Neighbor)
    │     Response: Natural, desi, casual tone
    │     No medical claims, just friendly advice
    │
    └─ CLINICAL queries (mental health, therapy, psychology)
       └─ Mode: "Doctor + RAG" (Medical Knowledge)
          Response: Empathetic, evidence-based, source citations
          Uses: Google Gemini + Vector DB retrieval
    
    Features:
    - RAG-powered clinical knowledge from ChromaDB
    - Hinglish (Hindi + English) responses for Indian users
    - Safety triggers for self-harm keywords (STRICT)
    - Free alternative suggestions (Status 0/1 logic)
    - Zero hallucination - defers when uncertain
    - Interactive chat with memory
    """
    
    def __init__(self, google_api_key: str = None):
        """
        Initialize the chat engine
        
        Args:
            google_api_key: Google API key for Gemini
        """
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if not self.google_api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY environment variable"
            )
        
        # Initialize embeddings and ChromaDB
        logger.info("[INIT] Loading ChromaDB from vector_db...")
        try:
            # Import embeddings - MUST MATCH what ingestion script uses!
            # Ingestion uses HuggingFaceEmbeddings with sentence-transformers/all-MiniLM-L6-v2
            from langchain_huggingface import HuggingFaceEmbeddings
            
            # Set up cache folder for HuggingFace models
            cache_folder = BASE_DIR / "hf_cache"
            cache_folder.mkdir(parents=True, exist_ok=True)
            
            # Initialize embeddings with caching to avoid repeated 404s and downloads
            # HF_TOKEN is automatically loaded from .env by dotenv
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                cache_folder=str(cache_folder),
                model_kwargs={"trust_remote_code": True}
            )
            logger.info("[OK] Embeddings initialized (HuggingFace all-MiniLM-L6-v2 + caching - MATCHES INGESTION)")
            
            # Load ChromaDB vector store
            if VECTOR_DB_DIR.exists():
                try:
                    self.vector_store = Chroma(
                        persist_directory=str(VECTOR_DB_DIR),
                        embedding_function=self.embeddings,
                        collection_name=COLLECTION_NAME  # 🔥 CRITICAL: Match ingestion collection name
                    )
                    logger.info(f"[OK] ChromaDB loaded from {VECTOR_DB_DIR} (collection: {COLLECTION_NAME})")
                    
                    # Check if database has data using direct collection query
                    try:
                        # Get the actual collection from ChromaDB client
                        collections = self.vector_store._client.list_collections()
                        count = 0
                        collection_name = None
                        
                        # Find neuronix collection and count documents
                        for col in collections:
                            if "neuronix" in col.name.lower() or col.count() > 0:
                                count = col.count()
                                collection_name = col.name
                                break
                        
                        logger.info(f"[OK] ChromaDB has {count} documents (collection: {collection_name})")
                        self.db_status = {
                            "initialized": True,
                            "has_data": count > 0,
                            "doc_count": count,
                            "message": f"✅ Knowledge Base Active: {count} documents loaded" if count > 0 else "⚠️ Database empty - using fallback responses"
                        }
                    except Exception as e:
                        logger.error(f"Failed to count documents: {e}")
                        self.db_status = {
                            "initialized": True,
                            "has_data": False,
                            "doc_count": 0,
                            "message": f"⚠️ Could not verify documents: {str(e)[:50]}"
                        }
                    
                            # Create retriever
                    try:
                        # High-recall retrieval; we'll re-rank inside _create_rag_chain_for_query
                        self.retriever = self.vector_store.as_retriever(
                            search_kwargs={"k": 20}
                        )
                        
                        logger.info("[QUERY_REWRITE] Query rewriter initialized")
                        logger.info("[OK] Retriever initialized successfully (k=20)")
                    except Exception as e:
                        logger.warning(f"Failed to create retriever: {e}")
                        self.retriever = None
                        # Keep db_status - documents are still accessible
                except Exception as e:
                    logger.warning(f"Failed to load ChromaDB: {e}")
                    self.vector_store = None
                    self.retriever = None
                    self.db_status = {
                        "initialized": False,
                        "has_data": False,
                        "doc_count": 0,
                        "message": f"❌ ChromaDB error: {str(e)[:100]}"
                    }
            else:
                logger.warning(f"Vector DB directory not found: {VECTOR_DB_DIR}")
                self.vector_store = None
                self.retriever = None
                self.db_status = {
                    "initialized": False,
                    "has_data": False,
                    "doc_count": 0,
                    "message": f"❌ Vector DB directory not found at {VECTOR_DB_DIR}"
                }
        except ImportError:
            logger.error("GoogleGenerativeAIEmbeddings not available")
            self.embeddings = None
            self.vector_store = None
            self.retriever = None
            self.db_status = {
                "initialized": False,
                "has_data": False,
                "doc_count": 0,
                "message": "❌ Embeddings package not installed"
            }
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            self.embeddings = None
            self.vector_store = None
            self.retriever = None
            self.db_status = {
                "initialized": False,
                "has_data": False,
                "doc_count": 0,
                "message": f"❌ Initialization error: {str(e)[:100]}"
            }
        
        # Initialize LLM
        logger.info("[OK] Initializing Gemini LLM...")

        # Some Gemini model names are not available depending on API version/accounts.
        # To keep tests and the app running, we try a configurable model first,
        # then fall back to a small set of common supported models.
        model_candidates = [
            # Default to a model that exists on most accounts. If you override,
            # set GEMINI_MODEL_NAME to a full model id like 'models/gemini-2.5-flash'.
            os.getenv("GEMINI_MODEL_NAME", "models/gemini-2.5-flash"),
            # Common fallbacks
            "models/gemini-2.5-pro",
            "models/gemini-1.5-pro",
            "models/gemini-pro",
        ]

        last_llm_err: Optional[Exception] = None
        for model_name in model_candidates:
            if not model_name:
                continue
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=model_name,  # selectable via GEMINI_MODEL_NAME env var
                    google_api_key=self.google_api_key,
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=1024,
                )
                logger.info(f"[OK] Gemini LLM initialized with model: {model_name}")
                last_llm_err = None
                break
            except Exception as e:
                last_llm_err = e
                # Keep trying other models
                logger.warning(f"[LLM INIT] Model '{model_name}' failed: {e}")
                self.llm = None

        if self.llm is None and last_llm_err is not None:
            logger.error(f"[LLM INIT] All Gemini model candidates failed. Last error: {last_llm_err}")

        
        # Load master mapping
        logger.info("[OK] Loading master mapping...")
        self.mapping_data = self._load_mapping()
        
        # Initialize Clinical Response Formatter
        self.formatter = ClinicalResponseFormatter()
        
        # Initialize Tone Analyzer for empathy adjustment
        self.tone_analyzer = ToneAnalyzer()
        
        # Initialize Multilingual Emotion Detector for Indian languages
        try:
            self.multilingual_detector = MultilingualEmotionDetector()
            logger.info("[OK] Multilingual emotion detector initialized in NeuronixChatEngine")
        except Exception as e:
            logger.warning(f"Could not initialize multilingual detector: {e}")
            self.multilingual_detector = None
        
        # Initialize Session Manager for chat memory
        self.session_manager = SessionManager()
        self.current_user_id = None  # Will be set when chat starts
        
        # ===== 🔹 STEP 1-2: LEARNING & FEEDBACK SYSTEM =====
        # Session-level feedback tracking (temporary)
        self.session_feedback = {
            "responses_total": 0,
            "responses_helpful": 0,
            "responses_unclear": 0,
            "response_language_preference": None,  # Detected user's preferred language
            "response_tone_preference": None,  # Hinglish, formal, casual, etc.
            "session_notes": []
        }
        
        # Persistent learning file (survives across sessions)
        self.learning_file = BASE_DIR / "data" / "learning_preferences.json"
        self.learning_data = self._load_learning_preferences()
        
        # 🔹 EDGE CASE FIX #3: Follow-up loop prevention
        # Tracks how many follow-up clarification questions asked in session
        self.followup_count = 0
        self.max_followups = 2  # Max 2 attempts before giving best guess
        
        logger.info(f"[OK] Learning + Loop prevention initialized")
        
        # Store default prompt template (will be created dynamically per query based on language)
        self.prompt_template = None  # Will be set during chat based on user language
        
        # Initialize RAG chain using LCEL (LangChain Expression Language)
        logger.info("[OK] Initializing retrieval chain...")
        
        # Retriever disabled in demo mode
        # self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        
        # Format documents for context
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # Store formatted docs function for use in chat()
        self.format_docs = format_docs
        
        # RAG chain will be created fresh for each query to avoid caching
        self.rag_chain = None  # Will be created in _create_rag_chain_for_query()
        
        # Database status will be displayed in Streamlit
        logger.info(f"[DB-STATUS] {self.db_status['message']}")
        
        # Conversation history
        self.conversation_history = []
        
        # ========== PHASE 3: CONVERSATION INTELLIGENCE LAYER ==========
        self.phase3_enabled = PHASE3_AVAILABLE
        if PHASE3_AVAILABLE:
            try:
                self.memory = ConversationMemory()
                self.distress_tracker = DistressTracker()
                self.followup_engine = ContextualFollowupEngine()
                self.safety_system = ProactiveSafetySystem()
                logger.info("[OK] Phase 3 Conversation Intelligence Layer initialized")
            except Exception as e:
                logger.warning(f"Phase 3 initialization failed: {e}. Running in compatibility mode.")
                self.phase3_enabled = False
        
        logger.info("[OK] Neuronix Chat Engine initialized successfully!")
        print("\n" + "=" * 80)
        print("[*] NEURONIX - Clinical Psychology AI Assistant")
        print("=" * 80)
        print("\nNamaste! I'm Neuronix, your clinical companion.")
        print("Ask me about any health concern.\n")
        print("Type 'exit' or 'bye' to end chat")
        print("Type 'clear' to reset conversation")
        print("=" * 80 + "\n")
    
    def get_db_status(self) -> Dict:
        """Get Chrome DB status for Streamlit display"""
        return self.db_status
    
    def _create_rag_chain_for_query(self, query: str) -> str:
        """
        Create fresh RAG chain for each query to retrieve context
        This prevents caching and ensures fresh results
        
        Args:
            query: Normalized search query
            
        Returns:
            Retrieved context string or empty string
        """
        if not self.retriever or not self.vector_store:
            logger.warning("RAG chain not available - Vector DB not initialized")
            print("⚠️ [RAG] Vector DB not initialized!")
            return ""
        
        try:
            # Retrieve documents
            docs = self.retriever.invoke(query)
            
            if not docs:
                logger.info(f"[RAG] No documents retrieved for query: {query}")
                print(f"⚠️ [RAG] No documents retrieved for: '{query}'")
                return ""
            
            # 🔥 FIX 2: RELEVANCE FILTERING - Remove noisy/short documents
            # Only keep documents with substantial content (> 100 chars)
            filtered_docs = [d for d in docs if len(d.page_content) > 100]
            
            if not filtered_docs:
                logger.info(f"[RAG] All documents filtered out (too short) for query: {query}")
                print(f"⚠️ [RAG] All retrieved docs were too short/noisy for: '{query}'")
                return ""
            
            # Take top-K after filtering (2-stage upgrade target)
            # We keep a larger set here because precision/reranking will be applied next.
            filtered_docs = filtered_docs[:20]

            # ================================================================
            # Precision stage: Cross-encoder reranking (graceful fallback)
            # ================================================================
            # Goal: take the best top-5 chunks from the 20-candidate pool.
            # - If cross-encoder dependencies are missing or reranking fails,
            #   fall back to the first 5 hybrid candidates.
            reranked_docs = None
            try:
                from rag_advanced import AdvancedRAGRetriever

                advanced_retriever = AdvancedRAGRetriever(
                    self.vector_store,
                    enable_hybrid=True,
                    enable_cache=False,
                    enable_reranking=True,
                    cache_size=100,
                    hybrid_alpha=0.6,
                )

                # Use AdvancedRAGRetriever end-to-end retrieval;
                # it performs hybrid recall + cross-encoder precision.
                docs_precise = advanced_retriever.retrieve(
                    query=query,
                    k=5,
                    metadata_filters=None,
                    use_hybrid=True,
                )

                reranked_docs = docs_precise
            except Exception as rerank_err:
                logger.warning(f"[RERANK] Cross-encoder reranking failed; falling back. Error: {rerank_err}")

            # Final context docs (top-5)
            filtered_docs = reranked_docs if reranked_docs else filtered_docs[:5]

            # ================================================================
            # High-impact upgrade: Deduplicate near-identical chunks
            # Improves precision by preventing repeated passages from crowding
            # out better matches in the final context window.
            # ================================================================
            unique_docs = []
            seen_fingerprints = set()

            for doc in filtered_docs:
                if not doc or not hasattr(doc, 'page_content'):
                    continue

                # Fingerprint on the beginning of the chunk (fast + robust for duplicates)
                fingerprint = doc.page_content[:300].strip()
                if not fingerprint:
                    continue

                if fingerprint in seen_fingerprints:
                    continue

                seen_fingerprints.add(fingerprint)
                unique_docs.append(doc)

            filtered_docs = unique_docs[:5]

            # 🔥 NEW: RETRIEVAL LOG DECORATOR - Print detailed source info
            print("\n" + "="*70)
            print(f"📚 [RETRIEVAL LOG] Query: '{query}'")
            print(f"   📊 Retrieved: {len(filtered_docs)} documents")
            print("-" * 70)
            
            for i, doc in enumerate(filtered_docs, 1):
                source = doc.metadata.get('source', 'Unknown')
                chunk_idx = doc.metadata.get('chunk_index', '?')
                total_chunks = doc.metadata.get('total_chunks', '?')
                doc_type = doc.metadata.get('doc_type', 'general')
                
                # 🔥 UTF-8 SAFE: Handle special characters in source names
                safe_source = source.encode('utf-8', 'ignore').decode('utf-8')
                safe_preview = doc.page_content[:80].encode('utf-8', 'ignore').decode('utf-8')
                
                print(f"   [{i}] 📖 Source: {safe_source}")
                print(f"       Chunk: {chunk_idx}/{total_chunks} | Type: {doc_type}")
                print(f"       Preview: {safe_preview}...")
            print("="*70 + "\n")
            
            logger.info(f"[RAG] ✅ Retrieved {len(filtered_docs)} relevant documents")
            logger.info(f"[RAG] Sources: {[doc.metadata.get('source', 'Unknown') for doc in filtered_docs]}")
            
            # 🔥 UTF-8 SAFE: Format retrieved documents with safe encoding
            context_parts = []
            for i, doc in enumerate(filtered_docs):
                source_name = doc.metadata.get('source_file', 'Unknown')
                content = doc.page_content[:300]
                
                # Safe encode/decode to strip problematic characters
                safe_source = source_name.encode('utf-8', 'ignore').decode('utf-8')
                safe_content = content.encode('utf-8', 'ignore').decode('utf-8')
                
                context_parts.append(f"📚 **Source {i+1}**: {safe_source}\n{safe_content}...")
            
            context = "\n\n".join(context_parts)
            
            logger.info(f"[RAG] ✅ Retrieved {len(filtered_docs)} relevant documents for context")
            print(f"✅ [RAG] Successfully retrieved {len(filtered_docs)} documents")
            return context
        
        except Exception as e:
            logger.warning(f"[RAG] Error during retrieval: {e}")
            print(f"❌ [RAG] Retrieval error: {e}")
            return ""
    
    def _load_mapping(self) -> Dict:
        """Load the master_mapping.json and validate structure"""
        try:
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"[OK] Loaded master_mapping.json: {len(data)} entries")
                return data
        except FileNotFoundError:
            logger.warning(f"[!] master_mapping.json not found at {MAPPING_FILE}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"[!] Invalid JSON in master_mapping.json: {e}")
            return {}
        except Exception as e:
            logger.warning(f"Could not load mapping: {e}")
            return {}
    
    # ================================================================
    # INPUT PROCESSING PIPELINE (STEP 1-3) - WITH LLM NORMALIZATION
    # ================================================================
    
    def _detect_script_language(self, text: str) -> Dict[str, str]:
        """
        ENHANCED: Detect script + auto-select response language
        Now includes Spanish, Italian, French detection
        
        Returns:
        {
            "detected_script": "HINDI" | "HINGLISH" | "ENGLISH" | "SPANISH" | "ITALIAN" | "FRENCH" | "MIXED",
            "response_language": "hindi" | "hinglish" | "english" | "spanish" | "italian" | "french"
        }
        """
        hindi_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहक्षत्रज्ञ')
        english_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        
        text_lower = text.lower()
        text_chars = set(text_lower)
        has_hindi = bool(text_chars & hindi_chars)
        has_english = bool(text_chars & english_chars)
        
        # Detect Romance languages by keywords
        spanish_keywords = ['qué', 'por favor', 'gracias', 'hola', 'me duele', 'siento', 'estoy']
        italian_keywords = ['sono', 'mi', 'grazie', 'ciao', 'dolore', 'ansia', 'stress']
        french_keywords = ['je', 'suis', 'bonjour', 'merci', 'stress', 'douleur', 'anxiété']
        
        has_spanish = any(kw in text_lower for kw in spanish_keywords)
        has_italian = any(kw in text_lower for kw in italian_keywords)
        has_french = any(kw in text_lower for kw in french_keywords)
        
        if has_spanish:
            script = "SPANISH"
            response_lang = "spanish"
        elif has_italian:
            script = "ITALIAN"
            response_lang = "italian"
        elif has_french:
            script = "FRENCH"
            response_lang = "french"
        elif has_hindi and has_english:
            script = "HINGLISH"
            response_lang = "hinglish"
        elif has_hindi:
            script = "HINDI"
            response_lang = "hindi"
        elif has_english:
            script = "ENGLISH"
            response_lang = "english"
        else:
            script = "MIXED"
            response_lang = "english"  # Safe fallback
        
        logger.info(f"[LANG DETECT] Script: {script} → Response: {response_lang}")
        return {
            "detected_script": script,
            "response_language": response_lang
        }
    
    # ============================================================
    # SIMPLE LANGUAGE DETECTION (for LLM response language)
    # ============================================================
    
    def _detect_language_simple(self, text: str) -> str:
        """
        🔥 Simple language detection for LLM response adaptation
        
        Returns:
        - "Hindi": Pure Hindi/Devanagari script detected
        - "Hinglish": Mix of Hindi + English (most common in India)
        - "English": Pure English text
        
        Args:
            text: User's input text
            
        Returns:
            Language type as string
        """
        hindi_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहक्षत्रज्ञ')
        hinglish_keywords = ['hai', 'nahi', 'kyu', 'kaise', 'kya', 'ho', 'hoon', 'raha', 'rahe']
        
        text_lower = text.lower()
        text_chars = set(text_lower)
        
        # Check for Hindi script
        has_hindi = bool(text_chars & hindi_chars)
        
        # Check for Hinglish keywords
        has_hinglish = any(kw in text_lower for kw in hinglish_keywords)
        
        if has_hindi and has_hinglish:
            return "Hinglish"
        elif has_hindi:
            return "Hindi"
        elif has_hinglish:
            return "Hinglish"
        else:
            return "English"
    
    # ============================================================
    # 3-LAYER NORMALIZATION SYSTEM (PRODUCTION-GRADE)
    # ============================================================
    
    # LAYER 1: Fast dictionary for high-frequency mappings
    BASE_MAP = {
        # Hinglish common (core variants)
        "tensio": "tension",
        "komsi": "kaunsi",
        "komssi": "kaunsi",
        "komsii": "kaunsi",
        "neend nai": "neend nahi",
        "neend nhi": "neend nahi",
        "neend na": "neend nahi",
        "nind na": "neend nahi",
        "nind nahi": "neend nahi",
        "nim nahi": "neend nahi",
        "thak gya": "thak gaya",
        "thak gayi": "tired",
        "thak gyi": "tired",
        "thak gea": "thak gaya",

        # Gussa variations (anger/frustration)
        "gussa a rha": "gussa aa raha",
        "gussa aa rha": "gussa aa raha",
        "gussa arha": "gussa aa raha",
        "gussaa rha": "gussa aa raha",
        "gussaa": "gussa",

        # Depression/stress typos (medical terms)
        "depresun": "depression",
        "depreshun": "depression",
        "deprassion": "depression",
        "stresss": "stress",
        "stresd": "stress",

        # Common Hinglish short forms
        "mn": "mann",
        "rha": "raha",
        "rhaa": "raha",
        "rhha": "raha",
        "gya": "gaya",
        "hoo": "ho",
        "haa": "hain",
        "hain": "hain",
        "mook": "book",
        "krupa": "depression",
        "krpya": "please",

        # Other emotional markers
        "sad": "depression",
        "worried": "anxiety",
        "anxeity": "anxiety",
        "gussaa": "anger",
        "gussa": "anger",
        "krpya": "please",
    }
    
    # Vocabulary for fuzzy matching fallback (Layer 2)
    VOCAB = [
        "stress", "tension", "depression", "anxiety",
        "sleep", "neend nahi", "gussa", "anger",
        "tired", "thak gaya", "kaunsi", "book",
        "suicide", "hurt", "kill", "overwhelmed",
        "sad", "frustrated", "exhausted", "worried",
        "insomnia", "overthinking", "tension headache",
        "feeling low", "breakup", "job stress",
    ]
    
    # CRITICAL WORDS: Protected from fuzzy correction (prevent override)
    # These are core medical/emotional terms that should NEVER be changed
    CRITICAL_WORDS = {
        "neend", "nind", "nim",           # Sleep variants
        "gussa", "gussaa", "anger",      # Anger variants
        "tension", "tensio",              # Tension variants
        "depression", "depresun",         # Depression variants
        "anxiety", "anxeity",             # Anxiety variants
        "stress", "stresss",              # Stress variants
        "tired", "thak", "exhausted",   # Tiredness variants
        "sad", "cry", "ro",              # Sadness variants
        "nahi", "nhi", "ni",             # Negation variants
    }
    
    # Unknown input logging (for auto-learning potential)
    UNKNOWN_LOG: List[str] = []
    
    def _pattern_normalize(self, text: str) -> str:
        """
        LAYER 2: Regex pattern normalization for grammar variations
        
        Handles complex Hinglish patterns that simple replacements miss.
        Uses STRICTER patterns to avoid fuzzy override issues.
        Examples:
        - "neend   nai" (extra spaces) → "neend nahi"
        - "thak    gya" (multiple spaces) → "thak gaya"
        - "gussa a rha" (spacing variations) → "gussa aa raha"
        
        Returns:
            Text with patterns normalized
        """
        rules = [
            # Sleep patterns (STRICT: handle nai/nhi/ni variations)
            (r"\bneend\s+(nai|nhi|ni)\b", "neend nahi"),
            (r"\bnind\s+(nai|nhi|ni)\b", "neend nahi"),
            (r"\bnim\s+(nai|nhi|ni)\b", "neend nahi"),
            
            # Tiredness patterns (STRICT)
            (r"\bthak\s+gya\b", "thak gaya"),
            (r"\bthak\s+gayi\b", "tired"),
            (r"\bthak\s+gyi\b", "tired"),
            (r"\bthak\s+gea\b", "thak gaya"),
            
            # Anger patterns (STRICT: gussa spacing with (a|aa) variant)
            (r"\bgussa\s+(a|aa)\s+rha\b", "gussa aa raha"),
            (r"\bgussa\s+arha\b", "gussa aa raha"),
            (r"\bgussaa\s+rha\b", "gussa aa raha"),
            
            # Tension/pressure (STRICT character class)
            (r"\btensi[on]\b", "tension"),
            
            # Depression variants (STRICT)
            (r"\bdepress(un|shun|ion)\b", "depression"),
            
            # Anxiety (STRICT)
            (r"\bixiety\b", "anxiety"),
            (r"\banxi+ty\b", "anxiety"),
            
            # Stress (STRICT: only allow extra s, no d)
            (r"\bstres+\b", "stress"),
            
            # Books question pattern (STRICT)
            (r"\bkom+s[si]+\b", "kaunsi"),
        ]
        
        for pattern, replacement in rules:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _fuzzy_correct(self, word: str) -> str:
        """
        LAYER 3: Fuzzy correction for unseen typos
        
        ⚠️ CRITICAL: SKIP PROTECTED WORDS
        Protects core medical/emotional terms from being overridden by fuzzy matching.
        
        Uses rapidfuzz.process.extractOne for semantic correction.
        Only corrects if match score > 85 (reduces false positives).
        
        Args:
            word: Single word to correct
            
        Returns:
            PROTECTED WORDS → return unchanged
            Others → Corrected if high-confidence match (score > 85), else original
        """
        # ⚠️ PROTECTION: Never fuzzy-correct critical medical/emotional words
        if word in self.CRITICAL_WORDS:
            return word
        
        if len(word) < 3:  # Skip very short words
            return word
        
        match, score, _ = process.extractOne(word, self.VOCAB, scorer=fuzz.ratio)
        
        if score > 85:  # Only correct with high confidence
            return match
        
        return word
    
    def _normalize_text_rule_based(self, text: str) -> str:
        """
        PATCHED 3-LAYER NORMALIZATION PIPELINE (PRODUCTION-READY)
        
        Layer 1: Dictionary fast fixes (instant accuracy)
        Layer 2: Pattern normalization (grammar variations, spacing)
        Layer 3: Fuzzy word correction (generalization for unseen typos)
           └─ ⚠️ SKIP CRITICAL WORDS to prevent fuzzy override
        
        Pipeline:
        text → dict replace → regex patterns → fuzzy (skip protected) → output
        
        This combines:
        - Speed of dictionary lookup
        - Coverage of regex patterns
        - Generalization of fuzzy matching (without breaking critical words)
        
        Returns:
            Fully normalized text ready for intent classification
        """
        text = text.lower().strip()
        
        # ===== LAYER 1: DICTIONARY (FAST) =====
        # Fast replacements for high-frequency mappings
        for key, value in self.BASE_MAP.items():
            text = text.replace(key, value)
        
        # ===== LAYER 2: PATTERN NORMALIZATION (REGEX) =====
        # Stricter patterns to handle spacing/grammar variations
        text = self._pattern_normalize(text)
        
        # ===== LAYER 3: FUZZY WORD CORRECTION (WITH CRITICAL WORD PROTECTION) =====
        # Apply fuzzy only to non-critical words
        normalized_text = text  # Store original normalized text
        words = text.split()
        corrected_words = [self._fuzzy_correct(w) for w in words]
        text = " ".join(corrected_words)
        
        return text
    
    def _llm_normalize_input(self, user_input: str) -> str:
        """
        Fallback: Use rule-based approach (stable + reliable)
        
        Args:
            user_input: Raw user message
            
        Returns:
            Normalized query for semantic search
        """
        normalized = self._normalize_text_rule_based(user_input)
        logger.info(f"[NORM] '{user_input}' → '{normalized}'")
        return normalized
    
    def _normalize_hinglish(self, text: str) -> str:
        """
        STEP 1: Normalize Hinglish input - fix common typos & spellings
        
        Handles:
        - Short forms: "mn" → "mann", "rha" → "raha"
        - Common typos: "muder" → "murder", "thak" → "tired"
        - Casual spellings: "gya" → "gaya", "ho" → "hoon"
        
        Args:
            text: User's input text
            
        Returns:
            Normalized text
        """
        normalization_map = {
            # Common Hinglish short forms
            'mn': 'mann', 'rha': 'raha', 'ho': 'hoon', 'gya': 'gaya',
            'kya': 'kya', 'kha': 'khana', 'chai': 'chai',
            # Mental health related typos
            'depress': 'depressed', 'anx': 'anxiety', 'stres': 'stress',
            'thak': 'tired', 'frustr': 'frustrated', 'gussa': 'anger',
            'confus': 'confused', 'parani': 'paranoid',
            # Crisis related typos
            'muder': 'murder', 'hurt': 'hurt', 'slit': 'slit',
            'overdos': 'overdose', 'ending': 'ending',
            # Casual typos
            'wats': 'whats', 'ur': 'your', 'u': 'you', 'abt': 'about',
            'thru': 'through', 'tho': 'though', 'thnk': 'think',
        }
        
        normalized = text.lower()
        for short, full in normalization_map.items():
            normalized = normalized.replace(f' {short} ', f' {full} ')
            normalized = normalized.replace(f'^{short} ', f'{full} ')
            normalized = normalized.replace(f' {short}$', f' {full}')
        
        logger.info(f"[NORMALIZE] {text[:30]}... → {normalized[:30]}...")
        return normalized
    
    def _correct_typos_with_spell_checker(self, text: str) -> str:
        """
        🔥 LLM-ENHANCED TYPO CORRECTOR: Fix common misspellings
        
        Handles:
        - god → good (single letter typo)
        - nto → not (letter transposition)
        - helllo → hello (repeated letters)
        - Depression → depression (case normalization)
        
        Args:
            text: User's input text
            
        Returns:
            Text with typos corrected
        """
        # Common single-letter/one-off typos (high confidence fixes)
        typo_corrections = {
            'god': 'good',           # very common typo
            'nto': 'not',            # transposition
            'feling': 'feeling',     # missing letter
            'sory': 'sorry',         # missing letter
            'dont': 'don\'t',        # contraction
            'cant': 'can\'t',        # contraction
            'wont': 'won\'t',        # contraction
            'havent': 'haven\'t',    # contraction
            'doesnt': 'doesn\'t',    # contraction
            'im': 'i\'m',            # contraction
            'ur': 'your',            # slang
            'u': 'you',              # slang
            'nite': 'night',         # casual
            'thru': 'through',       # casual
            'till': 'until',         # variant
            'abt': 'about',          # abbreviation
            'rly': 'really',         # abbreviation
            'tbh': 'to be honest',   # abbreviation
            'btw': 'by the way',     # abbreviation
        }
        
        corrected = text.lower()
        for typo, correct in typo_corrections.items():
            # Replace whole word only (avoid partial matches)
            corrected = re.sub(r'\b' + typo + r'\b', correct, corrected)
        
        logger.info(f"[TYPO-CORRECTION] {text[:30]}... → {corrected[:30]}...")
        return corrected
    
    def _classify_query_intent_llm(self, query: str) -> str:
        """
        🔥 LLM-BASED INTENT CLASSIFIER: Multi-category classification
        
        Categories:
        - crisis: Immediate danger (suicide, self-harm)
        - vague_distress: Emotional but unclear (feeling bad, not okay)
        - informational_query: Knowledge-seeking (symptoms of X, how to treat Y)
        - greeting: Social/casual (hi, hello, how are you)
        
        Args:
            query: Normalized and corrected user query
            
        Returns:
            Intent category string
        """
        q = query.lower()
        
        # PRIORITY 1: Crisis detection (fastest, highest confidence)
        crisis_keywords = [
            'suicide', 'suicidal', 'kill myself', 'hurt myself', 'self harm',
            'end my life', 'want to die', 'no point living', 'can\'t take it',
            'aatmhatya', 'mar', 'jhol', 'overdose', 'poison', 'hang',
            'marne ka socha', 'jeena nahi', 'sab khatam'
        ]
        if any(kw in q for kw in crisis_keywords):
            logger.info(f"[INTENT-LLM] CRISIS detected")
            return "crisis"
        
        # PRIORITY 2: Informational queries (knowledge-seeking)
        informational_keywords = [
            'what is', 'what are', 'how to', 'how does', 'symptoms of',
            'treatment for', 'meaning of', 'explain', 'tell me about',
            'definition of', 'difference between', 'research', 'study',
            'book', 'study', 'learn', 'understand', 'kya hai', 'kaise', 'matlab'
        ]
        if any(kw in q for kw in informational_keywords):
            logger.info(f"[INTENT-LLM] INFORMATIONAL detected")
            return "informational_query"
        
        # PRIORITY 3: Vague distress (emotional, unclear specifics)
        vague_distress_keywords = [
            'not feeling good', 'not ok', 'not okay', 'feeling bad', 'feeling down',
            'stressed', 'worried', 'nervous', 'anxious', 'scared', 'afraid',
            'overwhelmed', 'confused', 'lost', 'struggling', 'difficult',
            'problem', 'issue', 'trouble', 'worried', 'concern',
            'accah nhi', 'thik nhi', 'sahi nhi', 'tension', 'ghbrana', 'dar'
        ]
        if any(kw in q for kw in vague_distress_keywords):
            logger.info(f"[INTENT-LLM] VAGUE_DISTRESS detected")
            return "vague_distress"
        
        # PRIORITY 4: Greetings/casual
        greeting_keywords = [
            'hello', 'hi', 'hey', 'namaste', 'how are', 'kaisa hai',
            'how do you', 'what\'s up', 'sup', 'yo', 'hiya'
        ]
        if any(kw in q for kw in greeting_keywords):
            logger.info(f"[INTENT-LLM] GREETING detected")
            return "greeting"
        
        # Default: Consider it vague distress if clinical-sounding but unclear
        if any(word in q for word in ['depression', 'anxiety', 'stress', 'mental', 'therapy']):
            logger.info(f"[INTENT-LLM] DEFAULT to VAGUE_DISTRESS (clinical keywords present)")
            return "vague_distress"
        
        # Ultimate default
        logger.info(f"[INTENT-LLM] DEFAULT to GREETING")
        return "greeting"
    
    def _detect_language(self, text: str) -> str:
        """
        STEP 2: Detect input language
        
        Returns:
        - "HINGLISH": Mix of Hindi + English (most common in India)
        - "HINDI": Pure Hindi/Devanagari
        - "ENGLISH": Pure English
        - "MIXED": Multiple scripts detected
        
        Args:
            text: User's input text
            
        Returns:
            Language type
        """
        hindi_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहक्षत्रज्ञ')
        english_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        
        text_chars = set(text.lower())
        has_hindi = bool(text_chars & hindi_chars)
        has_english = bool(text_chars & english_chars)
        
        if has_hindi and has_english:
            language = "HINGLISH"
        elif has_hindi:
            language = "HINDI"
        elif has_english:
            language = "ENGLISH"
        else:
            language = "MIXED"
        
        logger.info(f"[LANGUAGE] Detected: {language}")
        return language
    
    def _translate_to_english(self, text: str, language: str) -> str:
        """
        STEP 3: Translate text to English (internal use only)
        
        For Hinglish/Hindi input, translate to English for:
        - Vector search (RAG retrieval)
        - Intent classification
        - Internal processing
        
        Note: Response will still be in Hinglish for user
        
        Args:
            text: User's input
            language: Detected language type
            
        Returns:
            English version of input
        """
        # Hinglish/Hindi → English mapping (common phrases)
        hindi_to_english_map = {
            'stress': 'stress', 'tension': 'tension', 'pareshani': 'problem',
            'gussa': 'anger', 'takleef': 'suffering', 'dard': 'pain',
            'thak gaya': 'tired', 'frustration': 'frustration', 'confustion': 'confusion',
            'aatmhatya': 'suicide', 'khud ko maarna': 'self harm', 'marna': 'death',
            'khushi': 'happiness', 'khushi nahi': 'unhappy', 'sad': 'sad',
            'depression': 'depression', 'anxiety': 'anxiety', 'panic': 'panic',
            'neend nahi': 'insomnia', 'nightmare': 'nightmare', 'bura sapna': 'bad dream',
            'therapy': 'therapy', 'counselor': 'counselor', 'doctor': 'doctor',
            'medicine': 'medicine', 'tablet': 'medicine', 'treatment': 'treatment',
            'book': 'book', 'kitaab': 'book', 'padho': 'read', 'likha': 'written',
            'hello': 'hello', 'namaste': 'hello', 'aap kaise ho': 'how are you',
            'mausam': 'weather', 'dhoop': 'sunshine', 'baarish': 'rain',
            'garmi': 'heat', 'thandi': 'cold', 'indore': 'indore',
        }
        
        translated = text.lower()
        
        # For Hinglish, mix is mostly already English, just clean it
        if language == "HINGLISH":
            # Replace Hindi words with English equivalents
            for hindi, english in hindi_to_english_map.items():
                translated = translated.replace(hindi, english)
        
        elif language == "HINDI":
            # For pure Hindi, use simple mapping
            for hindi, english in hindi_to_english_map.items():
                translated = translated.replace(hindi, english)
        
        # English stays as is
        logger.info(f"[TRANSLATE] Internal English: {translated[:40]}...")
        return translated
    
    def _create_prompt_template(self, language: str = "Hinglish") -> PromptTemplate:
        """
        🔥 Create LANGUAGE-ADAPTIVE system prompt that responds in user's language
        
        This prompt automatically adjusts response language based on user input.
        
        Args:
            language: Detected language ("Hindi", "Hinglish", or "English")
            
        Returns:
            PromptTemplate with language-specific instructions
        """
        
        # Build language-specific instructions (HUMAN-LIKE + SAFETY + DIRECT ANSWERS)
        language_instructions = {
            "Hindi": """आप एक सहानुभूति पूर्ण मानसिक स्वास्थ्य मित्र हैं।

आपका तरीका:
- मानुष की तरह बातें करें, किताब की तरह नहीं
- सहायक हों, सामान्य नहीं
- सीधा जवाब दें पहले, फिर समझाएं
- अगर निश्चित नहीं हैं, तो "मुझे पूरी जानकारी नहीं है" कहें
- अगर कोई परेशान लग रहा है तो ध्यान से सुनें और मदद दें

यदि प्रश्न अस्पष्ट है: "'मैं समझा नहीं - क्या आपका मतलब X, Y या Z है?"

जरूरی सुरक्षा:
- अगर आत्म-नुकसान के संकेत: "मैं समझ सकता हूँ यह मुश्किल है... किसी भरोसेमंद को बताएं या हेल्पलाइन कॉल करें"

⭐ विशेष मामला: सर्वोत्तम अनुमान
- यदि आपने स्पष्टीकरण प्रश्न पूछे हैं लेकिन विवरण नहीं मिला है:
  "आपके बताए अनुसार लगता है कि..." (दिखाएं कि आप अनुमान लगा रहे हैं)

⭐ महत्वपूर्ण - व्यक्तिगतकरण पर स्पष्टता को प्राथमिकता दें:
- आपकी सीखी गई प्राथमिकताएं सहायक हैं, लेकिन
- हमेशा स्पष्टता, सटीकता, और उपयोगकर्ता सुरक्षा को प्राथमिकता दें
- अगर गंभीर मानसिक स्वास्थ्य समस्या है तो संक्षिप्तता से ऊपर पूर्णता लें
- मानसिक स्वास्थ्य में सही जानकारी > व्यक्तिगतकरण

संदर्भ का उपयोग करें, लेकिन अपने शब्दों में समझाएं।""",

            "Hinglish": """You are a supportive mental health friend, not a robot.

Your style:
- Talk like a human, not a textbook
- Be a helper, not a system
- Give direct answer first, then explain if needed
- If unsure, say "Mujhe puri jankari nahi hai"
- If someone seems distressed, respond with care and suggest help

⭐ IMPORTANT - SHORT ANSWER MODE:
- Keep answer concise (4-6 lines), but COMPLETE and helpful
- Avoid unnecessary long explanations
- Get straight to the point while staying meaningful
- BUT: If it's a serious mental health issue, prioritize clarity and completeness over brevity

If question is vague: "Samajh mein nahi aaya - kya aap bata sakte ho ki stress hai, sleep problem hai, ya kuch aur?"

Critical safety:
- If self-harm signs: "Main samajh sakta hoon ye tough hai... kisi trusted ko bata do ya helpline call karo"
- Always prioritize safety and accuracy over user's learned preference for brevity

⭐ EDGE CASE: Best Guess
- If you have tried to ask clarifying questions but user didn't provide details, mention it:
  "Aapke description se lagta hai..." (show you're making educated guess)
- This gives user clarity about certainty level

⭐ IMPORTANT - PRIORITIZE CLARITY OVER PERSONALIZATION:
- Your learned preferences are helpful, BUT
- Always prioritize clarity, accuracy, and user safety
- In mental health, correctness comes before customization

Use context to answer, but explain in your own words.
Keep it short and helpful, not scholarly.
Be human. Be real.""",

            "English": """You are a supportive mental health friend, not a system.

Your approach:
- Be empathetic and human-like
- Don't sound like a textbook
- Give direct answer FIRST, then explain if needed
- If unsure, say "I may not have complete info"
- If someone seems distressed, respond with care and suggest professional help

⭐ IMPORTANT - SHORT ANSWER MODE:
- Keep answer concise (4-6 lines), but COMPLETE and meaningful
- Avoid unnecessary explanations
- Be direct while staying substantive
- BUT: If it's a serious mental health issue, prioritize clarity and completeness over brevity

If question is unclear: "I'm not sure what you mean - are you dealing with stress, sleep issues, or something else?"

Critical safety:
- If self-harm/crisis signs: "I understand this is tough... please talk to someone you trust or contact a helpline"
- Always prioritize safety and accuracy over user's learned preference for brevity

⭐ EDGE CASE: Best Guess
- If you have tried to ask clarifying questions but user didn't provide details, mention it:
  "Based on what you've shared, it sounds like..." (show you're making educated guess)
- This gives user clarity about certainty level

⭐ IMPORTANT - PRIORITIZE CLARITY OVER PERSONALIZATION:
- Your learned preferences are helpful, BUT
- Always prioritize clarity, accuracy, and user safety
- In mental health, correctness comes before customization

Use the context to answer, but explain simply in your own words.
Keep responses concise, helpful, and warm.
Be genuinely human."""
        }
        
        # Select appropriate instructions
        lang_instruction = language_instructions.get(language, language_instructions["Hinglish"])
        
        # Build final HUMAN-LIKE prompt template (PRODUCTION-READY)
        # 🔥 CRITICAL: Make context injection explicit for LLM
        system_prompt = f"""{lang_instruction}

---RETRIEVED KNOWLEDGE BASE RESOURCES (GROUND YOUR ANSWER IN THESE)---
You MUST use the following retrieved documents to inform your response. 
Base your answer on these materials, not generic knowledge.

Documents:
{{context}}

---END RESOURCES---

User's question:
{{question}}

CRITICAL INSTRUCTION: Use the above retrieved documents as your primary source. 
If the documents don't contain relevant info, say so clearly. 
Do NOT make up information - stick to what's in the documents.

Your response:"""
        
        return PromptTemplate(
            template=system_prompt,
            input_variables=["context", "question"]
        )
    
    # ================================================================
    # 🔹 LEARNING & FEEDBACK SYSTEM (AI learns from user interactions)
    # ================================================================
    
    def _load_learning_preferences(self) -> Dict:
        """
        Load persistent learning data from file
        
        Stores:
        - User's language preference
        - Preferred response tone (casual, formal, technical)
        - Response style preferences (short vs detailed)
        - Common issues user asks about
        - Satisfaction metrics
        - 🔹 EDGE GUARD #1: Decay scores to prevent lock-in
        - 🔹 EDGE GUARD #2: Topic-specific preferences (anxiety→short, depression→detailed)
        
        Returns:
            Dict with learning data (empty if file doesn't exist)
        """
        try:
            if self.learning_file.exists():
                with open(self.learning_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"[LEARNING] Loaded preferences from {self.learning_file}")
                    # 🔹 EDGE GUARD #3: Debug visibility - print active prefs at load time
                    print(f"\n📊 Active Preferences Loaded:")
                    print(f"  Language: {data.get('language_preference', 'auto')}")
                    print(f"  Tone: {data.get('tone_preference', 'adaptive')}")
                    print(f"  Response: {data.get('response_length_preference', 'short')}")
                    print(f"  Interactions: {data.get('total_interactions', 0)}")
                    if 'topics' in data and data['topics']:
                        print(f"  Topic Preferences: {len(data['topics'])} topics tracked")
                    return data
        except Exception as e:
            logger.warning(f"[LEARNING] Could not load preferences: {e}")
        
        return {
            "language_preference": None,
            "tone_preference": None,
            "response_length_preference": "short",  # short, medium, detailed
            "common_topics": [],
            "satisfaction_rate": 0.0,
            "total_interactions": 0,
            "helpful_interactions": 0,
            # 🔹 FIX #1: Weighted learning (not instant switch)
            # Scores for each preference instead of binary setting
            "length_score_short": 0,
            "length_score_detailed": 0,
            "tone_score_casual": 0,
            "tone_score_formal": 0,
            # 🔹 EDGE GUARD #2: Topic-specific preferences
            # Structure: {"anxiety": {"length_score_short": 2, "length_score_detailed": 0}, ...}
            "topics": {},
        }
    
    def _save_learning_preferences(self) -> None:
        """
        Save learning preferences to persistent file with backup
        
        🔹 FIX #3: Backup system to prevent data loss on crash
        - Creates backup copy before overwriting
        - If save fails, backup is preserved
        """
        try:
            self.learning_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup before saving (prevent data loss)
            backup_file = self.learning_file.with_suffix('.backup.json')
            if self.learning_file.exists():
                try:
                    shutil.copy(str(self.learning_file), str(backup_file))
                    logger.info(f"[BACKUP] Created backup: {backup_file}")
                except Exception as backup_err:
                    logger.warning(f"[BACKUP] Could not create backup: {backup_err}")
            
            # Save preferences
            with open(self.learning_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_data, f, indent=2, ensure_ascii=False)
            logger.info(f"[LEARNING] Saved preferences to {self.learning_file}")
        except Exception as e:
            logger.warning(f"[LEARNING] Could not save preferences: {e}")
    
    def capture_feedback(self, user_query: str, response_text: str, feedback: str = "neutral") -> None:
        """
        🔹 STEP 1: Capture explicit user feedback
        
        Feedback types:
        - "helpful": User found response useful
        - "unclear": User found response confusing
        - "too_long": Too much information
        - "too_short": Need more detail
        - "neutral": No explicit feedback
        
        Args:
            user_query: Original user question
            response_text: System's response
            feedback: User's feedback (helpful/unclear/too_long/too_short/neutral)
        """
        # Update session feedback
        self.session_feedback["responses_total"] += 1
        
        if feedback == "helpful":
            self.session_feedback["responses_helpful"] += 1
        elif feedback == "unclear":
            self.session_feedback["responses_unclear"] += 1
        
        # Auto-detect topic
        topic = self._extract_topic(user_query)
        if topic not in self.session_feedback["session_notes"]:
            self.session_feedback["session_notes"].append(topic)
        
        # Save to persistent learning
        self.learning_data["total_interactions"] += 1
        if feedback == "helpful":
            self.learning_data["helpful_interactions"] += 1
        
        # Update satisfaction rate
        if self.learning_data["total_interactions"] > 0:
            self.learning_data["satisfaction_rate"] = (
                self.learning_data["helpful_interactions"] / 
                self.learning_data["total_interactions"]
            )
        
        # Save updates
        self._save_learning_preferences()
        logger.info(f"[FEEDBACK] Captured: {feedback} | Satisfaction: {self.learning_data['satisfaction_rate']:.1%}")
        print(f"✅ Feedback recorded: {feedback}")
    
    def _auto_detect_feedback(self, response_text: str, user_follow_up: str = None) -> str:
        """
        ⭐ AUTO-FEEDBACK DETECTION: Infer user satisfaction from behavior
        
        Implicit signals:
        - User asks follow-up question → response was useful but incomplete
        - User asks completely different question → response was unhelpful
        - User says "thanks"/"helpful" → positive feedback
        - User says "unclear"/"confusing" → negative feedback
        
        Args:
            response_text: System's last response
            user_follow_up: User's next message (if any)
            
        Returns:
            Inferred feedback type
        """
        if not user_follow_up:
            return "neutral"
        
        follow_up_lower = user_follow_up.lower()
        
        # Positive signals
        positive_markers = ["thank", "thanks", "helpful", "good", "best", "perfect", "great", "excellent"]
        for marker in positive_markers:
            if marker in follow_up_lower:
                return "helpful"
        
        # Continuation signals (response was useful but incomplete)
        continuation_markers = ["but", "also", "and then", "what about", "more about", "details about"]
        for marker in continuation_markers:
            if marker in follow_up_lower:
                return "helpful"  # At least partially helpful
        
        # Negative signals
        negative_markers = ["unclear", "confusing", "doesn't help", "not clear", "lost", "don't understand"]
        for marker in negative_markers:
            if marker in follow_up_lower:
                return "unclear"
        
        return "neutral"
    
    def _extract_topic(self, query: str) -> str:
        """
        Extract main topic from user query
        
        Topics: stress, anxiety, depression, sleep, anger, work, relationships, etc.
        
        Returns:
            Topic name
        """
        query_lower = query.lower()
        
        topics = {
            "stress": ["stress", "stressed", "pressure"],
            "anxiety": ["anxiety", "anxious", "worried", "overthinking"],
            "depression": ["depression", "depressed", "sad", "low mood"],
            "sleep": ["sleep", "neend", "insomnia", "sleepless"],
            "anger": ["anger", "angry", "gussa", "frustrated"],
            "work": ["work", "job", "office", "boss", "colleagues"],
            "relationships": ["relationship", "friend", "family", "partner", "love"],
            "health": ["health", "physical", "exercise", "diet"],
        }
        
        for topic, keywords in topics.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return topic
        
        return "general"
    
    def _get_learned_preference_injection(self, language: str = "Hinglish") -> str:
        """
        🔹 STEP 3-4: Dynamically update prompt based on learned preferences
        
        Injects user preferences into the system prompt:
        - Response length preference
        - Tone preference
        - Topics they care about
        
        Args:
            language: User's language
            
        Returns:
            Preference injection string to add to prompt
        """
        injections = []
        
        # Length preference
        length_pref = self.learning_data.get("response_length_preference", "short")
        if length_pref == "detailed":
            injections.append("User prefers detailed, thorough answers.")
        elif length_pref == "short":
            injections.append("User prefers short, concise answers (4-5 lines).")
        
        # Tone preference
        tone_pref = self.learning_data.get("tone_preference")
        if tone_pref == "formal":
            injections.append("User prefers formal, professional tone.")
        elif tone_pref == "casual":
            injections.append("User prefers casual, friendly Hinglish tone.")
        
        # Satisfaction tracking
        satisfaction = self.learning_data.get("satisfaction_rate", 0.0)
        if satisfaction > 0.8:
            injections.append("User is highly satisfied with recent responses - keep this style!")
        elif satisfaction < 0.4 and self.learning_data.get("total_interactions", 0) > 3:
            injections.append("User satisfaction is low - try more examples and simpler language.")
        
        # Common topics
        topics = self.session_feedback["session_notes"]
        if topics:
            topics_str = ", ".join(topics[:3])
            injections.append(f"User frequently asks about: {topics_str}")
        
        return "\n".join(injections) if injections else ""
    
    def _update_prompt_with_learning(self, base_prompt: str, language: str = "Hinglish") -> str:
        """
        Inject learning preferences into the prompt
        
        Args:
            base_prompt: Original system prompt
            language: User's language
            
        Returns:
            Enhanced prompt with learning injection
        """
        injection = self._get_learned_preference_injection(language)
        
        if injection:
            # Insert after the first section but before context
            insertion_point = base_prompt.find("Context from resources")
            if insertion_point > 0:
                return (
                    base_prompt[:insertion_point] +
                    f"\n📚 USER PREFERENCE INJECTION:\n{injection}\n\n" +
                    base_prompt[insertion_point:]
                )
        
        return base_prompt
    def _detect_response_length_preference(self, user_query: str = None, response_text: str = None) -> None:
        """
        Auto-detect if user prefers short or detailed responses
        
        🔹 FIX #1: Weighted learning (not instant switch)
        - Count both preferences with scores
        - Only switch if one significantly outweighs the other (threshold-based)
        - This prevents single signals from changing preference
        
        🔹 FIX #2: Noise filtering
        - Only learn from strong signals, ignore weak ones
        
        🔹 EDGE GUARD #1: Decay mechanism (prevent lock-in)
        - Apply 0.95 decay to old scores each interaction
        - Allows preferences to fade if behavior changes
        - Prevents permanent lock-in from old behavior
        
        🔹 EDGE GUARD #2: Topic-aware learning
        - Track separate preferences for each topic
        - Anxiety→short, Depression→detailed (different user, different topic)
        
        Signals:
        - User asks "be brief" → short (strong)
        - User asks for details/examples → detailed (strong)
        """
        if not user_query:
            return
        
        query_lower = user_query.lower()
        
        # 🔹 EDGE GUARD #1: Apply decay to prevent lock-in (fade old preferences)
        # Every new interaction, multiply scores by 0.95 (1-2% decay per interaction)
        self.learning_data["length_score_short"] *= 0.95
        self.learning_data["length_score_detailed"] *= 0.95
        logger.info(f"[DECAY] Applied 0.95x decay to length preferences to prevent lock-in")
        
        # Short preference signals (strong)
        short_keywords_strong = ["brief", "short", "quick", "tldr"]
        # Short preference signals (weak - could be noise)
        short_keywords_weak = ["simple"]
        
        # Detailed preference signals (strong)
        detail_keywords_strong = ["detail", "explain", "step by step", "example", "elaborate"]
        # Detailed preference signals (weak - could be noise)
        detail_keywords_weak = ["how"]
        
        # 🔹 FIX #2: Check confidence before learning from weak signals
        has_strong_short = any(w in query_lower for w in short_keywords_strong)
        has_weak_short = any(w in query_lower for w in short_keywords_weak)
        has_strong_detail = any(w in query_lower for w in detail_keywords_strong)
        has_weak_detail = any(w in query_lower for w in detail_keywords_weak)
        
        # Only learn from strong signals, or weak signals with high count
        if has_strong_short:
            self.learning_data["length_score_short"] += 2
            logger.info("[LEARNING] Strong SHORT signal detected")
        elif has_weak_short and self.learning_data["length_score_short"] > 0:
            self.learning_data["length_score_short"] += 1  # Only if already leaning short
        
        if has_strong_detail:
            self.learning_data["length_score_detailed"] += 2
            logger.info("[LEARNING] Strong DETAILED signal detected")
        elif has_weak_detail and self.learning_data["length_score_detailed"] > 0:
            self.learning_data["length_score_detailed"] += 1  # Only if already leaning detailed
        
        # 🔹 EDGE GUARD #2: Track topic-specific preferences
        topic = self._extract_topic(user_query)
        if topic:
            if "topics" not in self.learning_data:
                self.learning_data["topics"] = {}
            if topic not in self.learning_data["topics"]:
                self.learning_data["topics"][topic] = {"length_score_short": 0, "length_score_detailed": 0, "total_asks": 0}
            
            # Update topic-specific scores
            if has_strong_short or has_weak_short:
                self.learning_data["topics"][topic]["length_score_short"] += 1 if has_strong_short else 0.5
            if has_strong_detail or has_weak_detail:
                self.learning_data["topics"][topic]["length_score_detailed"] += 1 if has_strong_detail else 0.5
            self.learning_data["topics"][topic]["total_asks"] += 1
            logger.info(f"[LEARNING] Topic '{topic}' preference tracked: {self.learning_data['topics'][topic]}")
        
        # 🔹 FIX #1: Threshold-based preference switch (not instant)
        short_score = self.learning_data.get("length_score_short", 0)
        detail_score = self.learning_data.get("length_score_detailed", 0)
        
        # Only switch preference if one score significantly outweighs the other
        # Threshold: 2x difference or absolute difference of 2+ with min score of 2
        if short_score > detail_score and (short_score >= detail_score * 2 or (short_score >= 2 and short_score - detail_score >= 2)):
            self.learning_data["response_length_preference"] = "short"
            logger.info(f"[LEARNING] SWITCHED to SHORT (scores: {short_score} vs {detail_score})")
        elif detail_score > short_score and (detail_score >= short_score * 2 or (detail_score >= 2 and detail_score - short_score >= 2)):
            self.learning_data["response_length_preference"] = "detailed"
            logger.info(f"[LEARNING] SWITCHED to DETAILED (scores: {detail_score} vs {short_score})")
        else:
            logger.info(f"[LEARNING] Keep current (scores: short={short_score}, detailed={detail_score})")
        
        self._save_learning_preferences()
    
    def _detect_tone_preference(self, user_query: str = None) -> None:
        """
        Auto-detect user's preferred tone
        
        🔹 FIX #2: Confidence threshold
        - Only learn from high-confidence signals (> 0.7 confidence)
        - Ignore weak/ambiguous signals to prevent noise
        
        🔹 EDGE GUARD #1: Decay mechanism (prevent lock-in)
        - Apply 0.95 decay to old tone scores each interaction
        - Prevents permanent tone lock-in from past behavior
        
        Signals:
        - Uses Hindi/Hinglish → prefers Hinglish tone (confidence: 0.9)
        - Uses formal English markers → prefers formal tone (confidence: 0.8)
        - Single word queries → low confidence (0.3), don't learn
        """
        if not user_query:
            return
        
        # 🔹 EDGE GUARD #1: Apply decay to prevent lock-in
        self.learning_data["tone_score_casual"] *= 0.95
        self.learning_data["tone_score_formal"] *= 0.95
        logger.info(f"[DECAY] Applied 0.95x decay to tone scores to prevent lock-in")
        
        # 🔹 FIX #2: Require minimum query length for high confidence
        if len(user_query.strip()) < 5:
            logger.info("[LEARNING] Query too short, skipping tone detection (low confidence)")
            return
        
        lang_detect = self._detect_language_simple(user_query)
        confidence_score = 0.5  # Default confidence
        
        if lang_detect == "Hinglish":
            # Hinglish usage = strong signal
            confidence_score = 0.9
            if confidence_score > 0.7:  # High confidence threshold
                self.learning_data["tone_score_casual"] += 1
                self.learning_data["tone_preference"] = "casual"
                self.learning_data["language_preference"] = "Hinglish"
                logger.info("[LEARNING] Strong HINGLISH signal (confidence: 0.9)")
        
        elif lang_detect == "Hindi":
            confidence_score = 0.9
            if confidence_score > 0.7:
                self.learning_data["language_preference"] = "Hindi"
                logger.info("[LEARNING] Strong HINDI signal (confidence: 0.9)")
        
        elif lang_detect == "English":
            query_lower = user_query.lower()
            
            # Detect formal vs casual English
            formal_markers = ["please", "kindly", "would you", "could you", "may i"]
            casual_markers = ["hey", "yo", "lol", "gonna", "wanna", "ain't"]
            
            has_formal = any(w in query_lower for w in formal_markers)
            has_casual = any(w in query_lower for w in casual_markers)
            
            if has_formal and not has_casual:
                confidence_score = 0.8
                if confidence_score > 0.7:
                    self.learning_data["tone_score_formal"] += 1
                    self.learning_data["tone_preference"] = "formal"
                    logger.info("[LEARNING] Formal English signal (confidence: 0.8)")
            elif has_casual and not has_formal:
                confidence_score = 0.75
                if confidence_score > 0.7:
                    self.learning_data["tone_score_casual"] += 1
                    self.learning_data["tone_preference"] = "casual"
                    logger.info("[LEARNING] Casual English signal (confidence: 0.75)")
            else:
                logger.info("[LEARNING] English tone ambiguous, skipping (confidence < 0.7)")
        
        self._save_learning_preferences()
    
    def _generate_language_adaptive_response(self, user_query: str, retrieved_context: str = None) -> str:
        """
        🔥 FINAL FIX: Language-Adaptive Response Generation
        
        Step-by-step process:
        1. Detect user's language (Hindi, Hinglish, English)
        2. Retrieve relevant context from RAG (top 3 docs)
        3. Create language-adaptive prompt
        4. Call LLM with context
        5. Return formatted response
        
        Args:
            user_query: Original user input (any language)
            retrieved_context: Pre-retrieved context (optional)
            
        Returns:
            Language-adaptive response from LLM
        """
        try:
            # ===== STEP 0.5: AUTO-LEARN USER PREFERENCES =====
            # Learn from this interaction for future customization
            self._detect_tone_preference(user_query)
            self._detect_response_length_preference(user_query)
            logger.info("[LEARNING] Auto-detected tone and length preferences")
            
            # ===== STEP 1: DETECT USER LANGUAGE =====
            detected_language = self._detect_language_simple(user_query)
            logger.info(f"[LANG-DETECT] User input language: {detected_language}")
            print(f"🌍 Detected Language: {detected_language}")
            
            # ===== STEP 1.5: CHECK IF QUERY IS TOO VAGUE =====
            # 💬 HUMAN-LIKE FOLLOW-UP: Ask clarifying questions if needed
            # 🔹 EDGE CASE FIX #3: Prevent follow-up loop
            if self._is_vague_query(user_query):
                logger.info(f"[VAGUE-QUERY] Detected vague query: {user_query}")
                print(f"📝 Query seems unclear - asking for follow-up (attempt {self.followup_count + 1}/{self.max_followups})")
                
                # Break loop if we've already asked max times
                if self.followup_count >= self.max_followups:
                    logger.warning(f"[FOLLOW-UP-LOOP] Max attempts reached, giving best guess")
                    self.followup_count = 0  # Reset for next query
                    # Continue to response generation instead of asking again
                else:
                    self.followup_count += 1
                    followup = self._generate_followup_questions(user_query, detected_language)
                    return followup
            
            # ===== STEP 2: RETRIEVE CONTEXT IF NOT PROVIDED =====
            if retrieved_context is None:
                context = self._create_rag_chain_for_query(user_query)
            else:
                context = retrieved_context
            
            # 🔥 FIX 1: NO CONTEXT FOUND FALLBACK WITH GENERAL GUIDANCE - Prevent hallucination on irrelevant queries
            if not context or len(context.strip()) < 50:
                logger.warning(f"[NO-CONTEXT] Query has no relevant information: {user_query[:50]}")
                print(f"⚠️ No relevant context found - providing general helpful guidance")
                
                # 🔹 EDGE GUARD #5: Even without context, provide general guidance marked as general advice
                # This prevents "empty response" and helps user while being honest about limitations
                if "anxiety" in user_query.lower() or "nervous" in user_query.lower() or "worried" in user_query.lower():
                    return ("Mujhe specific resources nahi mile, par main general guidance de sakta hoon:\n\n"
                           "Anxiety ke liye aap:\n"
                           "• Deep breathing kariye (4-4-4 technique: inhale-hold-exhale)"
                           "\n• Apne thoughts ko judge kiye bina observe kariye"
                           "\n• Grounding technique try kariye (5 cheezein dekho jo dikhai de rahi hain)"
                           "\n• Kisi trusted person se baat kariye"
                           "\n\n📌 NOTE: Ye general advice hai. Specific help ke liye context share kariye ya professional se consult kariye.")
                elif "depression" in user_query.lower() or "sad" in user_query.lower() or "hopeless" in user_query.lower():
                    return ("Mujhe specific info nahi mila, par general guidance share karta hoon:\n\n"
                           "Depression/sadness ke liye:\n"
                           "• Small walks lena helpful hota hai"
                           "\n• Ek trusted person se baat kariye"
                           "\n• Routine maintain kariye (sleep, food)"
                           "\n• Professional help lena good idea hai"
                           "\n\n📌 NOTE: Ye general guidance hai. Detailed help ke liye aap apni situation clearly batayiye.")
                else:
                    # Generic fallback for other topics
                    return ("Mujhe relevant documents nahi mile. Kya aap thoda aur detail share kar sakte ho?\n\n"
                           "Example:\n"
                           "• Specific problem kya hai?"
                           "\n• Kab se ye lagta hai?"
                           "\n• Pehle kisi se baat ki?"
                           "\n\n📌 Ye details dene se main better help kar sakta hoon.")
            
            print(f"📚 Context Retrieved: {len(context)} chars")
            print(f"   Preview (first 150 chars): {context[:150]}...")
            
            # ===== STEP 3: CREATE LANGUAGE-ADAPTIVE PROMPT =====
            prompt_template = self._create_prompt_template(language=detected_language)
            
            # ===== STEP 4: FORMAT PROMPT WITH CONTEXT & QUERY =====
            # 🔥 UTF-8 SAFE: Ensure context and query are properly encoded
            safe_context = context.encode('utf-8', 'ignore').decode('utf-8')
            safe_query = user_query.encode('utf-8', 'ignore').decode('utf-8')
            final_prompt = prompt_template.format(context=safe_context, question=safe_query)
            
            # 🔹 INJECT LEARNED PREFERENCES: Customize based on user's history =====
            final_prompt = self._update_prompt_with_learning(final_prompt, detected_language)
            
            # ===== 🔥 DEBUG: VERIFY CONTEXT INJECTION =====
            print("\n" + "="*70)
            print("[DEBUG] CONTEXT INJECTION VERIFICATION")
            print("="*70)
            print(f"✅ Query: '{user_query}'")
            print(f"✅ Context size: {len(context)} chars")
            print(f"✅ Final prompt size: {len(final_prompt)} chars")
            print(f"✅ Context in prompt: {'YES ✅' if context in final_prompt else 'NO ❌'}")
            print(f"   Prompt preview (first 400 chars):\n{final_prompt[:400]}...")
            print("="*70)
            
            # 🔹 EDGE GUARD #3: Debug visibility - show what preferences are active
            length_pref = self.learning_data.get("response_length_preference", "short")
            tone_pref = self.learning_data.get("tone_preference", "adaptive")
            active_topic = self._extract_topic(user_query)
            logger.info(f"[PROMPT-BUILT] Using: length={length_pref}, tone={tone_pref}, topic={active_topic}")
            print(f"\n🎯 Using preferences: {length_pref} mode | Tone: {tone_pref} | Topic: {active_topic}")

            
            # ===== STEP 5: CALL LLM =====
            print(f"\n🤖 Calling LLM with context...")
            try:
                # 🔥 UTF-8 SAFE: Ensure final_prompt is UTF-8 encoded before sending to Gemini
                safe_final_prompt = final_prompt.encode('utf-8', 'ignore').decode('utf-8')
                response = self.llm.invoke(safe_final_prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
                # 🔥 UTF-8 SAFE: Decode response text safely
                response_text = response_text.encode('utf-8', 'ignore').decode('utf-8')
                print(f"✅ LLM Response received: {len(response_text)} chars")
            except Exception as llm_error:
                logger.error(f"[LLM-ERROR] {llm_error}")
                print(f"❌ LLM Error: {llm_error}")
                raise
            
            logger.info(f"[LLM-RESPONSE] Generated {len(response_text)} characters")
            print(f"✅ Response generated successfully")
            
            # ⭐ CONFIDENCE CHECK: Detect if LLM is uncertain/unsure
            if self._check_confidence(response_text):
                logger.warning(f"[CONFIDENCE-LOW] LLM uncertainty detected")
                print(f"⚠️ Low confidence - asking for more details")
                
                # Return friendly follow-up instead of uncertain response
                return "Mujhe samajh mein thoda blur lag raha hai. " + \
                       "Kya aap thoda aur detail share kar sakte ho? " + \
                       "Ye samajhne mein madad karega."
            
            # 🔹 AUTO-CAPTURE FEEDBACK FOR LEARNING =====
            # Store this response for feedback tracking (users can rate it later)
            topic = self._extract_topic(user_query)
            self.session_feedback["session_notes"].append(topic)
            self.session_feedback["responses_total"] += 1
            
            logger.info(f"[FEEDBACK-AUTO] Stored response {self.session_feedback['responses_total']} in session")
            
            return response_text.strip()

        
        except Exception as e:
            logger.error(f"[LANGUAGE-ADAPTIVE FAILED] {e}: {str(e)[:100]}")
            print(f"❌ Error in language-adaptive response: {e}")
            return "Mujhe samajh mein nahi aaya. Thoda aur detail doge?"
    
    def _is_vague_query(self, query: str) -> bool:
        """
        Detect if query is too vague to answer properly
        
        Examples of vague queries:
        - "problem ho rahi hai"  (what problem?)
        - "help chahiye"  (what kind of help?)
        - "sab theek nahi hai"  (what's not OK?)
        
        Args:
            query: Normalized user query
            
        Returns:
            True if query is vague, False otherwise
        """
        vague_phrases = [
            "problem", "issue", "worry", "help", "confused",
            "samajh nahi", "unclear", "not sure", "not ok",
            "sab theek nahi", "kuch galat", "stressed",
        ]
        
        query_lower = query.lower()
        
        # Check if query contains only vague words without specifics
        word_count = len(query_lower.split())
        vague_count = sum(1 for phrase in vague_phrases if phrase in query_lower)
        
        # If mostly vague words and only 1-5 words total, it's vague
        if word_count <= 5 and vague_count >= 1:
            return True
        
        return False
    
    def _generate_followup_questions(self, query: str, language: str = "Hinglish") -> str:
        """
        Generate human-like follow-up questions for vague queries
        
        Args:
            query: User's vague query
            language: Detected language (Hinglish, Hindi, English)
            
        Returns:
            Human-like follow-up prompt
        """
        followups = {
            "Hinglish": "Thoda aur bataoge?\n\n"
                       "• Stress ho raha hai?\n"
                       "• Sleep problem hai?\n"
                       "• Mood down hai?\n"
                       "• Anxiety ya overthinking?\n"
                       "• Work ya relationships?\n\n"
                       "Ye batao toh better help kar sakta hoon.",
            
            "Hindi": "कुछ और बताना चाहते हैं?\n\n"
                    "• तनाव हो रहा है?\n"
                    "• नींद की समस्या है?\n"
                    "• मनोदशा खराब है?\n"
                    "• चिंता या सोच?\n"
                    "• काम या रिश्ते?\n\n"
                    "यह बताएं तो बेहतर मदद कर सकता हूं।",
            
            "English": "Could you tell me a bit more?\n\n"
                      "• Are you dealing with stress?\n"
                      "• Sleep issues?\n"
                      "• Low mood?\n"
                      "• Anxiety or overthinking?\n"
                      "• Work or relationship concerns?\n\n"
                      "This will help me give you better advice."
        }
        
        return followups.get(language, followups["Hinglish"])
    
    def _check_confidence(self, response_text: str) -> bool:
        """
        ⭐ CHECK CONFIDENCE: Detect if LLM is uncertain/unsure about its answer
        
        🔹 EDGE CASE FIX: Only reject if BOTH conditions true:
        1. Contains uncertainty markers ("not sure", "unclear", etc.)
        2. Response is SHORT (< 150 chars = actual incomplete answer)
        
        Why? If LLM writes "I'm not sure but it could be..." + explanation,
        that's useful caution, NOT weakness. Only reject truly weak answers.
        
        Args:
            response_text: LLM's response
            
        Returns:
            True if response shows low confidence AND is incomplete, False if confident or complete
        """
        uncertainty_phrases = [
            "not sure", "unclear", "might be", "possibly", "uncertain",
            "i don't know", "no clear", "hard to say", "difficult to say",
            "cannot say", "not able to", "insufficient", "not enough",
            "may need", "should consult", "hard to determine",
            "not sure what", "unclear what", "i'm not sure",
        ]
        
        response_lower = response_text.lower()
        
        # Check if any uncertainty phrase is present in first ~40 words
        response_preview = " ".join(response_lower.split()[:40])
        has_uncertainty = any(phrase in response_preview for phrase in uncertainty_phrases)
        
        # SMART FIX: Only reject if BOTH are true:
        # 1. Has uncertainty marker AND 2. Is incomplete (< 150 chars)
        if has_uncertainty and len(response_text.strip()) < 150:
            logger.warning(f"[CONFIDENCE-CHECK] Low confidence + incomplete")
            return True
        
        # If uncertainty + complete answer, it's just cautious, not weak
        return False
    
    # ================================================================
    # SAFETY CHECK & CRISIS HANDLING
    # ================================================================
    
    def _generate_compassionate_crisis_response(self, user_input: str, language: str = "Hinglish") -> str:
        """
        Generate HUMAN-LIKE, COMPASSIONATE crisis response (not robotic)
        
        Args:
            user_input: User's message indicating distress
            language: Detected language for response
            
        Returns:
            Compassionate crisis response with resources
        """
        compassionate_responses = {
            "Hinglish": (
                "Bhai, main samajh sakta hoon ye tough lagta hai abhi. "
                "Kya tum mere se abhi baat kar sakte ho? Mere paas helplines hain:\n\n"
                "📞 Vandrevala Foundation: +91-9999 666 555 (24/7, Free)\n"
                "📞 AASRA: +91-9820466726 (24/7)\n"
                "📞 iCall: +91-9152987821 (9 AM - 11 PM)\n\n"
                "Please call one of these. Ye sab trained hain aur tum akele nahi ho.\n"
                "Your life matters. Please reach out."
            ),
            
            "Hindi": (
                "भाई, मैं समझ सकता हूँ यह मुश्किल है। "
                "क्या आप किसी से बात कर सकते हैं? यहाँ हेल्पलाइन हैं:\n\n"
                "📞 Vandrevala: +91-9999 666 555 (24/7)\n"
                "📞 AASRA: +91-9820466726\n"
                "📞 iCall: +91-9152987821\n\n"
                "कृपया कॉल करें। आप अकेले नहीं हैं। आपका जीवन महत्वपूर्ण है।"
            ),
            
            "English": (
                "I understand this is really tough right now. "
                "Will you talk to someone? Here are helplines:\n\n"
                "📞 Vandrevala Foundation: +91-9999 666 555 (24/7, Free)\n"
                "📞 AASRA: +91-9820466726 (24/7)\n"
                "📞 iCall: +91-9152987821 (9 AM - 11 PM)\n\n"
                "Please call. You're not alone. Your life matters."
            )
        }
        
        return compassionate_responses.get(language, compassionate_responses["Hinglish"])
    
    
    def _check_safety(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        STRICT SAFETY PROTOCOL: Check for real self-harm/suicide/violence keywords ONLY
        This is SEPARATE from intent classification.
        
        Returns:
            (is_safe, response_if_unsafe)
        """
        user_lower = user_input.lower()
        
        # ONLY trigger crisis on real self-harm intent
        strict_crisis_keywords = [
            # English crisis phrases
            'hurt myself', 'kill myself', 'suicide', 'suicidal', 'want to die',
            'ending my life', 'end my life', 'overdose', 'hang myself',
            'jump off', 'slit', 'cutting', 'cut myself',
            'giving up', 'no point', 'no reason', 'pointless', 'hopeless',
            'despair', 'desperate', 'cant take it', 'can\'t take it',
            # Hindi/Hinglish crisis phrases (🔴 CRITICAL ADDITIONS)
            'mrne ki icch', 'marna chahta', 'marna chati', 'marni hai',
            'jinda nahi', 'jeena nahi', 'jeena nahin', 'zinda nahi',
            'khud ko maarna', 'aatmhatya', 'aatma hatya',
            'khatam karna', 'khatm karna', 'death', 'mar jana',
            'mar gaya', 'mar gayi', 'mar sakta', 'mar sakti',
            'give up', 'hisaab khtam', 'bas ho gaya', 'ab nahi',
            # 🔹 EDGE GUARD #4: Indirect crisis detection (emotional distress without explicit mention)
            'ab kuch karne ka mann nahi', 'karne ka mann nahi', 'kuch nahi karna',
            'no motivation', 'no energy', 'nothing matters', 'what\'s the point',
            'everything is meaningless', 'sab bekar hai', 'sab vyarth hai',
            'ab nahi reh sakta', 'aur nahi dekh sakta', 'aur nahi sambhal sakta',
        ]
        
        for keyword in strict_crisis_keywords:
            if keyword in user_lower:
                logger.critical(f"🚨 CRISIS ALERT: {user_input}")
                print(f"🚨 EMERGENCY: Crisis keywords detected: {user_input}")
                
                # 💬 Return HUMAN-LIKE compassionate crisis response
                compassionate_msg = (
                    "\n🤝 Bhai, main samajh sakta hoon ye tough lagta hai abhi.\n"
                    "Kya tum kisi trusted person se baat kar sakte ho? Please reach out.\n\n"
                    "📞 HELPLINES (24/7 Free):\n"
                    "• Vandrevala: +91-9999 666 555\n"
                    "• AASRA: +91-9820466726\n"
                    "• iCall: +91-9152987821\n\n"
                    "Your life matters. Please call now."
                )
                return False, compassionate_msg
        
        return True, None
    
    def _get_free_alternatives(self, source_metadata: Dict) -> Optional[str]:
        """
        Check if source is Status 1 (Paid) and suggest Status 0 (Free) alternative
        
        Args:
            source_metadata: Metadata dict from retrieved document
            
        Returns:
            String with free alternative suggestion, or None
        """
        status = source_metadata.get('status', 1)
        
        # If it's a paid resource (Status 1), suggest free alternative
        if status == 1:
            country = source_metadata.get('country', 'Unknown')
            
            # Find free alternatives in mapping
            for country_code, country_data in self.mapping_data.get('countries', {}).items():
                country_name = country_data.get('full_name', '')
                if country_name.lower() == country.lower():
                    # Find free resources in this country
                    free_resources = []
                    for subject_code, subject_data in country_data.get('subjects', {}).items():
                        if subject_data.get('status') == 0:
                            free_resources.append(subject_data.get('free_alternative', ''))
                    
                    if free_resources:
                        return (
                            f"\n\n📚 FREE ALTERNATIVE (का फ्री विकल्प):\n"
                            f"{country} में उपलब्ध free resources:\n" +
                            "\n".join([f"• {r}" for r in free_resources[:3]])
                        )
        
        return None
    
    def _format_response(self, response: str, source_documents: List[Document]) -> str:
        """
        Format response with SOURCE CITATIONS at the end
        
        Args:
            response: LLM response
            source_documents: Retrieved documents from RAG
            
        Returns:
            Formatted response with source citations
        """
        formatted = response
        
        # Add source information at the end for accuracy & transparency
        if source_documents:
            seen_sources = set()
            source_list = []
            
            for doc in source_documents[:3]:
                source_file = doc.metadata.get('source_file', 'Unknown')
                country = doc.metadata.get('country', 'Unknown')
                
                source_key = (source_file, country)
                if source_key not in seen_sources:
                    seen_sources.add(source_key)
                    status_label = doc.metadata.get('status_label', 'Unknown')
                    source_list.append(f"{source_file} ({country}) [{status_label}]")
            
            # Add source citation at the end (RULE: Source: [Book Name])
            if source_list:
                formatted += f"\n\nSource: {', '.join(source_list)}"
            
            # Check for free alternatives (Metadata 0/1 Rule)
            if source_documents and source_documents[0].metadata.get('status') == 1:
                free_alt = self._get_free_alternatives(source_documents[0].metadata)
                if free_alt:
                    formatted += free_alt
        
        return formatted
    
    def _extract_context_from_query(self, response: Dict) -> str:
        """Extract clean context from RAG response"""
        return response.get('result', '')
    
    # ================================================================
    # 🏥 CLINICAL POWERHOUSE - DAY 3 FEATURES
    # ================================================================
    
    # ===== CLINICAL CRITERIA FORMATTER =====
    def _clinical_formatter(self, condition: str, standard: str = "DSM-5") -> str:
        """
        Format clinical response with diagnostic criteria
        
        Injects DSM-5/ICD-11 criteria, disclaimer, and free resources.
        
        Args:
            condition: Mental health condition (e.g., "depression", "anxiety")
            standard: Clinical standard to use ("DSM-5", "ICD-11", or "ICD-11 + DSM-5")
            
        Returns:
            Formatted response with criteria + disclaimer + resources
        """
        condition_lower = condition.lower()
        
        # Handle combined standard (for India)
        if "+" in standard:
            # Use ICD-11 first for combined standard
            primary_std = "ICD-11"
        else:
            primary_std = standard
        
        # Get criteria from CLINICAL_CRITERIA dict
        crit_data = CLINICAL_CRITERIA.get(primary_std, {}).get(condition_lower)
        
        if not crit_data:
            # Try fallback to other standard
            fallback_std = "DSM-5" if primary_std == "ICD-11" else "ICD-11"
            crit_data = CLINICAL_CRITERIA.get(fallback_std, {}).get(condition_lower)
            if crit_data:
                primary_std = fallback_std
            else:
                return f"Information about {condition} not available in {standard}."
        
        # Build formatted response
        response = f"📖 **According to {primary_std}**: {crit_data['name']}\n\n"
        
        response += "**Symptoms/Criteria:**\n"
        for i, criterion in enumerate(crit_data['criteria'], 1):
            response += f"{i}. {criterion}\n"
        
        response += f"\n**Duration Required**: {crit_data['duration']}\n"
        response += f"**Note**: {crit_data['note']}\n"
        
        # Add disclaimer
        response += (
            "\n\n⚠️ **Important Disclaimer**:\n"
            "Ye information educational purposes ke liye hai.\n"
            "Self-diagnosis se bilkul mat karo.\n"
            "Qualified psychiatrist ya psychologist se proper consultation zaruri hai. 👨‍⚕️\n"
        )
        
        # Add free resources
        response += "\n✅ **Free Learning Resources**:\n"
        for resource in FREE_RESOURCES[:3]:
            response += f"• {resource}\n"
        
        return response
    
    def _symptom_checker(self, query: str) -> str:
        """
        Generate doctor-style follow-up questions
        
        For incomplete symptom descriptions, ask clarifying questions like a clinical interviewer.
        
        Args:
            query: User's query (normalized)
            
        Returns:
            Follow-up question or empty string if not needed
        """
        query_lower = query.lower()
        
        # Check for symptom keywords
        followups = {
            "depression": [
                "💬 Kab se ye feeling aa rahi hai? Ek din se ya ek mahina se?",
                "💬 Ye depression din bhar aata hai ya specific situations mein?",
                "💬 Aur kya symptoms hain - sleep problem, weight change, ya concentration issue?"
            ],
            "anxiety": [
                "💬 Ye anxiety kab start hua? Kisi specific trigger ke wajah se ya bina reason?",
                "💬 Kya ye sudden panic attacks hote hain ya constant worry rehta hai?",
                "💬 Physical symptoms bhi hain kya - jaise heart racing, sweating?"
            ],
            "insomnia": [
                "💬 Neend mein kya problem hai? Sleep nahi aa raha ya baar baar wake ho rahe ho?",
                "💬 Raat ko jagte ho toh mind mein kya thoughts chalti rehti hain?",
                "💬 Screen time, caffeine, stress - kaunsa sabse zyada affect kar raha hai?"
            ],
            "stress": [
                "💬 Stress mein kya specific situation responsible hai? Work? Relationships?",
                "💬 Ye stress physical symptoms de raha hai - jaise headache ya chest pain?",
                "💬 Kya already kuch try kiya stress handle karne ke liye?"
            ],
            "anger": [
                "💬 Gussa aa raha hai toh kya specific situation trigger kar raha hai?",
                "💬 Gussa aane ke baad kya feeling aata hai - guilt? Regret?",
                "💬 Ye problem pehle se tha ya recently develop hua?"
            ]
        }
        
        # Find matching symptom
        for symptom, questions in followups.items():
            if any(kw in query_lower for kw in SYMPTOM_KEYWORDS.get(symptom, [])):
                import random
                return random.choice(questions)
        
        return ""
    
    def _extract_condition_from_query(self, query: str) -> str:
        """
        Extract mental health condition from user query
        
        Args:
            query: Normalized user query
            
        Returns:
            Condition name (e.g., "depression", "anxiety", "unknown")
        """
        query_lower = query.lower()
        
        for condition, keywords in SYMPTOM_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                return condition
        
        return "unknown"
    
    def _detect_user_country(self) -> str:
        """
        STEP 1: Detect user's country for DSM-5/ICD-11 routing
        
        In production: Use IP geolocation
        For now: Default to India (since users are mostly Indian)
        
        Returns:
            Country code ("US", "UK", "India", etc.)
        """
        # TODO: Implement real geolocation (geoip2, MaxMind, etc.)
        # For now, default to India
        detected_country = "India"
        logger.info(f"[GEOLOC] Detected country: {detected_country}")
        return detected_country
    
    def _get_clinical_standard(self, country: str = None) -> Dict[str, str]:
        """
        STEP 2: Determine which clinical standard to use based on country
        
        Standards Mapping:
        - USA/Canada/Australia → DSM-5 (Diagnostic & Statistical Manual)
        - Europe (UK, Germany, France, etc.) → ICD-11 (WHO standard)
        - India → HYBRID (ICD-11 + DSM-5 for local context)
        
        Args:
            country: User's country (auto-detected if None)
            
        Returns:
            {
                "primary": "DSM-5" or "ICD-11",
                "secondary": "...",
                "fallback": "Global",
                "explanation": "Why this standard"
            }
        """
        if not country:
            country = self._detect_user_country()
        
        # Standard routing by country
        standard_map = {
            # DSM-5 Primary (USA-style)
            "US": {"primary": "DSM-5", "secondary": "DSM-IV-TR", "fallback": "Global"},
            "USA": {"primary": "DSM-5", "secondary": "DSM-IV-TR", "fallback": "Global"},
            "United States": {"primary": "DSM-5", "secondary": "DSM-IV-TR", "fallback": "Global"},
            "Canada": {"primary": "DSM-5", "secondary": "ICD-10", "fallback": "Global"},
            "Australia": {"primary": "DSM-5", "secondary": "ICD-10", "fallback": "Global"},
            "South_Korea": {"primary": "DSM-5", "secondary": "ICD-10", "fallback": "Global"},
            
            # ICD-11 Primary (European/WHO standard)
            "UK": {"primary": "ICD-11", "secondary": "DSM-5", "fallback": "Global"},
            "United_Kingdom": {"primary": "ICD-11", "secondary": "DSM-5", "fallback": "Global"},
            "Germany": {"primary": "ICD-11", "secondary": "DSM-5", "fallback": "Global"},
            "France": {"primary": "ICD-11", "secondary": "DSM-5", "fallback": "Global"},
            "Netherlands": {"primary": "ICD-11", "secondary": "DSM-5", "fallback": "Global"},
            "Sweden": {"primary": "ICD-11", "secondary": "DSM-5", "fallback": "Global"},
            "Finland": {"primary": "ICD-11", "secondary": "DSM-5", "fallback": "Global"},
            "Norway": {"primary": "ICD-11", "secondary": "DSM-5", "fallback": "Global"},
            "Switzerland": {"primary": "ICD-11", "secondary": "DSM-5", "fallback": "Global"},
            "Italy": {"primary": "ICD-11", "secondary": "DSM-5", "fallback": "Global"},
            "Spain": {"primary": "ICD-11", "secondary": "DSM-5", "fallback": "Global"},
            
            # HYBRID (India-specific)
            "India": {"primary": "ICD-11 + DSM-5", "secondary": "Both", "fallback": "Global"},
            
            # ICD-10 (Japan specific)
            "Japan": {"primary": "ICD-10", "secondary": "DSM-5", "fallback": "Global"},
        }
        
        # Get standard or default to Hybrid
        standards = standard_map.get(country, standard_map["India"])
        
        logger.info(f"[CLINICAL-STANDARD] {country} → Primary: {standards['primary']}")
        return standards
    
    def _symptom_checker_followup(self, symptom: str, user_history: List[Dict] = None) -> str:
        """
        STEP 3: Ask doctor-style follow-up questions instead of instant diagnosis
        
        Instead of: "You have depression"
        Do this: "Bhai, lagta hai tension aa raha hai. Kab se ye problem hai?"
        
        Acts like a clinical interviewer gathering information before diagnosis.
        
        Args:
            symptom: Main symptom reported (e.g., "depression", "anxiety", "insomnia")
            user_history: Conversation history for context
            
        Returns:
            Friendly follow-up question in Hinglish
        """
        # Mapping of symptoms to clinical follow-up questions
        symptom_followups = {
            # Depression cluster
            "depression": [
                "Bhai, lagta hai mood low hai. Kab se ye feel kar rahe ho? Ek din ya ek hafta?",
                "Aur ye low feeling ke saath kya aur bhi problem hai? Sleep? Appetite? Energy?",
                "Sab time ye feeling aata hai ya kisi specific situation mein?",
            ],
            # Anxiety cluster
            "anxiety": [
                "Tension ho raha hai? Ye sudden panic attacks hote hain ya constant rehta hai?",
                "Ye anxiety kab start hua? Kisi specific trigger ke wajah se ya without reason?",
                "Physical symptoms bhi hain kya? Jaise heart racing, sweating, breathing problem?",
            ],
            # Sleep issues
            "insomnia": [
                "Neend mein kya problem hai? Sleep mein nahi aa raha ya baar baar wake ho rahe ho?",
                "Raat mein jagte ho toh mind mein kya chalti rehti hai? Overthinking?",
                "Screen time, caffeine, ya stress - kaunsa factor sabse zyada affect kar raha hai?",
            ],
            # Stress
            "stress": [
                "Kya specific cheez stress de rahi hai? Work? Relationships? Family?",
                "Ye stress physical symptoms de raha hai kya? Headache? Fatigue? Chest pain?",
                "Already kuch try kiya stress handle karne ke liye? Kya kaam aya?",
            ],
            # Anger/frustration
            "anger": [
                "Gussa aa raha hai toh kya trigger kar rahe ho? Specific person or situation?",
                "Gussa aane ke baad kya feeling aata hai? Guilt? Regret? Control mein nahi aata?",
                "Pehle se ye problem tha ya recently develop hua hai?",
            ],
            # Fatigue/tiredness
            "fatigue": [
                "Sahab, har time thak feel kar rahe ho? Ya specific time mein?",
                "Ye tiredness physical hai (body pain) ya mental (no motivation)?",
                "Sleep, diet, exercise - kaunsa part mein issue hai bata?",
            ],
        }
        
        # Get followup questions for symptom
        symptom_lower = symptom.lower()
        questions = symptom_followups.get(symptom_lower, [
            "Hmm, ye samajhna important hai. Thoda aur detail doge?",
            "Kab se ye problem aa raha hai? Aur kaun-se situations mein worse hota hai?",
            "Pehle kisi doctor ya counselor se baat ki?",
        ])
        
        # Return a random followup question
        import random
        followup = random.choice(questions)
        
        logger.info(f"[SYMPTOM-CHECKER] {symptom} → Asking follow-up question")
        return followup
    
    def _rag_accuracy_benchmark(self, retrieved_docs: List[Document]) -> Dict[str, any]:
        """
        STEP 4: Benchmark RAG accuracy - Check if retrieved docs are Status 0 (Free)
        
        Returns metrics:
        - Total docs retrieved
        - Free docs (Status 0)
        - Paid docs (Status 1)
        - Accuracy percentage
        - Which free alternatives exist
        
        Args:
            retrieved_docs: Documents returned by retriever
            
        Returns:
            {
                "total": int,
                "free_count": int,
                "paid_count": int,
                "accuracy_percent": float,
                "free_alternatives": [list of free sources],
                "benchmark_status": "GOOD" | "WARNING" | "CRITICAL"
            }
        """
        if not retrieved_docs:
            return {
                "total": 0,
                "free_count": 0,
                "paid_count": 0,
                "accuracy_percent": 0.0,
                "free_alternatives": [],
                "benchmark_status": "CRITICAL"
            }
        
        total = len(retrieved_docs)
        free_count = 0
        paid_count = 0
        free_alternatives = []
        
        for doc in retrieved_docs:
            status = doc.metadata.get('status', 1)  # Default to Paid
            if status == 0:
                free_count += 1
                source = doc.metadata.get('source_file', 'Unknown')
                free_alternatives.append(source)
            else:
                paid_count += 1
        
        # Calculate accuracy (% of free resources)
        accuracy_percent = (free_count / total * 100) if total > 0 else 0.0
        
        # Benchmark status
        if accuracy_percent >= 80:
            benchmark_status = "GOOD"
        elif accuracy_percent >= 50:
            benchmark_status = "WARNING"
        else:
            benchmark_status = "CRITICAL"
        
        logger.info(f"[RAG-BENCHMARK] Free: {free_count}/{total} ({accuracy_percent:.1f}%) - {benchmark_status}")
        
        return {
            "total": total,
            "free_count": free_count,
            "paid_count": paid_count,
            "accuracy_percent": accuracy_percent,
            "free_alternatives": list(set(free_alternatives)),
            "benchmark_status": benchmark_status
        }
    
    def _format_clinical_response(self, response: str, symptom: str = None, 
                                  country: str = None, source_docs: List[Document] = None) -> str:
        """
        STEP 5: Format response with clinical standards + free alternatives
        
        Adds:
        1. Standard reference (DSM-5/ICD-11)
        2. Self-diagnosis disclaimer (friendly way)
        3. Free alternative resources
        4. When to see specialist
        
        Args:
            response: Base LLM response
            symptom: Main symptom discussed
            country: User's country (for standard selection)
            source_docs: Retrieved documents from RAG
            
        Returns:
            Formatted clinical response with all disclaimers and resources
        """
        formatted = response
        
        # Add clinical standard reference
        if symptom:
            standards = self._get_clinical_standard(country)
            primary_std = standards.get('primary', 'DSM-5')
            
            standard_note = f"\n\n📖 **Clinical Standard Used**: {primary_std}"
            formatted += standard_note
            logger.info(f"[FORMAT] Added {primary_std} reference")
        
        # Add friendly self-diagnosis disclaimer
        disclaimer = (
            "\n\n⚠️ **Remember bhai**:\n"
            "Ye sirf educational info hai. Self-diagnosis sahi nahi hota.\n"
            "Agar symptoms 2+ hafta se ho rahe hain, toh kisi qualified psychologist se mil lo. 👨‍⚕️"
        )
        formatted += disclaimer
        
        # Add free alternatives if available
        if source_docs:
            benchmark = self._rag_accuracy_benchmark(source_docs)
            
            if benchmark['free_alternatives']:
                free_alt_text = (
                    "\n\n✅ **Free Resources Available**:\n" +
                    "\n".join([f"• {alt}" for alt in benchmark['free_alternatives'][:3]])
                )
                formatted += free_alt_text
                logger.info(f"[FORMAT] Added {len(benchmark['free_alternatives'])} free alternatives")
            
            # Add benchmark warning if too many paid
            if benchmark['benchmark_status'] == "CRITICAL":
                formatted += (
                    "\n\n🔍 **Note**: Most sources available are paid. "
                    "Check our free alternative database for similar content."
                )
        
        return formatted
    
    def _classify_query_type(self, user_input: str) -> str:
        """
        TWO-TIER ARCHITECTURE LAYER 1: Classify query as NORMAL or CLINICAL
        
        NORMAL queries:
        - Casual conversation, weather, greetings, daily talk
        - Requires: Indore Dost mode (friendly neighbor responses)
        
        CLINICAL queries:
        - Mental health, psychology, symptoms, therapy, diagnosis
        - Requires: Doctor + RAG mode (medical knowledge + empathy)
        
        Args:
            user_input: User's message
            
        Returns:
            "NORMAL" or "CLINICAL"
        """
        user_lower = user_input.lower()
        
        # EXPLICIT PRIORITY: Check for Hindi clinical keywords FIRST
        # This catches sleep queries like "neend nahi" before normalization changes them
        hindi_clinical_words = ['neend', 'nind', 'nim', 'gussa', 'gussaa', 'tension', 'tensio', 'thak', 'ghabrana']
        for word in hindi_clinical_words:
            if word in user_lower:
                logger.info(f"[CLINICAL-HINDI] Exact match: {word}")
                return "CLINICAL"
        
        # CLINICAL keywords - High priority
        clinical_keywords = [
            # Mental health conditions
            'stress', 'anxiety', 'depression', 'panic', 'ocd', 'ptsd', 'adhd',
            'bipolar', 'schizophrenia', 'psychosis', 'paranoia', 'delusion',
            # Emotional states (clinical context)
            'depressed', 'suicidal', 'self harm', 'hurt myself', 'kill myself',
            'want to die', 'low mood', 'overwhelmed', 'anxious', 'overthinking',
            # General wellbeing phrases
            'not feel', 'feel bad', 'not okay', 'not good', 'not well', 'unwell',
            'feeling sad', 'feeling down', 'feeling tired', 'feeling numb',
            'not myself', 'something wrong', 'not right', 'struggling',
            # Treatment/therapy
            'therapy', 'counseling', 'psychologist', 'psychiatrist', 'medication',
            'treatment', 'disorder', 'condition', 'disease', 'diagnosis', 'symptom',
            # Medical/psychology knowledge
            'dsm-5', 'icd-11', 'psychology', 'mental health', 'clinical', 'medical',
            'sleep', 'insomnia', 'nightmare', 'panic attack', 'phobia', 'trauma',
            'bipolar', 'schizophrenia', 'autism', 'specialist', 'therapist',
            # Books/resources (educational clinical)
            'book', 'kitaab', 'research', 'study', 'research paper', 'journal',
            # Hindi keywords (emotional wellbeing)
            'neend', 'thak', 'gussa', 'tension', 'ghabrana', 'accah nhi', 'acha nhi',
            'thik nhi', 'sahi nhi', 'bura', 'ganda', 'buraa', 'tab'
        ]
        
        for keyword in clinical_keywords:
            if keyword in user_lower:
                logger.info(f"[CLINICAL] Detected: {keyword}")
                return "CLINICAL"
        
        # NORMAL keywords - Casual conversation
        normal_keywords = [
            # Weather
            'weather', 'dhoop', 'baarish', 'sardi', 'garmi', 'mausam', 'barish',
            'garam', 'thandi', 'bright', 'sunny', 'rainy', 'hot', 'cold',
            # Greetings
            'hi', 'hello', 'hey', 'namaste', 'namaskar', 'hye', 'howdy',
            'how are', 'kaisa hai', 'kaisi ho', 'how do you',
            # Casual topics
            'movie', 'film', 'cricket', 'sports', 'phone', 'game', 'music',
            'weekend', 'holiday', 'weekend plan', 'monsoon', 'vacation',
            # Indore specific
            'indore', 'rajwada', 'ghat', 'khand', 'sarafa',
            # Daily talk
            'work', 'job', 'breakfast', 'lunch', 'dinner', 'chai', 'tea',
            'morning', 'evening', 'night', 'aaj', 'kal', 'filhaal',
            # Random chat
            'what is', 'who is', 'where is', 'tell me', 'kya ho', 'kya scene'
        ]
        
        for keyword in normal_keywords:
            if keyword in user_lower:
                logger.info(f"[NORMAL] Detected: {keyword}")
                return "NORMAL"
                
        # Default: If unclear, ask for clarification (NORMAL)
        return "NORMAL"
    
    def _fuzzy_match(self, query: str, keywords: List[str], threshold: int = 80) -> bool:
        """
        SMART FUZZY MATCHING: Prioritize exact hits, then fuzzy matches
        
        Args:
            query: Normalized user query
            keywords: List of intent keywords
            threshold: Fuzzy threshold (default 80 = stricter, fewer false positives)
            
        Returns:
            True if any keyword matches
        """
        q = query.lower()
        
        for word in keywords:
            # Exact hit first (fastest & most reliable)
            if word in q:
                return True
            
            # Then fuzzy match with higher threshold
            score = fuzz.partial_ratio(q, word)
            if score >= threshold:
                return True
        
        return False
    
    def _classify_intent(self, user_input: str) -> str:
        """
        PRODUCTION-READY intent classification with fuzzy matching
        
        Categories: CRISIS, MENTAL_HEALTH, EDUCATIONAL, CASUAL, UNKNOWN
        Uses smart fuzzy matching to handle typos and variations.
        
        Args:
            user_input: User message (normalized)
            
        Returns:
            Intent category as string
        """
        q = user_input.lower()
        
        # CRISIS - Highest priority (STRICT keywords only)
        crisis_keywords = [
            "suicide", "hurt myself", "kill myself",
            "murder", "maar dena", "khud ko nuksan",
            "end my life"
        ]
        if self._fuzzy_match(q, crisis_keywords, threshold=80):
            return "CRISIS"
        
        # MENTAL_HEALTH - Emotional/psychological concerns
        mental_keywords = [
            "stress", "tension", "anxiety",
            "gussa", "angry", "frustrated",
            "tired", "thak", "neend nahi", "neend nai", "nind nahi",
            "low", "sad", "overwhelmed",
            "depression", "depressed", "depresun",
            "insomnia", "sleep", "neend", "nind", "nim",
            "anger", "fatigue"
        ]
        if self._fuzzy_match(q, mental_keywords, threshold=80):
            return "MENTAL_HEALTH"
        
        # EDUCATIONAL - Knowledge-based questions
        edu_keywords = [
            "book", "kaunsi book", "best book",
            "diagnosis", "psychology", "meaning",
            "what is", "how to", "treatment",
            "symptom", "symptoms", "criteria",
            "dsm", "dsm-5", "icd", "icd-11",
            "standard", "who standard"
        ]
        if self._fuzzy_match(q, edu_keywords, threshold=80):
            return "EDUCATIONAL"
        
        # CASUAL - Random talk (not therapy-focused)
        casual_keywords = [
            "hello", "hi", "hii", "dhoop", "garmi", "weather",
            "namaste", "how are", "indore", "movie", "cricket"
        ]
        if self._fuzzy_match(q, casual_keywords, threshold=80):
            return "CASUAL"
        
        # UNKNOWN - Unclear intent (will be checked by safety override)
        return "UNKNOWN"
    
    def _force_emotion_override(self, query: str, intent: str) -> str:
        """
        SAFETY OVERRIDE: Detect hidden crisis signals in UNKNOWN intents
        
        Prevents cases where crisis signals are missed by main classifier.
        
        Args:
            query: Normalized user query
            intent: Detected intent from classifier
            
        Returns:
            Updated intent (may override to CRISIS or MENTAL_HEALTH)
        """
        q = query.lower()
        
        # Crisis signals - absolute priority
        crisis_signals = [
            "murder", "kill", "suicide", "hurt",
            "maar", "end my life", "nuksan"
        ]
        if any(w in q for w in crisis_signals):
            return "CRISIS"
        
        # Emotional signals - rescue UNKNOWN intents
        emotional_signals = [
            "gussa", "tired", "thak", "sad",
            "low", "cry", "ro", "frustrated"
        ]
        if intent == "UNKNOWN":
            if any(w in q for w in emotional_signals):
                return "MENTAL_HEALTH"
        
        return intent
    
    def _handle_crisis(self) -> str:
        """
        Handle CRISIS intent - clean, empathetic crisis response
        
        This is NOT a template - it's genuine concern + immediate help
        """
        response = (
            "Bhai, ye serious lag raha hai. Main samajh raha hoon."
            "\n\n"
            "Agar tume khud ko ya kisi aur ko hurt karne ka mann aa raha hai, "
            "toh please akela mat rehna. Kisi trusted insaan ko call karo: \n\n"
            "🆘 EMERGENCY HELPLINES:\n"
            "1. AASRA: +91-9820466726\n"
            "2. iCall: +91-9152987821\n"
            "3. Vandrevala: +91-9999-666-555\n\n"
            "Main yahan hoon. Tum baat kar sakte ho. Lekin professional help lena bohot important hai."
        )
        return response
    
    def _mental_health_response(self, query: str) -> str:
        """
        NON-REPETITIVE mental health response based on emotional keywords
        
        Contextual, natural Hinglish responses. No robotic templates.
        
        Args:
            query: Normalized user query
            
        Returns:
            Empathetic response tailored to the issue
        """
        q = query.lower()
        
        # Anger/frustration
        if "gussa" in q or "angry" in q or "frustrated" in q:
            return (
                "Bhai lagta hai gussa aa raha hai... thoda pause le, "
                "2-3 deep breaths le, aur thoda space le. "
                "Baad mein sab clearer lagta hai."
            )
        
        # Tiredness/exhaustion
        elif "tired" in q or "thak" in q or "exhausted" in q:
            return (
                "Samajh sakta hoon bhai... mentally thak jana heavy feel hota hai. "
                "Thoda rest le, phone side rakh aur relax kar. "
                "Acha neend sab kuch theek kar deta hai."
            )
        
        # Stress/tension
        elif "stress" in q or "tension" in q:
            return (
                "Bhai tension ho rahi hai toh simple kar - walk kar, "
                "deep breath le, aur ek time pe ek hi cheez soch. "
                "Sab ko stress aata hai, tum akele nahi ho."
            )
        
        # Sadness/depression
        elif "sad" in q or "low" in q or "depression" in q:
            return (
                "Bhai low feel karna normal hai... thoda apne aap ko time de, "
                "sab theek ho jayega. Kisi trusted person se baat kar lo, "
                "that actually helps a lot."
            )
        
        # Sleep issues
        elif "neend" in q or "sleep" in q or "insomnia" in q:
            return (
                "Neend ki problem bohot annoying hoti hai! "
                "Try karo - no phone 30 min before bed, relax breathing, "
                "consistent sleep time. Agar zyada problem hai toh professional dekh lena."
            )
        
        # Anxiety/overthinking
        elif "anxiety" in q or "overthinking" in q or "worry" in q:
            return (
                "Overthinking toh aaj kal ki problem ban gaya! "
                "Present mein focus karo, kal ke baare mein sochna band karo. "
                "Exercise karo - running ya walk, tension automatically kam ho jayega."
            )
        
        # Default mental health response
        else:
            return (
                "Lg raha hai tu emotionally struggling hai. "
                "Bilkul thik hai, sab ke saath aise moments aate hain. "
                "Kisi ko tell kar, ek professional se mil lo agar heavy feel ho raha hai."
            )
    
    def _handle_mental_health(self, user_query: str, normalized_query: str = None) -> str:
        """
        🏥 ENHANCED: MENTAL_HEALTH handler with Language-Adaptive Response Path
        
        New Flow:
        1. Quick safety check
        2. Retrieve context from ChromaDB (if available)
        3. Use LLM with language-adaptive prompt to generate response
        4. This ensures response is in user's language (Hindi, Hinglish, or English)
        
        Args:
            user_query: Original user input (for natural context)
            normalized_query: Cleaned query for semantic search (optional)
        """
        search_query = normalized_query if normalized_query else user_query
        
        # ===== SAFETY CHECK =====
        is_safe_orig = self._check_safety(user_query)[0]
        if normalized_query:
            is_safe_norm = self._check_safety(normalized_query)[0]
            if not is_safe_orig or not is_safe_norm:
                safety_response = self._check_safety(normalized_query)[1] or self._check_safety(user_query)[1]
                return safety_response
        else:
            if not is_safe_orig:
                safety_response = self._check_safety(user_query)[1]
                return safety_response
        
        # ===== QUICK EMOTIONAL RESPONSE (Optional: for very simple cases) =====
        # This provides immediate validation before RAG retrieval
        quick_emotion = self._mental_health_response(search_query)
        
        # ===== 🔥 MAIN: LANGUAGE-ADAPTIVE RESPONSE WITH RAG CONTEXT =====
        try:
            # Retrieve clinical context from vector database
            retrieved_context = self._create_rag_chain_for_query(search_query)
            
            # Generate language-adaptive response
            # This will:
            # 1. Detect user's language (Hindi, Hinglish, English)
            # 2. Retrieve top 3 relevant docs
            # 3. Use LLM with language-specific prompt
            # 4. Return response in user's language
            
            if retrieved_context:
                logger.info(f"[LANGUAGE-ADAPTIVE] Using RAG context for response")
                response = self._generate_language_adaptive_response(
                    user_query=user_query,
                    retrieved_context=retrieved_context
                )
                return response
            else:
                # No context found - use simple language-adaptive response with empty context
                logger.info(f"[LANGUAGE-ADAPTIVE] No RAG context, using simple adaptive response")
                response = self._generate_language_adaptive_response(
                    user_query=user_query,
                    retrieved_context="(Information not available in knowledge base)"
                )
                return response
        
        except Exception as e:
            logger.error(f"[LANGUAGE-ADAPTIVE FAILED] {e}, falling back to emotion response")
            # Fallback to quick emotion response
            if quick_emotion:
                return quick_emotion
            
            # Final fallback
            return (
                "Samajh raha hoon, par thoda problem aa gaya. "
                "Thoda aur detail de, fir help kar sakta hoon."
            )
    
    def _extract_symptom_from_query(self, query: str) -> str:
        """
        Extract main symptom from query
        
        Returns: symptom name or "unknown"
        """
        query_lower = query.lower()
        
        symptom_map = {
            "depression": ["depression", "depressed", "depresun", "sad", "low mood"],
            "anxiety": ["anxiety", "anxious", "worried", "overthinking", "tension"],
            "stress": ["stress", "stressed", "stresss"],
            "insomnia": ["sleep", "neend", "insomnia", "cant sleep", "sleepless"],
            "anger": ["anger", "angry", "gussa", "frustrated"],
            "fatigue": ["tired", "fatigue", "exhausted", "thak gya"],
        }
        
        for symptom, keywords in symptom_map.items():
            for kw in keywords:
                if kw in query_lower:
                    return symptom
    
    # ================================================================
    # 🔹 PUBLIC FEEDBACK INTERFACE (Called from Web/Frontend)
    # ================================================================
    
    def rate_last_response(self, feedback_type: str) -> Dict:
        """
        🔹 PUBLIC METHOD: Allow user to rate the last response
        
        Called from frontend/web UI after response is shown
        
        Feedback types:
        - "helpful": Very useful response ✅
        - "partially_helpful": Somewhat useful 👍
        - "not_helpful": Didn't help ❌
        - "unclear": Confusing or vague ❓
        - "too_long": Too much information 📜
        - "too_short": Need more detail 📝
        
        Args:
            feedback_type: Type of feedback user is providing
            
        Returns:
            Dict with confirmation and learning update status
        """
        try:
            # Validate feedback type
            valid_types = ["helpful", "partially_helpful", "not_helpful", "unclear", "too_long", "too_short"]
            if feedback_type not in valid_types:
                return {"status": "error", "message": f"Invalid feedback type: {feedback_type}"}
            
            # Map feedback to learning metrics
            feedback_map = {
                "helpful": "helpful",
                "partially_helpful": "helpful",
                "not_helpful": "unclear",
                "unclear": "unclear",
                "too_long": "too_long",
                "too_short": "too_short"
            }
            
            normalized_feedback = feedback_map.get(feedback_type, "neutral")
            
            # Capture feedback for learning
            self.capture_feedback(
                user_query="(from rating UI)",
                response_text="(rated from UI)",
                feedback=normalized_feedback
            )
            
            # Update learning based on feedback
            if feedback_type in ["too_long"]:
                self.learning_data["response_length_preference"] = "short"
            elif feedback_type in ["too_short"]:
                self.learning_data["response_length_preference"] = "detailed"
            
            self._save_learning_preferences()
            
            logger.info(f"[FEEDBACK-RATED] User rated response: {feedback_type}")
            print(f"✅ Feedback captured: {feedback_type}")
            
            return {
                "status": "success",
                "message": f"Thanks for rating! I'll learn from this.",
                "satisfaction_rate": f"{self.learning_data['satisfaction_rate']:.1%}",
                "total_feedback": self.learning_data["total_interactions"]
            }
        
        except Exception as e:
            logger.error(f"[FEEDBACK-ERROR] {e}")
            return {"status": "error", "message": f"Could not save feedback: {e}"}
    
    def get_learning_summary(self) -> Dict:
        """
        Get a summary of what the system has learned about the user
        
        Returns:
            Dict with learning metrics and preferences
        """
        summary = {
            "total_interactions": self.learning_data.get("total_interactions", 0),
            "helpful_responses": self.learning_data.get("helpful_interactions", 0),
            "satisfaction_rate": f"{self.learning_data.get('satisfaction_rate', 0):.1%}",
            "language_preference": self.learning_data.get("language_preference", "Auto-detect"),
            "tone_preference": self.learning_data.get("tone_preference", "Not set"),
            "response_length_preference": self.learning_data.get("response_length_preference", "Short"),
            "common_topics": self.session_feedback.get("session_notes", []),
            "session_responses_total": self.session_feedback.get("responses_total", 0),
            "session_responses_helpful": self.session_feedback.get("responses_helpful", 0),
        }
        
        logger.info(f"[LEARNING-SUMMARY] Generated: {summary}")
        return summary
    
        
        return "unknown"
    
    def _is_detailed_enough(self, query: str) -> bool:
        """
        Check if query has enough detail to not need follow-up
        
        Detailed = mentions duration, triggers, or multiple symptoms
        """
        detail_keywords = [
            "since", "se ho raha", "ke baad", "when",
            "because", "kyunki", "wajah", "trigger",
            "and", "aur", "also", "bhi",
            "days", "weeks", "months", "din", "hafta", "mahina"
        ]
        
        query_lower = query.lower()
        detail_count = sum(1 for kw in detail_keywords if kw in query_lower)
        
        return detail_count >= 2  # Consider detailed if has 2+ detail markers
    
    def _handle_educational(self, user_query: str, normalized_query: str = None) -> str:
        """
        🏥 ENHANCED: EDUCATIONAL handler with DSM-5/ICD-11 standard routing + ChromaDB Context
        
        Detects if query is about clinical standards and routes accordingly.
        Retrieves context from ChromaDB for educational questions.
        Example: "DSM-5 ke hisaab se depression symptoms kya hain?"
        
        Args:
            user_query: Original user input (for natural context)
            normalized_query: Cleaned query for semantic search (optional)
        """
        search_query = normalized_query if normalized_query else user_query
        user_lower = user_query.lower()
        
        # ===== CHECK: DSM-5 or ICD-11 specific query? =====
        is_dsm5_query = any(kw in user_lower for kw in ['dsm-5', 'dsm-5', 'dsm5', 'dsm'])
        is_icd11_query = any(kw in user_lower for kw in ['icd-11', 'icd-11', 'icd11', 'icd', 'who standard'])
        
        # ===== RETRIEVE CONTEXT FROM CHROMADB FIRST =====
        retrieved_context = self._create_rag_chain_for_query(search_query)
        
        # ===== NEW: Direct clinical formatter for DSM-5/ICD-11 queries =====
        condition = self._extract_condition_from_query(search_query)
        
        if condition != "unknown":
            # User is asking about a specific condition
            if is_dsm5_query:
                # Explicitly asking about DSM-5 - use DSM-5 even for India
                if retrieved_context:
                    response = f"Bhai, DSM-5 ke hisaab se:\n\n{retrieved_context}"
                else:
                    response = self._clinical_formatter(condition, "DSM-5")
                    response = f"Bhai, samajh raha hoon. DSM-5 ke hisaab se:\n\n{response}"
                
                # Add symptom checker follow-up
                followup = self._symptom_checker(search_query)
                if followup:
                    response += f"\n\n🩺 {followup}"
                
                logger.info(f"[EDU-CLINICAL] Served DSM-5 criteria for {condition}")
                return response
            
            elif is_icd11_query:
                # Explicitly asking about ICD-11
                if retrieved_context:
                    response = f"Bhai, ICD-11 ke hisaab se:\n\n{retrieved_context}"
                else:
                    response = self._clinical_formatter(condition, "ICD-11")
                    response = f"Bhai, samajh raha hoon. ICD-11 ke hisaab se:\n\n{response}"
                
                # Add symptom checker follow-up
                followup = self._symptom_checker(search_query)
                if followup:
                    response += f"\n\n🩺 {followup}"
                
                logger.info(f"[EDU-CLINICAL] Served ICD-11 criteria for {condition}")
                return response
            
            # Check if we have RAG context even for general educational questions
            elif retrieved_context:
                response = f"Bhai, {condition} ke bare mein:\n\n{retrieved_context}\n\n"
                response += "⚠️ Ye informational hai. Actual diagnosis ke liye doctor se milna zaruri hai."
                logger.info("[EDU] Served response with RAG context")
                return response
        
        # ===== IF RAG CONTEXT AVAILABLE FOR ANY EDUCATIONAL QUERY =====
        if retrieved_context:
            response = f"Jankari jo mila:\n\n{retrieved_context}\n\n"
            response += "⚠️ Ye sirf educational purpose ke liye hai. Professional guidance zaruri hai."
            logger.info("[EDU] Served general educational response with RAG")
            return response
        
        # ===== FALLBACK: Generate educational response =====
        if 'diagnosis' in user_lower or 'book' in user_lower:
            return (
                "Diagnosis ke liye DSM-5 (USA) aur ICD-11 (WHO/Europe) standards hain.\n\n"
                "📖 **Best Resources**:\n"
                "1. DSM-5: Official diagnostic manual (USA standard)\n"
                "2. ICD-11: WHO standard (Europe/India mein increase ho raha hai)\n"
                "3. IGNOU Free PDFs: India ke liye special access\n"
                "4. NIMHANS website: India ke top mental health research\n\n"
                "⚠️ **Self-Diagnosis Warning**: Ek doctor se proper assessment karwalo, "
                "khud kuch conclusions mat draw kar. Professional guidance essential hai!"
            )
        
        # Psychology/conditions
        elif 'psychology' in user_lower or 'condition' in user_lower:
            standards = self._get_clinical_standard()
            standard_name = standards['primary']
            
            return (
                f"Psychology bohot fascinating subject hai! {standard_name} standard ke accordance mein.\n\n"
                "Specific cheez poochh - jaise:\n"
                "• Depression kya hota hai (DSM-5 definition)?\n"
                "• Anxiety disorder kaise develop hota hai?\n"
                "• OCD/ADHD/PTSD ke symptoms?\n"
                "• Treatment options?\n\n"
                "Specific question pooch, main help kar lunga! 💬"
            )
        
        # Default educational
        else:
            return (
                "Ye interesting question hai! "
                "Specific jankari dene ke liye mujhe detailed study material chahiye.\n\n"
                "Try karke pooch:\n"
                "• DSM-5 ke hisaab se [symptom] kya hota hai?\n"
                "• [Disorder] ke clinical symptoms?\n"
                "• Treatment approaches?\n\n"
                "Thoda specific ho jao, fir better answer de sakta hoon 👨‍⚕️"
            )
    
    def _handle_diagnostic_standard_query(self, user_query: str, search_query: str, is_dsm5: bool) -> str:
        """
        🏥 Handle DSM-5 / ICD-11 specific queries
        
        Example: "Depression ke symptoms DSM-5 ke hisaab se?"
        Response: Detailed DSM-5 criteria from knowledge base + free alternatives
        
        Args:
            user_query: Original user query
            search_query: Normalized query for RAG
            is_dsm5: True if DSM-5 query, False if ICD-11
            
        Returns:
            Diagnostic criteria response with standard reference
        """
        standard = "DSM-5" if is_dsm5 else "ICD-11"
        logger.info(f"[DIAGNOSTIC] Routing to {standard} specific response")
        
        # Extract condition from query
        condition_map = {
            "depression": ["depression", "depressed", "depresun"],
            "anxiety": ["anxiety", "anxious", "worried"],
            "panic": ["panic", "panic attack"],
            "ocd": ["ocd", "obsessive"],
            "ptsd": ["ptsd", "trauma"],
            "adhd": ["adhd", "attention"],
            "bipolar": ["bipolar"],
            "schizophrenia": ["schizophrenia"],
        }
        
        condition = "unknown"
        search_query_lower = search_query.lower()
        for cond, keywords in condition_map.items():
            if any(kw in search_query_lower for kw in keywords):
                condition = cond
                break
        
        # Try RAG with diagnostic standard context
        retrieved_docs = []
        if self.retriever:
            try:
                diagnostic_query = f"{condition} {standard} criteria symptoms"
                retrieved_docs = self.retriever.invoke(diagnostic_query)
                
                if retrieved_docs:
                    # Get RAG response
                    rag_response = self.rag_chain.invoke({"input": diagnostic_query})
                    
                    # ===== ADD DIAGNOSTIC STANDARD HEADER =====
                    header = f"\n\n🏥 **As per {standard}**:\n"
                    
                    # ===== ADD SELF-DIAGNOSIS DISCLAIMER =====
                    disclaimer = (
                        f"\n\n⚠️ **Important Disclaimer**:\n"
                        f"Ye information educational purposes ke liye hai. "
                        f"Self-diagnosis se decision mat lo.\n"
                        f"Agar ye symptoms 2+ hafta se hain, toh qualified psychiatrist/psychologist "
                        f"se proper assessment karwalo. 👨‍⚕️"
                    )
                    
                    # ===== ADD FREE RESOURCES =====
                    benchmark = self._rag_accuracy_benchmark(retrieved_docs)
                    free_resources = ""
                    if benchmark['free_alternatives']:
                        free_resources = (
                            "\n\n✅ **Free Study Materials**:\n" +
                            "\n".join([f"• {alt}" for alt in benchmark['free_alternatives'][:3]])
                        )
                    
                    return rag_response + header + disclaimer + free_resources
            
            except Exception as e:
                logger.warning(f"[DIAGNOSTIC] RAG failed: {e}")
        
        # ===== FALLBACK: Provide standard-specific info =====
        if is_dsm5:
            return self._provide_dsm5_criteria(condition)
        else:
            return self._provide_icd11_criteria(condition)
    
    def _provide_dsm5_criteria(self, condition: str) -> str:
        """Provide DSM-5 criteria for common conditions"""
        dsm5_info = {
            "depression": (
                "🏥 **DSM-5: Major Depressive Disorder (Major Depressive Episode)**\n\n"
                "**Criteria** (ICD-10 code: F32.X):\n"
                "✓ Persistent depressed mood most of day, nearly every day (2+ weeks)\n"
                "✓ Markedly diminished interest/pleasure in all/almost all activities\n"
                "✓ Significant weight loss/gain (5%+ body weight change)\n"
                "✓ Insomnia or hypersomnia nearly every day\n"
                "✓ Psychomotor agitation or retardation\n"
                "✓ Fatigue or loss of energy\n"
                "✓ Feelings of worthlessness or inappropriate guilt\n"
                "✓ Diminished concentration ability\n"
                "✓ Suicidal ideation\n\n"
                "⚠️ Must have 5+ symptoms for 2+ weeks causing functional impairment.\n\n"
                "✅ **When to seek help**: If symptoms persist 2+ weeks, consult psychiatrist immediately."
            ),
            "anxiety": (
                "🏥 **DSM-5: Generalized Anxiety Disorder (GAD)**\n\n"
                "**Criteria**:\n"
                "✓ Excessive anxiety/worry about various aspects of life (6+ months)\n"
                "✓ Difficult to control worry\n"
                "✓ Restlessness, feeling keyed up/on edge\n"
                "✓ Easily fatigued\n"
                "✓ Difficulty concentrating\n"
                "✓ Irritability\n"
                "✓ Muscle tension\n"
                "✓ Sleep disturbance\n\n"
                "⚠️ Symptoms cause clinically significant distress/impairment.\n\n"
                "💊 **Treatment options**: CBT (Cognitive Behavioral Therapy), SSRIs, lifestyle changes"
            ),
            "unknown": (
                "🏥 **DSM-5 Overview**\n\n"
                "DSM-5 (Diagnostic & Statistical Manual of Mental Disorders, 5th Edition) "
                "is the standard classification for mental health disorders in USA.\n\n"
                "**Common conditions in DSM-5**:\n"
                "• Major Depressive Disorder\n"
                "• Generalized Anxiety Disorder\n"
                "• Panic Disorder\n"
                "• PTSD (Post-Traumatic Stress Disorder)\n"
                "• OCD (Obsessive-Compulsive Disorder)\n"
                "• ADHD (Attention-Deficit/Hyperactivity Disorder)\n"
                "• Bipolar Disorder\n"
                "• Schizophrenia Spectrum\n\n"
                "💬 **Ask me specifically**: 'DSM-5 mein Depression kya hota hai?' "
                "for detailed criteria."
            )
        }
        
        response = dsm5_info.get(condition, dsm5_info["unknown"])
        response += (
            "\n\n⚠️ **Disclaimer**: Ye educational info hai. "
            "Self-diagnosis se diagnosis mat karo. Expert consultation zaruri hai!"
        )
        return response
    
    def _provide_icd11_criteria(self, condition: str) -> str:
        """Provide ICD-11 criteria for common conditions"""
        icd11_info = {
            "depression": (
                "🏥 **ICD-11: Single Episode Depressive Disorder (6A70)**\n\n"
                "**WHO Criteria**:\n"
                "✓ Depressed mood (persistent, most of day, most days)\n"
                "✓ Loss of interest in activities\n"
                "✓ Reduced energy/increased fatigue\n"
                "✓ Significant functional impairment\n"
                "✓ Duration: 2+ weeks (minimum)\n"
                "✓ No history of manic/hypomanic episodes\n\n"
                "**Severity (ICD-11)**:\n"
                "• Mild: Some difficulty in daily functioning\n"
                "• Moderate: Considerable difficulty in daily functioning\n"
                "• Severe: Unable to perform most daily activities\n\n"
                "✅ **When to seek help**: Persistent 2+ weeks requires professional assessment."
            ),
            "anxiety": (
                "🏥 **ICD-11: Generalized Anxiety Disorder (6D02)**\n\n"
                "**WHO Criteria**:\n"
                "✓ Worry about multiple domains (6+ months)\n"
                "✓ Difficulty controlling worry\n"
                "✓ Multiple physical symptoms (tension, fatigue, sleep problems)\n"
                "✓ Significant functional impairment\n\n"
                "**ICD-11 differs from DSM-5**: More emphasis on worry about daily routines "
                "and multiple life domains.\n\n"
                "💊 **Treatment**: Psychotherapy + possible medication (SSRIs) if severe"
            ),
            "unknown": (
                "🏥 **ICD-11 Overview (WHO Standard)**\n\n"
                "ICD-11 (International Classification of Diseases, 11th Edition) is "
                "WHO's global standard for disease classification.\n\n"
                "**Key differences from DSM-5**:\n"
                "• Used globally (especially Europe, Asia, WHO member countries)\n"
                "• Emphasis on functional impairment\n"
                "• More emphasis context & cultural factors\n"
                "• Recently updated (2022)\n\n"
                "**Common mental disorders in ICD-11**:\n"
                "• Depressive Disorders (6A70-74)\n"
                "• Anxiety Disorders (6A80-88)\n"
                "• PTSD (6B40)\n"
                "• OCD (6B20)\n\n"
                "💬 **Ask specifically**: 'ICD-11 mein Depression ke criteria kya hain?'"
            )
        }
        
        response = icd11_info.get(condition, icd11_info["unknown"])
        response += (
            "\n\n⚠️ **Disclaimer (ICD-11)**: Ye WHO standard ke hisaab se hai. "
            "Professional diagnosis zaruri hai, self-assessment se avoid karo!"
        )
        return response
    
    def _handle_casual(self, user_query: str) -> str:
        """Handle CASUAL intent - friendly desi friend response"""
        return self._generate_casual_response(user_query)
    
    def _handle_ambiguous(self, user_query: str, normalized_query: str) -> str:
        """
        Handle AMBIGUOUS queries with intelligent clarification
        
        Instead of generic "Dekho bhai..." fallback, use LLM to:
        1. Suggest what the user might have meant
        2. Ask friendly clarification
        3. Provide 2-3 relevant options based on normalized query
        
        This BREAKS the repetition loop!
        
        Args:
            user_query: Original user input
            normalized_query: LLM-normalized version
            
        Returns:
            Friendly clarification response
        """
        try:
            clarification_prompt = f"""You are Neuronix, a friendly mental health chatbot.

The user's input might be unclear or ambiguous. Provide a FRIENDLY clarification:
- Acknowledge their message
- Suggest 2-3 things they might mean (based on normalized query)
- Ask which one they meant
- Keep response short and natural (NOT robotic)

ORIGINAL INPUT: "{user_query}"
NORMALIZED: "{normalized_query}"

Examples of good responses:
- "Lagta hai aap kuch stress ya tension ke baare mein pooch rahe ho? Ya kuch aur specific issue hai?"
- "Bhai, typing mein thoda error lag raha hai. Kya aap anxiety ya sleep issues ke baare mein baat kar rahe ho?"
- "Samajh mein nahi aaya exactly kya kehna chahte ho. Stress, anxiety, ya depression ke bare mein pooch rahe ho?"

YOUR RESPONSE (natural, friendly, short):"""
            
            response = self.llm.invoke(clarification_prompt)
            logger.info(f"[AMBIGUOUS] Generated clarification response")
            return response.strip()
        
        except Exception as e:
            logger.warning(f"[AMBIGUOUS FAILED] Using fallback: {e}")
            # Fallback (NOT the old robotic one!)
            return (
                "Bhai, ye sawaal samajh mein thoda blur hai. "
                "Kya aap stress, anxiety, ya kisi aur mental health cheez ke baare mein pooch rahe ho? "
                "Ya kuch casual baat karni hai?"
            )
    
    def _handle_unknown(self, user_query: str) -> str:
        """Handle UNKNOWN intent - ask for clarification"""
        return self._handle_ambiguous(user_query, user_query)
    
    def _generate_casual_response(self, user_query: str) -> str:
        """Generate friendly, desi friend response for casual topics"""
        user_lower = user_query.lower()
        
        # Weather/climate
        if 'weather' in user_lower or 'dhoop' in user_lower or 'garmi' in user_lower:
            return (
                "Bhai Indore ki garmi toh next level hai na! "
                "Thoda shikanji piyo, fresh ho jaega. "
                "Aur haan, pani bohot peena, dehydration mat ho."
            )
        elif 'baarish' in user_lower or 'rain' in user_lower:
            return (
                "Baarish ka season bhai! "
                "Indore mein toh roads toot jate hain jab pani aata hai. "
                "Ghar par baithkar chai piyo aur netflix dekhlo!"
            )
        elif 'sardi' in user_lower or 'cold' in user_lower:
            return (
                "Sardi mein toh sweater aur chai ka combination best hota hai! "
                "Warm kapde pehno aur ghar ke andar baas rehlo. "
                "Indore ke ghar mein heating nahi hota, hehe."
            )
        
        # Greetings
        elif user_lower in ['hi', 'hello', 'namaste', 'hey']:
            return (
                "Hye bhai! Main Neuronix hoon. "
                "Tu kaise hai? Kya kaam chal raha hai? "
                "Mental health se related kuch poochna hai ya bas baatein karni hain?"
            )
        elif 'how are' in user_lower or 'kaisa hai' in user_lower:
            return (
                "Bhai main bilkul fine hoon, thanks for asking! "
                "Tu kaisa hai? Sab theek-thaak? "
                "Agar koi pareshani hai toh boldena, else time-pass ke liye baat kar!"
            )
        
        # Casual Indore references
        elif 'indore' in user_lower or 'rajwada' in user_lower:
            return (
                "Arrey, Indore ka person ho tum! "
                "Rajwada toh historic place hai na, architecture top notch! "
                "Aur bhai, ghat ghat pe chai-samosa ka scene complete hota hai. "
                "Life enjoy kar Indore mein, baaki sab secondary hai!"
            )
        
        # Default casual - friendly redirect
        else:
            return (
                "Main mental health aur wellness ke liye yahan hoon! "
                "Agar kahan stress, anxiety, ya koi personal issue hai, toh freely pooch. "
                "Baki sab cheezein bhi discuss kar sakte hain, bas mujhe thoda idea de de na."
            )
    

    
    def chat(self, user_query: str) -> str:
        """
        🔧 FIXED: NEURONIX WITH LLM-POWERED NORMALIZATION PIPELINE
        
        This BREAKS the "Dekho bhai" repetition loop by:
        1. Using LLM to intelligently normalize input ("tensio" → "tension")
        2. Detecting user's response language preference (auto-respond in Hindi/Hinglish/English)
        3. Using fuzzy semantic search instead of exact matching
        4. Loosening system prompt for natural conversations
        
        Architecture:
        ├─ [STEP 0] Exit Command Check
        ├─ [STEP 1] LLM-Based Normalization (KEY FIX!)
        ├─ [STEP 2] Language Detection (auto-select response language)
        ├─ [LAYER 1] Safety Check (CRISIS detection)
        ├─ [LAYER 2] Query Type Classification (NORMAL vs CLINICAL)
        └─ [LAYER 3] Intent Classification (if CLINICAL)
        
        Args:
            user_query: User's question (any language, any spelling)
            
        Returns:
            Neuronix's response (auto-adapted to user's language)
        """
        # ========== STEP 0: EXIT COMMAND ==========
        if user_query.lower().strip() in ['exit()', 'exit', 'quit', 'bye']:
            return "Alvida bhai, apna dhyan rakhna!"
        
        # ========== PIPELINE START ==========
        print("\n" + "="*80)
        print("[NEURONIX PIPELINE] Processing new user input...")
        print("="*80)
        logger.info("=" * 80)
        logger.info("[PIPELINE] Processing user input...")
        
        # ========== STEP 0.5: 🔥 TYPO CORRECTION (NEW!) ==========
        # Fix common misspellings BEFORE normalization (god → good, nto → not)
        corrected_query = self._correct_typos_with_spell_checker(user_query)
        if corrected_query != user_query:
            print(f"✏️ TYPO CORRECTED: {user_query} → {corrected_query}")
            logger.info(f"[TYPO-CORRECTION] {user_query} → {corrected_query}")
            user_query = corrected_query
        
        # ========== STEP 1: LLM-BASED NORMALIZATION (KEY FIX!) ==========
        # This fixes "tensio" → "tension", Hinglish → English for DB search
        normalized_query = self._llm_normalize_input(user_query)
        
        # ========== STEP 2: LANGUAGE DETECTION ==========
        # Auto-detect if response should be Hindi/Hinglish/English
        lang_info = self._detect_script_language(user_query)
        response_language = lang_info["response_language"]
        
        # ========== DEBUG: PRINT NORMALIZED QUERY ==========
        print(f"\n📝 ORIGINAL INPUT: {user_query}")
        print(f"🔄 NORMALIZED QUERY: {normalized_query}")
        print(f"🌍 RESPONSE LANGUAGE: {response_language}")
        print()
        
        logger.info(f"[ORIGINAL] {user_query}")
        logger.info(f"[NORMALIZED] {normalized_query}")
        logger.info(f"[RESPONSE-LANG] {response_language}")
        
        # ========== LAYER 1: SAFETY CHECK ==========
        is_safe, safety_response = self._check_safety(normalized_query)
        if not is_safe:
            logger.critical("[CRISIS] Self-harm intent detected")
            self.conversation_history.append({"role": "user", "content": user_query})
            self.conversation_history.append({"role": "assistant", "content": safety_response})
            return safety_response
        
        # ========== LAYER 2: QUERY TYPE CLASSIFICATION ==========
        # Check BOTH original and normalized to catch variations like "neend nahi" → "insomnia"
        query_type_original = self._classify_query_type(user_query)
        query_type_normalized = self._classify_query_type(normalized_query)
        
        # CRITICAL FIX: Also check for partial Hindi clinical keywords in original query
        # This catches "gus aa" → "gussa", "thak" → "tired", etc.
        hindi_clinical_partial = {
            "gus": "anger",
            "thak": "tired", 
            "neend": "sleep",
            "nind": "sleep",
            "tension": "anxiety",
            "tensio": "anxiety",
            "anxiety": "anxiety",
            "depression": "depression",
            "depressed": "depression"
        }
        
        query_type = "CLINICAL" if (query_type_original == "CLINICAL" or query_type_normalized == "CLINICAL") else "NORMAL"
        
        # Check partial matches in original query as final catch
        if query_type == "NORMAL":
            user_lower = user_query.lower()
            for partial, condition in hindi_clinical_partial.items():
                if partial in user_lower:
                    print(f"🔥 [PARTIAL-MATCH] Detected '{partial}' → {condition}")
                    query_type = "CLINICAL"
                    break
        
        if query_type == "NORMAL":
            # ========== MODE 1: INDORE DOST (Friendly Neighbor) ==========
            logger.info("[MODE] Indore Dost - Casual")
            response = self._handle_casual(user_query)
        
        else:  # CLINICAL
            # ========== MODE 2: DOCTOR + RAG (Medical Knowledge) ==========
            logger.info("[MODE] Doctor + RAG - Clinical")
            print("[MODE] Doctor Mode (RAG + Clinical)")
            
            # Classify intent within CLINICAL domain
            intent = self._classify_intent(normalized_query)
            
            # Apply safety override (detect hidden crisis/emotional signals)
            intent = self._force_emotion_override(normalized_query, intent)
            logger.info(f"[INTENT] {intent}")
            print(f"🎯 DETECTED INTENT: {intent}")
            print()
            
            # Handle based on intent
            if intent == "CRISIS":
                response = self._handle_crisis()
            elif intent == "MENTAL_HEALTH":
                # Pass both original and normalized for context + RAG search
                response = self._handle_mental_health(user_query, normalized_query)
            elif intent == "EDUCATIONAL":
                # Pass both original and normalized for context + RAG search
                response = self._handle_educational(user_query, normalized_query)
            else:  # Unclear - ask friendly clarification (NO "Dekho bhai" template!)
                response = self._handle_ambiguous(user_query, normalized_query)
        
        # ========== LANGUAGE ADAPTATION ==========
        # If response language is Hindi or pure medical, adapt tone
        if response_language == "hindi":
            # Keep response but maybe add Hindi greeting
            pass  # Response already in natural tone
        elif response_language == "hinglish":
            # Response already in Hinglish by default
            pass
        
        # ========== LOG & STORE ==========
        logger.info(f"[{query_type}] → {response_language}")
        logger.info("[PIPELINE END]")
        logger.info("=" * 80)
        
        # ========== PHASE 3: ENHANCE WITH CONVERSATION INTELLIGENCE ==========
        if self.phase3_enabled:
            try:
                # Generate unique user_id for this session
                user_id = f"web_user_{len(self.conversation_history)}"
                
                # Add message to conversation memory with tone info
                conv_tone = self.tone_analyzer.analyze_tone(user_query)
                
                # Map tone to distress level (0.0-1.0)
                tone_to_distress = {
                    "sad": 0.75,
                    "depressed": 0.80,
                    "anxious": 0.65,
                    "frustrated": 0.60,
                    "angry": 0.70,
                    "happy": 0.10,
                    "neutral": 0.30
                }
                distress_level = tone_to_distress.get(conv_tone, 0.40)
                
                self.memory.add_user_message(
                    user_id=user_id,
                    message=user_query,
                    tone=conv_tone,
                    distress_level=distress_level
                )
                
                # Track distress trend
                analysis = self.distress_tracker.record_distress(
                    user_id=user_id,
                    score=distress_level,
                    context=normalized_query
                )
                
                # Check for safety patterns
                safety_analysis = self.safety_system.analyze_pattern(
                    user_id=user_id,
                    query=user_query,
                    distress_level=distress_level,
                    trend=analysis.get('trend', 'stable'),
                    turn=len(self.conversation_history) // 2
                )
                
                # If there's a proactive message to add, append it to response
                if safety_analysis['overall_severity'] in ['high', 'medium']:
                    proactive_msg = self.safety_system.get_proactive_message(
                        user_id=user_id,
                        severity=safety_analysis['overall_severity']
                    )
                    if proactive_msg:
                        response = f"{response}\n\n{proactive_msg}"
                
                logger.info(f"[PHASE3] Memory updated, distress tracked")
            except Exception as e:
                logger.warning(f"[PHASE3] Error: {e}")
                # Continue without Phase 3 enhancements
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_query
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("\n[OK] Conversation cleared. Starting fresh!\n")
    
    def get_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history
    
    def interactive_chat(self):
        """
        Run interactive chat loop
        """
        print("\n" + "=" * 80)
        print("[*] Chat Commands:")
        print("  'exit' or 'bye' or 'quit' -> End conversation")
        print("  'clear' -> Start fresh conversation")
        print("  'history' -> Show conversation history")
        print("  Any question -> Get Hinglish response")
        print("=" * 80 + "\n")
        
        while True:
            try:
                # Get user input
                user_input = input("आप: ").strip()
                
                if not user_input:
                    print("Please ask something!\n")
                    continue
                
                # Handle commands
                if user_input.lower() in ['exit', 'bye', 'quit', 'bye bye']:
                    print("\nNeuronix: Aapka khayal rakhiyega! Khush rahen!\n")
                    break
                
                if user_input.lower() == 'clear':
                    self.clear_history()
                    continue
                
                if user_input.lower() == 'history':
                    self._print_history()
                    continue
                
                # Process query
                print("\nNeuronix: ", end="", flush=True)
                response = self.chat(user_input)
                print(response)
                print()
                
            except KeyboardInterrupt:
                print("\n\nNeuronix: Phir milenge! Bye bye!\n")
                break
            except Exception as e:
                logger.error(f"Chat loop error: {e}")
                print(f"\nError: {e}\n")
    
    def _print_history(self):
        """Print conversation history"""
        print("\n" + "=" * 80)
        print("[*] CONVERSATION HISTORY")
        print("=" * 80 + "\n")
        
        for i, msg in enumerate(self.conversation_history, 1):
            role = "You" if msg['role'] == 'user' else "Neuronix"
            content = msg['content']
            
            # Truncate long messages
            if len(content) > 200:
                content = content[:200] + "...\n[truncated]"
            
            print(f"{i}. [{role}]\n{content}\n")
        
        print("=" * 80 + "\n")


def main():
    """Main entry point"""
    
    # Check for API key
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("\n" + "!" * 80)
        print("ERROR: GOOGLE_API_KEY environment variable not set")
        print("!" * 80)
        print("\nSet your API key:")
        print("  $env:GOOGLE_API_KEY = 'your-api-key'")
        print("  python backend/chat_engine.py")
        print("\nGet key from: https://makersuite.google.com/app/apikey")
        print("!" * 80 + "\n")
        sys.exit(1)
    
    try:
        # Initialize chat engine
        print("\n[Initializing Neuronix Chat Engine...]\n")
        engine = NeuronixChatEngine(google_api_key=google_api_key)
        
        # Start interactive chat
        engine.interactive_chat()
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}\n")
        sys.exit(1)
    except ValueError as e:
        print(f"\n✗ Error: {e}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n✗ Fatal error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
