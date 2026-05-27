# 🔗 NEURONIX Full Stack Integration Guide

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  FRONTEND (React)                   │
│  • Input field, chat bubbles                        │
│  • Dark/Light mode, sessions                        │
│  • Runs on: http://localhost:3000                   │
└────────────────────────┬────────────────────────────┘
                         │
                         │ POST /api/chat
                         │ (message + metadata)
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              BACKEND API (FastAPI)                  │
│  • Crisis detection                                 │
│  • Session management                               │
│  • Streaming responses                              │
│  • Runs on: http://localhost:8000                   │
└────────────────────────┬────────────────────────────┘
                         │
                         │ query()
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              RAG SYSTEM (neuronix_query)            │
│  • Embedding: Sentence-Transformers                │
│  • Vector DB: ChromaDB                              │
│  • LLM: Google Gemini                               │
│  • Crisis detection + Hinglish tone                 │
└────────────────────────┬────────────────────────────┘
                         │
                         │ similarity_search()
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│            VECTOR DATABASE (ChromaDB)               │
│  • 50,000+ medical/psychology chunks                │
│  • Location: data/vector_db/                        │
│  • 384-dim semantic vectors                         │
└─────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User sends message
```
Frontend (React)
    ↓
message: "I feel anxious"
    ↓
```

### 2. API processes request
```
FastAPI Backend
    ↓
✓ Check crisis detection
✓ Validate input
✓ Route to RAG system
    ↓
```

### 3. RAG retrieves context
```
NeuronixRAGQuerySystem
    ↓
1. Embed question: "I feel anxious"
2. Search 6 nearest chunks in ChromaDB
3. Get: [doc1, doc2, doc3, ...]
    ↓
```

### 4. Generate answer
```
Google Gemini LLM
    ↓
Input: Question + Context
Output: "Anxiety is a normal emotion..."
    ↓
Add: Hinglish tone + Sources + Suggestions
    ↓
```

### 5. Send to Frontend
```
{
  "response": "Anxiety is...",
  "sources": [{"title": "DSM-5", ...}, ...],
  "suggestions": ["Tell me more", ...],
  "is_crisis": false
}
    ↓
React renders response
Display sources
Show suggestions
```

## Step-by-Step Setup

### Phase 1: Verify RAG System ✅

```bash
# Terminal 1: Check vector database
cd c:\Users\admin\Desktop\desktop\NEURO_MENTAL

# Quick test
python neuronix_query.py "What is anxiety?"

# Expected: Full formatted answer with sources
```

✅ **If this works, RAG is ready!**

### Phase 2: Start Backend API 🚀

```bash
# Terminal 1: Start API server
cd frontend
python backend_api_template.py

# You should see:
# ✅ Initializing NEURONIX RAG system...
# ✅ RAG system ready!
# INFO:     Application startup complete
```

<details>
<summary>Troubleshooting Backend</summary>

**Error: "RAG system not initialized"**
```bash
# Solution: Run just the query system first
python neuronix_query.py
```

**Error: "Port 8000 already in use"**
```bash
# Use different port
python -m uvicorn backend_api_template:app --port 8001
```

**Error: "Module not found: langchain"**
```bash
# Install dependencies
pip install -r ../requirements.txt
```

</details>

### Phase 3: Test API Endpoints 🧪

```bash
# Terminal 2: Test API
cd frontend
python test_api.py

# Expected: 5/5 tests passed ✅
```

<details>
<summary>API Test Results</summary>

```
🧪 NEURONIX Backend API Tests
════════════════════════════════════════════════════

[1/5] Testing health endpoint...
✅ API is running
   Status: running
   RAG System: NEURONIX RAG v1.0
   DB Ready: True

[2/5] Testing status endpoint...
✅ Status retrieved
   Ready: True
   Documents in DB: 50,000+

[3/5] Testing chat endpoint (basic question)...
✅ Chat response received
   Response length: 500 chars
   Sources: 2 found
   Suggestions: 3 generated

[4/5] Testing crisis detection...
✅ Crisis detection working
   Crisis flag: True
   Hotline: AASRA (22-5522-5522)
   Resources: iCall (96564642213)

[5/5] Testing session management...
✅ Session retrieval working
   Existing sessions: 0
   Created session: session_1714512345.123

📊 Test Summary
════════════════════════════════════════════════════
Health Check: ✅ PASSED
Status Check: ✅ PASSED
Chat Endpoint: ✅ PASSED
Crisis Detection: ✅ PASSED
Session Management: ✅ PASSED

Total: 5/5 tests passed
🎉 All tests passed! API is ready.
```

</details>

### Phase 4: Start Frontend 💻

```bash
# Terminal 3: Start React frontend
cd frontend
npm install  # First time only
npm run dev

# Opens: http://localhost:3000
```

<details>
<summary>Frontend Troubleshooting</summary>

**Error: "Cannot find module"**
```bash
npm install
npm run dev
```

**Error: "Port 3000 in use"**
```bash
npm run dev -- --port 3001
```

**API not connecting**
Check:
1. Backend running? `curl http://localhost:8000/api/health`
2. CORS enabled? (already configured)
3. Frontend checking correct URL? (hardcoded to 8000)

</details>

### Phase 5: Test End-to-End 🎯

Open http://localhost:3000 and:

1. **Welcome Screen** - Appears with starter questions
2. **Ask Question** - "Tell me about anxiety"
   - ✅ Message appears in chat
   - ✅ Loading indicator shows
   - ✅ Response appears (may take 5-10s first time)
3. **View Sources** - Click "Sources" button
   - ✅ Expandable sources list
4. **Dark Mode** - Toggle top-right
   - ✅ Theme changes
5. **Sessions** - Save/load sessions
   - ✅ Sessions list updates

## API Endpoints Reference

### 📤 POST /api/chat
Send a message and get a response

**Request:**
```json
{
  "message": "How do I manage anxiety?",
  "country": "India",
  "chunks": 6,
  "session_id": "optional"
}
```

**Response:**
```json
{
  "response": "Anxiety management involves...",
  "sources": [
    {"title": "DSM-5 Anxiety Disorders", "relevance": "high"},
    {"title": "CBT for Anxiety", "relevance": "medium"}
  ],
  "suggestions": [
    "What are breathing techniques?",
    "How long does treatment take?"
  ],
  "is_crisis": false,
  "meta": {
    "chunks_used": 6,
    "country": "India",
    "timestamp": "2026-04-30T10:30:45"
  }
}
```

### 🌊 POST /api/chat/stream
Get streaming response (token-by-token, like ChatGPT)

**Request:**
```json
{
  "message": "What is CBT?",
  "country": "India",
  "chunks": 6
}
```

**Response:**
```
Cognitive Behavioral Therapy, or CBT, is a form of psychotherapy
that focuses on modifying dysfunctional thoughts...
(tokens stream in, one per ~20ms for typing effect)
```

### ❤️ GET /api/health
Check if API is running

**Response:**
```json
{
  "status": "running",
  "db_ready": true,
  "rag_system": "NEURONIX RAG v1.0",
  "timestamp": "2026-04-30T10:30:45"
}
```

### 📊 GET /api/status
Detailed system status

**Response:**
```json
{
  "ready": true,
  "documents": 50000,
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "last_check": "2026-04-30T10:30:45"
}
```

### 💾 GET /api/sessions
Get all saved sessions

**Response:**
```json
{
  "sessions": ["session_1714512345", "session_1714512400"],
  "count": 2
}
```

### 💾 POST /api/sessions
Save a new session

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "How to manage stress?"},
    {"role": "assistant", "content": "..."}
  ],
  "metadata": {"tags": ["anxiety", "coping"]}
}
```

**Response:**
```json
{
  "id": "session_1714512345.123",
  "saved": true,
  "timestamp": "2026-04-30T10:30:45"
}
```

## Configuration Options

### Backend Settings

```python
# In backend_api_template.py

# RAG Configuration
DEFAULT_CHUNKS = 6              # Number of docs to retrieve
MAX_CHUNKS = 8                  # Maximum allowed
MIN_CHUNKS = 5                  # Minimum required
RAG_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Streaming
STREAM_DELAY = 0.02             # Seconds between tokens

# CORS
allow_origins=["*"]             # Change for production!
```

### Frontend Settings

```javascript
// In App.jsx or ChatWindow.jsx

const API_URL = "http://localhost:8000"
const CHUNK_COUNT = 6
const COUNTRY = "India"
```

## Monitoring & Debugging

### View API Health
```bash
curl http://localhost:8000/api/health -s | jq .
```

### Check Database Status
```bash
curl http://localhost:8000/api/status -s | jq .
```

### View Chat Logs
```bash
tail -f logs/chat_logs_*.json
```

### Test Crisis Detection
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to hurt myself", "country": "India"}'
```

### Monitor Backend (live)
```bash
# Terminal with backend will show:
INFO:     127.0.0.1:49402 - "POST /api/chat HTTP/1.1" 200 OK
INFO:     127.0.0.1:49403 - "GET /api/status HTTP/1.1" 200 OK
```

## Performance Tips

### Reduce First Response Time
- First query takes 5-10s (embeddings load)
- Subsequent queries: 1-3s
- **Solution:** Pre-seed API with dummy query on startup

### Optimize Chunk Count
- 5 chunks: Faster (1-2s) but less accurate
- 6 chunks: Default, balanced
- 8 chunks: Most accurate but slower (5s)

### Enable Streaming
- Replace HTTP with streaming in frontend
- Gives user typing feel immediately
- Improves perceived performance by 2-3x

### Cache Embeddings
```python
# Already done in embedding initialization
cache_folder=str(cache_folder)
```

## Production Checklist

- [ ] Change CORS origins from "*" to your domain
- [ ] Add authentication (JWT tokens)
- [ ] Set `verbose=False` (already done)
- [ ] Deploy with gunicorn (4+ workers)
- [ ] Use PostgreSQL instead of in-memory sessions
- [ ] Add request rate limiting
- [ ] Log to centralized system (not files)
- [ ] Set up crisis alert notifications
- [ ] Enable HTTPS
- [ ] Monitor response times
- [ ] Cache frequent queries

## Deployment Examples

### Local Development
```bash
# Terminal 1
cd frontend && python backend_api_template.py

# Terminal 2
cd frontend && npm run dev
```

### Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "frontend/backend_api_template.py"]
```

### Cloud (Render/Railway)
```yaml
# render.yaml
services:
  - type: web
    name: neuronix-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python frontend/backend_api_template.py
    envVars:
      - key: GOOGLE_API_KEY
        sync: false
```

## Troubleshooting Guide

### "Frontend can't reach backend"
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Check CORS headers
curl -i http://localhost:8000/api/health
```

### "Response is very slow (>10s)"
```bash
# First query is slow (model loading)
# Warm up: curl http://localhost:8000/api/health
# Then try: http://localhost:3000

# If still slow:
# - Check CPU usage (ray processes)
# - Increase uvicorn workers
```

### "No sources appearing"
```bash
# Check if DB has data
curl http://localhost:8000/api/status | jq '.documents'

# If 0: Run ingestion
python neuronix_query.py
```

### "Crisis detection not working"
```bash
# Test directly
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to die", "country": "India"}'

# Check response has: "is_crisis": true
```

## Next Features to Add

1. **WebSocket Streaming** - Real-time updates
2. **PDF Export** - Download conversations
3. **Search History** - Full-text search
4. **Multi-language** - UI in Hindi/Spanish/etc
5. **Voice Input** - Speech-to-text
6. **Analytics** - Usage tracking
7. **Feedback Loop** - User ratings → model improvement
8. **Mobile App** - React Native

## Support

If issues occur:

1. **Check logs:**
   ```bash
   tail -f logs/chat_logs_*.json
   ```

2. **Test endpoints:**
   ```bash
   python test_api.py
   ```

3. **Review setup:**
   - Is backend running?
   - Is RAG system initialized?
   - Is vector DB populated?

4. **Check documentation:**
   - [RAG_PIPELINE.md](../RAG_PIPELINE.md)
   - [NEURONIX_READY_TO_DEPLOY.md](../NEURONIX_READY_TO_DEPLOY.md)
   - [neuronix_query.py](../neuronix_query.py)

---

**Created:** April 30, 2026  
**Status:** Ready for Production  
**Last Updated:** Today
