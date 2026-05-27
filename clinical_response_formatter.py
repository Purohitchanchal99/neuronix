"""
Clinical Response Formatter Module
===================================

Ensures all RAG responses meet:
1. DSM-5/ICD-11/Hybrid/Global clinical standards
2. Hinglish tone (not formal clinical jargon)
3. Doctor-style follow-up questions (symptom checker)
4. Auto-appended disclaimers + resources
5. Crisis detection + immediate routing

Use in: Phase 6 (RAG Generation) + Phase 7 (API Server)
"""

from typing import Dict, List, Optional, Tuple
import re


class ClinicalResponseFormatter:
    """
    Formats RAG responses to meet clinical safety + accuracy standards
    """
    
    # Country to clinical standard mapping
    COUNTRY_STANDARD_MAP = {
        "USA": "DSM-5",
        "Canada": "DSM-5",
        "Australia": "DSM-5",
        "South Korea": "DSM-5",
        "UK": "ICD-11",
        "Germany": "ICD-11",
        "France": "ICD-11",
        "Netherlands": "ICD-11",
        "Sweden": "ICD-11",
        "Finland": "ICD-11",
        "Norway": "ICD-11",
        "Switzerland": "ICD-11",
        "Italy": "ICD-11",
        "Spain": "ICD-11",
        "Japan": "ICD-10",
        "India": "Hybrid",  # ICD-11 + DSM-5
    }
    
    # Crisis keywords (English + Hinglish)
    CRISIS_KEYWORDS = {
        "english": [
            "suicide", "kill myself", "overdose", "poison", "hang", "jump", "rope",
            "hate myself", "self-harm", "cut", "hurt myself", "end it all"
        ],
        "hindi": [
            "aatmhatya", "maut", "mar jaun", "apne aap ko maarna", "khud ko maarna",
            "sab khatam", "jaan de duun", "jhooth bolna", "khud se nuksaan"
        ]
    }
    
    # Symptom trigger keywords
    SYMPTOM_TRIGGERS = {
        "sleep": ["neend", "sleep", "insomnia", "sone mein", "raat ko"],
        "anxiety": ["anxiety", "tension", "worry", "fear", "ghabrana", "tension"],
        "depression": ["depression", "sad", "hopeless", "udaas", "nihaar"],
        "stress": ["stress", "pressure", "tension", "load", "daba"]
    }
    
    # Helplines by country
    HELPLINES = {
        "India": [
            ("AASRA", "+91-9820466726", "24/7, Free"),
            ("iCall", "+91-9152987821", "9 AM-11 PM"),
            ("Vandrevala", "+91-9999 666 555", "24/7, Free"),
        ],
        "USA": [
            ("988 Suicide & Crisis Lifeline", "Call 988", "24/7, Free"),
            ("Crisis Text Line", "Text HOME to 741741", "24/7, Free"),
            ("SAMHSA National Helpline", "1-800-662-4357", "24/7, Free"),
        ],
        "UK": [
            ("Samaritans", "116 123", "24/7, Free"),
            ("Mind Infoline", "0300 123 3393", "9 AM-6 PM"),
            ("Rethink Mental Illness", "0808 801 0414", "9 AM-5 PM"),
        ],
    }
    
    def __init__(self):
        pass
    
    def format_response(
        self,
        rag_output: str,
        user_query: str,
        country: str = "India",
        standard_preference: Optional[str] = None
    ) -> str:
        """
        Format RAG output with clinical standards + safety layer
        
        Args:
            rag_output: Raw RAG response from LLM
            user_query: User's input query
            country: User's country (for standard + helplines)
            standard_preference: Force specific standard (e.g., "DSM-5")
        
        Returns:
            Formatted response with tone, disclaimer, resources
        """
        
        # Step 1: Detect crisis (immediate routing)
        if self._is_crisis_query(user_query):
            return self._route_crisis(country)
        
        # Step 2: Determine clinical standard
        standard = standard_preference or self.COUNTRY_STANDARD_MAP.get(country, "Global")
        
        # Step 3: Add Hinglish tone wrapper
        response = self._wrap_hinglish_tone(rag_output, standard)
        
        # Step 4: Add symptom checker follow-up
        follow_up = self._symptom_checker(user_query)
        if follow_up:
            response += f"\n\n🩺 Doctor-style follow-up questions:\n{follow_up}"
        
        # Step 5: Auto-append disclaimer + resources
        response += self._append_disclaimer_and_resources(country)
        
        return response
    
    def _is_crisis_query(self, query: str) -> bool:
        """Detect if query contains crisis keywords"""
        query_lower = query.lower()
        
        # Check English crisis keywords
        if any(keyword in query_lower for keyword in self.CRISIS_KEYWORDS["english"]):
            return True
        
        # Check Hindi crisis keywords
        if any(keyword in query_lower for keyword in self.CRISIS_KEYWORDS["hindi"]):
            return True
        
        return False
    
    def _route_crisis(self, country: str) -> str:
        """Return immediate crisis helplines (no RAG query)"""
        
        response = f"""
🚨 CRISIS SUPPORT AVAILABLE (24/7, FREE)

I understand you're in distress. Please reach out to one of these services immediately:
"""
        
        helplines = self.HELPLINES.get(country, self.HELPLINES["India"])
        
        for service_name, contact, hours in helplines:
            response += f"\n• {service_name}: {contact} ({hours})"
        
        response += """

PLEASE CALL IMMEDIATELY. 💙
You are not alone. We care about you.
"""
        
        return response
    
    def _wrap_hinglish_tone(self, clinical_facts: str, standard: str) -> str:
        """Wrap clinical facts in Hinglish tone (not formal)"""
        
        tone_templates = {
            "DSM-5": "Bhai, samajh raha hoon. DSM-5 ke hisaab se ye symptoms ho sakte hain:\n\n",
            "ICD-11": "Samajh raha hoon. ICD-11 standard ke anusar ye ho sakta hai:\n\n",
            "ICD-10": "Samajhta hoon. ICD-10 classification ke anusar:\n\n",
            "Hybrid": "Bilkul samajhta hoon. India mein ICD-11 aur DSM-5 dono use hote hain:\n\n",
            "Global": "Samajh raha hoon. Global medical standards ke anusar:\n\n"
        }
        
        opener = tone_templates.get(standard, tone_templates["Global"])
        return opener + clinical_facts
    
    def _symptom_checker(self, user_query: str) -> Optional[str]:
        """Ask doctor-style follow-up questions if symptoms detected"""
        
        triggers_for_query = {
            "sleep": [
                "Ye problem kab se ho rahi hai?",
                "Din bhar ya sirf raat ko?",
                "Kya racing thoughts aate hain?",
                "Kya body tension mahsus hota hai?"
            ],
            "anxiety": [
                "Anxiety kab worst hota hai?",
                "Kya specific situations trigger karte hain?",
                "Kya physical symptoms bhi hain (racing heart, sweating)?",
                "Family history mein anxiety?"
            ],
            "depression": [
                "Ye mood kab badla?",
                "Sleep/food/energy bhi affected ho rahe?",
                "Social activities mein interest gaya?",
                "Major life changes ho rahi hain?"
            ],
            "stress": [
                "Stress kis baat se ho raha?",
                "Kitne din se ye chal raha hai?",
                "Family ya work mein problem?",
                "Support system hai?"
            ]
        }
        
        query_lower = user_query.lower()
        
        for symptom, triggers in self.SYMPTOM_TRIGGERS.items():
            if any(trigger in query_lower for trigger in triggers):
                followups = triggers_for_query.get(symptom, [])
                return "\n".join(followups[:2])  # Return first 2 questions
        
        return None
    
    def _append_disclaimer_and_resources(self, country: str) -> str:
        """Auto-append disclaimer + country-specific resources"""
        
        disclaimer = """
---
⚠️ IMPORTANT DISCLAIMER:
मैं एक AI educator हूँ, doctor नहीं।
(I am an AI educator, not a doctor.)

Self-diagnosis करना सही नहीं है।
(Self-diagnosis is not advisable.)

कृपया किसी qualified mental health professional से consult करें।
(Please consult a qualified mental health professional.)
"""
        
        # Get country-specific resources
        resources = self._get_country_resources(country)
        
        return disclaimer + resources
    
    def _get_country_resources(self, country: str) -> str:
        """Return country-specific free resources + helplines"""
        
        resources_map = {
            "India": """
🏥 HELPLINES (24/7, FREE):
• AASRA: +91-9820466726
• iCall: +91-9152987821
• Vandrevala: +91-9999 666 555

📚 FREE LEARNING RESOURCES:
• OpenStax Psychology 2e (free textbook)
• NOBA Project (nobaproject.com)
• Khan Academy Psychology
• IGNOU Psychology Materials
""",
            "USA": """
🏥 CRISIS LINES (24/7, FREE):
• 988 Suicide & Crisis Lifeline
• Crisis Text Line: Text HOME to 741741
• SAMHSA: 1-800-662-4357

📚 FREE LEARNING RESOURCES:
• OpenStax Psychology 2e
• Khan Academy
• MIT OCW Psychology
• Coursera Psychology Courses (audit free)
""",
            "UK": """
🏥 HELPLINES (24/7, MOST FREE):
• Samaritans: 116 123
• Mind Infoline: 0300 123 3393
• Rethink Mental Illness: 0808 801 0414

📚 FREE LEARNING RESOURCES:
• Mind (mind.org.uk)
• Every Mind Matters (nhs.uk)
• BBC Learning - Psychology
• Khan Academy
""",
        }
        
        default = resources_map["India"]
        return resources_map.get(country, default)
    
    @staticmethod
    def validate_response_quality(response: str) -> Dict[str, bool]:
        """
        Validate response against quality criteria
        Returns dict of validation checks
        """
        
        checks = {
            "has_disclaimer": "⚠️" in response or "DISCLAIMER" in response,
            "has_resources": "📚" in response or "FREE" in response.upper(),
            "has_helplines": "🏥" in response or "+" in response,  # Phone numbers
            "has_empathy": "samajh" in response.lower() or "understand" in response.lower(),
            "no_formal_tone": "hereby" not in response.lower() and "aforementioned" not in response.lower(),
            "uses_citations": "•" in response or "-" in response,  # List format
        }
        
        return checks


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    formatter = ClinicalResponseFormatter()
    
    # Example 1: DSM-5 Depression query
    print("="*70)
    print("EXAMPLE 1: DSM-5 Depression (USA)")
    print("="*70)
    
    sample_rag_output = """
    Depression is characterized by persistent low mood. Key features include:
    - Loss of interest in activities (anhedonia)
    - Changes in sleep pattern
    - Fatigue or loss of energy
    - Difficulty concentrating
    - Feelings of worthlessness or guilt
    """
    
    formatted = formatter.format_response(
        rag_output=sample_rag_output,
        user_query="I feel sad and hopeless. Am I depressed?",
        country="USA"
    )
    
    print(formatted)
    
    # Example 2: Symptom checker (India)
    print("\n" + "="*70)
    print("EXAMPLE 2: Symptom Checker (India)")
    print("="*70)
    
    sample_rag_output2 = """
    Sleep problems can be caused by anxiety, stress, or medical conditions.
    """
    
    formatted2 = formatter.format_response(
        rag_output=sample_rag_output2,
        user_query="Mujhe neend nahi aa rahi",
        country="India"
    )
    
    print(formatted2)
    
    # Example 3: Crisis detection
    print("\n" + "="*70)
    print("EXAMPLE 3: Crisis Detection")
    print("="*70)
    
    formatted3 = formatter.format_response(
        rag_output="[Would not be called]",
        user_query="I want to hurt myself",
        country="USA"
    )
    
    print(formatted3)
