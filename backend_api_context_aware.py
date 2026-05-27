"""
🔗 INTEGRATION: Context-Aware Engine + FastAPI Backend
========================================================
Shows how to integrate the personalization engine into your existing API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

# Import your existing components
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

# Import the new personalization engine
from context_aware_engine import NeuronixPersonalizationEngine, ResponseQualityValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="NEURONIX Context-Aware API", version="2.0")

# Initialize personalization engine
personalization_engine = NeuronixPersonalizationEngine(storage_dir="user_contexts")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ChatRequest(BaseModel):
    """Enhanced chat request with user context"""
    user_id: str  # User identifier for personalization
    message: str
    session_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Enhanced chat response with metadata"""
    user_id: str
    response: str
    sources: list
    user_type: str  # Detected expertise level
    quality_score: int
    crisis_detected: bool
    metadata: dict


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_context(request: ChatRequest):
    """
    Enhanced chat endpoint with:
    ✅ User context injection
    ✅ System prompt personalization
    ✅ Few-shot examples
    ✅ Response quality validation
    ✅ Crisis detection
    ✅ User profiling
    """
    
    try:
        user_id = request.user_id
        message = request.message
        
        logger.info(f"📩 Message from {user_id}: {message}")
        
        # ===== STEP 1: ENHANCE QUERY WITH CONTEXT =====
        enhanced_payload = personalization_engine.enhance_query(user_id, message)
        
        logger.info(f"✅ Context injected. User type: {enhanced_payload['user_type']}")
        
        # ===== STEP 2: PREPARE LLM CALL =====
        system_prompt = enhanced_payload['system_prompt']
        few_shots = enhanced_payload['few_shot_examples']
        
        # Build the complete prompt
        full_prompt = f"""{system_prompt}

{few_shots}

CURRENT USER CONTEXT:
{enhanced_payload['user_context']}

USER QUESTION: {message}

Remember:
- Stay true to the system prompt above
- Use the examples as guidance for answer quality
- Provide cited sources from your knowledge base
- Include crisis resources if relevant
"""
        
        # ===== STEP 3: RETRIEVE RAG CONTEXT =====
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = Chroma(
            collection_name="neuronix_medical_kb",
            persist_directory="data/vector_db",
            embedding_function=embeddings
        )
        
        # Retrieve relevant documents
        docs = vector_store.similarity_search(message, k=3)
        sources = [doc.metadata for doc in docs]
        
        logger.info(f"📚 Retrieved {len(docs)} sources from knowledge base")
        
        # ===== STEP 4: GENERATE RESPONSE =====
        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
        response = llm.invoke(full_prompt)
        response_text = response.content
        
        logger.info(f"✅ Response generated ({len(response_text)} chars)")
        
        # ===== STEP 5: VALIDATE RESPONSE QUALITY =====
        validation = ResponseQualityValidator.validate(response_text)
        
        if validation["requires_regeneration"]:
            logger.warning(f"⚠️ Response quality issues: {validation['issues']}")
            # Could retry here or flag for review
        
        # ===== STEP 6: PROCESS & UPDATE USER PROFILE =====
        result = personalization_engine.process_response(
            user_id, message, response_text
        )
        
        logger.info(f"✅ Profile updated. Crisis detected: {result['crisis_detected']}")
        
        # ===== STEP 7: CRISIS DETECTION & RESOURCES =====
        crisis_resources = {}
        if result['crisis_detected'] or "suicide" in message.lower():
            crisis_resources = {
                "crisis_detected": True,
                "resources": get_crisis_resources(message),
                "immediate_help": "Please contact emergency services or a mental health professional immediately"
            }
            logger.warning("🚨 CRISIS DETECTED - Resources provided")
        
        # ===== RETURN RESPONSE =====
        return ChatResponse(
            user_id=user_id,
            response=response_text,
            sources=sources,
            user_type=enhanced_payload['user_type'],
            quality_score=validation['quality_score'],
            crisis_detected=result['crisis_detected'],
            metadata={
                "system_prompt_used": result['user_type'],
                "few_shot_examples_included": True,
                "context_injected": True,
                "quality_feedback": result['quality_feedback'],
                "crisis_resources": crisis_resources,
                "query_count": result['user_type']  # Could be expanded
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/{user_id}/profile")
async def get_user_profile(user_id: str):
    """
    Get user's personalization profile:
    - Expertise level
    - Topics of interest
    - Preferences
    - Analytics
    """
    try:
        analytics = personalization_engine.get_user_analytics(user_id)
        return {
            "status": "success",
            "data": analytics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/user/{user_id}/preferences")
async def update_user_preferences(user_id: str, preferences: dict):
    """
    Update user preferences:
    - Language
    - Explanation style
    - Response length
    - Tone
    """
    try:
        profile = personalization_engine.profile_manager.load_profile(user_id)
        if not profile:
            profile = personalization_engine.profile_manager.create_user_profile(user_id)
        
        profile["preferences"].update(preferences)
        personalization_engine.profile_manager.save_profile(user_id, profile)
        
        return {
            "status": "success",
            "message": "Preferences updated",
            "preferences": profile["preferences"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/{user_id}/analytics")
async def get_user_analytics(user_id: str):
    """Get detailed user analytics"""
    try:
        analytics = personalization_engine.get_user_analytics(user_id)
        return {
            "status": "success",
            "data": analytics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_crisis_resources(user_message: str = None) -> dict:
    """
    Get crisis resources based on detected context
    Returns hotlines and resources for different countries
    """
    resources = {
        "India": {
            "Aasra": "+91-22-2754-6669",
            "AMAI": "+91-22-5661-6060",
            "iCall": "9152987821",
            "Vandrevala Foundation": "+91-99999-77722",
            "websites": [
                "iCall.in",
                "vandrevalafoundation.com",
                "aasra.info"
            ]
        },
        "USA": {
            "National Suicide Prevention Lifeline": "988",
            "Crisis Text Line": "Text HOME to 741741",
            "988Lifeline": "1-800-273-8255",
            "websites": [
                "suicidepreventionlifeline.org",
                "crisistextline.org"
            ]
        },
        "UK": {
            "Samaritans": "116 123",
            "Crisis": "Text SHOUT to 85258",
            "Rethink Mental Illness": "0300 500 0927",
            "websites": [
                "samaritans.org",
                "shout.org.uk"
            ]
        }
    }
    
    return resources


# ============================================================================
# STARTUP & MONITORING
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 NEURONIX Context-Aware API Starting")
    logger.info("✅ Personalization Engine Active")
    logger.info("✅ RAG System Connected")
    logger.info("✅ Context Injection Ready")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "NEURONIX Context-Aware API",
        "features": [
            "User context injection",
            "System prompt personalization",
            "Few-shot training",
            "Response quality validation",
            "Crisis detection",
            "User profiling",
            "Analytics tracking"
        ],
        "version": "2.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting NEURONIX Context-Aware API")
    logger.info("Endpoints:")
    logger.info("  POST   /api/chat - Send message with context")
    logger.info("  GET    /api/user/{user_id}/profile - Get user profile")
    logger.info("  POST   /api/user/{user_id}/preferences - Update preferences")
    logger.info("  GET    /api/user/{user_id}/analytics - Get analytics")
    logger.info("  GET    /api/health - Health check")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
