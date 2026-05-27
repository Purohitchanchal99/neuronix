#!/usr/bin/env python3
"""
Phase 6: Session Summarizer
============================
Auto-generates session insights and learning summaries

Features:
- Extract key learnings
- Identify struggle points
- Summarize topics covered
- Generate insights about learning style
- Recommend next steps
- Create session reports

Example:
  summarizer = SessionSummarizer()
  
  summary = summarizer.summarize_session(
      conversation,
      metrics,
      learning_tracker
  )
  
  print(summary.executive_summary)
  # "Today you learned about loops and struggled with nested loops"
  
  print(summary.recommendations)
  # ["Next: Practice nested loops", "Revisit: Variable scope"]
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
import json


# ================================================================
# SUMMARY MODELS
# ================================================================

@dataclass
class LearningInsight:
    """Single insight about learning"""
    type: str  # "breakthrough", "struggle", "misconception", "pattern"
    description: str
    evidence: List[str]  # Supporting quotes/data
    confidence: float  # 0-1
    action_item: Optional[str] = None
    
    def to_dict(self):
        return {
            "type": self.type,
            "insight": self.description,
            "confidence": round(self.confidence, 2),
            "action": self.action_item
        }


@dataclass
class SessionSummary:
    """Complete session summary"""
    session_id: str
    user_id: str
    duration_minutes: int
    executive_summary: str
    topics_covered: List[str]
    topics_mastered: List[str]
    topics_struggled: List[str]
    key_learnings: List[str]
    misconceptions_identified: List[str]
    insights: List[LearningInsight]
    recommendations: List[str]
    next_steps: List[str]
    emotional_journey: str  # "frustrated -> confident"
    learning_style_indicators: List[str]
    productivity_score: float  # 0-1
    
    def to_dict(self):
        return {
            "summary": self.executive_summary,
            "duration": f"{self.duration_minutes} min",
            "topics_covered": self.topics_covered,
            "mastered": self.topics_mastered,
            "struggled_with": self.topics_struggled,
            "key_learnings": self.key_learnings,
            "misconceptions": self.misconceptions_identified,
            "insights": [i.to_dict() for i in self.insights],
            "recommendations": self.recommendations,
            "next_steps": self.next_steps,
            "productivity_score": round(self.productivity_score, 2)
        }


# ================================================================
# SESSION SUMMARIZER
# ================================================================

class SessionSummarizer:
    """
    Generates intelligent session summaries
    
    Usage:
    ```python
    summarizer = SessionSummarizer()
    
    # After session ends
    conversation = store.close_conversation(user_id)
    metrics = tracker.get_metrics(user_id)
    
    summary = summarizer.summarize_session(
        conversation,
        metrics,
        tracker
    )
    
    # Print beautiful summary
    print(summary.executive_summary)
    print("Next time:", summary.next_steps)
    ```
    """
    
    def __init__(self):
        """Initialize summarizer"""
        self.llm_available = False
        
        try:
            import google.generativeai as genai
            self.llm_available = True
            self.use_llm = True
        except ImportError:
            self.use_llm = False
    
    def summarize_session(
        self,
        conversation,  # Conversation object from memory_system
        metrics,  # LearningMetrics from learning_tracker
        tracker  # LearningTracker instance
    ) -> SessionSummary:
        """Summarize complete session"""
        
        # Extract conversation data
        messages = conversation.messages if hasattr(conversation, 'messages') else []
        
        # Topic analysis
        all_topics = self._extract_topics(messages)
        topics_covered = list(set(all_topics))
        
        # Get mastered vs struggled topics
        topics_mastered = getattr(metrics, 'mastered_topics', 0) if metrics else 0
        topics_struggled = getattr(metrics, 'focus_areas', []) if metrics else []
        
        # Extract key learnings
        key_learnings = self._extract_key_learnings(messages, tracker)
        
        # Identify misconceptions
        misconceptions = self._identify_misconceptions(messages, tracker)
        
        # Generate insights
        insights = self._generate_insights(messages, metrics, tracker)
        
        # Create executive summary
        executive_summary = self._create_executive_summary(
            metrics,
            topics_covered,
            key_learnings,
            misconceptions
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            metrics,
            topics_struggled,
            misconceptions
        )
        
        # Generate next steps
        next_steps = self._generate_next_steps(
            metrics,
            topics_covered,
            recommendations
        )
        
        # Analyze emotional journey
        emotional_journey = self._analyze_emotional_journey(messages)
        
        # Detect learning style indicators
        learning_indicators = self._detect_learning_indicators(messages)
        
        # Calculate productivity score
        productivity_score = self._calculate_productivity_score(
            metrics,
            messages,
            key_learnings
        )
        
        return SessionSummary(
            session_id=conversation.session_id if hasattr(conversation, 'session_id') else "unknown",
            user_id=conversation.user_id if hasattr(conversation, 'user_id') else "unknown",
            duration_minutes=conversation.duration_minutes or 0,
            executive_summary=executive_summary,
            topics_covered=topics_covered,
            topics_mastered=[t for t in topics_covered if any(
                tracker.get_mastery(conversation.user_id, t) and
                tracker.get_mastery(conversation.user_id, t).confidence >= 0.8
                for _ in [1]  # Hack to use tracker in comprehension
            )] if tracker else [],
            topics_struggled=topics_struggled,
            key_learnings=key_learnings,
            misconceptions_identified=misconceptions,
            insights=insights,
            recommendations=recommendations,
            next_steps=next_steps,
            emotional_journey=emotional_journey,
            learning_style_indicators=learning_indicators,
            productivity_score=productivity_score
        )
    
    def _extract_topics(self, messages: List) -> List[str]:
        """Extract topics from conversation"""
        topics = []
        
        for msg in messages:
            if hasattr(msg, 'topics') and msg.topics:
                topics.extend(msg.topics)
        
        return topics
    
    def _extract_key_learnings(
        self,
        messages: List,
        tracker
    ) -> List[str]:
        """Extract main things user learned"""
        learnings = []
        
        for msg in messages:
            if hasattr(msg, 'role') and msg.role == "assistant":
                # Assistant messages contain learnings
                if hasattr(msg, 'content') and len(msg.content) > 20:
                    # Extract first sentence (often the key learning)
                    first_sentence = msg.content.split('.')[0]
                    if len(first_sentence) > 10:
                        learnings.append(first_sentence)
        
        return learnings[:5]  # Top 5 learnings
    
    def _identify_misconceptions(
        self,
        messages: List,
        tracker
    ) -> List[str]:
        """Identify common misconceptions"""
        misconceptions = []
        
        for msg in messages:
            if hasattr(msg, 'role') and msg.role == "user":
                # Look for confusion signals
                content = msg.content.lower() if hasattr(msg, 'content') else ""
                if any(word in content for word in ["confused", "don't understand", "isn't it", "so it's"]):
                    misconceptions.append(msg.content if hasattr(msg, 'content') else "")
        
        return [m for m in misconceptions if m][:3]  # Top 3
    
    def _generate_insights(
        self,
        messages: List,
        metrics,
        tracker
    ) -> List[LearningInsight]:
        """Generate intelligent insights"""
        insights = []
        
        # Insight 1: Breakthrough
        if any(msg.role == "user" and "now I understand" in (msg.content or "").lower() 
               for msg in messages if hasattr(msg, 'role')):
            insights.append(LearningInsight(
                type="breakthrough",
                description="You had a breakthrough moment in understanding!",
                evidence=["Expressed clarity during session"],
                confidence=0.8,
                action_item="Build on this momentum with related concepts"
            ))
        
        # Insight 2: Persistence
        if len([m for m in messages if hasattr(m, 'role') and m.role == "user"]) > 8:
            insights.append(LearningInsight(
                type="pattern",
                description="You asked many questions - great curiosity!",
                evidence=[f"Asked {len([m for m in messages if hasattr(m, 'role') and m.role == 'user'])} questions"],
                confidence=0.9,
                action_item="Keep asking questions - it's how you learn best"
            ))
        
        # Insight 3: Misconceptions found
        if len([m for m in messages if hasattr(m, 'role') and "misconception" in (m.metadata or {})]) > 0:
            insights.append(LearningInsight(
                type="misconception",
                description="Identified some misconceptions to address",
                evidence=["Several concepts needed clarification"],
                confidence=0.7,
                action_item="Review these specific areas in next session"
            ))
        
        return insights[:3]  # Top 3 insights
    
    def _create_executive_summary(
        self,
        metrics,
        topics_covered: List[str],
        key_learnings: List[str],
        misconceptions: List[str]
    ) -> str:
        """Create friendly executive summary"""
        
        summary_parts = []
        
        if topics_covered:
            summary_parts.append(f"🎯 You covered: {', '.join(topics_covered[:3])}")
        
        if key_learnings:
            summary_parts.append(f"💡 Key learning: {key_learnings[0]}")
        
        if metrics and hasattr(metrics, 'mastered_topics'):
            summary_parts.append(f"✅ Progress: {metrics.mastered_topics} topics mastered")
        
        if misconceptions:
            summary_parts.append(f"🔍 Watch out for: {misconceptions[0]}")
        
        return "\n".join(summary_parts)
    
    def _generate_recommendations(
        self,
        metrics,
        topics_struggled: List[str],
        misconceptions: List[str]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if topics_struggled:
            recommendations.append(f"Practice more with {topics_struggled[0]} tomorrow")
        
        if misconceptions:
            recommendations.append(f"Review misconception about {misconceptions[0]}")
        
        if metrics and hasattr(metrics, 'recommended_next'):
            if metrics.recommended_next:
                recommendations.append(f"Then learn: {metrics.recommended_next[0]}")
        
        recommendations.append("Take a break - spaced repetition helps!")
        
        return recommendations[:3]
    
    def _generate_next_steps(
        self,
        metrics,
        topics_covered: List[str],
        recommendations: List[str]
    ) -> List[str]:
        """Generate next steps for next session"""
        next_steps = []
        
        next_steps.append("📋 Session plan for tomorrow:")
        
        if recommendations:
            next_steps.extend(recommendations[:2])
        
        next_steps.append("Practice 1-2 problems on topics covered")
        next_steps.append("Review your notes or create a summary")
        
        if metrics and hasattr(metrics, 'recommended_next'):
            if metrics.recommended_next:
                next_steps.append(f"Explore: {metrics.recommended_next[0]}")
        
        return next_steps[:5]
    
    def _analyze_emotional_journey(self, messages: List) -> str:
        """Analyze emotional progression during session"""
        tones = [m.tone for m in messages if hasattr(m, 'tone') and m.tone]
        
        if not tones:
            return "steady"
        
        # Simple progression
        if tones[0] == "confused" and tones[-1] == "confident":
            return "📈 Confused → Confident (Great improvement!)"
        elif "frustrated" in tones and tones[-1] == "satisfied":
            return "🎯 Frustrated → Satisfied (Perseverance paid off!)"
        elif all(t == "confident" for t in tones):
            return "💪 Consistently confident"
        else:
            return f"Mixed: {tones[0]} → {tones[-1]}"
    
    def _detect_learning_indicators(self, messages: List) -> List[str]:
        """Detect how user prefers to learn"""
        indicators = []
        
        content = " ".join([m.content.lower() if hasattr(m, 'content') else "" for m in messages])
        
        if "show me" in content or "example" in content:
            indicators.append("Prefers examples")
        if "why" in content or "how" in content:
            indicators.append("Asks conceptual questions")
        if "code" in content or "write" in content:
            indicators.append("Wants to code")
        if "visual" in content or "diagram" in content:
            indicators.append("Wants diagrams")
        
        return indicators or ["Balanced learner"]
    
    def _calculate_productivity_score(
        self,
        metrics,
        messages: List,
        key_learnings: List[str]
    ) -> float:
        """Score overall productivity (0-1)"""
        
        score = 0.0
        
        # Message count (more engagement = higher score, but not too many)
        message_count = len(messages)
        if 4 <= message_count <= 20:
            score += 0.3
        elif 20 < message_count <= 30:
            score += 0.25
        
        # Learning outcomes
        if key_learnings:
            score += 0.3 * len(key_learnings) / 5  # Up to 0.3
        
        # Progress
        if metrics and hasattr(metrics, 'mastered_topics'):
            if metrics.mastered_topics > 0:
                score += 0.4
        
        return min(1.0, score)


# ================================================================
# EXAMPLE USAGE
# ================================================================

if __name__ == "__main__":
    print("📝 Session Summarizer Demo\n")
    
    from memory_system import ConversationStore, Message
    from learning_tracker import LearningTracker, LearningMetrics, InteractionType
    from datetime import datetime
    
    # Create test data
    store = ConversationStore()
    tracker = LearningTracker()
    summarizer = SessionSummarizer()
    
    user_id = "student_789"
    
    print("1️⃣  Creating test session...")
    
    # Start conversation
    store.start_conversation(user_id)
    
    # Add messages simulating a learning session
    store.add_message(user_id, "I'm confused about recursion", role="user", tone="confused")
    store.add_message(user_id, "Recursion is when a function calls itself", role="assistant")
    store.add_message(user_id, "Can you show an example?", role="user", tone="curious")
    store.add_message(user_id, "Sure! Here's factorial...", role="assistant")
    store.add_message(user_id, "Oh! Now I understand!", role="user", tone="confident")
    store.add_message(user_id, "So the base case stops it?", role="user", tone="learning")
    store.add_message(user_id, "Exactly! That's the key.", role="assistant")
    
    print("✅ Created 7-message session\n")
    
    print("2️⃣  Recording learning progress...")
    
    # Record learning for metrics
    tracker.record_interaction(user_id, "recursion", InteractionType.CONFUSION)
    tracker.record_interaction(user_id, "recursion", InteractionType.PARTIAL)
    tracker.record_interaction(user_id, "recursion", InteractionType.SUCCESS)
    tracker.record_interaction(user_id, "functions", InteractionType.SUCCESS)
    tracker.record_interaction(user_id, "functions", InteractionType.MASTERY)
    
    print("✅ Recorded 5 interactions\n")
    
    print("3️⃣  Closing session and generating summary...")
    
    # Close and get metrics
    conversation = store.close_conversation(user_id)
    metrics = tracker.get_metrics(user_id)
    
    print("✅ Session closed\n")
    
    print("4️⃣  Generating summary...")
    
    summary = summarizer.summarize_session(conversation, metrics, tracker)
    
    print("\n" + "="*60)
    print("📊 SESSION SUMMARY")
    print("="*60)
    print(f"\n{summary.executive_summary}")
    print(f"\nDuration: {summary.duration_minutes} minutes")
    print(f"Topics covered: {', '.join(summary.topics_covered)}")
    print(f"Productivity: {summary.productivity_score:.0%}")
    print(f"\nEmotional journey: {summary.emotional_journey}")
    print(f"Learning style: {', '.join(summary.learning_style_indicators)}")
    
    print(f"\n💡 Key insights:")
    for insight in summary.insights:
        print(f"  • {insight.description}")
    
    print(f"\n✅ Recommendations:")
    for rec in summary.recommendations:
        print(f"  • {rec}")
    
    print(f"\n📋 Next steps:")
    for step in summary.next_steps:
        print(f"  • {step}")
    
    print("\n" + "="*60)
    print("✅ Demo complete!")
