#!/usr/bin/env python3
"""
Phase 6: Long-Term Memory System
================================
Makes AI remember users across sessions

Features:
- Conversation history storage & retrieval
- Semantic memory search (find past discussions)
- Topic extraction & tagging
- User relationship graphs
- Session metadata tracking

Architecture:
├── ConversationStore (PostgreSQL backend)
├── VectorMemory (Embedding-based search)
├── TopicExtractor (What was discussed?)
├── UserGraph (User learning journey)
└── SessionMetadata (Session analytics)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import hashlib
from collections import defaultdict, Counter
import uuid

# Import sentence transformer for embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️  sentence-transformers not installed")
    print("   Install with: pip install sentence-transformers")


# ================================================================
# DATA MODELS
# ================================================================

@dataclass
class Message:
    """Single message in conversation"""
    id: str
    user_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    tone: Optional[str] = None  # emotional tone
    distress_level: Optional[float] = None
    topics: List[str] = None  # extracted topics
    embeddings: Optional[List[float]] = None  # vector representation
    metadata: Dict = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tone": self.tone,
            "distress_level": self.distress_level,
            "topics": self.topics or [],
            "metadata": self.metadata or {}
        }


@dataclass
class Conversation:
    """Full conversation session"""
    session_id: str
    user_id: str
    messages: List[Message]
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    primary_topic: Optional[str] = None
    topics: List[str] = None
    distress_trend: Optional[str] = None  # escalating/stable/improving
    summary: Optional[str] = None
    
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "message_count": len(self.messages),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_minutes": self.duration_minutes,
            "primary_topic": self.primary_topic,
            "topics": self.topics or [],
            "distress_trend": self.distress_trend,
            "summary": self.summary
        }


@dataclass
class UserProfile:
    """User learning profile"""
    user_id: str
    created_at: datetime
    topics_learned: Dict[str, float]  # topic -> confidence (0-1)
    struggle_points: Dict[str, int]  # topic -> times struggled
    learning_style: Optional[str]  # visual/code/text/mixed
    total_sessions: int
    total_messages: int
    average_distress: float
    last_active: datetime
    preferred_tone: Optional[str]  # hinglish/formal/casual
    
    def to_dict(self):
        return asdict(self)


# ================================================================
# VECTOR MEMORY SYSTEM
# ================================================================

class VectorMemory:
    """
    Semantic memory search using embeddings
    
    Usage:
    ```python
    memory = VectorMemory()
    memory.add("User struggled with recursion", embedding)
    results = memory.search("How do I understand recursion?", k=3)
    # Returns top 3 semantically similar memories
    ```
    """
    
    def __init__(self, use_embeddings: bool = True):
        """Initialize vector memory"""
        self.memories: List[Dict] = []
        self.use_embeddings = use_embeddings
        
        if use_embeddings and EMBEDDINGS_AVAILABLE:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Loaded embedding model (all-MiniLM-L6-v2)")
        elif use_embeddings:
            print("⚠️  Embeddings disabled (model not available)")
            self.use_embeddings = False
    
    def add(self, text: str, metadata: Dict = None, embedding: List[float] = None):
        """Add memory with optional embedding"""
        if embedding is None and self.use_embeddings:
            embedding = self.model.encode(text).tolist()
        
        memory = {
            "id": str(uuid.uuid4()),
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {},
            "timestamp": datetime.now(),
            "access_count": 0,
            "relevance_score": 1.0
        }
        self.memories.append(memory)
        return memory["id"]
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar memories"""
        if not self.memories:
            return []
        
        if self.use_embeddings:
            query_embedding = self.model.encode(query).tolist()
            
            # Calculate cosine similarity
            results = []
            for memory in self.memories:
                if memory["embedding"]:
                    similarity = self._cosine_similarity(
                        query_embedding,
                        memory["embedding"]
                    )
                    memory["similarity"] = similarity
                    results.append(memory)
            
            # Sort by similarity
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Update access count & timestamp
            for result in results[:k]:
                result["access_count"] += 1
                result["last_accessed"] = datetime.now()
            
            return results[:k]
        else:
            # Fallback: keyword search (split by words)
            query_words = set(query.lower().split())
            results = []
            
            for memory in self.memories:
                text_words = set(memory["text"].lower().split())
                overlap = len(query_words & text_words) / len(query_words)
                memory["similarity"] = overlap
                if overlap > 0:
                    results.append(memory)
            
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:k]
    
    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity"""
        import math
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x ** 2 for x in a))
        norm_b = math.sqrt(sum(x ** 2 for x in b))
        
        if norm_a == 0 or norm_b == 0:
            return 0
        
        return dot_product / (norm_a * norm_b)


# ================================================================
# CONVERSATION STORE
# ================================================================

class ConversationStore:
    """
    In-memory conversation storage
    
    Production: Replace with PostgreSQL
    
    Usage:
    ```python
    store = ConversationStore()
    store.start_conversation("user_123")
    store.add_message("user_123", "Hello", role="user")
    store.add_message("user_123", "Hi there!", role="assistant")
    conv = store.get_conversation("user_123")
    store.close_conversation("user_123")
    ```
    """
    
    def __init__(self):
        """Initialize in-memory store"""
        self.conversations: Dict[str, Conversation] = {}
        self.active_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.vector_memory = VectorMemory()
        self.user_profiles: Dict[str, UserProfile] = {}
    
    def start_conversation(self, user_id: str) -> str:
        """Start new conversation session"""
        session_id = str(uuid.uuid4())
        self.active_sessions[user_id] = session_id
        
        conversation = Conversation(
            session_id=session_id,
            user_id=user_id,
            messages=[],
            start_time=datetime.now()
        )
        self.conversations[session_id] = conversation
        
        print(f"✅ Started conversation {session_id} for {user_id}")
        return session_id
    
    def add_message(
        self,
        user_id: str,
        content: str,
        role: str = "user",
        tone: Optional[str] = None,
        distress_level: Optional[float] = None,
        topics: Optional[List[str]] = None
    ) -> str:
        """Add message to active conversation"""
        session_id = self.active_sessions.get(user_id)
        if not session_id:
            session_id = self.start_conversation(user_id)
        
        conversation = self.conversations[session_id]
        
        message = Message(
            id=str(uuid.uuid4()),
            user_id=user_id,
            role=role,
            content=content,
            timestamp=datetime.now(),
            tone=tone,
            distress_level=distress_level,
            topics=topics or []
        )
        
        conversation.messages.append(message)
        
        # Add to vector memory
        self.vector_memory.add(
            content,
            metadata={
                "user_id": user_id,
                "role": role,
                "tone": tone,
                "topics": topics or []
            }
        )
        
        return message.id
    
    def get_conversation(self, user_id: str) -> Optional[Conversation]:
        """Get active conversation"""
        session_id = self.active_sessions.get(user_id)
        if session_id:
            return self.conversations.get(session_id)
        return None
    
    def get_context_for_response(
        self,
        user_id: str,
        max_messages: int = 5
    ) -> str:
        """Build context string from recent messages"""
        conversation = self.get_conversation(user_id)
        if not conversation or not conversation.messages:
            return ""
        
        # Get last N messages
        recent_messages = conversation.messages[-max_messages:]
        
        context = "Recent conversation:\n"
        for msg in recent_messages:
            prefix = "User" if msg.role == "user" else "Assistant"
            context += f"{prefix}: {msg.content}\n"
        
        return context
    
    def search_memories(self, query: str, k: int = 3) -> List[Dict]:
        """Search past memories by semantic similarity"""
        return self.vector_memory.search(query, k=k)
    
    def close_conversation(self, user_id: str) -> Conversation:
        """Close conversation session"""
        session_id = self.active_sessions.pop(user_id, None)
        if not session_id:
            return None
        
        conversation = self.conversations[session_id]
        conversation.end_time = datetime.now()
        conversation.duration_minutes = int(
            (conversation.end_time - conversation.start_time).total_seconds() / 60
        )
        
        print(f"✅ Closed conversation {session_id}")
        print(f"   Duration: {conversation.duration_minutes} minutes")
        print(f"   Messages: {len(conversation.messages)}")
        
        return conversation
    
    def get_user_profile(self, user_id: str) -> UserProfile:
        """Get or create user profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                created_at=datetime.now(),
                topics_learned={},
                struggle_points={},
                learning_style=None,
                total_sessions=0,
                total_messages=0,
                average_distress=0.0,
                last_active=datetime.now(),
                preferred_tone=None
            )
        return self.user_profiles[user_id]
    
    def update_user_profile(
        self,
        user_id: str,
        topics_learned: Dict[str, float] = None,
        struggle_points: Dict[str, int] = None,
        learning_style: str = None,
        preferred_tone: str = None
    ):
        """Update user learning profile"""
        profile = self.get_user_profile(user_id)
        
        if topics_learned:
            profile.topics_learned.update(topics_learned)
        if struggle_points:
            profile.struggle_points.update(struggle_points)
        if learning_style:
            profile.learning_style = learning_style
        if preferred_tone:
            profile.preferred_tone = preferred_tone
        
        profile.last_active = datetime.now()
    
    def get_session_metrics(self, user_id: str) -> Dict:
        """Get detailed session metrics"""
        conversation = self.get_conversation(user_id)
        if not conversation:
            conversation = list(self.conversations.values())[-1] if self.conversations else None
        
        if not conversation:
            return {}
        
        # Calculate metrics
        messages_count = len(conversation.messages)
        user_messages = [m for m in conversation.messages if m.role == "user"]
        
        distress_levels = [m.distress_level for m in user_messages if m.distress_level]
        avg_distress = sum(distress_levels) / len(distress_levels) if distress_levels else 0
        
        # Extract all topics
        all_topics = []
        for msg in user_messages:
            all_topics.extend(msg.topics or [])
        
        # Most common topic
        primary_topic = Counter(all_topics).most_common(1)[0][0] if all_topics else None
        
        return {
            "session_id": conversation.session_id,
            "message_count": messages_count,
            "duration_minutes": conversation.duration_minutes,
            "avg_distress": avg_distress,
            "primary_topic": primary_topic,
            "topics": list(set(all_topics)),
            "start_time": conversation.start_time.isoformat(),
            "end_time": conversation.end_time.isoformat() if conversation.end_time else None
        }
    
    def export_conversation(self, user_id: str) -> Dict:
        """Export conversation for analysis or backup"""
        conversation = self.get_conversation(user_id)
        if not conversation:
            return {}
        
        return {
            "session": conversation.to_dict(),
            "messages": [msg.to_dict() for msg in conversation.messages],
            "metrics": self.get_session_metrics(user_id)
        }


# ================================================================
# EXAMPLE USAGE
# ================================================================

if __name__ == "__main__":
    print("🧠 Phase 6: Memory System Demo\n")
    
    # Initialize store
    store = ConversationStore()
    user_id = "student_001"
    
    # Start conversation
    print("1️⃣  Starting conversation...")
    store.start_conversation(user_id)
    
    # Add messages
    print("2️⃣  Adding messages...")
    store.add_message(
        user_id,
        "I'm confused about recursion. Can you explain?",
        role="user",
        tone="confused",
        distress_level=0.4,
        topics=["recursion", "algorithms"]
    )
    
    store.add_message(
        user_id,
        "Recursion is when a function calls itself. Think of it like looking in mirrors...",
        role="assistant",
        topics=["recursion", "functions", "explanation"]
    )
    
    store.add_message(
        user_id,
        "So every recursive call needs a base case?",
        role="user",
        tone="learning",
        topics=["recursion", "base-case"]
    )
    
    store.add_message(
        user_id,
        "Exactly! The base case is what stops the recursion. Otherwise it goes infinite.",
        role="assistant",
        topics=["recursion", "base-case", "loops"]
    )
    
    # Get conversation context
    print("\n3️⃣  Getting conversation context...")
    context = store.get_context_for_response(user_id)
    print(context)
    
    # Search memories
    print("\n4️⃣  Searching memories...")
    results = store.search_memories("How do I avoid infinite recursion?")
    for i, result in enumerate(results, 1):
        print(f"  Result {i}: {result['text'][:80]}...")
        print(f"    Similarity: {result.get('similarity', 'N/A'):.2f}")
    
    # Get metrics
    print("\n5️⃣  Session metrics...")
    metrics = store.get_session_metrics(user_id)
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Update user profile
    print("\n6️⃣  Updating user profile...")
    store.update_user_profile(
        user_id,
        topics_learned={"recursion": 0.6, "functions": 0.8},
        learning_style="visual",
        preferred_tone="hinglish"
    )
    profile = store.get_user_profile(user_id)
    print(f"  Topics learned: {profile.topics_learned}")
    print(f"  Learning style: {profile.learning_style}")
    
    # Close conversation
    print("\n7️⃣ Closing conversation...")
    store.close_conversation(user_id)
    
    # Export
    print("\n8️⃣  Exporting for backup...")
    export = store.export_conversation(user_id)
    print(json.dumps(export, indent=2, default=str)[:500] + "...")
    
    print("\n✅ Demo complete!")
