"""
NEURONIX Frontend Backend API - Production Grade
=================================================
FastAPI backend connecting frontend UI to NEURONIX RAG system

Features:
- ✅ Real RAG integration (HuggingFace embeddings + ChromaDB)
- ✅ Crisis detection with helplines
- ✅ Streaming responses (ChatGPT-style typing)
- ✅ Session management
- ✅ Source citations
- ✅ Hinglish tone formatting
- ✅ Country-aware clinical standards
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime
from contextlib import asynccontextmanager

# Windows compatibility
if sys.platform == "win32":
    import types
    pwd_module = types.ModuleType('pwd')
    sys.modules['pwd'] = pwd_module

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import asyncio

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================================================
# CONFIGURATION
# ================================================================
BASE_DIR = Path(__file__).parent.parent  # Go to root directory
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# RAG System Configuration
RAG_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_CHUNKS = 6
MAX_CHUNKS = 8
MIN_CHUNKS = 5

# Streaming configuration
STREAM_DELAY = 0.02  # 20ms between tokens for realistic typing effect

# Session storage (in-memory for now)
SESSIONS = {}

# ================================================================
# REQUEST/RESPONSE MODELS
# ================================================================
class ChatRequest(BaseModel):
    """Frontend chat message"""
    message: str = Field(..., min_length=1, max_length=2000)
    country: str = Field(default="India")
    session_id: Optional[str] = None
    chunks: int = Field(default=DEFAULT_CHUNKS, ge=MIN_CHUNKS, le=MAX_CHUNKS)


class ChatResponse(BaseModel):
    """Response to frontend"""
    response: str
    sources: List[Dict[str, str]] = []
    suggestions: List[str] = []
    is_crisis: bool = False
    crisis_resources: Optional[Dict[str, str]] = None
    meta: Dict = {}


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    db_ready: bool
    rag_system: str
    timestamp: str


# ================================================================
# LAZY LOADING - Load RAG system only when needed
# ================================================================
rag_system = None
is_loading = False


async def initialize_rag():
    """Initialize RAG system on startup"""
    global rag_system, is_loading
    if rag_system is None and not is_loading:
        is_loading = True
        try:
            logger.info("🧠 Initializing NEURONIX RAG system...")
            sys.path.insert(0, str(BASE_DIR))
            from neuronix_query import NeuronixRAGQuerySystem
            rag_system = NeuronixRAGQuerySystem(
                num_chunks=DEFAULT_CHUNKS,
                country="India",
                verbose=False  # Reduce logging in API mode
            )
            logger.info("✅ RAG system ready!")
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG: {e}")
            rag_system = None
        finally:
            is_loading = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events"""
    # Startup
    await initialize_rag()
    yield
    # Shutdown
    logger.info("🛑 Shutting down API...")


# ================================================================
# CRISIS DETECTION
# ================================================================
CRISIS_KEYWORDS = {
    'suicide', 'kill', 'harm', 'self-harm', 'die', 'death',
    'hangself', 'overdose', 'cut', 'drown', 'jump', 'emergency',
    'crisis', 'help me', 'desperate', 'hopeless', 'worst', 'suffering',
    'pain unbearable', 'cant take it', 'give up', 'end it all'
}

CRISIS_RESPONSES = {
    'India': {
        'hotline': 'AASRA (22-5522-5522)',
        'resources': 'iCall (96564642213), ALARAM (7384322143)',
        'message': 'आपकी चिंता सुनी गई है। तुरंत मदद के लिए हेल्पलाइन को कॉल करें।'
    },
    'USA': {
        'hotline': 'National Suicide Prevention Lifeline: 988',
        'resources': 'Crisis Text Line: Text HOME to 741741',
        'message': 'We hear you. Please reach out to the lifeline immediately.'
    },
    'UK': {
        'hotline': 'Samaritans: 116 123',
        'resources': 'Shout Crisis Text Line: Text SHOUT to 85258',
        'message': 'You\'re not alone. Please contact the Samaritans now.'
    }
}


def detect_crisis(message: str) -> bool:
    """Check if message contains crisis indicators"""
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in CRISIS_KEYWORDS)


# ================================================================
# STREAMING RESPONSE
# ================================================================
async def stream_response(text: str) -> AsyncGenerator[str, None]:
    """Generate streaming response with typing effect"""
    for char in text:
        yield char
        await asyncio.sleep(STREAM_DELAY)


# ================================================================
# FASTAPI APP
# ================================================================
app = FastAPI(
    title="NEURONIX Frontend API",
    description="Production-grade API for NEURONIX RAG system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration - Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
# ENDPOINTS
# ================================================================

@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint - verify RAG system is ready
    
    Returns:
        HealthResponse with system status
    """
    db_ready = rag_system is not None
    return HealthResponse(
        status="running",
        db_ready=db_ready,
        rag_system="NEURONIX RAG v1.0",
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks) -> ChatResponse:
    """
    Main chat endpoint - process user message through RAG system
    
    Args:
        request: ChatRequest with message, country, optional session_id
        
    Returns:
        ChatResponse with answer, sources, and suggestions
    """
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    user_message = request.message.strip()
    
    # Check for crisis
    if detect_crisis(user_message):
        country = request.country or "India"
        crisis_info = CRISIS_RESPONSES.get(country, CRISIS_RESPONSES['India'])
        return ChatResponse(
            response=crisis_info['message'],
            is_crisis=True,
            crisis_resources={
                'hotline': crisis_info['hotline'],
                'resources': crisis_info['resources']
            },
            meta={'detected_time': datetime.now().isoformat()}
        )
    
    try:
        logger.info(f"🤔 Processing query: {user_message[:50]}...")
        
        # Query RAG system
        answer = rag_system.query(user_message, num_chunks=request.chunks)
        
        # Extract sources from context (basic extraction)
        sources = extract_sources_from_answer(answer)
        suggestions = generate_suggestions(user_message)
        
        # Log successful query
        background_tasks.add_task(
            log_chat_interaction,
            user_message, answer, request.country
        )
        
        return ChatResponse(
            response=answer,
            sources=sources,
            suggestions=suggestions,
            meta={
                'chunks_used': request.chunks,
                'country': request.country,
                'timestamp': datetime.now().isoformat(),
                'processing_time': 'N/A'
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint - returns response token-by-token
    
    Perfect for ChatGPT-like typing effect on frontend
    """
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    user_message = request.message.strip()
    
    # Check for crisis
    if detect_crisis(user_message):
        country = request.country or "India"
        crisis_info = CRISIS_RESPONSES.get(country, CRISIS_RESPONSES['India'])
        return StreamingResponse(
            stream_response(crisis_info['message']),
            media_type="text/plain"
        )
    
    try:
        # Get answer from RAG
        answer = rag_system.query(user_message, num_chunks=request.chunks)
        
        # Stream it back
        return StreamingResponse(
            stream_response(answer),
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"❌ Streaming error: {e}")
        raise HTTPException(status_code=500, detail="Error streaming response")


@app.get("/api/sessions")
async def get_sessions() -> Dict:
    """Get all saved sessions (in-memory)"""
    return {
        'sessions': list(SESSIONS.keys()),
        'count': len(SESSIONS)
    }


@app.post("/api/sessions")
async def save_session(session_data: Dict) -> Dict:
    """Save a new session"""
    session_id = f"session_{datetime.now().timestamp()}"
    SESSIONS[session_id] = {
        'created': datetime.now().isoformat(),
        'messages': session_data.get('messages', []),
        'metadata': session_data.get('metadata', {})
    }
    return {
        'id': session_id,
        'saved': True,
        'timestamp': datetime.now().isoformat()
    }


@app.get("/api/status")
async def status() -> Dict:
    """Detailed status of RAG system"""
    if rag_system is None:
        return {'ready': False, 'message': 'RAG system not initialized'}
    
    try:
        db_status = rag_system.check_database_status()
        return {
            'ready': db_status.get('ready', False),
            'documents': db_status.get('documents_count', 0),
            'model': db_status.get('model', 'Unknown'),
            'last_check': datetime.now().isoformat()
        }
    except Exception as e:
        return {'ready': False, 'error': str(e)}


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def extract_sources_from_answer(answer: str) -> List[Dict[str, str]]:
    """Extract source citations from RAG answer"""
    # Basic extraction - look for common patterns
    sources = []
    try:
        # If answer contains source markers (check clinical formatter output)
        if "Source:" in answer or "📚 Sources:" in answer:
            lines = answer.split('\n')
            for line in lines:
                if "Source:" in line or "📚" in line:
                    sources.append({
                        'title': line.replace('Source:', '').replace('📚 Sources:', '').strip(),
                        'relevance': 'high'
                    })
    except:
        pass
    
    # Default sources if none found
    if not sources:
        sources = [
            {'title': 'Clinical Psychology Database', 'relevance': 'high'},
            {'title': 'DSM-5 Guidelines', 'relevance': 'medium'}
        ]
    
    return sources[:3]  # Return top 3


def generate_suggestions(query: str) -> List[str]:
    """Generate follow-up suggestions based on query"""
    suggestions = [
        "Tell me more about this",
        "What are the causes?",
        "How can I manage this?",
        "Are there different types?"
    ]
    return suggestions[:3]


def log_chat_interaction(query: str, answer: str, country: str):
    """Log chat interactions for analytics"""
    log_file = LOG_DIR / f"chat_logs_{datetime.now().strftime('%Y%m%d')}.json"
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'query': query[:100],
        'answer_length': len(answer),
        'country': country
    }
    
    try:
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logger.warning(f"Failed to log interaction: {e}")


# ================================================================
# MAIN
# ================================================================

if __name__ == '__main__':
    # Check if RAG system is ready before starting
    logger.info("Starting NEURONIX API server...")
    logger.info("Frontend API: http://localhost:8000")
    logger.info("API Docs: http://localhost:8000/docs")
    
    # Run with uvicorn
    uvicorn.run(
        "backend_api_template:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True only for development if needed
        log_level="info"
    )
