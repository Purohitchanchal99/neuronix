#!/usr/bin/env python3
"""
Phase 3B: Distress Tracking System
===================================
Detects emotional state trends and escalation patterns

Critical for:
  - Proactive safety (escalation detection)
  - Intervention timing
  - Pattern recognition
  - Long-term trend analysis
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import mean, stdev


@dataclass
class DistressPoint:
    """Single distress measurement"""
    timestamp: datetime
    score: float  # 0.0 to 1.0
    context: str  # User query that caused this
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'score': self.score,
            'context': self.context[:50]  # Truncate
        }


class DistressTracker:
    """
    Tracks emotional distress over time and detects patterns
    
    Detects:
    - Escalation (trending upward)
    - Improvement (trending downward)
    - Chronic stress (consistently high)
    - Crisis signals (sudden spike)
    """
    
    def __init__(self, window_size: int = 5):
        """
        Args:
            window_size: Number of recent measurements to track
        """
        self.window_size = window_size
        self.distress_history: Dict[str, List[DistressPoint]] = {}
        self.escalation_alerts: Dict[str, List[Dict]] = {}
    
    def record_distress(
        self,
        user_id: str,
        score: float,
        context: str = ""
    ) -> Dict:
        """
        Record distress measurement and analyze trends
        
        Args:
            user_id: User identifier
            score: Distress level 0.0 (calm) to 1.0 (crisis)
            context: Reason for the score
        
        Returns:
            Analysis dict with trend info
        """
        
        # Initialize history if needed
        if user_id not in self.distress_history:
            self.distress_history[user_id] = []
            self.escalation_alerts[user_id] = []
        
        # Add new measurement
        point = DistressPoint(
            timestamp=datetime.now(),
            score=score,
            context=context
        )
        self.distress_history[user_id].append(point)
        
        # Only keep recent measurements
        if len(self.distress_history[user_id]) > self.window_size:
            self.distress_history[user_id].pop(0)
        
        # Analyze trend
        analysis = self._analyze_trend(user_id)
        
        # Check for alerts
        self._check_alerts(user_id, analysis)
        
        return analysis
    
    def _analyze_trend(self, user_id: str) -> Dict:
        """Analyze distress trend for user"""
        
        history = self.distress_history.get(user_id, [])
        
        if len(history) == 0:
            return {
                'trend': 'unknown',
                'current_score': 0.0,
                'average_score': 0.0,
                'status': 'no_data'
            }
        
        # Current measurement
        current_score = history[-1].score
        
        # Calculate average
        scores = [p.score for p in history]
        avg_score = mean(scores)
        
        # Trend analysis (need at least 3 points)
        trend = 'stable'
        volatility = 0.0
        
        if len(history) >= 3:
            # Simple linear trend: compare first vs last
            first_third_avg = mean([p.score for p in history[:len(history)//3 + 1]])
            last_third_avg = mean([p.score for p in history[-len(history)//3:]])
            
            diff = last_third_avg - first_third_avg
            
            if diff > 0.15:
                trend = 'escalating'
            elif diff < -0.15:
                trend = 'improving'
            else:
                trend = 'stable'
            
            # Calculate volatility (standard deviation)
            volatility = stdev(scores) if len(scores) > 1 else 0.0
        
        # Determine urgency level
        urgency = 'low'
        if current_score > 0.8:
            urgency = 'critical'
        elif current_score > 0.6:
            urgency = 'high'
        elif current_score > 0.4:
            urgency = 'medium'
        
        return {
            'trend': trend,
            'current_score': current_score,
            'average_score': avg_score,
            'volatility': volatility,
            'urgency': urgency,
            'measurements': len(history),
            'history': [p.to_dict() for p in history[-3:]]  # Last 3
        }
    
    def _check_alerts(self, user_id: str, analysis: Dict):
        """Check for alert conditions"""
        
        alerts = []
        
        # Alert 1: Escalating trend
        if analysis['trend'] == 'escalating':
            alerts.append({
                'type': 'escalating_trend',
                'severity': 'high',
                'message': 'User distress is increasing',
                'recommendation': 'Offer additional support'
            })
        
        # Alert 2: High volatility
        if analysis['volatility'] > 0.3:
            alerts.append({
                'type': 'high_volatility',
                'severity': 'medium',
                'message': 'Large swings in emotional state',
                'recommendation': 'Provide grounding techniques'
            })
        
        # Alert 3: Critical urgency
        if analysis['urgency'] == 'critical':
            alerts.append({
                'type': 'critical_distress',
                'severity': 'critical',
                'message': 'Distress level is critical (>0.8)',
                'recommendation': 'Escalate to crisis protocol'
            })
        
        # Alert 4: Chronic high stress
        if analysis['average_score'] > 0.6 and analysis['measurements'] >= 3:
            alerts.append({
                'type': 'chronic_stress',
                'severity': 'high',
                'message': 'Consistently elevated distress',
                'recommendation': 'Suggest professional help'
            })
        
        # Store alerts
        if alerts:
            self.escalation_alerts[user_id].extend(alerts)
    
    def get_user_trend(self, user_id: str) -> str:
        """Get simple trend status"""
        analysis = self._analyze_trend(user_id)
        return analysis.get('trend', 'unknown')
    
    def get_user_urgency(self, user_id: str) -> str:
        """Get current urgency level"""
        analysis = self._analyze_trend(user_id)
        return analysis.get('urgency', 'low')
    
    def get_alerts(self, user_id: str, clear: bool = False) -> List[Dict]:
        """Get and optionally clear alerts"""
        alerts = self.escalation_alerts.get(user_id, [])
        
        if clear:
            self.escalation_alerts[user_id] = []
        
        return alerts
    
    def get_full_analysis(self, user_id: str) -> Dict:
        """Get full distress analysis for user"""
        analysis = self._analyze_trend(user_id)
        alerts = self.get_alerts(user_id)
        
        return {
            'analysis': analysis,
            'alerts': alerts,
            'total_alerts': len(alerts),
            'timestamp': datetime.now().isoformat()
        }


# ================================================================
# USAGE EXAMPLE & TESTING
# ================================================================

if __name__ == "__main__":
    
    print("\n" + "="*80)
    print("PHASE 3B: DISTRESS TRACKING SYSTEM - DEMO")
    print("="*80)
    
    tracker = DistressTracker()
    user_id = "user_456"
    
    # Simulate escalating distress pattern
    print("\n📊 Simulating escalating distress pattern:")
    print("─" * 80)
    
    measurements = [
        (0.35, "Feeling a bit worried"),
        (0.45, "Getting more anxious"),
        (0.55, "Can't concentrate"),
        (0.65, "Feeling overwhelmed"),
        (0.75, "Can't sleep, very distressed"),
    ]
    
    for score, context in measurements:
        analysis = tracker.record_distress(user_id, score, context)
        
        print(f"\n[Measurement {analysis['measurements']}]")
        print(f"  Score: {score:.0%}")
        print(f"  Context: {context}")
        print(f"  Trend: {analysis['trend'].upper()}")
        print(f"  Urgency: {analysis['urgency'].upper()}")
        
        # Check for alerts
        full = tracker.get_full_analysis(user_id)
        if full['alerts']:
            print(f"  🚨 ALERTS: {len(full['alerts'])} triggered")
            for alert in full['alerts']:
                print(f"     - {alert['type']}: {alert['message']}")
    
    # Final analysis
    print("\n" + "─" * 80)
    print("📈 FINAL ANALYSIS:")
    print("─" * 80)
    
    full_analysis = tracker.get_full_analysis(user_id)
    
    print(f"\nTrend Analysis:")
    print(f"  Current Score: {full_analysis['analysis']['current_score']:.0%}")
    print(f"  Average Score: {full_analysis['analysis']['average_score']:.0%}")
    print(f"  Trend: {full_analysis['analysis']['trend'].upper()}")
    print(f"  Urgency: {full_analysis['analysis']['urgency'].upper()}")
    print(f"  Volatility: {full_analysis['analysis']['volatility']:.2f}")
    
    print(f"\nActive Alerts: {full_analysis['total_alerts']}")
    for alert in full_analysis['alerts']:
        print(f"  🔴 [{alert['severity'].upper()}] {alert['type']}")
        print(f"     Message: {alert['message']}")
        print(f"     Action: {alert['recommendation']}")
    
    # Test improvement scenario
    print("\n\n" + "="*80)
    print("Test 2: Improvement Pattern")
    print("="*80)
    
    user_id2 = "user_789"
    
    print("\n📊 User shows improvement:")
    print("─" * 80)
    
    improvements = [
        (0.75, "Very distressed"),
        (0.65, "Getting support"),
        (0.55, "Feeling a bit better"),
        (0.45, "Making progress"),
        (0.35, "Much better now"),
    ]
    
    for score, context in improvements:
        analysis = tracker.record_distress(user_id2, score, context)
        print(f"  {score:.0%} → {analysis['trend'].upper()}")
    
    # Show improvement
    final = tracker.get_full_analysis(user_id2)
    print(f"\n✅ Final Trend: {final['analysis']['trend'].upper()}")
    print(f"✅ Active Alerts: {final['total_alerts']}")
    
    print("\n" + "="*80)
    print("✅ DISTRESS TRACKING DEMO COMPLETE")
    print("="*80)
    print("\n🎯 Key Achievements:")
    print("  ✓ Tracks distress over time")
    print("  ✓ Detects escalation patterns")
    print("  ✓ Detects improvement")
    print("  ✓ Measures volatility")
    print("  ✓ Generates proactive alerts")
    print("  ✓ Enables trend-based intervention")
    print("\n")
