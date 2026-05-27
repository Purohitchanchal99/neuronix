"""
🚀 NEURONIX BACKEND API v2.2 - Phase 6 + Voice Support
=====================================================
Enhanced API with Memory + Adaptive Learning + Voice 🎤

Endpoints:
- POST /api/chat - Chat with Phase 6 memory & learning
- POST /api/chat/voice - Chat with voice (STT + TTS)
- GET /api/users/{user_id}/profile - Get learning profile & progress
- POST /api/sessions/close - Close session with summarization
- GET /api/users/{user_id}/recommendations - Get next learning topics
- GET /api/users/{user_id}/history - Get conversation history
- GET /api/voice/languages - Get supported languages
- POST /api/voice/synthesize - Synthesize text to speech
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import logging
from datetime import datetime
import io
import time
import uuid

try:
    from scripts.neuronix_core import NeuronixCore
    from scripts.memory_system import ConversationStore
    from scripts.learning_tracker import LearningTracker
    from scripts.adaptive_recommender import AdaptiveRecommender
    from scripts.session_summarizer import SessionSummarizer
    from scripts.voice_support import VoiceSupport, VoiceProfile, VoiceGender, SpeakingRate, TranscriptionResult
    PHASE6_AVAILABLE = True
    VOICE_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Phase 6 not fully available: {e}")
    PHASE6_AVAILABLE = False
    VOICE_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# FastAPI Setup
# ============================================================================

app = FastAPI(title="NEURONIX API v2.1 - Phase 6", version="2.1")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# INITIALIZATION
# ============================================================================

# Phase 6 vector store: use the real ChromaDB collection
# (Must match embedding model + collection configuration used by chat_engine.py)

from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

try:
    from scripts.neuronix_constants import COLLECTION_NAME
except Exception:
    COLLECTION_NAME = "neuronix_medical_kb"

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma

    cache_folder = BASE_DIR / "hf_cache"
    cache_folder.mkdir(parents=True, exist_ok=True)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        cache_folder=str(cache_folder),
        model_kwargs={"trust_remote_code": True},
    )

    if VECTOR_DB_DIR.exists():
        vector_store = Chroma(
            persist_directory=str(VECTOR_DB_DIR),
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME,
        )
    else:
        vector_store = None
except Exception as e:
    logger.error(f"❌ Failed to initialize ChromaDB for Phase 6: {e}")
    vector_store = None

# Initialize NeuronixCore with Phase 6
try:
    ncore = NeuronixCore(vector_store, llm=None)
    logger.info("✅ NeuronixCore initialized with Phase 6")
except Exception as e:
    logger.error(f"❌ Failed to initialize NeuronixCore: {e}")
    ncore = None

# Initialize Voice Support
try:
    voice_support = VoiceSupport()
    logger.info("✅ Voice Support initialized (STT + TTS)")
except Exception as e:
    logger.warning(f"⚠️ Voice Support initialization: {e}")
    voice_support = None

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request with Phase 6 support"""
    user_id: Optional[str] = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:8]}")
    message: str
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    country: Optional[str] = "India"
    chunks: Optional[int] = 6

class ChatResponse(BaseModel):
    """Enhanced response with Phase 6 metadata"""
    user_id: str
    response: str
    topics: List[str] = []
    tone: str = "neutral"
    next_recommended_topic: Optional[str] = None
    learning_progress: Dict = {}
    sources: List[str] = []
    meta: Dict = {}

class UserProfileResponse(BaseModel):
    """User learning profile"""
    user_id: str
    topics_studied: int = 0
    topics_mastered: int = 0
    mastery_rate: float = 0.0
    learning_style: str = "mixed"
    total_interactions: int = 0
    focus_areas: List[str] = []

class RecommendationResponse(BaseModel):
    """Topic recommendation"""
    topic: str
    priority: float  # 0.0 - 1.0
    reason: str
    estimated_time_minutes: int
    prerequisites: List[str] = []

class SessionSummaryResponse(BaseModel):
    """Session summary with insights"""
    user_id: str
    session_duration_minutes: int
    messages_exchanged: int
    topics_covered: List[str] = []
    executive_summary: str = ""
    insights: List[str] = []
    productivity_score: float = 0.0

class ConversationMessage(BaseModel):
    """Single conversation message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    tone: Optional[str] = None
    topics: List[str] = []


class VoiceChatRequest(BaseModel):
    """Voice chat request"""
    user_id: str
    audio_file: Optional[bytes] = None  # Audio data
    language: Optional[str] = "en"
    enable_audio_response: bool = True


class VoiceChatResponse(BaseModel):
    """Voice chat response"""
    user_id: str
    transcribed_text: str  # What user said
    response_text: str  # What system responds
    audio_response: Optional[bytes] = None  # Audio response (if enabled)
    detected_emotion: Optional[str] = None
    is_crisis: bool = False
    topics: List[str] = []


class VoiceProfileUpdateRequest(BaseModel):
    """Update user's voice preferences"""
    user_id: str
    preferred_gender: Optional[str] = "neutral"
    speaking_rate: Optional[str] = "normal"
    language: Optional[str] = "en"
    emotional_tone: Optional[str] = "compassionate"
    enable_voice: bool = True


class SynthesisRequest(BaseModel):
    """Request to synthesize text to speech"""
    text: str
    user_id: str
    gender: Optional[str] = "neutral"
    language: Optional[str] = "en"

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    🧠 Chat endpoint with Phase 6 Memory + Adaptive Learning
    
    Features:
    ✅ Long-term conversation memory (semantic search)
    ✅ Learning progress tracking (topics + mastery)
    ✅ Personalized recommendations (next topics)
    ✅ Response personalization (learning style)
    ✅ Session continuation (context injection)
    """
    
    try:
        logger.info(f"📨 Chat request from {request.user_id}: {request.message[:50]}...")
        
        if not ncore:
            raise HTTPException(status_code=503, detail="Service not available")
        
# ----------------------------
        # Crisis Hard-Routing (deterministic)
        # ----------------------------
        def _risk_classifier(text: str) -> str:
            t = (text or "").lower()
            crisis_signals = [
                "want to die",
                "suicide",
                "kill myself",
                "hurt myself",
                "overdose",
                "jeena nahi",
                "jeena nahin",
                "marna",
                "aatmhatya",
                "no point living",
                "end my life",
            ]
            violence_signals = [
                "hurt someone",
                "hurt my neighbor",
                "hurt my neighbour",
                "i want to hurt",
                "violent",
                "get violent",
                "snap",
            ]
            if any(s in t for s in crisis_signals) or any(s in t for s in violence_signals):
                return "high"
            return "low"

        def _crisis_safe_response(country: str) -> str:
            # Deterministic fixed template; no retrieval/ontology/planner dependencies.
            india = "Please contact immediate help: India — AASRA +91-22-27546669, iCall +91-9152987821, Crisis Line 1-800-110-7000 (24/7)."
            us = "Please contact immediate help: USA — Call/text 988 (Lifeline)."
            uk = "Please contact immediate help: UK — Samaritans 116 123."
            resources = india if (country or "").lower() == "india" else (us if (country or "").lower() == "us" else uk)
            return (
                "It sounds like you’re going through something very painful right now.\n"
                "You deserve support, and you do not have to handle this alone.\n\n"
                f"{resources}\n\n"
                "If you’re in immediate danger, contact your local emergency services right now."
            )

        risk = _risk_classifier(request.message)
        if risk == "high":
            response_text = _crisis_safe_response(request.country or "India")
            return ChatResponse(
                user_id=request.user_id,
                response=response_text,
                topics=[],
                tone="neutral",
                next_recommended_topic=None,
                learning_progress={},
                sources=[],
                meta={"route": "crisis_hard_route", "risk": "high"},
            )

        # Normal cognitive pipeline
        result = ncore.handle_query_phase6(request.user_id, request.message)

        return ChatResponse(
            user_id=request.user_id,
            response=result.get("response", ""),
            topics=result.get("topics", []),
            tone=result.get("tone", "neutral"),
            next_recommended_topic=result.get("next_recommended_topic"),
            learning_progress=result.get("learning_progress", {}),
            sources=result.get("sources", []),
            meta=result.get("meta", {})
        )
    
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: str):
    """
    📊 Get user's learning profile
    
    Returns:
    - Topics studied and mastered
    - Mastery rate (%)
    - Learning style
    - Total interactions
    - Focus areas
    """
    
    try:
        logger.info(f"📊 Getting profile for {user_id}")
        
        if not ncore:
            raise HTTPException(status_code=503, detail="Service not available")
        
        # Get user profile and metrics
        user_profile = ncore.memory_store.get_user_profile(user_id)
        metrics = ncore.learning_tracker.get_metrics(user_id)
        
        # Get focus areas from memory
        conversation = ncore.memory_store.get_conversation(user_id)
        focus_areas = []
        if conversation:
            topics_set = set()
            for msg in conversation.messages:
                if hasattr(msg, 'topics'):
                    topics_set.update(msg.topics or [])
            focus_areas = list(topics_set)
        
        mastery_rate = 0.0
        if metrics and metrics.total_topics > 0:
            mastery_rate = metrics.mastered_topics / metrics.total_topics
        
        return UserProfileResponse(
            user_id=user_id,
            topics_studied=metrics.total_topics if metrics else 0,
            topics_mastered=metrics.mastered_topics if metrics else 0,
            mastery_rate=mastery_rate,
            learning_style=metrics.learning_style.value if metrics and metrics.learning_style else "mixed",
            total_interactions=len(conversation.messages) if conversation else 0,
            focus_areas=focus_areas
        )
    
    except Exception as e:
        logger.error(f"❌ Profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/{user_id}/recommendations", response_model=List[RecommendationResponse])
async def get_recommendations(user_id: str):
    """
    🎯 Get personalized topic recommendations
    
    Returns:
    - Next recommended topic(s)
    - Priority score (0.0 - 1.0)
    - Reasoning
    - Estimated time to learn
    - Prerequisites
    """
    
    try:
        logger.info(f"🎯 Getting recommendations for {user_id}")
        
        if not ncore:
            raise HTTPException(status_code=503, detail="Service not available")
        
        # Get recommendations
        recommendations = []
        
        for i in range(3):  # Get top 3 recommendations
            next_topic = ncore.recommender.recommend_next_topic(
                ncore.learning_tracker, 
                user_id
            )
            
            if next_topic and next_topic.priority > 0.3:
                recommendations.append(
                    RecommendationResponse(
                        topic=next_topic.topic,
                        priority=next_topic.priority,
                        reason=next_topic.reason,
                        estimated_time_minutes=next_topic.estimated_time or 30,
                        prerequisites=next_topic.prerequisites or []
                    )
                )
        
        return recommendations
    
    except Exception as e:
        logger.error(f"❌ Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/close", response_model=SessionSummaryResponse)
async def close_session(user_id: str):
    """
    📝 Close session and generate summary with insights
    
    Returns:
    - Session duration
    - Messages exchanged
    - Topics covered
    - Executive summary (high-level overview)
    - Key insights
    - Productivity score
    """
    
    try:
        logger.info(f"📝 Closing session for {user_id}")
        
        if not ncore:
            raise HTTPException(status_code=503, detail="Service not available")
        
        # Get conversation
        conversation = ncore.memory_store.get_conversation(user_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get metrics
        metrics = ncore.learning_tracker.get_metrics(user_id)
        
        # Generate summary
        summary = ncore.summarizer.summarize_session(conversation, metrics)
        
        # Calculate session duration (mock - real implementation would track time)
        duration_minutes = len(conversation.messages) * 5  # Estimate 5 min per message
        
        # Collect topics
        topics = set()
        for msg in conversation.messages:
            if hasattr(msg, 'topics'):
                topics.update(msg.topics or [])
        
        return SessionSummaryResponse(
            user_id=user_id,
            session_duration_minutes=duration_minutes,
            messages_exchanged=len(conversation.messages),
            topics_covered=list(topics),
            executive_summary=summary.executive_summary if summary else "",
            insights=[s.strip() for s in (summary.insights or [])] if summary else [],
            productivity_score=summary.productivity_score if summary else 0.5
        )
    
    except Exception as e:
        logger.error(f"❌ Session close error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/{user_id}/history", response_model=List[ConversationMessage])
async def get_conversation_history(user_id: str, limit: int = 50):
    """
    📚 Get user's conversation history
    
    Parameters:
    - user_id: User identifier
    - limit: Maximum messages to return (default: 50)
    
    Returns:
    - List of conversation messages with tone and topics
    """
    
    try:
        logger.info(f"📚 Getting history for {user_id} (limit: {limit})")
        
        if not ncore:
            raise HTTPException(status_code=503, detail="Service not available")
        
        # Get conversation
        conversation = ncore.memory_store.get_conversation(user_id)
        if not conversation:
            return []
        
        # Format messages
        messages = []
        for msg in conversation.messages[-limit:]:
            tone = getattr(msg, 'tone', 'neutral')
            topics = getattr(msg, 'topics', []) or []
            timestamp = getattr(msg, 'timestamp', datetime.now().isoformat())
            
            messages.append(
                ConversationMessage(
                    role=msg.role or "user",
                    content=msg.content or "",
                    timestamp=timestamp,
                    tone=tone,
                    topics=topics
                )
            )
        
        return messages
    
    except Exception as e:
        logger.error(f"❌ History error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# VOICE SUPPORT ENDPOINTS
# ============================================================================

@app.post("/api/chat/voice", response_model=VoiceChatResponse)
async def voice_chat_endpoint(
    user_id: str,
    file: UploadFile = File(...),
    language: str = "en",
    enable_audio_response: bool = True
):
    """
    🎤 Voice chat endpoint - Speech-to-Text + Response + Optional Text-to-Speech
    
    Upload audio file:
    - Supported formats: mp3, wav, m4a, flac, ogg, opus
    - Max size: 25MB
    
    Returns:
    - Transcribed user speech
    - AI response
    - Optional audio response (if enable_audio_response=True)
    - Emotion detection
    - Crisis signals
    """
    
    try:
        if not voice_support:
            raise HTTPException(status_code=503, detail="Voice support not available")
        
        logger.info(f"🎤 Voice chat from {user_id}")
        
        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            # Step 1: Validate audio
            is_valid, error = voice_support.validate_audio_file(tmp_path)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid audio: {error}")
            
            # Step 2: Transcribe audio
            logger.info("   [1/4] Transcribing speech...")
            transcription = voice_support.transcribe_audio(tmp_path, language)
            
            if not transcription.text:
                raise HTTPException(status_code=400, detail="Could not transcribe audio")
            
            user_text = transcription.text
            logger.info(f"   ✓ Transcribed: {user_text[:60]}...")
            
            # Step 3: Check for crisis
            if transcription.is_crisis_signal:
                logger.warning(f"   ⚠️ CRISIS SIGNAL IN VOICE - {user_id}")
            
            # Step 4: Generate response using Phase 6
            logger.info("   [2/4] Generating response...")
            result = ncore.handle_query_phase6(user_id, user_text)
            response_text = result.get("response", "I'm here to help. Can you tell me more?")
            
            logger.info(f"   ✓ Response generated ({len(response_text)} chars)")
            
            # Step 5: Synthesize audio response (if requested)
            audio_response = None
            if enable_audio_response:
                logger.info("   [3/4] Synthesizing audio response...")
                voice_profile = voice_support.get_voice_profile(user_id)
                audio_response = voice_support.synthesize_speech(response_text, voice_profile)
                if audio_response:
                    logger.info(f"   ✓ Audio synthesized ({len(audio_response)} bytes)")
            
            logger.info("   [4/4] Complete ✓")
            
            return VoiceChatResponse(
                user_id=user_id,
                transcribed_text=user_text,
                response_text=response_text,
                audio_response=audio_response,
                detected_emotion=transcription.detected_emotion,
                is_crisis=transcription.is_crisis_signal,
                topics=result.get("topics", [])
            )
        
        finally:
            import os
            os.unlink(tmp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Voice chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/users/{user_id}/voice/profile")
async def update_voice_profile(user_id: str, request: VoiceProfileUpdateRequest):
    """
    🎤 Update user's voice preferences
    
    Customize:
    - Voice gender (male/female/neutral)
    - Speaking rate (slow/normal/fast)
    - Language
    - Emotional tone (compassionate/clinical/supportive)
    """
    
    try:
        if not voice_support:
            raise HTTPException(status_code=503, detail="Voice support not available")
        
        logger.info(f"🎤 Updating voice profile for {user_id}")
        
        profile = VoiceProfile(
            user_id=user_id,
            preferred_gender=VoiceGender(request.preferred_gender or "neutral"),
            speaking_rate=SpeakingRate[request.speaking_rate.upper()] if request.speaking_rate else SpeakingRate.NORMAL,
            language=request.language or "en",
            emotional_tone=request.emotional_tone or "compassionate",
            enable_voice=request.enable_voice
        )
        
        voice_support.set_voice_profile(profile)
        
        return {
            "status": "success",
            "message": "Voice profile updated",
            "profile": {
                "gender": profile.preferred_gender.value,
                "speaking_rate": profile.speaking_rate.name.lower(),
                "language": profile.language,
                "emotional_tone": profile.emotional_tone
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Voice profile update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/synthesize", response_model=Dict)
async def synthesize_speech(request: SynthesisRequest):
    """
    🎤 Synthesize text to speech
    
    Convert text to natural-sounding audio
    Returns audio bytes (base64 encoded)
    """
    
    try:
        if not voice_support:
            raise HTTPException(status_code=503, detail="Voice support not available")
        
        logger.info(f"🎤 Synthesizing speech: {request.text[:50]}...")
        
        profile = voice_support.get_voice_profile(request.user_id)
        profile.preferred_gender = VoiceGender(request.gender or "neutral")
        profile.language = request.language or "en"
        
        audio_bytes = voice_support.synthesize_speech(request.text, profile)
        
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Failed to synthesize audio")
        
        # Encode audio as base64 for JSON response
        import base64
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        return {
            "status": "success",
            "audio_base64": audio_base64,
            "audio_size_bytes": len(audio_bytes)
        }
    
    except Exception as e:
        logger.error(f"❌ Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voice/languages")
async def get_supported_languages():
    """🎤 Get list of supported languages for voice"""
    
    if not voice_support:
        return {"languages": []}
    
    return {
        "supported_languages": voice_support.get_supported_languages(),
        "total": len(voice_support.get_supported_languages())
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.2",
        "phase6_available": PHASE6_AVAILABLE,
        "voice_available": VOICE_AVAILABLE,
        "ncore_initialized": ncore is not None,
        "voice_initialized": voice_support is not None
    }


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """API documentation"""
    return {
        "title": "NEURONIX API v2.2 - Phase 6 + Voice Support",
        "version": "2.2",
        "chat_endpoints": {
            "text_chat": "POST /api/chat - Send message with Phase 6 memory & learning",
            "voice_chat": "POST /api/chat/voice - Send audio (Speech-to-Text + Response + Optional Text-to-Speech)"
        },
        "user_profile_endpoints": {
            "get_profile": "GET /api/users/{user_id}/profile - Get learning profile",
            "voice_profile": "POST /api/users/{user_id}/voice/profile - Set voice preferences"
        },
        "learning_endpoints": {
            "recommendations": "GET /api/users/{user_id}/recommendations - Get topic recommendations",
            "history": "GET /api/users/{user_id}/history - Get conversation history"
        },
        "session_endpoints": {
            "close_session": "POST /api/sessions/close - Close session with summary"
        },
        "voice_endpoints": {
            "synthesize": "POST /api/voice/synthesize - Convert text to speech",
            "languages": "GET /api/voice/languages - Get supported languages"
        },
        "system_endpoints": {
            "health": "GET /api/health - Health check"
        },
        "features": [
            "✅ Long-term conversation memory (semantic search)",
            "✅ Learning progress tracking (topics + mastery velocity)",
            "✅ Personalized recommendations (next topics with prerequisites)",
            "✅ Automatic session summarization (insights + productivity score)",
            "✅ Response personalization (by learning style)",
            "🎤 Voice input (Speech-to-Text with OpenAI Whisper)",
            "🎤 Voice output (Text-to-Speech with ElevenLabs/Google)",
            "🎤 Emotion detection from speech",
            "🎤 Crisis signal detection in voice",
            "🎤 Multi-language support (40+ languages)"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
