#!/usr/bin/env python3
"""
Phase 3A: Conversation Memory System
=====================================
Tracks conversation history and context across messages

Critical for:
  - Understanding "It's been happening for 2 weeks" (needs prior context)
  - Detecting patterns over time
  - Building real relationship
  - Contextual responses
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Message:
    """Single message in conversation"""
    timestamp: datetime
    role: str  # 'user' or 'assistant'
    content: str
    tone: Optional[str] = None  # emotional, informational, neutral
    distress_level: Optional[float] = None  # 0.0 to 1.0
    keywords: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'role': self.role,
            'content': self.content,
            'tone': self.tone,
            'distress_level': self.distress_level,
            'keywords': self.keywords
        }


@dataclass
class ConversationHistory:
    """Full conversation history for a user"""
    user_id: str
    created_at: datetime
    messages: List[Message] = field(default_factory=list)
    primary_topic: Optional[str] = None  # Main concern (anxiety, depression, etc.)
    session_distress_avg: float = 0.0
    
    def add_message(self, message: Message):
        """Add message to history"""
        self.messages.append(message)
        self._update_metrics()
    
    def _update_metrics(self):
        """Update session averages"""
        distress_levels = [m.distress_level for m in self.messages 
                          if m.distress_level is not None]
        if distress_levels:
            self.session_distress_avg = sum(distress_levels) / len(distress_levels)
        
        # Extract primary topic from keywords
        all_keywords = []
        for m in self.messages:
            all_keywords.extend(m.keywords)
        
        if all_keywords:
            # Count keyword frequency
            keyword_count = {}
            for kw in all_keywords:
                keyword_count[kw] = keyword_count.get(kw, 0) + 1
            self.primary_topic = max(keyword_count, key=keyword_count.get)
    
    def get_context(self, num_messages: int = 5) -> str:
        """Get recent conversation context as string"""
        recent = self.messages[-num_messages:]
        context_parts = []
        
        for msg in recent:
            if msg.role == 'user':
                context_parts.append(f"User: {msg.content}")
            else:
                # Truncate assistant responses for brevity
                truncated = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                context_parts.append(f"Assistant: {truncated}")
        
        return "\n".join(context_parts)
    
    def get_distress_trend(self) -> str:
        """Analyze distress trend over conversation"""
        user_messages = [m for m in self.messages if m.role == 'user']
        
        if len(user_messages) < 2:
            return "initial"  # First or second message
        
        distress_levels = [m.distress_level for m in user_messages 
                          if m.distress_level is not None]
        
        if len(distress_levels) < 2:
            return "unknown"
        
        # Compare first vs last distress level
        first = distress_levels[0]
        last = distress_levels[-1]
        
        if last > first + 0.15:
            return "escalating"
        elif last < first - 0.15:
            return "improving"
        else:
            return "stable"
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'messages': [m.to_dict() for m in self.messages],
            'primary_topic': self.primary_topic,
            'session_distress_avg': self.session_distress_avg,
            'distress_trend': self.get_distress_trend()
        }


class ConversationMemory:
    """
    Manages conversation memory across users
    
    Stores:
    - Conversation history for current session
    - User profiles across sessions
    - Pattern detection
    """
    
    def __init__(self):
        # Active conversations
        self.active_conversations: Dict[str, ConversationHistory] = {}
        
        # Long-term user profiles (persisted)
        self.user_profiles: Dict[str, Dict] = {}
    
    def start_conversation(self, user_id: str) -> ConversationHistory:
        """Start new conversation with user"""
        conversation = ConversationHistory(
            user_id=user_id,
            created_at=datetime.now()
        )
        self.active_conversations[user_id] = conversation
        return conversation
    
    def get_conversation(self, user_id: str) -> Optional[ConversationHistory]:
        """Get active conversation"""
        return self.active_conversations.get(user_id)
    
    def add_user_message(
        self,
        user_id: str,
        content: str,
        tone: str = "neutral",
        distress_level: float = 0.0,
        keywords: List[str] = None
    ) -> Message:
        """Add user message to conversation history"""
        
        # Create conversation if doesn't exist
        if user_id not in self.active_conversations:
            self.start_conversation(user_id)
        
        message = Message(
            timestamp=datetime.now(),
            role='user',
            content=content,
            tone=tone,
            distress_level=distress_level,
            keywords=keywords or []
        )
        
        self.active_conversations[user_id].add_message(message)
        return message
    
    def add_assistant_message(
        self,
        user_id: str,
        content: str
    ) -> Message:
        """Add assistant response to history"""
        if user_id not in self.active_conversations:
            self.start_conversation(user_id)
        
        message = Message(
            timestamp=datetime.now(),
            role='assistant',
            content=content
        )
        
        self.active_conversations[user_id].add_message(message)
        return message
    
    def get_context_for_response(self, user_id: str, num_messages: int = 5) -> str:
        """Get conversation context for response generation"""
        conversation = self.get_conversation(user_id)
        if not conversation:
            return ""
        return conversation.get_context(num_messages)
    
    def get_distress_trend(self, user_id: str) -> str:
        """Get whether distress is escalating/improving/stable"""
        conversation = self.get_conversation(user_id)
        if not conversation:
            return "unknown"
        return conversation.get_distress_trend()
    
    def get_session_metrics(self, user_id: str) -> Dict:
        """Get metrics for current session"""
        conversation = self.get_conversation(user_id)
        if not conversation:
            return {}
        
        user_messages = [m for m in conversation.messages if m.role == 'user']
        distress_levels = [m.distress_level for m in user_messages 
                          if m.distress_level is not None]
        
        return {
            'message_count': len(conversation.messages),
            'user_message_count': len(user_messages),
            'avg_distress': sum(distress_levels) / len(distress_levels) if distress_levels else 0.0,
            'primary_topic': conversation.primary_topic,
            'distress_trend': conversation.get_distress_trend(),
            'session_duration_minutes': (datetime.now() - conversation.created_at).total_seconds() / 60
        }
    
    def save_user_profile(self, user_id: str, profile: Dict):
        """Save long-term user profile"""
        self.user_profiles[user_id] = profile
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get long-term user profile"""
        return self.user_profiles.get(user_id)
    
    def close_conversation(self, user_id: str) -> Optional[ConversationHistory]:
        """End conversation and save profile"""
        conversation = self.active_conversations.pop(user_id, None)
        
        if conversation:
            # Save long-term profile
            profile = {
                'user_id': user_id,
                'primary_topics': [conversation.primary_topic] if conversation.primary_topic else [],
                'avg_distress': conversation.session_distress_avg,
                'last_conversation': conversation.created_at.isoformat(),
                'message_count': len(conversation.messages)
            }
            self.save_user_profile(user_id, profile)
        
        return conversation


# ================================================================
# USAGE EXAMPLE
# ================================================================

if __name__ == "__main__":
    
    print("\n" + "="*80)
    print("PHASE 3A: CONVERSATION MEMORY SYSTEM - DEMO")
    print("="*80)
    
    # Initialize memory
    memory = ConversationMemory()
    user_id = "user_123"
    
    # Simulate conversation flow
    print("\n📝 Simulating multi-turn conversation:")
    print("─" * 80)
    
    # Message 1
    print("\n[Turn 1]")
    print("User: I feel anxious all the time")
    memory.add_user_message(
        user_id,
        "I feel anxious all the time",
        tone="emotional",
        distress_level=0.45,
        keywords=["anxiety", "persistent"]
    )
    print("Assistant: That sounds difficult...")
    memory.add_assistant_message(user_id, "That sounds difficult...")
    
    # Message 2
    print("\n[Turn 2]")
    print("User: It's been happening for 2 weeks now")
    memory.add_user_message(
        user_id,
        "It's been happening for 2 weeks now",
        tone="emotional",
        distress_level=0.55,
        keywords=["anxiety", "duration"]
    )
    
    context = memory.get_context_for_response(user_id, num_messages=5)
    print(f"\n📚 CONTEXT FOR RESPONSE GENERATION:")
    print("─" * 40)
    print(context)
    
    print("\nAssistant: I see this has been going on for a while...")
    memory.add_assistant_message(user_id, "I see this has been going on for a while...")
    
    # Message 3
    print("\n[Turn 3]")
    print("User: It's getting worse, I can't sleep")
    memory.add_user_message(
        user_id,
        "It's getting worse, I can't sleep",
        tone="emotional",
        distress_level=0.65,
        keywords=["anxiety", "escalating", "sleep"]
    )
    
    # Check escalation
    trend = memory.get_distress_trend(user_id)
    print(f"\n🚨 DISTRESS TREND: {trend.upper()}")
    if trend == "escalating":
        print("→ System should escalate support!")
    
    metrics = memory.get_session_metrics(user_id)
    print(f"\n📊 SESSION METRICS:")
    print("─" * 40)
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Close conversation
    print("\n[Session Ending]")
    profile = memory.close_conversation(user_id)
    
    print(f"\n💾 SAVED USER PROFILE:")
    print("─" * 40)
    saved = memory.get_user_profile(user_id)
    print(json.dumps(saved, indent=2))
    
    print("\n" + "="*80)
    print("✅ MEMORY SYSTEM DEMO COMPLETE")
    print("="*80)
    print("\n🎯 Key Achievements:")
    print("  ✓ Stores full conversation history")
    print("  ✓ Tracks distress trend (escalating/improving/stable)")
    print("  ✓ Provides context for response generation")
    print("  ✓ Saves user profiles across sessions")
    print("  ✓ Enables detection of patterns")
    print("\n")
