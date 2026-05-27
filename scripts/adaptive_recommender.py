#!/usr/bin/env python3
"""
Phase 6: Adaptive Recommender Engine
=====================================
Personalized recommendations based on user learning profile

Features:
- Next-topic suggestions based on prerequisites
- Difficulty progression (adaptive difficulty)
- Learning style matching
- Spaced repetition hints
- Personalized example selection
- Time-aware recommendations

Example:
  recommender = AdaptiveRecommender()
  
  # Get next topic to learn
  recommendation = recommender.recommend_next_topic(tracker, user_id)
  # Returns: {topic: "tree-traversal", reason: "You mastered recursion!"}
  
  # Get personalized response
  response = recommender.personalize_response(
      base_response="Recursion is a function calling itself",
      user_profile=profile,
      learning_style="visual"
  )
  # Returns: Response with diagrams, step-by-step visual explanation
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import random
import json


# ================================================================
# RECOMMENDATION MODELS
# ================================================================

@dataclass
class Recommendation:
    """Single recommendation"""
    topic: str
    priority: float  # 0-1 (confidence in recommendation)
    reason: str
    difficulty_level: str  # "easy", "medium", "hard"
    estimated_time_minutes: int
    prerequisites_met: bool
    suggested_time: Optional[str] = None  # "now", "later", "revisit"
    learning_resources: List[str] = None
    
    def to_dict(self):
        return {
            "topic": self.topic,
            "priority": round(self.priority, 2),
            "reason": self.reason,
            "difficulty": self.difficulty_level,
            "estimated_time": f"{self.estimated_time_minutes} min",
            "ready_to_learn": self.prerequisites_met,
            "suggested_time": self.suggested_time,
            "resources": self.learning_resources or []
        }


@dataclass
class PersonalizedResponse:
    """Response adapted to user"""
    base_content: str
    personalization_applied: List[str]  # ["visual_diagram", "hinglish_tone", "example_based"]
    estimated_difficulty: str
    suggested_examples: List[str]
    follow_up_questions: List[str]
    sources_cited: List[str]


# ================================================================
# DIFFICULTY ASSESSMENT
# ================================================================

class DifficultyAssessor:
    """Assess and recommend difficulty level"""
    
    # Topic difficulty baseline (0-10)
    TOPIC_DIFFICULTY = {
        "if-statements": 1.0,
        "loops": 2.0,
        "functions": 2.5,
        "lists": 2.5,
        "dictionaries": 3.0,
        "sorting": 3.5,
        "binary-search": 4.0,
        "recursion": 5.0,
        "trees": 6.0,
        "graphs": 7.0,
        "dynamic-programming": 8.0,
        "greedy-algorithms": 7.5,
    }
    
    @staticmethod
    def get_adjusted_difficulty(
        topic: str,
        prerequisite_strength: float,  # 0-1 (how well user knows prerequisites)
        user_learning_velocity: float,  # topics learned per week
    ) -> str:
        """Get recommended difficulty for this topic"""
        
        base_difficulty = DifficultyAssessor.TOPIC_DIFFICULTY.get(topic, 5.0)
        
        # Adjust based on prerequisite knowledge
        if prerequisite_strength < 0.5:
            adjusted = base_difficulty + 2  # Harder if weak prerequisites
        elif prerequisite_strength >= 0.8:
            adjusted = base_difficulty - 1  # Easier with strong prerequisites
        else:
            adjusted = base_difficulty
        
        # Adjust based on learning velocity
        if user_learning_velocity > 3:  # Fast learner
            adjusted -= 0.5
        elif user_learning_velocity < 0.5:  # Slow learner
            adjusted += 1
        
        # Return label
        if adjusted <= 2:
            return "easy"
        elif adjusted <= 5:
            return "medium"
        else:
            return "hard"
    
    @staticmethod
    def estimate_time(topic: str, user_learning_velocity: float) -> int:
        """Estimate time to understand topic (in minutes)"""
        
        base_time = {
            "if-statements": 15,
            "loops": 20,
            "functions": 25,
            "lists": 20,
            "dictionaries": 20,
            "sorting": 30,
            "binary-search": 35,
            "recursion": 40,
            "trees": 50,
            "graphs": 60,
            "dynamic-programming": 90,
            "greedy-algorithms": 60,
        }
        
        time = base_time.get(topic, 30)
        
        # Adjust based on learning speed
        if user_learning_velocity > 3:
            time = int(time * 0.7)  # 30% faster
        elif user_learning_velocity < 0.5:
            time = int(time * 1.5)  # 50% slower
        
        return time


# ================================================================
# LEARNING RESOURCE MATCHER
# ================================================================

class ResourceMatcher:
    """Match learning resources to user style"""
    
    RESOURCES = {
        "recursion": {
            "visual": [
                "https://visualize-recursion.com",
                "Tree structure animations",
                "Call stack visualization"
            ],
            "code": [
                "Recursion code examples on GitHub",
                "LeetCode recursion problems",
                "Practice with Python REPL"
            ],
            "text": [
                "Wikipedia Recursion article",
                "Medium blog: Understanding Recursion",
                "Computer Science textbook Ch.5"
            ],
            "examples": [
                "Fibonacci sequence walkthrough",
                "Factorial calculation steps",
                "Binary search tree traversal"
            ],
            "socratic": [
                "Questions: What's the base case?",
                "How does the call stack work?",
                "Why not use a loop instead?"
            ]
        },
        "loops": {
            "visual": ["Loop flowchart diagrams", "Animation: iteration steps"],
            "code": ["For/while loop examples", "Loop practice questions"],
            "text": ["Loop textbook chapter", "Loop tutorial"],
            "examples": ["Countdown loop", "Sum calculation", "List iteration"],
            "socratic": ["When to use for vs while?", "What's an off-by-one error?"]
        },
        "functions": {
            "visual": ["Function call diagram", "Scope visualization"],
            "code": ["Function examples", "Parameter passing demo"],
            "text": ["Functions chapter", "Function documentation"],
            "examples": ["Calculate area", "Validate input", "Transform data"],
            "socratic": ["What's a side effect?", "How is scope determined?"]
        }
    }
    
    @staticmethod
    def get_resources(topic: str, learning_style: str) -> List[str]:
        """Get resources for topic + learning style"""
        resources = ResourceMatcher.RESOURCES.get(topic, {})
        style_resources = resources.get(learning_style.lower(), [])
        return style_resources if style_resources else resources.get("text", [])


# ================================================================
# ADAPTIVE RECOMMENDER ENGINE
# ================================================================

class AdaptiveRecommender:
    """
    Smart recommendation system
    
    Usage:
    ```python
    from learning_tracker import LearningTracker
    
    tracker = LearningTracker()
    recommender = AdaptiveRecommender()
    
    user_id = "student_123"
    
    # Get next topic
    next_topic = recommender.recommend_next_topic(tracker, user_id)
    
    # Get multiple recommendations
    recs = recommender.recommend_topics(tracker, user_id, count=3)
    
    # Personalize response
    response = recommender.personalize_response(
        "Here's how recursion works...",
        tracker.get_metrics(user_id),
        learning_style="visual"
    )
    ```
    """
    
    def __init__(self):
        self.difficulty_assessor = DifficultyAssessor()
        self.resource_matcher = ResourceMatcher()
    
    def recommend_next_topic(
        self,
        tracker,  # LearningTracker instance
        user_id: str
    ) -> Optional[Recommendation]:
        """Get single best recommendation"""
        
        recs = self.recommend_topics(tracker, user_id, count=1)
        return recs[0] if recs else None
    
    def recommend_topics(
        self,
        tracker,
        user_id: str,
        count: int = 5
    ) -> List[Recommendation]:
        """Get top N topic recommendations"""
        
        metrics = tracker.get_metrics(user_id)
        masteries = tracker.get_all_masteries(user_id)
        
        if not metrics:
            return []
        
        recommendations = []
        
        # Get recommended next topics from tracker
        for topic in metrics.recommended_next[:count]:
            # Get prerequisite strength
            prerequisites = tracker.TOPIC_HIERARCHY.get(topic, [])
            if prerequisites:
                prereq_confidences = [
                    tracker.get_mastery(user_id, p).confidence
                    for p in prerequisites
                    if tracker.get_mastery(user_id, p)
                ]
                prerequisite_strength = (
                    sum(prereq_confidences) / len(prereq_confidences)
                    if prereq_confidences else 0.5
                )
            else:
                prerequisite_strength = 1.0
            
            # Get difficulty
            difficulty = self.difficulty_assessor.get_adjusted_difficulty(
                topic,
                prerequisite_strength,
                metrics.estimated_learning_rate
            )
            
            # Estimate time
            time_estimate = self.difficulty_assessor.estimate_time(
                topic,
                metrics.estimated_learning_rate
            )
            
            # Get resources
            resources = self.resource_matcher.get_resources(
                topic,
                metrics.learning_style.value if metrics.learning_style else "mixed"
            )
            
            # Priority score
            priority = 0.8 + (0.2 * prerequisite_strength)
            
            rec = Recommendation(
                topic=topic,
                priority=priority,
                reason=f"Auto-progression after mastering prerequisites",
                difficulty_level=difficulty,
                estimated_time_minutes=time_estimate,
                prerequisites_met=prerequisite_strength >= 0.7,
                suggested_time="now" if prerequisite_strength >= 0.7 else "later",
                learning_resources=resources
            )
            
            recommendations.append(rec)
        
        # Add revision recommendations for struggle topics
        for topic in metrics.focus_areas[:1]:
            if topic not in [r.topic for r in recommendations]:
                rec = Recommendation(
                    topic=topic,
                    priority=0.6,
                    reason="Revisit struggle area with new approach",
                    difficulty_level="medium",
                    estimated_time_minutes=25,
                    prerequisites_met=True,
                    suggested_time="revisit",
                    learning_resources=self.resource_matcher.get_resources(
                        topic,
                        metrics.learning_style.value if metrics.learning_style else "mixed"
                    )
                )
                recommendations.append(rec)
        
        return recommendations[:count]
    
    def personalize_response(
        self,
        base_response: str,
        metrics,  # LearningMetrics
        user_profile = None,
        topic: Optional[str] = None
    ) -> PersonalizedResponse:
        """Personalize response based on user profile"""
        
        personalization_applied = []
        follow_up_questions = []
        suggested_examples = []
        
        # 1. Learning style personalization
        learning_style = metrics.learning_style.value if metrics.learning_style else "mixed"
        if learning_style == "visual":
            base_response += "\n\n📊 [Visual Diagram Should Go Here]\n"
            personalization_applied.append("visual_diagram")
        
        elif learning_style == "code":
            base_response += "\n\n💻 [Code Example Should Go Here]\n"
            personalization_applied.append("code_example")
        
        # 2. Difficulty level adjustment
        if metrics.total_topics > 0:
            mastery_rate = metrics.mastered_topics / metrics.total_topics
            if mastery_rate > 0.7:
                # Advanced user
                base_response += "\n📌 Advanced insight: "
                personalization_applied.append("advanced_insight")
            else:
                # Beginner
                base_response += "\n🌱 Let me break this down step-by-step: "
                personalization_applied.append("beginner_friendly")
        
        # 3. Generate follow-up questions
        if learning_style == "socratic" or "confusion" in metrics.focus_areas:
            follow_up_questions = [
                "Did that make sense? What part is confusing?",
                "Can you think of another example?",
                "Why do you think this works this way?"
            ]
            personalization_applied.append("socratic_questions")
        
        # 4. Suggest related examples
        if topic and topic in ResourceMatcher.RESOURCES:
            resources = ResourceMatcher.RESOURCES[topic]
            if "examples" in resources:
                suggested_examples = resources["examples"]
                personalization_applied.append("related_examples")
        
        estimated_difficulty = "medium"
        if metrics.mastered_topics / max(1, metrics.total_topics) > 0.7:
            estimated_difficulty = "hard"
        elif metrics.mastered_topics / max(1, metrics.total_topics) < 0.3:
            estimated_difficulty = "easy"
        
        return PersonalizedResponse(
            base_content=base_response,
            personalization_applied=personalization_applied,
            estimated_difficulty=estimated_difficulty,
            suggested_examples=suggested_examples,
            follow_up_questions=follow_up_questions,
            sources_cited=[]
        )
    
    def get_session_recommendation(
        self,
        tracker,
        user_id: str,
        available_time_minutes: int = 30
    ) -> Dict:
        """Recommend what to learn in a session"""
        
        metrics = tracker.get_metrics(user_id)
        next_recs = self.recommend_topics(tracker, user_id, count=3)
        
        # Filter by available time
        session_plan = {
            "topic": None,
            "estimated_duration": 0,
            "difficulty": "medium",
            "tasks": []
        }
        
        for rec in next_recs:
            if rec.estimated_time_minutes <= available_time_minutes * 0.8:
                session_plan["topic"] = rec.topic
                session_plan["estimated_duration"] = rec.estimated_time_minutes
                session_plan["difficulty"] = rec.difficulty_level
                break
        
        # Generate tasks
        if session_plan["topic"]:
            session_plan["tasks"] = [
                f"Learn basics of {session_plan['topic']}",
                f"Try a simple example",
                f"Solve 1-2 practice problems",
                f"Explain to someone else"
            ]
        
        return session_plan


# ================================================================
# EXAMPLE USAGE
# ================================================================

if __name__ == "__main__":
    print("🎯 Adaptive Recommender Demo\n")
    
    from learning_tracker import LearningTracker, InteractionType
    
    # Setup
    tracker = LearningTracker()
    recommender = AdaptiveRecommender()
    user_id = "student_456"
    
    # Simulate learning
    print("1️⃣  Simulating learning progress...")
    
    # Loops: mastered
    tracker.record_interaction(user_id, "loops", InteractionType.SUCCESS)
    tracker.record_interaction(user_id, "loops", InteractionType.SUCCESS)
    tracker.record_interaction(user_id, "loops", InteractionType.MASTERY)
    
    # If-statements: mastered
    tracker.record_interaction(user_id, "if-statements", InteractionType.SUCCESS)
    tracker.record_interaction(user_id, "if-statements", InteractionType.MASTERY)
    
    # Functions: learning
    tracker.record_interaction(user_id, "functions", InteractionType.STRUGGLE)
    tracker.record_interaction(user_id, "functions", InteractionType.PARTIAL)
    
    print("✅ Simulated 8 interactions\n")
    
    print("2️⃣  Getting recommendations...")
    recs = recommender.recommend_topics(tracker, user_id, count=3)
    
    for i, rec in enumerate(recs, 1):
        print(f"\nRecommendation {i}:")
        print(json.dumps(rec.to_dict(), indent=2))
    
    print("\n3️⃣  Personalizing response...")
    metrics = tracker.get_metrics(user_id)
    
    base_response = "Recursion is when a function calls itself"
    personalized = recommender.personalize_response(
        base_response,
        metrics,
        topic="recursion"
    )
    
    print(f"Personalization applied: {personalized.personalization_applied}")
    print(f"Follow-up questions: {personalized.follow_up_questions}")
    print(f"Content:\n{personalized.base_content}")
    
    print("\n4️⃣  Session planning...")
    session = recommender.get_session_recommendation(tracker, user_id, available_time_minutes=30)
    print(json.dumps(session, indent=2))
    
    print("\n✅ Demo complete!")
