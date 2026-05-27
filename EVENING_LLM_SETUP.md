# 🚀 EVENING SESSION - LLM + DATABASE INTEGRATION

**Time Estimate:** 4 hours  
**Difficulty:** Medium  
**Impact:** System becomes production-ready

---

## ⚡ QUICK START (Do This First)

### Step 0: Get API Key (5 min)

**Choose ONE:**

**Option A: Google Gemini (EASIER)**
```
1. Go to: https://ai.google.dev/
2. Click "Get API key" (top right)
3. Click "Create API key in new project"
4. Copy the key
5. Paste into .env as GEMINI_API_KEY=YOUR_KEY
```

**Option B: OpenAI GPT (More Popular)**
```
1. Go to: https://platform.openai.com/api-keys
2. Login with your account
3. Click "Create new secret key"
4. Copy the key
5. Paste into .env as OPENAI_API_KEY=YOUR_KEY
6. Change LLM_PROVIDER=openai in .env
```

### Step 1: Create .env File (2 min)
```bash
cd c:\Users\admin\Desktop\desktop\NEURO_MENTAL
cp .env.example .env
# Now edit .env and paste your API key
```

### Step 2: Test LLM Integration (5 min)
```bash
python llm_integration_wrapper.py
```

Should see:
```
✅ Testing LLM Integration
📋 Test 1: Simple Question
Response: Anxiety is... [REAL RESPONSE FROM API]
```

---

## 🎯 MAIN WORK (Order Matters)

### PHASE 1: Connect Real LLM (60 min)

**What to do:**
- Replace simulated responses in `context_aware_ai_system.py`
- Current: Line ~850 returns `simulated_response`
- Replace with: `real_llm_response()` using our wrapper

**Exact Steps:**

1. Open: `context_aware_ai_system.py`

2. Around line 850, find:
```python
# CURRENT (Simulated)
simulated_response = f"I understand you're asking about '{question}'..."
return simulated_response
```

3. Replace with:
```python
# NEW (Real LLM)
from llm_integration_wrapper import get_llm_response

response = get_llm_response(
    prompt=full_prompt,  # Already has context
    system_prompt=self.system_prompt_manager.get_system_prompt(user_context),
    temperature=0.7
)

return response
```

4. Test:
```bash
python scripts/quick_clinical_queries.py
```

Should see: Real responses + 7/7 PASS

---

### PHASE 2: Add Database Persistence (90 min)

**What to do:**
- Save user profiles + interactions to database (not memory)
- This enables multi-session learning

**Exact Steps:**

1. Create `database_models.py`:
```python
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True)
    expertise_level = Column(String, default="beginner")
    interests = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Interaction(Base):
    __tablename__ = "interactions"
    
    interaction_id = Column(String, primary_key=True)
    user_id = Column(String)
    question = Column(String)
    response = Column(String)
    quality_score = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
```

2. Modify `context_aware_ai_system.py`:
```python
# Add at start of ContextAwareAISystem class
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_models import Base, User, Interaction

class ContextAwareAISystem:
    def __init__(self, db_path="sqlite:///neuronix.db"):
        # ... existing code ...
        
        # Add database
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
```

3. Save interactions:
```python
def _save_interaction(self, user_id, question, response, score):
    session = self.Session()
    interaction = Interaction(
        interaction_id=str(uuid.uuid4()),
        user_id=user_id,
        question=question,
        response=response,
        quality_score=score
    )
    session.add(interaction)
    session.commit()
    session.close()
```

4. Load user profiles from DB:
```python
def register_user(self, user_id):
    session = self.Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    
    if not user:
        user = User(user_id=user_id)
        session.add(user)
        session.commit()
    
    session.close()
    return user
```

5. Test:
```bash
python scripts/quick_clinical_queries.py
# Check neuronix.db file was created
# Query the database to verify data is saved
```

---

### PHASE 3: Integration Test (30 min)

**What to test:**

1. User 1 asks question → Response saved to DB
2. User 1 asks again → System reads from DB, improves response
3. User 2 asks question → Uses own profile, not User 1's context

```bash
# Run full test suite
python scripts/quick_clinical_queries.py

# Check database
sqlite3 neuronix.db
> SELECT COUNT(*) FROM interactions;
> SELECT * FROM users;
```

---

### PHASE 4: Update Documentation (15 min)

**Add to deployment guide:**
```markdown
## Production Setup

1. Get API key (Gemini or OpenAI)
2. Create .env file from .env.example
3. Add API key to .env
4. Install: pip install -r requirements.txt
5. Run: python scripts/quick_clinical_queries.py

Database automatically created on first run.
```

---

## ✅ Success Checklist

By end of evening:

- [ ] .env file created with API key
- [ ] `llm_integration_wrapper.py` tested successfully
- [ ] `context_aware_ai_system.py` modified to use real LLM
- [ ] `database_models.py` created
- [ ] Database persistence working
- [ ] Clinical queries return REAL responses (not simulated)
- [ ] 7/7 test queries PASS with real responses
- [ ] Database has saved interactions
- [ ] Documentation updated

---

## 🔧 Troubleshooting

**"API key not found"**
- Check .env file has GEMINI_API_KEY or OPENAI_API_KEY
- Restart Python (old env variables cached)

**"Module not found: google.generativeai"**
- Run: `pip install google-generativeai` (for Gemini)
- Or: `pip install openai` (for OpenAI)

**"Database locked"**
- Close all Python instances
- Delete neuronix.db
- Restart

**"Tests still showing simulated responses"**
- Check import was added to context_aware_ai_system.py
- Verify get_llm_response() is being called
- Check .env has valid API key

---

## 📝 Reference Code Locations

**Where to add imports:**
- Top of `context_aware_ai_system.py` (after existing imports)

**Where simulated_response is called:**
- Search for: `simulated_response =`
- Replace entire block

**Where to add DB initialization:**
- `ContextAwareAISystem.__init__()` method

**Where to save responses:**
- `ContextAwareAISystem.process_query()` method (after quality_assessment)

---

## ⏰ Timeline

| Phase | Time | Status |
|-------|------|--------|
| Get API Key | 5 min | ✅ Easy |
| Test LLM Wrapper | 5 min | ✅ Easy |
| Integrate Real LLM | 60 min | 🔶 Medium |
| Add Database | 90 min | 🔶 Medium |
| Integration Test | 30 min | ✅ Easy |
| Documentation | 15 min | ✅ Easy |
| **TOTAL** | **4 hrs** | ✅ Doable |

---

## 🚀 After This Session

System will have:
- ✅ Real LLM responses (no more simulation)
- ✅ Persistent user profiles
- ✅ Learning across sessions
- ✅ Ready for frontend integration
- ✅ Production-deployable

Next: Docker containerization → Live deployment
