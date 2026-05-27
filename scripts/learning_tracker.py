#!/usr/bin/env python3
"""
Phase 6: Learning Progress Tracker
===================================
Tracks what user learned, where they struggle, learning velocity

Features:
- Topic mastery scoring (0-1 confidence)
- Struggle point detection
- Learning velocity (progress over time)
- Misconception tracking
- Adaptive difficulty recommendations
- Spaced repetition hints

Example:
  Tracker.record_interaction("user_123", "loops", "struggle", attempt=1)
  Tracker.record_interaction("user_123", "loops", "success", attempt=3)
  
  mastery = Tracker.get_mastery("user_123", "loops")
  # Returns: {confidence: 0.6, attempts: 3, last_attempt: datetime}
  
  recommendation = Tracker.get_next_topic("user_123")
  # Returns: "tree-traversal" (next logical topic after knowing loops)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from enum import Enum
import json


# ================================================================
# ENUMS & MODELS
# ================================================================

class InteractionType(Enum):
    """Type of learning interaction"""
    SUCCESS = "success"  # User got it right
    STRUGGLE = "struggle"  # User had difficulty
    CONFUSION = "confusion"  # User misunderstood
    INCORRECT = "incorrect"  # User got wrong answer
    PARTIAL = "partial"  # Half right, half wrong
    MASTERY = "mastery"  # User demonstrated full understanding


class LearningStyle(Enum):
    """Detected learning style"""
    VISUAL = "visual"  # Prefers diagrams/videos
    CODE = "code"  # Learns by coding
    TEXT = "text"  # Prefers reading
    EXAMPLES = "examples"  # Learns from examples
    SOCRATIC = "socratic"  # Prefers questioning
    MIXED = "mixed"  # No clear preference


@dataclass
class MasteryRecord:
    """Single mastery record for a topic"""
    topic: str
    user_id: str
    confidence: float  # 0-1 (0=no idea, 1=expert)
    attempts: int
    successes: int
    failures: int
    last_attempt: datetime
    interactions: List[Dict] = field(default_factory=list)
    misconceptions: List[str] = field(default_factory=list)
    learning_velocity: Optional[float] = None  # progress per day
    date_mastered: Optional[datetime] = None  # when reached 0.8+
    
    def to_dict(self):
        return {
            "topic": self.topic,
            "confidence": round(self.confidence, 2),
            "attempts": self.attempts,
            "success_rate": round(self.successes / max(1, self.attempts), 2),
            "last_attempt": self.last_attempt.isoformat(),
            "misconceptions": self.misconceptions,
            "learning_velocity": self.learning_velocity,
            "date_mastered": self.date_mastered.isoformat() if self.date_mastered else None,
            "status": self._get_status()
        }
    
    def _get_status(self) -> str:
        """Get status badge"""
        if self.confidence >= 0.8:
            return "🎓 Mastered"
        elif self.confidence >= 0.5:
            return "📚 Intermediate"
        elif self.confidence >= 0.2:
            return "🌱 Beginner"
        else:
            return "❓ Not Started"


@dataclass
class LearningMetrics:
    """Aggregated learning metrics for user"""
    user_id: str
    total_topics: int
    mastered_topics: int
    in_progress_topics: int
    struggle_topics: int
    estimated_learning_rate: float  # topics/week
    predicted_mastery_date: Optional[datetime] = None
    learning_style: Optional[LearningStyle] = None
    focus_areas: List[str] = field(default_factory=list)  # struggle topics to focus on
    recommended_next: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return {
            "total_topics": self.total_topics,
            "mastered_topics": self.mastered_topics,
            "in_progress_topics": self.in_progress_topics,
            "struggle_topics": self.struggle_topics,
            "mastery_rate": round(self.mastered_topics / max(1, self.total_topics), 2),
            "learning_rate_topics_per_week": round(self.estimated_learning_rate, 1),
            "focus_areas": self.focus_areas[:3],
            "recommended_next": self.recommended_next[:3]
        }


# ================================================================
# LEARNING TRACKER
# ================================================================

class LearningTracker:
    """
    Tracks user progress across topics
    
    Usage:
    ```python
    tracker = LearningTracker()
    
    # Record interactions
    tracker.record_interaction("user_123", "recursion", InteractionType.STRUGGLE)
    tracker.record_interaction("user_123", "recursion", InteractionType.SUCCESS)
    
    # Get mastery info
    mastery = tracker.get_mastery("user_123", "recursion")
    print(mastery.confidence)  # 0.6
    
    # Get recommendations
    metrics = tracker.get_metrics("user_123")
    print(metrics.recommended_next)  # ["tree-traversal", "graphs"]
    ```
    """
    
    # Topic hierarchy for prerequisite chains
    TOPIC_HIERARCHY = {
        "if-statements": [],
        "loops": ["if-statements"],
        "functions": ["loops", "if-statements"],
        "lists": ["loops"],
        "recursion": ["functions"],
        "tree-traversal": ["recursion", "trees"],
        "trees": ["recursion"],
        "graphs": ["trees", "lists"],
        "binary-search": ["loops", "lists"],
        "sorting": ["loops", "functions"],
        "hashing": ["dictionaries"],
        "dictionaries": ["loops"],
        "dynamic-programming": ["recursion"],
        "greedy-algorithms": ["sorting"],
    }
    
    def __init__(self):
        """Initialize learning tracker"""
        self.masteries: Dict[str, Dict[str, MasteryRecord]] = defaultdict(dict)
        # user_id -> {topic -> MasteryRecord}
        
        self.misconceptions_db: Dict[str, List[str]] = {}
        # user_id -> [list of misconceptions]
        
        self.learning_style_detector = LearningStyleDetector()
    
    def record_interaction(
        self,
        user_id: str,
        topic: str,
        interaction_type: InteractionType,
        misconception: Optional[str] = None,
        explanation: Optional[str] = None,
        difficulty_rating: Optional[int] = None  # 1-5
    ) -> MasteryRecord:
        """Record a learning interaction"""
        
        # Get or create mastery record
        if topic not in self.masteries[user_id]:
            self.masteries[user_id][topic] = MasteryRecord(
                topic=topic,
                user_id=user_id,
                confidence=0.0,
                attempts=0,
                successes=0,
                failures=0,
                last_attempt=datetime.now()
            )
        
        record = self.masteries[user_id][topic]
        record.last_attempt = datetime.now()
        record.attempts += 1
        
        # Update confidence based on interaction
        if interaction_type == InteractionType.SUCCESS:
            record.successes += 1
            record.confidence = min(1.0, record.confidence + 0.15)
        
        elif interaction_type == InteractionType.STRUGGLE:
            record.failures += 1
            record.confidence = max(0.0, record.confidence - 0.05)
        
        elif interaction_type == InteractionType.CONFUSION:
            record.failures += 1
            record.confidence = max(0.0, record.confidence - 0.10)
            if misconception:
                record.misconceptions.append(misconception)
        
        elif interaction_type == InteractionType.INCORRECT:
            record.failures += 1
            record.confidence = max(0.0, record.confidence - 0.15)
        
        elif interaction_type == InteractionType.PARTIAL:
            record.successes += 0.5
            record.confidence = max(0.0, record.confidence + 0.05)
        
        elif interaction_type == InteractionType.MASTERY:
            record.successes += 1
            record.confidence = 1.0
            if not record.date_mastered:
                record.date_mastered = datetime.now()
        
        # Calculate learning velocity
        record.learning_velocity = self._calculate_velocity(record)
        
        # Record interaction details
        record.interactions.append({
            "type": interaction_type.value,
            "timestamp": datetime.now().isoformat(),
            "difficulty": difficulty_rating,
            "misconception": misconception,
            "confidence_before": record.confidence,
            "explanation": explanation
        })
        
        return record
    
    def _calculate_velocity(self, record: MasteryRecord) -> float:
        """Calculate learning velocity (confidence gain per day)"""
        if len(record.interactions) < 2:
            return 0.0
        
        first_interaction = record.interactions[0]
        last_interaction = record.interactions[-1]
        
        first_time = datetime.fromisoformat(first_interaction["timestamp"])
        last_time = datetime.fromisoformat(last_interaction["timestamp"])
        
        days_elapsed = (last_time - first_time).days + 1
        if days_elapsed == 0:
            days_elapsed = 1
        
        # How much confidence improved per day
        velocity = record.confidence / days_elapsed
        return round(velocity, 2)
    
    def get_mastery(self, user_id: str, topic: str) -> Optional[MasteryRecord]:
        """Get mastery record for topic"""
        return self.masteries[user_id].get(topic)
    
    def get_all_masteries(self, user_id: str) -> List[MasteryRecord]:
        """Get all topic masteries for user"""
        return list(self.masteries[user_id].values())
    
    def get_metrics(self, user_id: str) -> LearningMetrics:
        """Get aggregated learning metrics"""
        masteries = self.get_all_masteries(user_id)
        
        if not masteries:
            return LearningMetrics(
                user_id=user_id,
                total_topics=0,
                mastered_topics=0,
                in_progress_topics=0,
                struggle_topics=0,
                estimated_learning_rate=0.0
            )
        
        # Count by status
        mastered = sum(1 for m in masteries if m.confidence >= 0.8)
        in_progress = sum(1 for m in masteries if 0.2 <= m.confidence < 0.8)
        struggle = sum(1 for m in masteries if m.confidence < 0.2 and m.attempts > 0)
        
        # Calculate learning rate (topics mastered per week)
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        topics_mastered_this_week = sum(
            1 for m in masteries
            if m.date_mastered and m.date_mastered > week_ago
        )
        learning_rate = topics_mastered_this_week if topics_mastered_this_week > 0 else 0.0
        
        # Detect learning style
        learning_style = self.learning_style_detector.detect(user_id, masteries)
        
        # Find focus areas (topics with low confidence)
        focus_areas = [m.topic for m in masteries if m.confidence < 0.5 and m.attempts > 0]
        focus_areas.sort(key=lambda t: self.masteries[user_id][t].confidence)
        
        # Recommend next topics based on prerequisites
        recommended = self._recommend_next_topics(user_id, masteries)
        
        return LearningMetrics(
            user_id=user_id,
            total_topics=len(masteries),
            mastered_topics=mastered,
            in_progress_topics=in_progress,
            struggle_topics=struggle,
            estimated_learning_rate=float(learning_rate),
            learning_style=learning_style,
            focus_areas=focus_areas,
            recommended_next=recommended
        )
    
    def _recommend_next_topics(
        self,
        user_id: str,
        masteries: List[MasteryRecord]
    ) -> List[str]:
        """Find topics user should learn next"""
        mastered_topics = {m.topic for m in masteries if m.confidence >= 0.8}
        
        recommendations = []
        for topic, prerequisites in self.TOPIC_HIERARCHY.items():
            # Skip if already mastered
            if topic in mastered_topics:
                continue
            
            # Check if prerequisites met
            if all(prereq in mastered_topics for prereq in prerequisites):
                recommendations.append(topic)
        
        # Sort by difficulty (fewer prerequisites = earlier)
        recommendations.sort(key=lambda t: len(self.TOPIC_HIERARCHY.get(t, [])))
        
        return recommendations[:5]  # Top 5 recommendations
    
    def get_performance_stats(self, user_id: str) -> Dict:
        """Get detailed performance statistics"""
        masteries = self.get_all_masteries(user_id)
        
        if not masteries:
            return {}
        
        # Most struggled topic
        most_struggled = max(
            masteries,
            key=lambda m: m.failures,
            default=None
        )
        
        # Fast learner topic
        fastest = max(
            masteries,
            key=lambda m: m.learning_velocity or 0,
            default=None
        )
        
        # Average success rate
        avg_success_rate = sum(m.successes / max(1, m.attempts) for m in masteries) / len(masteries)
        
        return {
            "most_struggled_topic": most_struggled.topic if most_struggled else None,
            "fastest_learned_topic": fastest.topic if fastest else None,
            "overall_success_rate": round(avg_success_rate, 2),
            "average_attempts_per_topic": round(sum(m.attempts for m in masteries) / len(masteries), 1),
            "topics_with_misconceptions": [
                m.topic for m in masteries if m.misconceptions
            ]
        }


# ================================================================
# LEARNING STYLE DETECTOR
# ================================================================

class LearningStyleDetector:
    """Detect user's preferred learning style"""
    
    def detect(
        self,
        user_id: str,
        masteries: List[MasteryRecord]
    ) -> Optional[LearningStyle]:
        """Detect learning style from interactions"""
        
        if not masteries:
            return LearningStyle.MIXED
        
        # Analyze interaction types
        style_votes = defaultdict(int)
        
        for mastery in masteries:
            for interaction in mastery.interactions:
                if "misconception" in interaction and interaction["misconception"]:
                    # User struggles with conceptual understanding -> needs more explanation
                    style_votes[LearningStyle.SOCRATIC] += 1
                
                if interaction["type"] == "success":
                    # User is successful, track how
                    style_votes[LearningStyle.MIXED] += 1
        
        # Default to MIXED if no clear pattern
        if not style_votes:
            return LearningStyle.MIXED
        
        best_style = max(style_votes, key=style_votes.get)
        return best_style


# ================================================================
# EXAMPLE USAGE
# ================================================================

if __name__ == "__main__":
    print("📊 Learning Tracker Demo\n")
    
    tracker = LearningTracker()
    user_id = "student_123"
    
    print("1️⃣  Recording learning interactions...")
    
    # User learns loops
    tracker.record_interaction(user_id, "loops", InteractionType.STRUGGLE, difficulty_rating=2)
    tracker.record_interaction(user_id, "loops", InteractionType.STRUGGLE, difficulty_rating=2)
    tracker.record_interaction(user_id, "loops", InteractionType.PARTIAL, difficulty_rating=3)
    tracker.record_interaction(user_id, "loops", InteractionType.SUCCESS, difficulty_rating=4)
    tracker.record_interaction(user_id, "loops", InteractionType.SUCCESS, difficulty_rating=4)
    
    # User learns functions
    tracker.record_interaction(user_id, "functions", InteractionType.STRUGGLE,
                              misconception="Functions must return something")
    tracker.record_interaction(user_id, "functions", InteractionType.SUCCESS)
    tracker.record_interaction(user_id, "functions", InteractionType.MASTERY)
    
    # User struggles with recursion
    tracker.record_interaction(user_id, "recursion", InteractionType.CONFUSION,
                              misconception="Recursion is same as loops")
    tracker.record_interaction(user_id, "recursion", InteractionType.STRUGGLE)
    
    print("✅ Recorded 11 interactions\n")
    
    print("2️⃣  Getting individual masteries...")
    loops_mastery = tracker.get_mastery(user_id, "loops")
    functions_mastery = tracker.get_mastery(user_id, "functions")
    recursion_mastery = tracker.get_mastery(user_id, "recursion")
    
    print(f"\nLoops: {loops_mastery.to_dict()}")
    print(f"\nFunctions: {functions_mastery.to_dict()}")
    print(f"\nRecursion: {recursion_mastery.to_dict()}")
    
    print("\n3️⃣  Getting overall metrics...")
    metrics = tracker.get_metrics(user_id)
    print(json.dumps(metrics.to_dict(), indent=2))
    
    print("\n4️⃣  Performance statistics...")
    stats = tracker.get_performance_stats(user_id)
    print(json.dumps(stats, indent=2))
    
    print("\n✅ Demo complete!")
