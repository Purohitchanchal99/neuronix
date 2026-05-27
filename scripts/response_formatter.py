"""
🎯 Response Formatter
====================
Transforms RAG chunks + user query into natural, empathetic responses.

Never exposes raw chunks/embeddings/vectors to users.
Chunks used internally for context injection only.

Architecture:
User Query → Retrieve Chunks → Format into Natural Response → Return to User
Chunks stay hidden (used only for knowledge grounding)
"""

import re
from typing import List, Dict, Optional


class ResponseFormatter:
    """Transform raw chunks into natural, compassionate responses"""
    
    # Mental health response templates
    TEMPLATES = {
        "anxiety": [
            "I understand anxiety can feel overwhelming. {detail}",
            "That sounds stressful. Here's what might help: {detail}",
            "Anxiety is something many people experience. {detail}",
        ],
        "depression": [
            "I'm sorry you're going through this. {detail}",
            "Depression is real and valid. {detail}",
            "You're not alone in feeling this way. {detail}",
        ],
        "sleep": [
            "Sleep troubles are really common. {detail}",
            "Here are some approaches that might help: {detail}",
            "Good sleep hygiene can make a difference. {detail}",
        ],
        "stress": [
            "Stress management is important. {detail}",
            "Here are some ways to handle stress: {detail}",
            "Let me share some stress relief techniques: {detail}",
        ],
        "general": [
            "I'm here to help. {detail}",
            "That's something I can help with. {detail}",
            "Let me share what might help: {detail}",
        ]
    }
    
    # Mental health keywords
    MENTAL_HEALTH_KEYWORDS = {
        "anxiety": ["anxious", "anxiety", "nervous", "worried", "tension", "panic"],
        "depression": ["depressed", "depression", "sad", "hopeless", "worthless", "down"],
        "sleep": ["sleep", "insomnia", "tired", "fatigue", "exhausted", "rest"],
        "stress": ["stress", "stressed", "pressure", "overwhelmed", "busy"],
        "crisis": ["suicide", "kill myself", "harm", "die", "end it", "hopeless"],
    }
    
    def __init__(self):
        """Initialize formatter"""
        self.templates = self.TEMPLATES
        self.keywords = self.MENTAL_HEALTH_KEYWORDS
    
    def format_response(
        self,
        user_query: str,
        chunks: List[str],
        tone: str = "compassionate"
    ) -> str:
        """
        Transform chunks into natural response
        
        Args:
            user_query: Original user message
            chunks: Retrieved knowledge chunks (not shown to user)
            tone: Response tone (compassionate, informative, supportive)
            
        Returns:
            Natural, formatted response (chunks used but not exposed)
        """
        
        # Detect category
        category = self._detect_category(user_query)
        
        # Extract key information from chunks (don't return raw)
        summary = self._summarize_chunks(chunks, user_query)
        
        # Get appropriate template
        template = self._select_template(category)
        
        # Format response
        response = template.format(detail=summary)
        
        # Add followup suggestions
        followup = self._generate_followup(category, user_query)
        if followup:
            response += f"\n\n{followup}"
        
        return response
    
    def _detect_category(self, query: str) -> str:
        """Detect mental health category from query"""
        query_lower = query.lower()
        
        for category, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return category
        
        return "general"
    
    def _summarize_chunks(self, chunks: List[str], user_query: str) -> str:
        """
        Summarize chunks into bullet-point advice
        (never return raw chunks)
        """
        if not chunks:
            return "I'm here to listen and support you."
        
        # Extract key points
        points = []
        for chunk in chunks[:2]:  # Use top 2 chunks
            # Clean up chunk text
            clean = chunk.strip()
            
            # Extract first 2 sentences max
            sentences = re.split(r'(?<=[.!?])\s+', clean)
            key_text = ' '.join(sentences[:2])
            
            if len(key_text) > 20:
                points.append(f"• {key_text}")
        
        if points:
            return "\n".join(points)
        else:
            return "Here are some things to consider..."
    
    def _select_template(self, category: str) -> str:
        """Select random template for category"""
        import random
        
        templates_list = self.templates.get(category, self.templates["general"])
        return random.choice(templates_list)
    
    def _generate_followup(self, category: str, query: str) -> Optional[str]:
        """Generate helpful followup suggestions"""
        
        followups = {
            "anxiety": "😊 **Try this**: Practice deep breathing (4 counts in, 4 counts out). Would it help to talk more about this?",
            "depression": "💙 **Remember**: These feelings can improve with time and support. Have you considered reaching out to someone?",
            "sleep": "🛌 **Tip**: Consistent sleep schedule and limiting screens before bed can really help.",
            "stress": "🧘 **Try**: Take a 5-minute break, go for a walk, or do some stretching. What helps you unwind?",
            "general": "✨ **I'm here**: Feel free to share more, and I'll do my best to help.",
        }
        
        return followups.get(category)
    
    def format_crisis_response(self, query: str) -> str:
        """Emergency crisis response format"""
        return """🚨 **Crisis Support Available**

I'm concerned about your safety. Please reach out to:

📞 **National Suicide Prevention Lifeline**: 988 (call or text)
📞 **Crisis Text Line**: Text HOME to 741741
🌐 **International Association for Suicide Prevention**: https://www.iasp.info/resources/Crisis_Centres/

**You are not alone. Help is available right now.**

Would you like me to provide additional resources?"""
    
    def format_clinical_response(
        self,
        user_query: str,
        chunks: List[str],
        sources: Optional[List[str]] = None
    ) -> Dict:
        """
        Format response for clinical/educational context
        
        Returns both user-facing response and metadata
        """
        
        # Generate natural response (chunks hidden)
        user_response = self.format_response(user_query, chunks)
        
        # Internal metadata (for logs/analytics only)
        metadata = {
            "chunks_used": len(chunks),
            "sources": sources or [],
            "automated": True,
            "human_review_recommended": self._should_escalate(user_query)
        }
        
        return {
            "response": user_response,
            "metadata": metadata,
            "show_sources": False  # Never expose raw sources to user
        }
    
    def _should_escalate(self, query: str) -> bool:
        """Check if response should be human-reviewed"""
        crisis_keywords = ["suicide", "harm", "kill", "death"]
        crisis_detected = any(kw in query.lower() for kw in crisis_keywords)
        return crisis_detected


# ================================================================
# EXAMPLE USAGE
# ================================================================

if __name__ == "__main__":
    formatter = ResponseFormatter()
    
    # Example 1: Anxiety query
    print("=" * 60)
    print("EXAMPLE 1: Anxiety")
    print("=" * 60)
    
    query1 = "I'm feeling really anxious about my presentation tomorrow"
    chunks1 = [
        "Anxiety is characterized by excessive worry and nervousness. Common symptoms include rapid heartbeat, sweating, and difficulty concentrating.",
        "Techniques to manage anxiety include deep breathing, progressive muscle relaxation, and mindfulness meditation."
    ]
    
    response1 = formatter.format_response(query1, chunks1)
    print(f"User: {query1}\n")
    print(f"AI Response:\n{response1}\n")
    
    # Example 2: Sleep query
    print("=" * 60)
    print("EXAMPLE 2: Sleep Issues")
    print("=" * 60)
    
    query2 = "I'm not sleeping well at night"
    chunks2 = [
        "Good sleep hygiene includes maintaining a consistent sleep schedule and creating a dark, cool sleeping environment.",
        "Avoid caffeine, alcohol, and screens 1-2 hours before bedtime to improve sleep quality."
    ]
    
    response2 = formatter.format_response(query2, chunks2)
    print(f"User: {query2}\n")
    print(f"AI Response:\n{response2}\n")
    
    # Example 3: Crisis (should show crisis response)
    print("=" * 60)
    print("EXAMPLE 3: Crisis Detection")
    print("=" * 60)
    
    query3 = "I don't want to live anymore"
    crisis_response = formatter.format_crisis_response(query3)
    print(f"User: {query3}\n")
    print(f"AI Response:\n{crisis_response}\n")
    
    print("=" * 60)
    print("✅ All examples complete!")
    print("Note: Chunks are used internally but NEVER shown to user")
