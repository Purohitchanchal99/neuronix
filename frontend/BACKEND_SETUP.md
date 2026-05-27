# 🚀 NEURONIX Backend API Setup Guide

## Quick Start (2 minutes)

### Step 1️⃣ - Make sure RAG system is ready
```bash
cd c:\Users\admin\Desktop\desktop\NEURO_MENTAL

# Check if vector database exists
ls data/vector_db

# If not, run ingestion first (one time only)
python neuronix_query.py  # This loads the system
```

### Step 2️⃣ - Start the Backend API
```bash
cd frontend

# Run the backend API
python backend_api_template.py
# OR with explicit settings:
python -m uvicorn backend_api_template:app --host 0.0.0.0 --port 8000 --reload
```

✅ **API is running!** Check: http://localhost:8000/docs

### Step 3️⃣ - Run Frontend in another terminal
```bash
cd frontend
npm run dev
# Opens http://localhost:3000
```

## 📋 What You Get

### Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Check if API & RAG system are ready |
| `/api/chat` | POST | Send message, get response (JSON) |
| `/api/chat/stream` | POST | Streaming response (token-by-token) |
| `/api/status` | GET | Detailed RAG system status |
| `/api/sessions` | GET/POST | Save & retrieve chat sessions |

### Request Format
```json
{
  "message": "I feel anxious",
  "country": "India",
  "chunks": 6,
  "session_id": "optional_session_id"
}
```

### Response Format
```json
{
  "response": "Answer from RAG system...",
  "sources": [
    {"title": "DSM-5", "relevance": "high"},
    {"title": "Clinical Review", "relevance": "medium"}
  ],
  "suggestions": [
    "Tell me more",
    "What are causes?"
  ],
  "is_crisis": false,
  "meta": {
    "chunks_used": 6,
    "timestamp": "2026-04-30T...",
    "country": "India"
  }
}
```

## 🚨 Crisis Detection

The API automatically detects crisis keywords and returns:
- ✅ Immediate helpline numbers
- ✅ Crisis resources
- ✅ Flag: `"is_crisis": true`

**Supported Countries:**
- 🇮🇳 India (AASRA: 22-5522-5522)
- 🇺🇸 USA (988 Lifeline)
- 🇬🇧 UK (Samaritans: 116 123)

Add more countries in `CRISIS_RESPONSES` dict!

## ⚙️ Configuration

### Chunk Count
```python
# In frontend request:
"chunks": 6  # Range: 5-8 (default: 6)
```

### Streaming Effect
```python
# In backend_api_template.py
STREAM_DELAY = 0.02  # seconds between tokens
# Lower = faster, Higher = slower typing effect
```

### RAG Model
```python
RAG_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# MUST match ingestion model
```

## 🔧 Troubleshooting

### ❌ "RAG system not initialized"
**Solution:** Vector database not loaded
```bash
# Check database exists
python neuronix_query.py
```

### ❌ "Module not found"
**Solution:** Missing dependencies
```bash
pip install -r requirements.txt
```

### ❌ CORS errors in browser
**Solution:** Already handled! CORS middleware is configured.
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

### ❌ Port 8000 already in use
**Solution:** Use different port
```bash
python -m uvicorn backend_api_template:app --port 8001
```

## 🎯 Next Steps

### Phase 1: Testing
- ✅ Start backend
- ✅ Start frontend
- ✅ Send test message: "Tell me about depression"
- ✅ Verify sources appear

### Phase 2: Streaming (Pro)
```javascript
// Frontend code
const response = await fetch('/api/chat/stream', {
  method: 'POST',
  body: JSON.stringify({message: 'Your question'})
});
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const {done, value} = await reader.read();
  if (done) break;
  setResponse(prev => prev + decoder.decode(value));
}
```

### Phase 3: Database Sessions
```bash
# Currently in-memory (sessions lost on restart)
# TODO: Connect to PostgreSQL/MongoDB for persistence
```

### Phase 4: Authentication
```bash
# Add user accounts
# TODO: Implement JWT tokens
```

## 📊 Monitoring

### Check API Health
```bash
curl http://localhost:8000/api/health
```

### View Detailed Status
```bash
curl http://localhost:8000/api/status
```

### Check Auto-Logs
```bash
cat logs/chat_logs_*.json
```

## 🚀 Production Deployment

When ready to deploy:

1. **Change CORS origins:**
```python
allow_origins=["your-frontend-domain.com"]
```

2. **Update RAG loading:**
```python
verbose=False  # Already set in API
```

3. **Use production ASGI:**
```bash
gunicorn backend_api_template:app --workers 4 --timeout 60
```

4. **Add authentication:**
```python
from fastapi.security import HTTPBearer
security = HTTPBearer()

@app.post("/api/chat")
async def chat(request: ChatRequest, credentials: HTTPAuthCredentials):
    # Verify token...
```

5. **Database sessions:**
```python
# Replace SESSIONS dict with PostgreSQL
from sqlalchemy import create_engine
```

## 📝 Files Modified

- ✅ `backend_api_template.py` - Now a production API!
- ❌ No changes to frontend needed (already compatible)
- ❌ No changes to NEURONIX RAG system

## ✨ That's it!

```bash
# 2 terminals, 2 commands:

# Terminal 1 (Backend)
cd frontend && python backend_api_template.py

# Terminal 2 (Frontend)
cd frontend && npm run dev
```

Visit http://localhost:3000 and start chatting! 🎉

---

Questions? Check:
- [neuronix_query.py](../neuronix_query.py) - RAG system
- [RAG_PIPELINE.md](../RAG_PIPELINE.md) - Architecture
- [NEURONIX_READY_TO_DEPLOY.md](../NEURONIX_READY_TO_DEPLOY.md) - System status
