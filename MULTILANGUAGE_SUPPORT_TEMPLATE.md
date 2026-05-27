# Multi-Language Support Template

**For adding new languages to NEURONIX chat engine**

## Current Supported Languages
- ✅ Hindi (हिंदी)
- ✅ Hinglish (हिंग्लिश/English Mix)
- ✅ English

## Languages to Add (Future)
- 🔜 Italian (Italiano)
- 🔜 French (Français)
- 🔜 Korean (한국어)
- 🔜 Japanese (日本語)
- 🔜 Russian (Русский)
- 🔜 Chinese (中文)
- 🔜 Latvian (Latviešu)
- 🔜 [Any other language]

---

## How to Add a New Language

### **Step 1: Add to `language_instructions` Dictionary**

Location: `backend/chat_engine.py`, in `_create_prompt_template()` method

```python
language_instructions = {
    "Hindi": """...""",
    "Hinglish": """...""",
    "English": """...""",
    
    # NEW LANGUAGE TEMPLATE:
    "[LANGUAGE_NAME]": """[Your language text here]
    
Your role: Supportive mental health friend, not a system

Your style:
- Be empathetic and human-like
- Don't sound like a textbook
- Give direct answer FIRST, then explain if needed
- If unsure, indicate uncertainty
- If someone seems distressed, respond with care and suggest professional help

⭐ SHORT ANSWER MODE:
- Keep answer concise (4-6 lines), but COMPLETE and meaningful
- Avoid unnecessary explanations
- Be direct while staying substantive
- BUT: If serious mental health issue, prioritize clarity and completeness over brevity

If question is unclear: [Translation of clarification request]

Critical safety:
- If self-harm/crisis signs: [Translation of crisis response with local resources]
- Always prioritize safety and accuracy over learned preferences

⭐ EDGE CASE: Best Guess
- If you have tried to ask clarifying questions but didn't get details:
  [Translation: "Based on what you've shared, it sounds like..."]
- This gives user clarity about certainty level

⭐ IMPORTANT - PRIORITIZE CLARITY OVER PERSONALIZATION:
- Your learned preferences are helpful, BUT
- Always prioritize clarity, accuracy, and user safety
- In mental health, correctness comes before customization

[Use context to answer, but explain simply in your own words.]
Be genuinely [language-appropriate].
"""
}
```

### **Step 2: Update `_detect_language_simple()`**

Location: Around line 1150 in `backend/chat_engine.py`

Add language detection for your language:

```python
def _detect_language_simple(self, text: str) -> str:
    """Detect user's language"""
    text_lower = text.lower()
    
    # Existing detections...
    if any(c in text for c in hindi_chars):
        return "Hindi"
    if any(w in text_lower for w in hinglish_keywords):
        return "Hinglish"
    
    # NEW LANGUAGE DETECTION:
    # For Italian
    if any(w in text_lower for w in ["ciao", "grazie", "aiuto", "mamma", "papà"]):
        return "Italian"
    
    # For French
    if any(w in text_lower for w in ["bonjour", "merci", "aide", "maman", "papa"]):
        return "French"
    
    # [Add more language detection logic]
    
    return "English"  # Default fallback
```

### **Step 3: Update Crisis Keywords**

Location: Around line 2025 in `_check_safety()` method

```python
strict_crisis_keywords = [
    # English crisis phrases
    'hurt myself', 'kill myself', 'suicide', 'suicidal', 'want to die',
    # ...existing keywords...
    
    # Italian crisis phrases
    'suicidio', 'voglio morire', 'farmi male', 'non ne posso più',
    
    # French crisis phrases
    'suicide', 'je veux mourir', 'me faire mal', 'c\'est trop',
    
    # [Add more language crisis keywords]
]
```

### **Step 4: Test New Language**

Create a test file:

```python
engine = NeuronixChatEngine()

# Test detection
print(engine._detect_language_simple("Ciao, come stai?"))  # Should return "Italian"

# Test response
response = engine._handle_mental_health("Ho problemi di stress")
print(response)
```

---

## Template Components (Must Include in ALL Languages)

Every new language prompt must contain:

✅ **Role Definition**
```
"You are a supportive mental health friend, not..."
```

✅ **Style Guidelines** (be empathetic, human-like, etc.)

✅ **Short Answer Mode** (4-6 lines, but complete)

✅ **Safety Priority Over Brevity**
```
"If serious mental health issue, prioritize clarity over brevity"
```

✅ **Vague Query Handling**
```
"If question is unclear: [How to ask for clarification]"
```

✅ **Crisis Response**
```
"If self-harm/crisis signs: [Compassionate response + local helplines]"
```

✅ **Best Guess Clarity**
```
"Show when making educated guess: 'Based on what you've shared...'"
```

✅ **IMPORTANT - PRIORITIZE CLARITY**
```
"Always prioritize clarity, accuracy, and user safety
In mental health, correctness comes before customization"
```

---

## Language-Specific Considerations

### **Italian (Italiano)**
- Use formal "Lei" or informal "tu" based on context
- Local crisis resources: Telefono Amico, Centro Nazionale Salute Mentale
- Mention "stai bene?" for wellness check

### **French (Français)**
- Use "vous" for formal, "tu" for informal
- Local resources: SOS Amitié, France 3 Santé Mentale
- Common phrases: "Je comprends," "Comment ça va?"

### **Korean (한국어)**
- Use appropriate formal/informal speech levels (존댓말, 반말)
- Local resources: 전국 정신건강 위기상담 전화
- Important: Respect hierarchical communication

### **Japanese (日本語)**
- Use keigo (敬語) for formal settings
- Local resources: 厚生労働省 こころの相談
- Important: Context and implied meaning are crucial

### **Russian (Русский)**
- Use appropriate formal/informal "ты" vs "вы"
- Local resources: Служба психологической помощи
- Note: Emotional directness is culturally appropriate

### **Chinese (中文)**
- Distinguish Simplified vs Traditional characters
- Local resources: 全国心理援助热线 (National Mental Aid Hotline)
- Important: Consider cultural context of mental health stigma

### **Latvian (Latviešu)**
- Use appropriate formality levels
- Local resources: Latvijas Psihologu Savieniba (Psychological Association)
- Note: Language learners may have different expectations

---

## Pattern for Crisis Resources by Language

**Hindi:**
```
📞 Vandrevala: +91-9999 666 555
📞 AASRA: +91-9820466726
📞 iCall: +91-9152987821
```

**Add for each language:**
```
**[Language]:**
📞 [Organization 1]: [Phone/Contact]
📞 [Organization 2]: [Phone/Contact]
📞 [Organization 3]: [Phone/Contact]
```

---

## Detection Keywords for Each Language

Keep keyword lists for:
1. Mental health specific terms (stress, anxiety, depression, etc.)
2. Crisis indicators (hopeless, give up, etc.)
3. Uncertainty markers (not sure, unclear, might be, etc.)
4. Preference signals (short, detailed, etc.)

Example for Italian:
```python
italian_stress_keywords = ["stress", "ansia", "depressione", "tristezza", "preoccupazione"]
italian_crisis_keywords = ["disperato", "senza speranza", "voglio morire", "mi faccio male"]
italian_uncertainty = ["non sono sicuro", "forse", "potrebbe essere", "non so"]
```

---

## Multi-Language Auto-Detection Priority

The system detects language in this order (update as needed):

1. **Character-based** (Hindi script, Chinese characters, etc.)
2. **Keyword-based** (Common words)
3. **Fallback:** English

---

## File Locations to Update for New Language

- ✏️ `backend/chat_engine.py`:
  - Line ~1240: Add to `language_instructions` dict
  - Line ~1150: Update `_detect_language_simple()` 
  - Line ~2025: Add crisis keywords in `_check_safety()`
  - Line ~710-730: Add to learning system for tone/language preference
  
- ✏️ Any data files or mapping files if language-specific resources needed

---

## Testing Checklist for New Language

- ✅ Language detection works
- ✅ Prompts render correctly (no encoding issues)
- ✅ Crisis keywords trigger appropriately
- ✅ Vague query detection works
- ✅ Safety always prioritized
- ✅ Learning system tracks language preference
- ✅ No syntax errors in chat_engine.py

---

## Future: Locale-Specific Features

```python
# Could add in future:
locale_settings = {
    "Italian": {
        "currency": "EUR",
        "helpline_country": "Italy",
        "local_resources": [...],
        "cultural_notes": [...],
    },
    "Japanese": {
        "currency": "JPY",
        "helpline_country": "Japan",
        "local_resources": [...],
        "cultural_notes": [...],
    },
}
```

---

**Use this template when adding: Italian, French, Korean, Japanese, Russian, Chinese, Latvian, or any other language!** 🌍
