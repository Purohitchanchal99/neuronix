"""
CLINICAL RESPONSE LAYER - INTEGRATION GUIDE
============================================

How to integrate DSM-5/ICD-11 routing + Hinglish tone + symptom checker
into Phase 6 (RAG Generation) and Phase 7 (REST API)

Status: Ready before Phase 6 starts
"""

# ============================================================================
# PHASE 6: RAG GENERATION LAYER MODIFICATIONS
# ============================================================================

"""
FILE: scripts/rag_pipeline/6_rag_generator.py

ADD THIS IMPORT AT TOP:
"""

from clinical_response_formatter import ClinicalResponseFormatter

"""
INSIDE get_response() function, add these modifications:

BEFORE (Basic RAG):
---
def get_response(query, context_chunks, llm):
    # 1. Format context
    formatted_context = format_for_llm(context_chunks)
    
    # 2. Send to LLM
    answer = llm.generate(formatted_context, query)
    
    # 3. Return answer
    return answer

---

AFTER (Clinical-Safe RAG):
---
def get_response(query, context_chunks, llm, user_country="India"):
    # 0. SAFETY CHECK: Detect crisis FIRST
    crisis_detector = ClinicalResponseFormatter()
    if crisis_detector._is_crisis_query(query):
        return crisis_detector._route_crisis(user_country)
    
    # 1. Format context
    formatted_context = format_for_llm(context_chunks)
    
    # 2. Create safe prompt (different for diagnosis-risk queries)
    if contains_diagnostic_keywords(query):
        safe_prompt = get_diagnosis_safe_prompt()
    else:
        safe_prompt = get_normal_prompt()
    
    # 3. Send to LLM
    answer = llm.generate(formatted_context, query, safe_prompt)
    
    # 4. Format response with clinical standards + Hinglish tone + follow-up
    formatter = ClinicalResponseFormatter()
    formatted_answer = formatter.format_response(
        rag_output=answer,
        user_query=query,
        country=user_country
    )
    
    # 5. Return formatted answer
    return formatted_answer

---

HELPER FUNCTIONS TO ADD:
"""

def contains_diagnostic_keywords(query):
    """Check if query is asking for diagnosis"""
    diagnosis_keywords = [
        "do i have", "am i", "mujhe kya hai", "mujhe ho", "kya mujhe",
        "diagnosis", "diagnose", "diagnosed", "condition", "disorder"
    ]
    return any(kw in query.lower() for kw in diagnosis_keywords)

def get_diagnosis_safe_prompt():
    """Special prompt for diagnosis-risk queries"""
    return """
You are an educational AI, NOT a doctor or therapist.
Your job is to EDUCATE about psychology, not to diagnose.

IMPORTANT RULES:
1. NEVER say "You have [condition]" or "You are [diagnosis]"
2. ALWAYS start with: "I cannot diagnose, but I can explain..."
3. Use phrases like: "Research suggests...", "Some people experience...", "This might be related to..."
4. ALWAYS end by recommending professional consultation
5. Provide educational context from the textbooks

Example response structure:
"I cannot diagnose conditions. However, based on research and psychology textbooks:
[Educational explanation]
If you're concerned, please consult a qualified mental health professional."
"""

def get_normal_prompt():
    """Normal prompt for educational queries"""
    return """
You are a helpful psychology educator.
Use the provided textbook context to answer questions.
Be clear, empathetic, and accurate.
Always provide citations.
Use conversational, friendly Hinglish tone where appropriate.
"""


# ============================================================================
# PHASE 7: REST API MODIFICATIONS
# ============================================================================

"""
FILE: scripts/rag_pipeline/7_api_server.py

MODIFY THE /chat ENDPOINT:

BEFORE (No safety layer):
---
@app.post("/chat")
async def chat(request: ChatRequest):
    response = rag_system.get_response(
        query=request.message,
        context_chunks=retrieve_context(request.message)
    )
    return {"response": response}

---

AFTER (With safety layer):
---
@app.post("/chat")
async def chat(request: ChatRequest):
    # Get user's country (from request or config)
    country = request.country or "India"
    
    # Generate response with clinical safety layer
    response = rag_system.get_response(
        query=request.message,
        context_chunks=retrieve_context(request.message),
        user_country=country
    )
    
    return {
        "response": response,
        "country": country,
        "timestamp": datetime.now().isoformat(),
        "safety_checked": True
    }

---

ADD HEALTH CHECK ENDPOINT:
---
@app.get("/health/clinical")
async def health_check():
    '''Verify clinical safety layer is active'''
    formatter = ClinicalResponseFormatter()
    
    # Test crisis detection
    crisis_test = formatter._is_crisis_query("I want to die")
    
    # Test standard routing
    countries_check = all(
        country in formatter.COUNTRY_STANDARD_MAP
        for country in ["USA", "UK", "India"]
    )
    
    return {
        "status": "healthy" if (crisis_test and countries_check) else "unhealthy",
        "crisis_detection": crisis_test,
        "country_routing": countries_check,
        "timestamp": datetime.now().isoformat()
    }

---
"""


# ============================================================================
# TESTING & VALIDATION
# ============================================================================

"""
BEFORE DEPLOYING PHASE 6-7:

1. Run clinical response tests:
   python test_clinical_framework.py
   
   Expected output: All 5 tests passing
   
2. Test integration with dummy RAG:
   python test_integration.py
   
   Expected output: Responses include disclaimer + resources + follow-up
   
3. Test crisis detection (no actual harm):
   curl -X POST http://localhost:8000/chat \\
     -H "Content-Type: application/json" \\
     -d '{"message":"I want to hurt myself", "country":"USA"}'
   
   Expected output: Immediate helplines (no RAG processing)
   
4. Test country routing:
   For query "explain depression":
   - USA → DSM-5 criteria
   - UK → ICD-11 criteria
   - India → Hybrid (ICD-11 + DSM-5)
"""


# ============================================================================
# CONFIGURATION FOR PHASE 6-7
# ============================================================================

"""
Create: config/clinical_safety_config.json

{
  "safety_layer": {
    "crisis_detection": true,
    "crisis_response_time_ms": 100,
    "disclaimer_required": true,
    "resources_required": true,
    "followup_questions": true
  },
  "clinical_standards": {
    "default_country": "India",
    "force_standard": null,  // Can override to force DSM-5, ICD-11, etc.
    "enable_hybrid": true
  },
  "helplines": {
    "primary_country": "India",
    "fallback_to_global": true,
    "update_frequency_days": 30
  },
  "tone": {
    "style": "Hinglish",
    "formality": "conversational",
    "empathy_required": true
  },
  "logging": {
    "log_crisis_queries": true,
    "log_diagnosis_risk": true,
    "log_all_responses": false
  }
}
"""


# ============================================================================
# MONITORING & METRICS
# ============================================================================

"""
Add monitoring for:

1. Crisis Detection Rate
   - How many queries trigger crisis detection?
   - Expected: <1% of queries
   
2. Response Compliance
   - % of responses with disclaimer
   - % of responses with resources
   - % of responses with follow-up (if symptom-related)
   - Target: 100% for all

3. Clinical Standard Routing
   - Accuracy of country-based standard selection
   - % of non-USA queries getting DSM-5 (should be 0)
   - % of USA queries getting DSM-5 (should be 100)

4. Crisis Response Time
   - Average time to show helplines for crisis queries
   - Target: <100ms

5. User Feedback
   - Tone appropriateness (does Hinglish feel natural?)
   - Helpful follow-up questions?
   - Would user consult professional?
"""


# ============================================================================
# ERROR HANDLING
# ============================================================================

"""
What if clinical_response_formatter.py fails?

Add fallback in Phase 6-7:

def safe_format_response(rag_output, query, country="India"):
    try:
        formatter = ClinicalResponseFormatter()
        return formatter.format_response(rag_output, query, country)
    except Exception as e:
        # Fallback: Return minimalist response with disclaimer
        logging.error(f"Clinical formatter failed: {e}")
        return f"{rag_output}\\n\\n---\\n⚠️ Always consult a professional.\\n"

This ensures even if formatter breaks, safety layer is never removed.
"""


# ============================================================================
# PHASE 6-7 TIMELINE WITH CLINICAL LAYER
# ============================================================================

"""
PHASE 6: RAG GENERATION (35 minutes)
  □ Core RAG logic (20 min)
  □ Integrate clinical_response_formatter (10 min)
  □ Test with dummy data (5 min)

PHASE 7: REST API (40 minutes)
  □ FastAPI setup (15 min)
  □ /chat endpoint with safety layer (15 min)
  □ /health/clinical endpoint (5 min)
  □ Test all endpoints with clinical cases (5 min)

TOTAL: ~75 minutes (within 3-hour Express window)
"""


# ============================================================================
# ROLLOUT STRATEGY
# ============================================================================

"""
OPTION A: Full Rollout (Express)
- Deploy with all safety features enabled
- Risk: Lower (all features are safe additions)
- Timeline: Deploy with Phase 7

OPTION B: Phased Rollout (Recommended)
- Day 1: Deploy crisis detection only
  - Test corner cases
  - Verify <100ms response time
- Day 2: Deploy Hinglish tone + follow-up
  - Gather user feedback on tone
  - Refine templates if needed
- Day 3: Deploy disclaimer + resources
  - Verify compliance metrics
  - Check user understanding

OPTION C: A/B Testing
- 50% users get new clinical layer
- 50% users get baseline
- Compare metrics after 1 week
- Rollout based on results
"""

print(__doc__)
