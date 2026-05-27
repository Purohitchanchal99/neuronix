# 🏥 CLINICAL POWERHOUSE - TEST COMMAND REFERENCE

## Quick Copy-Paste Commands

### Step 1: Navigate to Project
```powershell
cd "C:\Users\admin\Desktop\desktop\NEURO_MENTAL"
```

### Step 2: Set API Key (Required)
```powershell
$env:GOOGLE_API_KEY = 'your-actual-google-api-key-here'
```

Verify it's set:
```powershell
Write-Host $env:GOOGLE_API_KEY
```

---

## 🧪 TEST SUITE EXECUTION

### Run All 5 Tests (Automated)
```powershell
python test_clinical_powerhouse.py
```

**Expected Output:**
```
🏥 NEURONIX CLINICAL POWERHOUSE - COMPREHENSIVE TEST SUITE
================================================================================
🏥 TEST 1: DSM-5 Depression Criteria
  ✅ PASS: DSM-5 Reference Present
  ✅ PASS: Symptoms Listed
  ✅ PASS: Self-Diagnosis Disclaimer
  ✅ PASS: Free Alternative Suggested
  ✅ PASS: Friendly Tone (Hinglish)

🏥 TEST 2: ICD-11 Anxiety Criteria
  ✅ PASS: ICD-11 Reference Present
  ✅ PASS: Anxiety Criteria Mentioned
  ✅ PASS: WHO Standard Mentioned
  ✅ PASS: Professional Advice Given
  ✅ PASS: Friendly Response

🏥 TEST 3: Symptom Checker Follow-up Questions
  ✅ PASS: Follow-up Question Present
  ✅ PASS: Doctor-like Inquiry
  ✅ PASS: Not Instant Diagnosis
  ✅ PASS: Empathetic Tone

🏥 TEST 4: Clinical Standard Routing
  ✅ PASS: USA uses DSM-5
  ✅ PASS: India uses Hybrid
  ✅ PASS: UK uses ICD-11

🏥 TEST 5: Free Resource Detection
  ✅ PASS: Correctly counts total
  ✅ PASS: Correctly counts free
  ✅ PASS: Correctly counts paid
  ✅ PASS: Accuracy % calculated
  ✅ PASS: Correct benchmark status

📋 TEST SUMMARY
✅ PASS: Test 1: DSM-5 Depression
✅ PASS: Test 2: ICD-11 Anxiety
✅ PASS: Test 3: Symptom Checker
✅ PASS: Test 4: Multi-Country Routing
✅ PASS: Test 5: Free Resource Detection

TOTAL: 5/5 tests passed
🎉 ALL TESTS PASSED! Clinical Powerhouse is ready to go! 🚀
```

---

## 💬 MANUAL TEST QUERIES

### Start Interactive Chat
```powershell
python backend/chat_engine.py
```

### Test Query 1️⃣: DSM-5 Depression (PRIMARY TEST)
```
INPUT:  Bhai, mujhe lag raha hai mujhe Depression hai, DSM-5 ke hisaab se kya symptoms hote hain?

EXPECTED CHECKS ✅:
  ✅ Contains "DSM-5" reference
  ✅ Lists depression symptoms/criteria
  ✅ Mentions "self-diagnosis" disclaimer
  ✅ References free resources (IGNOU, Psychology2e, etc.)
  ✅ Uses Hinglish tone ("Bhai", "toh", "sab theek", etc.)
```

### Test Query 2️⃣: ICD-11 Support
```
INPUT:  Mujhe anxiety bohot h, ICD-11 standard ke hisaab?

EXPECTED CHECKS ✅:
  ✅ References "ICD-11" or "WHO"
  ✅ Explains anxiety criteria
  ✅ Mentions it's WHO standard
  ✅ Suggests professional consultation
```

### Test Query 3️⃣: Symptom Checker (Insomnia)
```
INPUT:  Mujhe neend nahi aa rahi

EXPECTED CHECKS ✅:
  ✅ Response includes follow-up question (with "?" mark)
  ✅ Questions like: "Kab se?", "Baar baar jagte ho?", "Kyun aata hai?"
  ✅ Does NOT say "You have insomnia" immediately
  ✅ Shows empathy: "bohot annoying", "normal problem", etc.
```

### Test Query 4️⃣: Spelling + Hinglish
```
INPUT:  stres aur depresun ho gya (misspelled + Hinglish)

EXPECTED CHECKS ✅:
  ✅ Correctly normalizes "stres" → "stress"
  ✅ Correctly normalizes "depresun" → "depression"
  ✅ Addresses both stress AND depression
  ✅ Provides solutions for both
```

### Test Query 5️⃣: Casual Query (Should NOT be Medical)
```
INPUT:  Indore ke weather kaise hai?

EXPECTED CHECKS ✅:
  ✅ Friendly, casual response
  ✅ NOT clinical/medical tone
  ✅ Natural Hinglish conversational style
  ✅ May include Indore-specific reference (rajwada, ghat, etc.)
```

---

## 📊 VALIDATION CHECKLIST

### After Running Tests, Verify:

```
✅ Syntax (Compile Check):
   python -m py_compile backend/chat_engine.py
   python -m py_compile test_clinical_powerhouse.py

✅ Test Suite Results:
   TOTAL: 5/5 tests passed ✅

✅ Manual Test 1 (DSM-5):
   [ ] Response mentions DSM-5
   [ ] Lists 5+ symptoms
   [ ] Includes disclaimer
   [ ] Free resources mentioned
   [ ] Hinglish tone present

✅ Manual Test 2 (ICD-11):
   [ ] Mentions ICD-11/WHO
   [ ] Explains standard
   [ ] Professional advice given

✅ Manual Test 3 (Symptom Checker):
   [ ] Follow-up question asked
   [ ] No instant diagnosis
   [ ] Doctor-like inquiry

✅ Manual Test 4 (Typo Handling):
   [ ] Misspellings corrected
   [ ] Hinglish interpreted
   [ ] Dual symptoms handled

✅ Manual Test 5 (Casual):
   [ ] Friendly tone
   [ ] Not overly clinical
   [ ] Conversational
```

---

## 🔍 LOG ANALYSIS

### Check Logs for Clinical Routing:
```powershell
# View recent logs
Get-Content scripts/chat_engine_log.txt -Tail 50
```

### Look for These Log Lines:
```
[CLINICAL-STANDARD] India → Primary: ICD-11 + DSM-5  ✅
[CLINICAL] Detected: depression                       ✅
[SYMPTOM-CHECKER] depression → Asking follow-up      ✅
[RAG-ACCURACY] Free: 4/5 (80.0%) - GOOD              ✅
[FORMAT] Added DSM-5 reference                        ✅
[MENTAL-HEALTH] Detected symptom: depression         ✅
```

---

## 🚨 TROUBLESHOOTING

### "API Error" or "Connection Error"
```powershell
# Solution 1: Check API key is valid
$env:GOOGLE_API_KEY = 'your-key-here'

# Solution 2: Check internet connection
Test-NetConnection google.com -Port 443

# Solution 3: Check if Gemini API is enabled in Google Cloud
# Visit: https://console.cloud.google.com/
```

### "Module not found" Error
```powershell
# Install missing dependencies
pip install python-dotenv langchain rapidfuzz langchain-google-genai langchain-community
```

### Tests Fail Unexpectedly
```powershell
# Check chat engine runs without test framework
python backend/chat_engine.py

# Type a simple test query:
# INPUT: "Hello"
# Should get: Friendly response

# Then exit with: exit
```

---

## 📈 SUCCESS METRICS

✅ **All 5 automated tests pass**
✅ **DSM-5/ICD-11 queries answered correctly**
✅ **Symptom checker asks follow-up questions**
✅ **Free resources are identified and listed**
✅ **Multi-language support working**

---

## 🎯 FINAL VERIFICATION

Run this complete sequence:

```powershell
# 1. Setup
cd "C:\Users\admin\Desktop\desktop\NEURO_MENTAL"
$env:GOOGLE_API_KEY = 'your-key'

# 2. Syntax Check
python -m py_compile backend/chat_engine.py
python -m py_compile test_clinical_powerhouse.py

# 3. Run Test Suite
python test_clinical_powerhouse.py

# 4. Watch for: "5/5 tests passed" ✅

# 5. Expected Result:
# 🎉 ALL TESTS PASSED! Clinical Powerhouse is ready to go! 🚀
```

---

## 📝 NOTES

- **Duration**: Full test suite takes ~30-60 seconds (depends on API)
- **Internet**: Required for Gemini API calls
- **API Cost**: Minimal (Gemini free tier usually covers testing)
- **Logs**: Check `scripts/chat_engine_log.txt` for detailed info

---

**Status**: ✅ READY FOR TESTING  
**Next**: Run `python test_clinical_powerhouse.py`  
**Target**: 5/5 tests passed ✅  

---

## 🎬 START HERE

```powershell
# Copy-paste this complete sequence:

cd "C:\Users\admin\Desktop\desktop\NEURO_MENTAL"
$env:GOOGLE_API_KEY = 'your-api-key-here'
python test_clinical_powerhouse.py
```

Expected: **All 5 tests PASS** ✅
