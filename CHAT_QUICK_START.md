# Neuronix Chat Engine - Quick Start

## One-Command Startup

### Prerequisites ✅
1. Vector database created: ✅ (from ingest_data.py)
2. Google API key: ✅ (from makersuite.google.com)
3. Dependencies installed: ✅ (from setup.py)

### Start Chat Engine

**Set API Key:**
```powershell
$env:GOOGLE_API_KEY = "your-api-key"
```

**Run Chat:**
```bash
python backend/chat_engine.py
```

---

## What You'll See

```
[Initializing Neuronix Chat Engine...]

[OK] Initializing Google Gemini embeddings...
[OK] Loading Chroma vector database...
[OK] Initializing Gemini LLM (1.5 Pro)...
[OK] Loading master mapping...
[OK] Initializing RetrievalQA chain...
[OK] Neuronix Chat Engine initialized successfully!

================================================================================
✨ NEURONIX - Clinical Psychology AI Assistant
================================================================================

नमस्ते! 👋 I'm Neuronix, your clinical companion.
आप अपने स्वास्थ्य के बारे में कुछ भी पूछ सकते हैं।

Type 'exit' or 'bye' to end chat
Type 'clear' to reset conversation
================================================================================

आप: [Type your question here]
```

---

## Example Queries to Try

### Simple Questions
```
आप: क्या है depression?
आप: Anxiety कैसे होती है?
आप: Mental health क्यों important है?
आप: थेरेपी से क्या फायदा होता है?
```

### Personal Concerns (with Empathy)
```
आप: मुझे बहुत चिंता होती है, ये चलेगा नहीं
आप: मुझे नींद की समस्या है
आप: मेरा confidence बहुत कम हो गया
आप: रिलेशनशिप की समस्या है
```

### Seeking Help
```
आप: मुझे कहां Counseling मिल सकती है?
आप: Depression का treatment क्या होता है?
आप: Therapy session कैसे काम करती है?
```

---

## Chat Commands

| Command | What It Does |
|---------|-------------|
| Any question | Get Hinglish response with sources |
| `clear` | Start fresh conversation |
| `history` | Show all messages so far |
| `exit` | End chat and save logs |
| `bye` | Same as exit |
| `quit` | Same as exit |

---

## Sample Interaction

```
आप: मुझे बहुत stress feel हो रहा है पिछले दिनों में

Neuronix: आपकी चिंता बिल्कुल valid है! Stress एक common experience है,
खासकर modern life में।

Stress के symptoms:
• Physical: headaches, muscle tension
• Emotional: irritability, anxiety
• Behavioral: sleep issues, appetite changes

**क्या आप कर सकते हैं?**
1. Daily exercise करें (30 minutes)
2. Meditation या deep breathing करें
3. अपने दिन को structured बनाएं
4. Friends/family से बात करें

अगर 2 weeks से ज्यादा चले तो एक mental health specialist 
से consult करना अच्छा रहेगा।

📚 Sources:
• stress_psychology.txt (India) - [Free]

आप: ठीक है, meditation कैसे करते हैं?

Neuronix: [Continues conversation with more guidance...]
```

---

## Features Demo

### Feature 1: Hinglish Response
```
English + Hindi mixed naturally
"Aapke darr ki baat bilkul valid hai. 
Yeh condition treat ho sakti hai."
```

### Feature 2: Source Citations
```
📚 Sources:
• cognitive_psychology.txt (India) - [Free]
• modern_psychology.pdf (Germany) - [Paid]
```

### Feature 3: Free Alternatives
```
📚 FREE ALTERNATIVE (का फ्री विकल्प):
India में available:
• IGNOU Cognitive Module - Free
• Psychology Foundation Resources - Free
```

### Feature 4: Safety Detection
If you mention self-harm keywords:
```
🆘 MENTAL HEALTH CRISIS HELPLINES (भारत):

1. AASRA: +91-9820466726 (24/7, Free)
2. Vandrevala Foundation: +91-9999 666 555
3. iCall: +91-9152987821 (Teens)
4. Indore Mental Health: 0731-2538888

आपका जीवन important है। Please call करें।
```

---

## Tips for Best Results

### 1. Be Specific
❌ "मैं upset हूँ"
✅ "मुझे हर रोज सुबह anxiety attack आता है, heart तेज़ चलने लगता है"

### 2. Share Context
❌ "क्या ये depression है?"
✅ "मुझे 2 महीने से नींद नहीं आ रही, सब boring लगता है, खाना नहीं खा रहा हूँ"

### 3. Ask Follow-ups
✅ Ask multiple questions in one chat
✅ Neuronix remembers context
✅ Progressive conversation works better

### 4. Clear if Starting Over
```
आप: clear
✓ Conversation cleared. नया बातचीत शुरू करते हैं!

आप: [Complete new topic]
```

---

## Troubleshooting

### "GOOGLE_API_KEY environment variable not set"
```powershell
$env:GOOGLE_API_KEY = "your-api-key-here"
python backend/chat_engine.py
```

### "Vector database not found"
```bash
# First run the ingestion pipeline
python scripts/ingest_data.py
# Then try chat again
python backend/chat_engine.py
```

### "Responses are too generic"
- Be more specific in your question
- Provide more context
- Neuronix responds better to detailed queries

### "Response is very long"
- Type `clear` and start fresh
- Ask more specific questions
- Neuronix will tailor responses

---

## What Neuronix Can Do

✅ **Can Do:**
- Explain mental health concepts
- Provide emotional support and validation
- Suggest coping strategies
- Recommend when to see specialist
- Answer clinical psychology questions
- Provide crisis helplines

❌ **Cannot Do:**
- Diagnose medical conditions
- Prescribe medications
- Replace therapy/professional help
- Provide emergency medical treatment
- Handle legal/financial advice

---

## For Developers

### Running Programmatically

```python
from backend.chat_engine import NeuronixChatEngine
import os

# Initialize
engine = NeuronixChatEngine(
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# Single query
response = engine.chat("मुझे anxiety है")
print(response)

# Get history
history = engine.get_history()
print(history)

# Clear and start fresh
engine.clear_history()
```

### Accessing in Flask/FastAPI

```python
from fastapi import FastAPI
from backend.chat_engine import NeuronixChatEngine

app = FastAPI()
engine = NeuronixChatEngine()

@app.post("/chat")
def chat(message: str):
    response = engine.chat(message)
    return {"response": response}
```

---

## Cost & Performance

**Google API Costs:**
- ~$0.00001 per query (very cheap!)
- Free tier: 60 queries/minute
- Only charged when running

**Response Speed:**
- First response: 5-10 seconds
- Subsequent queries: 2-5 seconds
- Safety check: <100ms

---

## File Structure

```
NEURO_MENTAL/
├── backend/
│   ├── chat_engine.py        [Main chat engine]
│   └── [FastAPI endpoints - coming soon]
├── data/
│   ├── master_mapping.json   [Resource mapping]
│   └── vector_db/            [Knowledge base]
├── scripts/
│   ├── ingest_data.py        [Create vector_db]
│   └── chat_engine_log.txt   [Logs]
└── CHAT_ENGINE.md            [Full documentation]
```

---

## Next Steps

1. ✅ Run: `python backend/chat_engine.py`
2. ✅ Try sample questions
3. ⏳ Integrate with FastAPI (REST API)
4. ⏳ Build frontend UI (React/Streamlit)
5. ⏳ Add user authentication
6. ⏳ Deploy to production

---

## Questions?

📖 Full docs: [CHAT_ENGINE.md](CHAT_ENGINE.md)
📖 RAG info: [RAG_PIPELINE.md](RAG_PIPELINE.md)
📖 Setup help: [QUICK_START.md](QUICK_START.md)

---

**Ready?** Run this:
```bash
python backend/chat_engine.py
```

Then type: `मेरी चिंता के बारे में बताऊँ?`

Enjoy chatting with Neuronix! 🧠💙
