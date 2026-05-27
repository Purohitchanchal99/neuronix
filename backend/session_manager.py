# -*- coding: utf-8 -*-
"""
NEURONIX SESSION MANAGER
========================
SQLite-based chat history storage with memory retrieval

Features:
- Unique user IDs for session tracking
- Persistent chat history storage
- Memory retrieval (last 5 exchanges for context)
- Conversation statistics
- Session metadata (mood, language, country)
"""

import sqlite3
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import uuid

# ================================================================
# CONFIGURATION
# ================================================================
BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / "data"
DB_FILE = DB_DIR / "neuronix_sessions.db"

# Ensure data directory exists
DB_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logger = logging.getLogger(__name__)


# ================================================================
# SESSION MANAGER - SQLite Chat History
# ================================================================
class SessionManager:
    """
    Manages user sessions and chat history using SQLite
    
    Stores:
    - User profiles (unique ID, country, language preference)
    - Chat messages (user query, AI response, timestamp)
    - Conversation metadata (mood, intent, standard used)
    """
    
    def __init__(self, db_path: Path = DB_FILE):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        self.connection = None
        self.db_lock = threading.Lock()  # Thread-safe lock for database operations
        self._initialize_db()
    
    def _initialize_db(self):
        """Create database tables if they don't exist"""
        try:
            # Use check_same_thread=False for Streamlit multi-threading compatibility
            # Timeout: wait up to 5 seconds if database is locked
            self.connection = sqlite3.connect(
                str(self.db_path), 
                check_same_thread=False, 
                timeout=5.0
            )
            self.connection.row_factory = sqlite3.Row
            cursor = self.connection.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT DEFAULT 'Anonymous',
                    country TEXT DEFAULT 'India',
                    language TEXT DEFAULT 'Hinglish',
                    preferred_standard TEXT DEFAULT 'Hybrid',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Chat history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    user_query TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    detected_mood TEXT,
                    detected_intent TEXT,
                    clinical_standard TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Conversation metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_date DATE DEFAULT CURRENT_DATE,
                    total_exchanges INTEGER DEFAULT 0,
                    mood_trend TEXT,
                    primary_topics TEXT,
                    crisis_detected BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            self.connection.commit()
            logger.info(f"[DB] Initialized at {self.db_path}")
        
        except sqlite3.Error as e:
            logger.error(f"[DB] Initialization failed: {e}")
            raise
    
    def create_user(self, username: str = "Anonymous", country: str = "India", 
                   language: str = "Hinglish", preferred_standard: str = "Hybrid") -> str:
        """
        Create a new user session with unique ID
        
        Args:
            username: User's name
            country: User's country (for standard routing)
            language: Response language preference (Hinglish/Hindi/English)
            preferred_standard: DSM-5/ICD-11/Hybrid
            
        Returns:
            Unique user_id
        """
        user_id = str(uuid.uuid4())[:8]  # Short 8-char ID
        
        try:
            with self.db_lock:  # Thread-safe database access
                cursor = self.connection.cursor()
                cursor.execute("""
                    INSERT INTO users (user_id, username, country, language, preferred_standard)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, username, country, language, preferred_standard))
                
                self.connection.commit()
                cursor.close()  # Close cursor immediately
            
            logger.info(f"[USER] Created: {user_id} ({username}, {country})")
            return user_id
        
        except sqlite3.Error as e:
            logger.error(f"[USER-CREATE] Failed: {e}")
            raise
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Retrieve user profile by ID"""
        try:
            with self.db_lock:  # Thread-safe database access
                cursor = self.connection.cursor()
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                cursor.close()  # Close cursor immediately
            
            if row:
                return dict(row)
            return None
        
        except sqlite3.Error as e:
            logger.error(f"[USER-GET] Failed: {e}")
            return None
    
    def add_message(self, user_id: str, user_query: str, ai_response: str,
                   detected_mood: str = None, detected_intent: str = None,
                   clinical_standard: str = None) -> int:
        """
        Store a chat exchange in history
        
        Args:
            user_id: User's unique ID
            user_query: User's message
            ai_response: Neuronix's response
            detected_mood: Mood detected (sad/anxious/frustrated/neutral)
            detected_intent: Intent (MENTAL_HEALTH/EDUCATIONAL/CASUAL)
            clinical_standard: Standard used (DSM-5/ICD-11/Hybrid)
            
        Returns:
            Message ID (row inserted)
        """
        try:
            with self.db_lock:  # Thread-safe database access
                cursor = self.connection.cursor()
                cursor.execute("""
                    INSERT INTO chat_history 
                    (user_id, user_query, ai_response, detected_mood, detected_intent, clinical_standard)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, user_query, ai_response, detected_mood, detected_intent, clinical_standard))
                
                # Update last_active
                cursor.execute(
                    "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (user_id,)
                )
                
                self.connection.commit()
                message_id = cursor.lastrowid
                cursor.close()  # Close cursor immediately
            
            logger.info(f"[MSG] Stored: {user_id} | Mood: {detected_mood} | Intent: {detected_intent}")
            return message_id
        
        except sqlite3.Error as e:
            logger.error(f"[MSG-ADD] Failed: {e}")
            raise
    
    def get_memory(self, user_id: str, limit: int = 5) -> List[Dict]:
        """
        Retrieve last N exchanges for SHORT-TERM MEMORY
        
        Used to provide context to LLM before generating response
        
        Args:
            user_id: User's unique ID
            limit: Number of recent exchanges (default: last 5)
            
        Returns:
            List of chat exchanges with metadata
        """
        try:
            with self.db_lock:  # Thread-safe database access
                cursor = self.connection.cursor()
                cursor.execute("""
                    SELECT user_query, ai_response, detected_mood, detected_intent, 
                           clinical_standard, timestamp
                    FROM chat_history
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
                
                rows = cursor.fetchall()
                memory = [dict(row) for row in rows]
                cursor.close()  # Close cursor immediately
            
            logger.info(f"[MEMORY] Retrieved {len(memory)} exchanges for {user_id}")
            return memory
        
        except sqlite3.Error as e:
            logger.error(f"[MEMORY-GET] Failed: {e}")
            return []
    
    def get_conversation_context(self, user_id: str, limit: int = 5) -> str:
        """
        Generate formatted context string from memory for LLM prompting
        
        Example output:
        ```
        PREVIOUS CONVERSATION:
        User: Mujhe anxiety hai
        Neuronix: Samajh sakta hoon...
        [Mood: anxious, Intent: MENTAL_HEALTH]
        
        User: Kya ye serious hai?
        Neuronix: Haan, anxiety...
        [Mood: anxious, Intent: EDUCATIONAL]
        ```
        
        Args:
            user_id: User's unique ID
            limit: Number of exchanges to include
            
        Returns:
            Formatted context string
        """
        memory = self.get_memory(user_id, limit)
        
        if not memory:
            return "[NO PREVIOUS CONTEXT]"
        
        context_lines = ["PREVIOUS CONVERSATION CONTEXT:"]
        
        # Reverse to show chronological order (oldest first)
        for exchange in reversed(memory):
            context_lines.append(f"\nUser: {exchange['user_query']}")
            context_lines.append(f"Neuronix: {exchange['ai_response'][:100]}...")  # Truncate
            
            metadata = []
            if exchange['detected_mood']:
                metadata.append(f"Mood: {exchange['detected_mood']}")
            if exchange['detected_intent']:
                metadata.append(f"Intent: {exchange['detected_intent']}")
            
            if metadata:
                context_lines.append(f"[{', '.join(metadata)}]")
        
        return "\n".join(context_lines)
    
    def get_mood_trend(self, user_id: str, limit: int = 10) -> Dict[str, int]:
        """
        Analyze recent mood patterns (for empathy adjustment)
        
        Args:
            user_id: User's unique ID
            limit: Number of recent messages to analyze
            
        Returns:
            Dictionary with mood counts {'sad': 3, 'anxious': 5, 'neutral': 2}
        """
        try:
            with self.db_lock:  # Thread-safe database access
                cursor = self.connection.cursor()
                cursor.execute("""
                    SELECT detected_mood, COUNT(*) as count
                    FROM chat_history
                    WHERE user_id = ? AND detected_mood IS NOT NULL
                    GROUP BY detected_mood
                    ORDER BY count DESC
                    LIMIT ?
                """, (user_id, limit))
                
                rows = cursor.fetchall()
                mood_trend = {row['detected_mood']: row['count'] for row in rows}
                cursor.close()  # Close cursor immediately
            
            logger.info(f"[MOOD-TREND] {user_id}: {mood_trend}")
            return mood_trend
        
        except sqlite3.Error as e:
            logger.error(f"[MOOD-TREND] Failed: {e}")
            return {}
    
    def get_conversation_stats(self, user_id: str) -> Dict:
        """Get overall conversation statistics"""
        try:
            with self.db_lock:  # Thread-safe database access
                cursor = self.connection.cursor()
                
                # Total messages
                cursor.execute(
                    "SELECT COUNT(*) as total FROM chat_history WHERE user_id = ?",
                    (user_id,)
                )
                total_messages = cursor.fetchone()['total']
                
                # Most common mood
                cursor.execute("""
                    SELECT detected_mood, COUNT(*) as count
                    FROM chat_history
                    WHERE user_id = ? AND detected_mood IS NOT NULL
                    GROUP BY detected_mood
                    ORDER BY count DESC
                    LIMIT 1
                """, (user_id,))
                
                mood_row = cursor.fetchone()
                primary_mood = mood_row['detected_mood'] if mood_row else "neutral"
                
                # Most common intent
                cursor.execute("""
                    SELECT detected_intent, COUNT(*) as count
                    FROM chat_history
                    WHERE user_id = ? AND detected_intent IS NOT NULL
                    GROUP BY detected_intent
                    ORDER BY count DESC
                    LIMIT 1
                """, (user_id,))
                
                intent_row = cursor.fetchone()
                primary_intent = intent_row['detected_intent'] if intent_row else "CASUAL"
                cursor.close()  # Close cursor immediately
            
            return {
                'total_messages': total_messages,
                'primary_mood': primary_mood,
                'primary_intent': primary_intent,
                'user_id': user_id
            }
        
        except sqlite3.Error as e:
            logger.error(f"[STATS] Failed: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("[DB] Connection closed")
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.close()


# ================================================================
# HELPER: Get or Create User Session
# ================================================================
def get_or_create_session(username: str = None, country: str = "India") -> Tuple[SessionManager, str]:
    """
    Convenience function to get or create user session
    
    Args:
        username: Optional user name
        country: User's country
        
    Returns:
        (SessionManager instance, user_id)
    """
    manager = SessionManager()
    user_id = manager.create_user(
        username=username or "Anonymous",
        country=country
    )
    return manager, user_id


if __name__ == "__main__":
    # Quick test
    manager = SessionManager()
    
    # Create test user
    test_user = manager.create_user("TestBhai", country="India")
    print(f"✅ Test User Created: {test_user}")
    
    # Get user
    user_profile = manager.get_user(test_user)
    print(f"✅ User Profile: {user_profile}")
    
    # Add test messages
    manager.add_message(
        test_user,
        "Mujhe anxiety hai",
        "Samajh sakta hoon ki worry bohot zyada ho rahi hai...",
        detected_mood="anxious",
        detected_intent="MENTAL_HEALTH"
    )
    
    manager.add_message(
        test_user,
        "Kya ye serious hai?",
        "Haan, anxiety ek serious condition hai jisme...",
        detected_mood="anxious",
        detected_intent="EDUCATIONAL"
    )
    
    # Retrieve memory
    memory = manager.get_memory(test_user, limit=5)
    print(f"✅ Memory Retrieved: {len(memory)} exchanges")
    
    # Get context
    context = manager.get_conversation_context(test_user, limit=2)
    print(f"✅ Context:\n{context}")
    
    # Get stats
    stats = manager.get_conversation_stats(test_user)
    print(f"✅ Stats: {stats}")
    
    manager.close()
    print("[OK] Session manager test complete!")
