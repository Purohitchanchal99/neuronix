#!/usr/bin/env python3
"""
Phase 3D: Proactive Safety System
==================================
Detects escalation patterns BEFORE crisis occurs

Monitors:
- Repeated negative queries (same topic, worsening)
- Escalation over time
- Crisis signal combinations
- Intervention opportunities
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


class ProactiveSafetySystem:
    """
    Detects concerning patterns and triggers interventions proactively
    
    Patterns it detects:
    1. Repeated negative queries (asking about same problem repeatedly)
    2. Escalating distress trend
    3. Crisis keywords with increasing intensity
    4. Isolation signals (no support system)
    5. Treatment refusal pattern
    """
    
    def __init__(self):
        # Track query patterns
        self.user_query_history: Dict[str, List[Dict]] = {}
        self.escalation_patterns: Dict[str, Dict] = {}
    
    def analyze_pattern(
        self,
        user_id: str,
        query: str,
        distress_level: float,
        distress_trend: str,
        conversation_turn: int
    ) -> Dict:
        """
        Analyze query for concerning patterns
        
        Args:
            user_id: User ID
            query: User query
            distress_level: Current distress (0-1)
            distress_trend: Whether escalating/improving/stable
            conversation_turn: Which turn in conversation
        
        Returns:
            Pattern analysis with recommendations
        """
        
        # Initialize if needed
        if user_id not in self.user_query_history:
            self.user_query_history[user_id] = []
            self.escalation_patterns[user_id] = {}
        
        # Record this query
        self.user_query_history[user_id].append({
            'timestamp': datetime.now(),
            'query': query,
            'distress_level': distress_level,
            'turn': conversation_turn
        })
        
        # Trim to recent queries only
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.user_query_history[user_id] = [
            q for q in self.user_query_history[user_id]
            if q['timestamp'] > cutoff_time
        ]
        
        # Analyze patterns
        patterns = self._detect_patterns(user_id, query, distress_level, distress_trend)
        
        return patterns
    
    def _detect_patterns(
        self,
        user_id: str,
        current_query: str,
        current_distress: float,
        distress_trend: str
    ) -> Dict:
        """Detect multiple concerning patterns"""
        
        q_lower = current_query.lower()
        history = self.user_query_history[user_id]
        
        patterns_detected = []
        severity = 'low'
        recommendation = ""
        
        # Pattern 1: REPEATED NEGATIVE QUERIES
        # Same topic asked multiple times, distress increasing
        if len(history) >= 3:
            recent_queries = [h['query'].lower() for h in history[-3:]]
            
            # Check for repeated distress topics
            distress_words = ['anxious', 'depressed', 'sad', 'stressed', 'overwhelmed']
            distress_count = sum(1 for q in recent_queries if any(w in q for w in distress_words))
            
            if distress_count >= 2:
                distress_levels = [h['distress_level'] for h in history[-3:]]
                avg_recent = sum(distress_levels) / len(distress_levels)
                
                if avg_recent > 0.55:
                    patterns_detected.append({
                        'type': 'repeated_negative_patterns',
                        'severity': 'medium',
                        'message': f'User has mentioned distress {distress_count} of last 3 times',
                        'intervention': 'Acknowledge pattern: "I notice this has been coming up repeatedly..."'
                    })
                    severity = 'medium'
        
        # Pattern 2: ESCALATING TREND + HIGH DISTRESS
        if distress_trend == 'escalating' and current_distress > 0.65:
            patterns_detected.append({
                'type': 'escalating_crisis_risk',
                'severity': 'high',
                'message': 'Distress escalating and currently high',
                'intervention': 'Proactively offer: "I\'m noticing this is getting harder. Would it help to talk about getting some support?"'
            })
            severity = 'high'
        
        # Pattern 3: CRISIS KEYWORDS + TREND
        crisis_keywords = [
            'hurt myself', 'kill myself', 'suicide', 'end it',
            'can\'t take it', 'give up', 'worthless', 'hopeless'
        ]
        
        has_crisis_keyword = any(kw in q_lower for kw in crisis_keywords)
        
        if has_crisis_keyword:
            # Only add if not already high severity
            if severity != 'high':
                patterns_detected.append({
                    'type': 'crisis_keywords_present',
                    'severity': 'critical',
                    'message': 'Crisis keywords detected',
                    'intervention': 'ACTIVATE CRISIS PROTOCOL'
                })
                severity = 'critical'
        
        # Pattern 4: ISOLATION SIGNALS
        isolation_keywords = ['alone', 'no one cares', 'nobody', 'alone at night']
        
        if any(kw in q_lower for kw in isolation_keywords):
            patterns_detected.append({
                'type': 'isolation_signal',
                'severity': 'high' if current_distress > 0.6 else 'medium',
                'message': 'User expressing feelings of isolation',
                'intervention': 'Ask: "Do you have someone in your life you feel safe talking to?"'
            })
            if current_distress > 0.6:
                severity = 'high'
        
        # Pattern 5: TREATMENT REFUSAL
        refusal_keywords = ['won\'t help', 'tried everything', 'nothing works', 'pointless']
        
        if any(kw in q_lower for kw in refusal_keywords):
            patterns_detected.append({
                'type': 'treatment_refusal',
                'severity': 'medium',
                'message': 'User expressing hopelessness about treatment',
                'intervention': 'Gently explore: "What has helped a little, even temporarily?"'
            })
            severity = 'medium'
        
        # Pattern 6: DURATION ESCALATION
        # User mentioning longer durations with increasing distress
        if 'weeks' in q_lower or 'months' in q_lower or 'a while' in q_lower:
            if len(history) >= 2:
                prev_distress = history[-1]['distress_level'] if len(history) > 1 else 0
                
                if current_distress > 0.6 and current_distress > prev_distress:
                    patterns_detected.append({
                        'type': 'chronic_worsening',
                        'severity': 'high',
                        'message': 'Chronic issue getting worse',
                        'intervention': 'Recommend: "This has been going on, and it\'s getting harder. Professional support could really help."'
                    })
                    severity = 'high'
        
        # Determine priority action
        action = self._get_action_for_severity(severity, patterns_detected)
        
        return {
            'patterns_detected': patterns_detected,
            'total_patterns': len(patterns_detected),
            'overall_severity': severity,
            'recommended_action': action,
            'should_escalate': severity in ['high', 'critical'],
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_action_for_severity(self, severity: str, patterns: List[Dict]) -> str:
        """Get recommended action based on severity"""
        
        if severity == 'critical':
            return (
                "IMMEDIATELY activate crisis protocol. "
                "Call crisis line, alert mental health professional. "
                "Do not leave conversation."
            )
        
        elif severity == 'high':
            return (
                "Escalate support. Offer professional referral. "
                "Express genuine concern. "
                "Suggest immediate steps (call therapist, go to ER if thinking of self-harm)."
            )
        
        elif severity == 'medium':
            return (
                "Acknowledge pattern. Validate experience. "
                "Suggest that professional support could help. "
                "Provide specific resources."
            )
        
        else:
            return (
                "Continue supportive conversation. "
                "Monitor for pattern development. "
                "Be ready to escalate if needed."
            )
    
    def get_proactive_message(
        self,
        user_id: str,
        severity: str
    ) -> Optional[str]:
        """Get proactive message to add to response if pattern detected"""
        
        if severity == 'critical':
            return None  # Crisis handled separately
        
        elif severity == 'high':
            return (
                "\n\n🛡️ **I want to check in:** You've been dealing with this for a while, "
                "and it sounds like it's getting harder. You don't have to handle this alone. "
                "Professional support—talking to a therapist or counselor—can make a real difference. "
                "Would you be open to that?"
            )
        
        elif severity == 'medium':
            return (
                "\n\n💙 **I notice:** You've mentioned this concern a few times now. "
                "That tells me it's really weighing on you. This is exactly what therapists are trained for. "
                "Would talking to someone professional feel helpful?"
            )
        
        return None


# ================================================================
# DEMO & TESTING
# ================================================================

if __name__ == "__main__":
    
    print("\n" + "="*80)
    print("PHASE 3D: PROACTIVE SAFETY SYSTEM - DEMO")
    print("="*80)
    
    safety = ProactiveSafetySystem()
    user_id = "user_safety_test"
    
    # Scenario 1: Escalating pattern
    print("\n[Scenario 1] Escalating Distress Pattern")
    print("─" * 80)
    
    queries_scenario1 = [
        ("I've been feeling anxious", 0.35, "stable", 1),
        ("It's getting worse lately", 0.50, "stable", 2),
        ("I can't sleep and I'm overwhelmed", 0.70, "escalating", 3),
    ]
    
    for query, distress, trend, turn in queries_scenario1:
        analysis = safety.analyze_pattern(user_id, query, distress, trend, turn)
        
        print(f"\n[Turn {turn}] \"{query}\"")
        print(f"  Distress: {distress:.0%} | Trend: {trend}")
        print(f"  Severity: {analysis['overall_severity'].upper()}")
        print(f"  Patterns: {analysis['total_patterns']}")
        
        if analysis['patterns_detected']:
            for pattern in analysis['patterns_detected']:
                print(f"    - [{pattern['severity']}] {pattern['type']}")
                print(f"      Action: {pattern['intervention']}")
        
        if analysis['recommended_action']:
            print(f"  Recommended Action: {analysis['recommended_action'][:100]}...")
        
        msg = safety.get_proactive_message(user_id, analysis['overall_severity'])
        if msg:
            print(f"  Proactive Message to Add:")
            print(f"  {msg}")
    
    # Scenario 2: Isolation + distress
    print("\n\n[Scenario 2] Isolation Signals")
    print("─" * 80)
    
    safety2 = ProactiveSafetySystem()
    user_id2 = "user_isolation"
    
    queries_scenario2 = [
        ("I feel so alone", 0.60, "stable", 1),
        ("Nobody understands me", 0.65, "stable", 2),
    ]
    
    for query, distress, trend, turn in queries_scenario2:
        analysis = safety2.analyze_pattern(user_id2, query, distress, trend, turn)
        
        print(f"\n[Turn {turn}] \"{query}\"")
        print(f"  Severity: {analysis['overall_severity'].upper()}")
        
        if analysis['patterns_detected']:
            for pattern in analysis['patterns_detected']:
                print(f"    - {pattern['type']}: {pattern['message']}")
    
    # Scenario 3: Treatment refusal
    print("\n\n[Scenario 3] Treatment Refusal Pattern")
    print("─" * 80)
    
    safety3 = ProactiveSafetySystem()
    user_id3 = "user_refusal"
    
    analysis = safety3.analyze_pattern(
        user_id3,
        "I've tried everything and nothing works",
        0.65,
        "stable",
        1
    )
    
    print(f"Query: \"I've tried everything and nothing works\"")
    print(f"Severity: {analysis['overall_severity'].upper()}")
    
    if analysis['patterns_detected']:
        for pattern in analysis['patterns_detected']:
            print(f"  Pattern: {pattern['type']}")
            print(f"  Intervention: {pattern['intervention']}")
    
    print("\n" + "="*80)
    print("✅ PROACTIVE SAFETY SYSTEM DEMO COMPLETE")
    print("="*80)
    print("\n🎯 Key Capabilities:")
    print("  ✓ Detects repeated negative patterns")
    print("  ✓ Identifies escalation trends")
    print("  ✓ Recognizes crisis keywords")
    print("  ✓ Detects isolation signals")
    print("  ✓ Recognizes treatment refusal")
    print("  ✓ Triggers proactive interventions")
    print("  ✓ Generates proactive messages")
    print("\n")
