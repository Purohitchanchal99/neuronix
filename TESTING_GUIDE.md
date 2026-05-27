# 🧪 How to Test Neuronix Chatbot Answer Generation

## Quick Tests (No Code)

### Method 1: Use the Web UI with Debug Mode ✅ RECOMMENDED

1. **Open the chat**: http://localhost:8501
2. **Enable Debug Mode** in sidebar (checkbox: 🔧 Debug Mode)
3. **Type a test message** like: `"i am stressed"`
4. **Click Send**
5. **Look for** the "🔍 Debug Info" section that appears below the response

**What to check in Debug Info:**
- ✅ **Retrieval Results**: Shows if documents were found
  - If it says "3 documents found" → Vector DB is working!
  - If it says "No documents" → Vector DB is empty
- ✅ **Query Type**: Should show "CLINICAL" for mental health questions
- ✅ **Raw chunks**: Shows actual content retrieved

---

### Method 2: Check Server Logs

Watch the **terminal where Streamlit is running** (http://localhost:8501 terminal):

**Good Signs:**
```
✅ [RAG] Successfully retrieved 2 documents
🎯 DETECTED INTENT: MENTAL_HEALTH
[MODE] Doctor Mode (RAG + Clinical)
```

**Bad Signs (Retrieval Failing):**
```
⚠️ [RAG] No documents retrieved for: 'depression'
⚠️ [RAG] All retrieved docs were too short/noisy
```

---

## Test Cases (What to Try)

### Test 1: Clinical Query (Should retrieve documents)
```
User: "i am depressed"
Expected: Response with mental health advice
Bad: "No relevant documents found"
```

### Test 2: Hindi Query
```
User: "majhe tension hai"
Expected: Response in Hinglish with advice
Bad: Generic greeting repeated
```

### Test 3: Very Specific Query
```
User: "how to manage anxiety symptoms?"
Expected: Detailed response with coping strategies  
Bad: Empty or "no documents"
```

### Test 4: Casual Query
```
User: "how is weather?"
Expected: Friendly casual response
Good: Different from clinical response mode
```

---

## Verification Checklist

### ✅ Vector Database
- [ ] Vector DB file exists: `data/vector_db/chroma.sqlite3`
- [ ] DB directory has subdirectories: `data/vector_db/[uuid]/`

### ✅ Document Retrieval
```
Enable Debug Mode → Ask: "depression"
→ Check if "Retrieval Results: X documents found"
```

### ✅ Response Quality
- [ ] Responses are **not repeated** generic text
- [ ] Different queries get **different answers**
- [ ] Mental health queries → Clinical response
- [ ] Casual queries → Friendly response

### ✅ Language Detection
- [ ] English → English response
- [ ] Hindi/Hinglish → Hinglish response
- [ ] Mixed → Appropriate response

---

## Quick Test in Browser

1. Click sidebar arrow `>>` to collapse sidebar
2. Open browser DevTools (F12)
3. Go to **Console** tab
4. Type a message in chat
5. Watch the **Network** tab for API calls
6. Check **Elements** tab to see if response container has content

---

## Debug Mode Output Example

```
🔍 Debug Info

Retrieval Results: 3 documents found
Doc 1:
Depression is a mental health condition...
[Shows 300 chars of actual content]

Query Type: CLINICAL
```

---

## If Retrieval is Failing (Empty DB)

### Action 1: Check DB Status Button
1. Enable Debug Mode
2. Click "📊 Show DB Status" button
3. Look at output

### Action 2: Run Ingestion Script
If DB is empty, ingest documents:
```bash
python ingest_target_pdfs.py
```

### Action 3: Verify Vector Store
After ingestion, check:
```bash
python check_db_status.py
```

---

## What Each Response Type Means

### ✅ Good Response (with Documents)
```
Aapka stress samajh raha hoon.  
Stress management ke liye ye tips:
1. Deep breathing...
2. Exercise...
```
→ **Has retrieval context**

### ⚠️ Fallback Response (no documents)
```
Mujhe relevant documents nahi mile. 
Example: • Specific problem kya hai?
📌 Ye details dene se main better help kar sakta hoon
```
→ **No retrieval context - DB might be empty**

### ✅ Casual Response (non-clinical)
```
Bilkul bhai! 🌂 Weather accha hai aaj...
```
→ **Handled as casual query, not clinical**

---

## Terminal Log Monitoring

Keep the Streamlit terminal visible to see real-time:
```
[NEURONIX PIPELINE] Processing new user input...
📝 ORIGINAL INPUT: anxiety attacks
🔄 NORMALIZED QUERY: anxiety attacks
🌍 RESPONSE LANGUAGE: english

[MODE] Doctor Mode (RAG + Clinical)        ← GOOD!
🎯 DETECTED INTENT: MENTAL_HEALTH
✅ [RAG] Successfully retrieved 2 documents ← GOOD!
```

---

## Summary: How to Know If It's Working

| Check | Working ✅ | Not Working ❌ |
|-------|-----------|-----------------|
| **Type message** | Response appears | No response |
| **Debug Mode** | Shows retrieved docs | "No documents" |
| **Logs** | `[MODE] Doctor Mode` | `[MODE] Indore Dost` for clinical q |
| **DB Status** | Documents shown | Empty/error |
| **Response variety** | Different per question | Same generic text |

Good luck testing! 🍀
