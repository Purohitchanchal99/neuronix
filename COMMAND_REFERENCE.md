# Neuronix Chat Engine - Command Reference

## 🚀 Quick Startup Commands

### 1️⃣ Set API Key (First Time Only)
```powershell
$env:GOOGLE_API_KEY = "your-api-key-here"
```
Get your key from: https://makersuite.google.com/app/apikey

### 2️⃣ Create Vector Database (First Time Only)
```powershell
python scripts/ingest_data.py
```

**Expected output:**
```
[OK] Documents loaded successfully
[OK] Chunks created with overlap
[OK] Database initialized
[OK] Full pipeline completed
```

### 3️⃣ Start Chat Engine
```powershell
python backend/chat_engine.py
```

---

## 💬 Sample Chat Queries

### Test Basic Anxiety Response
```
You: मुझे anxiety से बहुत tension हो जाता है
Neuronix: आपका डर बिल्कुल valid है...
```

### Test Depression Query
```
You: मेरी motivation खो गई है
Neuronix: Depression में ये feeling normal है...
```

### Test Resource Finding
```
You: free counseling कहाँ मिल सकता है
Neuronix: India में available free resources...
```

### Test Safety System (Detection Testing)
```
You: mujhe apne aap ko maarna hai
Neuronix: 🆘 CRISIS DETECTED - Shows helplines immediately
```

---

## ⌨️ Chat Engine Commands

While chatting, use these commands:

```
clear       → Clear all conversation history
history     → Show full conversation
exit        → End chat
bye         → End chat
quit        → End chat
help        → Show available commands
```

### Example Usage:
```
You: clear
[History cleared]

You: history
[Shows your full conversation]

You: exit
[Chat engine closes]
```

---

## 📋 File Reference

### Core Scripts
```
scripts/ingest_data.py      → RAG pipeline (creates vector DB)
scripts/query_rag.py        → Search interface
backend/chat_engine.py      → Interactive chat engine
```

### Documentation
```
CHAT_ENGINE.md              → Full technical documentation
CHAT_QUICK_START.md         → Quick usage guide
PROJECT_STATUS.md           → Implementation status
COMMAND_REFERENCE.md        → This file
```

### Data Files
```
data/vector_db/             → Vector database (created by ingest_data.py)
data/master_mapping.json    → Free/paid resource mapping
docs/India/                 → Sample documents for RAG
logs/chat_engine_log.txt    → Chat engine logs
```

---

## 🔍 Testing Commands

### Test 1: Verify Imports Are Working
```powershell
python -c "from langchain_google_genai import ChatGoogleGenerativeAI; print('[OK] Gemini ready')"
```

### Test 2: Check Vector Database
```powershell
python -c "import chromadb; print('[OK] ChromaDB ready')"
```

### Test 3: Quick Demo (No API Key Needed)
```powershell
python scripts/demo_ingest.py
```

### Test 4: Full Chat Engine
```powershell
python backend/chat_engine.py
# Type: नमस्ते
# Type: exit
```

---

## 🛠️ Troubleshooting Commands

### Check Your API Key is Set
```powershell
Write-Host $env:GOOGLE_API_KEY
# Should show your key (or be empty if not set)
```

### Set API Key Again
```powershell
$env:GOOGLE_API_KEY = "your-actual-key"
```

### Verify Paths Exist
```powershell
dir "c:\Users\admin\Desktop\desktop\NEURO_MENTAL\data\vector_db\"
# Should show files (or be empty if not created yet)
```

### View Recent Logs
```powershell
Get-Content -Tail 20 "logs\chat_engine_log.txt"
```

### Clear Vector Database (To Start Fresh)
```powershell
Remove-Item -Recurse -Force "data\vector_db\"
# Then run: python scripts/ingest_data.py
```

---

## 📊 Sample Conversation Flow

```
=== Neuronix Chat Engine Started ===
Neuronix: नमस्ते! मैं Neuronix हूँ।
         आपकी mental health के लिए यहाँ हूँ।
         कृपया बताएं, क्या समस्या है?

You: मुझे बहुत चिंता होती है

Neuronix: आपकी चिंता bilkul valid है।
         आज कल stress सब को होता है।
         यह एक natural response है।

You: thanks

Neuronix: आपका स्वागत है।

You: exit

[Chat engine closed]
```

---

## ⚡ One-Line Quick Commands

### Setup Everything at Once
```powershell
$env:GOOGLE_API_KEY = "your-key"; python scripts/ingest_data.py; python backend/chat_engine.py
```

### Just Run Chat (After Setup)
```powershell
python backend/chat_engine.py
```

### View Last 50 Lines of Logs
```powershell
Get-Content "logs\chat_engine_log.txt" -Tail 50
```

---

## 🎓 Hinglish Examples the System Understands

✅ "मुझे anxiety है"  
✅ "depression se kaise bachu"  
✅ "therapy kahan milgi"  
✅ "free resources de"  
✅ "aaj ka mood bohot badh hai"  
✅ "sleep bilkul nahi aa rahi"  
✅ "feeling very alone"  
✅ "निराशा महसूस हो रही है"  

---

## 📱 Key Features You Can Test

### Feature 1: Symptom Explanation
```
Ask: क्या मुझे depression है?
Neuronix explains symptoms, causes, treatment
```

### Feature 2: Coping Strategies
```
Ask: Anxiety से बचने के लिए क्या करूँ?
Neuronix suggests practical techniques
```

### Feature 3: Resource Finding
```
Ask: Free counseling कहाँ मिल सकता है?
Neuronix maps paid -> free alternatives
```

### Feature 4: Crisis Support (Automatic)
```
Ask: Any self-harm keyword
Neuronix: 🆘 HELPLINES DISPLAYED IMMEDIATELY
```

### Feature 5: Conversation History
```
Command: history
Shows full conversation with sources
```

---

## 🔐 Safety System Test

### Crisis Keywords That Trigger (Don't use unless testing)
English: suicide, kill, overdose, poison, hang, jump, rope  
Hinglish: aatmhatya, maut, mar jaun, khud ko maarna, sab khatam

### Automatic Response When Detected
```
🆘 CRISIS SUPPORT AVAILABLE:

AASRA: +91-9820466726 (24/7, Free)
Vandrevala: +91-9999 666 555 (24/7)
iCall: +91-9152987821 (9 AM-11 PM)
Indore: 0731-2538888 (Local)

Please call immediately. 💙
```

---

## 📈 What Happens Behind the Scenes

```
1. You: Type Hinglish query
2. Engine: Checks for crisis keywords (instant)
3. Engine: Retrieves top 3 relevant docs from ChromaDB
4. Engine: Sends to Gemini 1.5 Pro with context
5. Engine: Gemini generates Hinglish response
6. Engine: Adds source citations
7. Engine: Suggests free alternatives
8. Engine: Saves to conversation history
9. You: See formatted response with sources
```

---

## 🎯 Most Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: GOOGLE_API_KEY` | Set: `$env:GOOGLE_API_KEY = "key"` |
| Vector database not found | Run: `python scripts/ingest_data.py` |
| Empty responses | Check `/data/vector_db/` exists |
| No sources in response | Database not initialized |
| Permission errors | Run PowerShell as Administrator |

---

## 🏃 Quick Start (Copy & Paste This)

```powershell
# Step 1: Set API key (get from https://makersuite.google.com/app/apikey)
$env:GOOGLE_API_KEY = "YOUR-API-KEY-HERE"

# Step 2: Create database
python scripts/ingest_data.py

# Step 3: Start chatting
python backend/chat_engine.py

# Step 4: Type these to test:
# English: why am i anxious
# Hinglish: मुझे क्या depression है
# Hinglish: therapy कहाँ मिल सकता है
# Command: history
# Command: exit
```

---

## 📞 Getting Help

### For Technical Issues
- Check diagnostic: `python backend/chat_engine.py`
- View logs: `Get-Content logs/chat_engine_log.txt -Tail 50`
- Run demo: `python scripts/demo_ingest.py`

### For Usage Questions
- Read: `CHAT_QUICK_START.md`
- Try sample queries from this file
- Use 'history' command to see context

---

## ✨ Summary

✅ **Simple to use**: Just 3 commands  
✅ **Natural Hinglish**: Talks like a human  
✅ **Safe**: Detects crises instantly  
✅ **Smart**: Uses RAG for accuracy  
✅ **Production-ready**: Enterprise code quality  

---

**Ready to start? Copy the Quick Start section above and paste into PowerShell!** 🚀

---

Created: April 15, 2026  
Version: 1.0  
Status: ✅ Ready to Use
$env:GOOGLE_API_KEY = "your-api-key-from-makersuite.google.com"
python scripts/ingest_data.py
python backend/chat_engine.py