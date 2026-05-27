# Day 4: Memory & Empathy - Setup & Quick Start

## 🎯 What's New in Day 4

### 1. **Short-Term Memory System** 🧠
- **File:** `backend/session_manager.py` (SQLite database)
- **Feature:** Stores last 5 exchanges before responding
- **Benefit:** Neuronix now remembers conversation context and mood patterns

### 2. **Tone Analyzer** 😊
- **Location:** `backend/chat_engine.py` (ToneAnalyzer class)
- **Detects:** Sad, Anxious, Frustrated, or Neutral emotions
- **Adjusts:** System prompt intensity based on emotional state

### 3. **Streamlit Web Interface** 🌐
- **File:** `app.py`
- **Run:** `streamlit run app.py`
- **Access:** Browser-based chat (no terminal needed!)

---

## 📦 Installation

### Step 1: Install Streamlit
```powershell
pip install streamlit
```

### Step 2: Verify Session Manager
```powershell
python backend/session_manager.py
# Should output: ✅ Session manager test complete!
```

### Step 3: Start the Web App
```powershell
streamlit run app.py
```

This will:
- Open your browser automatically
- Show Neuronix chat interface
- Display conversation stats in sidebar
- Store all messages in SQLite database

---

## 🗂️ File Structure

```
NEURO_MENTAL/
├── app.py                          [NEW] Streamlit web interface
├── backend/
│   ├── chat_engine.py             [UPDATED] Integrated session manager + tone analyzer
│   ├── session_manager.py          [NEW] SQLite chat history + memory
│   └── __pycache__/
└── data/
    ├── neuronix_sessions.db        [AUTO-CREATED] SQLite database
    └── vector_db/
```

---

## 🎮 Using the Web App

### Step 1: Enter Your Info (Sidebar)
- Select your country (USA, India, UK, Germany, France)
- Choose response language (Hinglish, Hindi, English)

### Step 2: Chat
- Type question in the input box
- Neuronix responds with empathetic Hinglish
- Conversation is automatically saved

### Step 3: View Stats (Sidebar)
- Total messages count
- Primary mood detected
- Mood trend chart
- Conversation history

### Step 4: Session Management
- **Clear Chat**: Delete current session history (keeps user profile)
- **New Session**: Create new user + start fresh conversation

---

## 🧠 Memory System Details

### What Gets Stored?
Each chat exchange stores:
```json
{
  "user_id": "59c52486",
  "user_query": "Mujhe anxiety hai",
  "ai_response": "Samajh sakta hoon...",
  "detected_mood": "anxious",
  "detected_intent": "MENTAL_HEALTH",
  "clinical_standard": "ICD-11 + DSM-5",
  "timestamp": "2026-04-23 13:50:14"
}
```

### Memory Retrieval
Before answering, Neuronix gets:
- Last 5 exchanges
- Mood trend (how many sad/anxious messages)
- Conversation stats (primary mood, intent)

**Example:** If user sent 3 anxious messages, Neuronix increases empathy level automatically.

---

## 😊 Tone Analyzer Levels

| Tone | Example Input | System Prompt Adjustment | Response Style |
|------|---------------|--------------------------|------------------|
| **Sad** | "I feel so alone" | HIGH empathy | Reassuring + Hopeful |
| **Anxious** | "I'm very worried" | MEDIUM-HIGH empathy | Calming + Structured |
| **Frustrated** | "I'm fed up" | MEDIUM empathy | Validating + Solution-focused |
| **Neutral** | "What is anxiety?" | STANDARD | Professional + Friendly |

---

## 🔄 Session Manager API

```python
from backend.session_manager import SessionManager

manager = SessionManager()

# Create user
user_id = manager.create_user("Kratik", country="India")

# Store message
manager.add_message(
    user_id,
    "Mujhe anxiety hai",
    "Samajh sakta hoon...",
    detected_mood="anxious"
)

# Retrieve memory (last 5 exchanges)
memory = manager.get_memory(user_id, limit=5)

# Get formatted context for LLM
context = manager.get_conversation_context(user_id)

# Analyze mood trend
trend = manager.get_mood_trend(user_id)

# Get stats
stats = manager.get_conversation_stats(user_id)
```

---

## 📊 Database Schema

### users table
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    country TEXT,
    language TEXT,
    preferred_standard TEXT,
    created_at TIMESTAMP,
    last_active TIMESTAMP
);
```

### chat_history table
```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_query TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    detected_mood TEXT,
    detected_intent TEXT,
    clinical_standard TEXT,
    timestamp TIMESTAMP
);
```

### conversation_metrics table
```sql
CREATE TABLE conversation_metrics (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_date DATE,
    total_exchanges INTEGER,
    mood_trend TEXT,
    primary_topics TEXT,
    crisis_detected BOOLEAN
);
```

---

## 🧪 Test the Integration

### Terminal Test (Chat Engine Memory)
```powershell
python backend/chat_engine.py
```
Then chat normally - messages will be stored in SQLite.

### Web App Test
```powershell
streamlit run app.py
```
- Open browser to http://localhost:8501
- Chat and watch sidebar stats update in real-time

### Database Inspection
```powershell
python -c "
from backend.session_manager import SessionManager
m = SessionManager()
stats = m.get_conversation_stats('YOUR_USER_ID')
print(stats)
"
```

---

## ⚙️ Customization

### Change Mood Keywords (ToneAnalyzer)
Edit `backend/chat_engine.py` → `ToneAnalyzer.__init__()`:
```python
self.emotion_keywords = {
    "sad": ["your", "custom", "keywords"],
    # ...
}
```

### Change Memory Limit
Default: last 5 exchanges
```python
# In app.py or chat_engine.py
memory = manager.get_memory(user_id, limit=10)  # Get 10 instead
```

### Change Streamlit Theme
Edit `app.py` → `st.set_page_config()`:
```python
st.set_page_config(
    theme="dark",  # or "light"
)
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"
```powershell
pip install streamlit
```

### "Database locked" error
- Only one Streamlit instance can access database at a time
- Close other terminals and try again

### "GOOGLE_API_KEY not set"
```powershell
$env:GOOGLE_API_KEY = "your-key-here"
streamlit run app.py
```

### Streamlit page not loading
```powershell
# Clear Streamlit cache
streamlit cache clear
streamlit run app.py --logger.level=debug
```

---

## 📈 Next Steps (Day 5 onwards)

1. **Multi-language Support** 🌍
   - Detect user's language (Hindi/English/Spanish)
   - Auto-respond in same language

2. **Advanced Memory** 🧠
   - Long-term trend analysis (mood over weeks)
   - Personalized coping strategies based on history

3. **Integration with Real DB** 🗄️
   - PostgreSQL/MySQL for production
   - Cloud storage for scalability

4. **Mobile App** 📱
   - React Native / Flutter app
   - Native notifications for crisis support

---

## 📞 Support

For issues or questions:
1. Check logs: `scripts/chat_engine_log.txt`
2. Test components: `python backend/session_manager.py`
3. Review database: SQLite browser (download free tool)

---

**Status: ✅ Day 4 Complete**
- Memory system: ✅ Working
- Tone analyzer: ✅ Working
- Web interface: ✅ Working
- 5/5 Clinical tests: ✅ Passing

Ready for Day 5! 🚀
