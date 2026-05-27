# 🚀 QUICK START CARD - NEURONIX FULL STACK

## 🎯 TL;DR - 3 Commands to Run Everything

```bash
# Terminal 1 - Backend API
cd c:\Users\admin\Desktop\desktop\NEURO_MENTAL\frontend
python backend_api_template.py

# Terminal 2 - Frontend UI
cd c:\Users\admin\Desktop\desktop\NEURO_MENTAL\frontend
npm run dev

# Open Browser
http://localhost:3000
```

**That's it! Start chatting.** 💬

---

## ✅ Used Correctly?

### ✅ Backend loads without errors?
```
✅ Initializing NEURONIX RAG system...
✅ RAG system ready!
INFO: Application startup complete
```

### ✅ Frontend runs and shows welcome screen?
```
✅ Open http://localhost:3000
✅ See welcome screen with starter questions
```

### ✅ Can send a message?
```
✅ Type "Tell me about anxiety"
✅ See response appear
✅ See sources section
```

If all ✅ = **YOU'RE DONE!** System works!

---

## 🔥 Quick Test (30 seconds)

```bash
# Before starting frontend, test API directly:
cd frontend
python test_api.py

# You should see:
# ✅ Health Check: PASSED
# ✅ Chat Endpoint: PASSED
# ✅ Crisis Detection: PASSED
# 🎉 All tests passed!
```

If all pass = Backend is 100% working!

---

## ⚡ Performance Expectations

| Scenario | Time | Notes |
|----------|------|-------|
| Backend start | 2-3s | Normal |
| 1st chat query | 5-10s | Model warmup (patient!) |
| 2nd+ queries | 1-3s | Much faster |
| Crisis detection | <100ms | Instant |
| Health check | <10ms | Very fast |

---

## 🎯 Features You Have

✅ **Chat** - Ask anything about mental health
✅ **RAG** - Answers from 50,000+ documents
✅ **Sources** - Click to see where answer came from
✅ **Crisis Help** - Auto-detects emergency keywords
✅ **Suggestions** - Follow-up questions suggested
✅ **Dark Mode** - Toggle top-right
✅ **Sessions** - Save and load chats
✅ **Mobile Ready** - Works on phone too

---

## 🐛 If Something Breaks

### Backend won't start?
```bash
# Make sure Python version is 3.11+
python --version

# If modules missing:
pip install -r requirements.txt

# Try different port:
python -m uvicorn backend_api_template:app --port 8001
```

### Frontend won't connect?
```bash
# Check backend is running:
curl http://localhost:8000/api/health

# Then refresh browser (hard refresh: Ctrl+Shift+R)
```

### Responses very slow (>10s)?
```bash
# 1st time is always slow (models load)
# Ask another question - should be faster

# If still slow:
# - Check CPU/RAM (might be low)
# - Try with fewer chunks: {"chunks": 5}
```

### No response at all?
```bash
# Check DB is populated:
curl http://localhost:8000/api/status

# If documents = 0, run:
python neuronix_query.py "test"
# Wait for it to load database, then try API again
```

---

## 📱 API Endpoints (For Power Users)

```bash
# Test health
curl http://localhost:8000/api/health

# Send message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How to manage anxiety?","country":"India","chunks":6}'

# Check status
curl http://localhost:8000/api/status

# Get sessions
curl http://localhost:8000/api/sessions
```

---

## 🚨 Crisis Mode

If user types something like:
- "I want to kill myself"
- "Help I'm suicidal"  
- "How to harm myself"

**System automatically:**
1. ✅ Detects it
2. ✅ Shows hotline number
3. ✅ Gives resources
4. ✅ Doesn't process as normal query

**For India:** AASRA (22-5522-5522)
**For USA:** 988 Lifeline
**For UK:** Samaritans (116 123)

---

## 📁 Where Files Are

```
NEURO_MENTAL/
├── frontend/
│   ├── backend_api_template.py    ← Main API (run this!)
│   ├── test_api.py                ← Test script
│   ├── BACKEND_SETUP.md           ← Full setup guide
│   ├── src/                        ← React components
│   ├── package.json               ← Frontend config
│   └── package-lock.json
├── neuronix_query.py              ← RAG system (don't modify)
├── data/
│   └── vector_db/                 ← Vector database (50k docs)
├── APP.jsx                        ← React main
├── PHASE3_COMPLETE.md             ← Full docs
└── FRONTEND_BACKEND_INTEGRATION.md ← Architecture
```

---

## 🎓 How It Works (In Plain English)

1. **You type:** "How to manage stress?"
2. **Frontend sends:** Message to backend
3. **Backend receives:** Request with message
4. **Backend checks:** Is this a crisis? (No)
5. **Backend calls:** NEURONIX RAG system
6. **RAG system:**
   - Converts question to 384-dim vector
   - Searches 50,000+ documents
   - Gets 6 most similar documents
   - Sends to Gemini LLM
7. **Gemini returns:** Full formatted answer
8. **Backend extracts:** Sources from answer
9. **Backend returns:** Response + Sources + Suggestions
10. **Frontend displays:** Answer in chat bubble
11. **User sees:** Sources button they can click

---

## ⏱️ One Day Schedule

```
Morning:
9:00am - Start backend (Terminal 1)
       - Verify initialization
9:05am - Run tests (Terminal 2)
       - Ensure API working
9:10am - Start frontend (Terminal 3)
       - Open in browser

10:00am - Testing
       - Send various questions
       - Test crisis detection
       - Try dark mode
       - Save sessions

Afternoon:
2:00pm - Show to users!
       - Get feedback
       - Note issues
       - Make improvements

Evening:
6:00pm - Deploy (optional)
       - If working well, show more people
```

---

## 🎉 Congratulations!

You've built a **full-stack mental health AI assistant** with:

✅ React frontend  
✅ FastAPI backend  
✅ RAG system with 50,000+ documents  
✅ Crisis detection  
✅ Gemini LLM integration  
✅ Session management  
✅ Source citations  

This is **production-ready**!

---

## 📞 Support Quick Links

- **Setup Guide:** `BACKEND_SETUP.md`
- **Architecture:** `FRONTEND_BACKEND_INTEGRATION.md`
- **Full Docs:** `PHASE3_COMPLETE.md`
- **Test Suite:** `test_api.py` (run anytime)
- **RAG System:** `neuronix_query.py` (don't modify)
- **Logs:** `logs/chat_logs_*.json`

---

## 🚀 You're Ready!

```bash
# Just run:
cd frontend
python backend_api_template.py

# In another terminal:
cd frontend
npm run dev

# Open http://localhost:3000
# Start chatting!
```

**Enjoy your NEURONIX system! 🧠**

---

*Created: April 30, 2026*  
*Status: ✅ READY TO USE*
