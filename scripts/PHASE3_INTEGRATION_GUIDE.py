#!/usr/bin/env python3
from typing import Dict, List
from datetime import datetime
from scripts.conversation_memory import ConversationMemory, Message
from scripts.distress_tracker import DistressTracker
from scripts.contextual_followup_engine import ContextualFollowupEngine
from scripts.proactive_safety import ProactiveSafetySystem
from scripts.response_quality_engine import ResponseQualityEngine

"""
Phase 3: Complete Integration Guide
====================================
How to add Conversation Intelligence Layer to your chat engine

Architecture After Phase 3:

User Query
   ↓
[MEMORY] Get conversation context + distress history
   ↓
[TONE DETECTION] Analyze emotion (Phase 2)
   ↓
[DISTRESS TRACKING] Record score, detect trends
   ↓
[PROACTIVE SAFETY] Detect escalation patterns
   ↓
[RAG RETRIEVAL] Get relevant knowledge
   ↓
[RESPONSE GENERATION] Phase 2 quality response
   ↓
[CONTEXTUAL FOLLOWUP] Smart question based on context
   ↓
Add Proactive Message (if pattern detected)
   ↓
Final Response with Context Awareness
"""

# ================================================================
# STEP 1: ADD IMPORTS TO neuronix_core.py
# ================================================================

"""
Add these imports at the top:

from scripts.conversation_memory import ConversationMemory, Message
from scripts.distress_tracker import DistressTracker
from scripts.contextual_followup_engine import ContextualFollowupEngine
from scripts.proactive_safety import ProactiveSafetySystem
from scripts.response_quality_engine import ResponseQualityEngine
"""


# ================================================================
# STEP 2: MODIFY NeuronixCore __init__
# ================================================================

class NeuronixCorePhase3Integration:
    """
    Example integration showing Phase 3 additions to NeuronixCore
    """
    
    def __init__(self, vector_store, llm=None):
        """
        Add Phase 3 systems to existing init
        """
        # Existing systems
        self.vector_store = vector_store
        self.llm = llm
        
        # 🆕 Phase 3 Systems
        self.memory = ConversationMemory()
        self.distress_tracker = DistressTracker()
        self.followup_engine = ContextualFollowupEngine()
        self.safety_system = ProactiveSafetySystem()
        self.response_quality = ResponseQualityEngine()  # Phase 2
    
    # ================================================================
    # STEP 3: NEW MAIN QUERY HANDLER (Replaces old one)
    # ================================================================
    
    def handle_query_phase3(
        self,
        user_id: str,
        query: str,
        context: str = ""
    ) -> Dict:
        """
        MAIN ENTRY POINT for Phase 3
        
        Replaces the old handle_query() - this is the new flow
        """
        
        # ┌─ STEP 1: MEMORY & CONTEXT
        # │
        print("[1/7] Loading conversation context...")
        conversation = self.memory.get_conversation(user_id)
        if not conversation:
            self.memory.start_conversation(user_id)
        
        # Add user message to memory
        prior_context = self.memory.get_context_for_response(user_id)
        
        # ┌─ STEP 2: TONE DETECTION (Phase 2)
        # │
        print("[2/7] Detecting tone and distress level...")
        tone_analysis = self.response_quality.tone_detector.detect(query)
        distress_level = tone_analysis.distress_level
        
        # Add to memory
        self.memory.add_user_message(
            user_id,
            query,
            tone=tone_analysis.tone,
            distress_level=distress_level,
            keywords=tone_analysis.keywords
        )
        
        # ┌─ STEP 3: DISTRESS TRACKING
        # │
        print("[3/7] Tracking distress trends...")
        distress_analysis = self.distress_tracker.record_distress(
            user_id,
            distress_level,
            query
        )
        
        distress_trend = distress_analysis['trend']
        
        # ┌─ STEP 4: PROACTIVE SAFETY CHECK
        # │
        print("[4/7] Checking for concerning patterns...")
        conversation_turn = len([m for m in self.memory.get_conversation(user_id).messages 
                                if m.role == 'user'])
        
        safety_analysis = self.safety_system.analyze_pattern(
            user_id,
            query,
            distress_level,
            distress_trend,
            conversation_turn
        )
        
        # 🚨 If critical, activate crisis protocol now
        if safety_analysis['overall_severity'] == 'critical':
            return self._handle_crisis(user_id, query, safety_analysis)
        
        # ┌─ STEP 5: RAG RETRIEVAL (Existing)
        # │
        print("[5/7] Retrieving relevant context...")
        retrieved_docs = self._retrieve_documents(query, limit=3)
        retrieved_text = "\n".join([doc.page_content for doc in retrieved_docs])
        
        # ┌─ STEP 6: RESPONSE GENERATION (Phase 2 Quality)
        # │
        print("[6/7] Generating response...")
        response_result = self.response_quality.build_response(
            query,
            educational_content=retrieved_text,
            is_crisis=False
        )
        
        response_text = response_result['response']
        
        # ┌─ STEP 7: CONTEXTUAL FOLLOW-UP & PROACTIVE MESSAGE
        # │
        print("[7/7] Adding contextual follow-up...")
        
        # Get smart follow-up
        followup = self.followup_engine.generate_followup(
            query,
            conversation_count=conversation_turn,
            distress_trend=distress_trend,
            distress_level=distress_level
        )
        
        # Add to response
        response_text += f"\n\n{followup}"
        
        # Add proactive message if pattern detected
        proactive_msg = self.safety_system.get_proactive_message(
            user_id,
            safety_analysis['overall_severity']
        )
        if proactive_msg:
            response_text += proactive_msg
        
        # Add to memory
        self.memory.add_assistant_message(user_id, response_text)
        
        # ┌─ RETURN COMPLETE RESPONSE
        # │
        return {
            "response": response_text,
            "user_id": user_id,
            "tone_detected": tone_analysis.tone,
            "distress_level": distress_level,
            "distress_trend": distress_trend,
            "safety_severity": safety_analysis['overall_severity'],
            "patterns_detected": safety_analysis['patterns_detected'],
            "conversation_turn": conversation_turn,
            "sources": [doc.metadata.get('source_file', 'Unknown') for doc in retrieved_docs[:3]],
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "memory_enabled": True,
                "phase": "3_conversation_intelligence"
            }
        }
    
    def _handle_crisis(self, user_id: str, query: str, safety_analysis: Dict) -> Dict:
        """Handle critical crisis situation"""
        return {
            "response": (
                "I'm truly concerned about what you've shared. Your safety is the priority right now.\n\n"
                "🚨 CRISIS RESOURCES:\n"
                "• 988 Lifeline (US): Call/text 988 - Available 24/7\n"
                "• Crisis Text Line: Text HOME to 741741\n"
                "• International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/\n\n"
                "Please reach out to one of these resources right now. You don't have to handle this alone."
            ),
            "user_id": user_id,
            "is_crisis": True,
            "safety_severity": "critical",
            "action": "ACTIVATE CRISIS PROTOCOL"
        }
    
    def _retrieve_documents(self, query: str, limit: int = 3) -> List:
        """Retrieve documents from vector store"""
        # This is your existing RAG retrieval
        pass


# ================================================================
# STEP 4: UPGRADE EXISTING METHODS
# ================================================================

"""
Replace old methods with Phase 3 versions:

OLD _build_acknowledgment():
```python
def _build_acknowledgment(self, query, risk_level, user):
    if any(w in query.lower() for w in ["sad", "anxious"]):
        return "I hear that you're struggling..."
    return "Thank you for asking."
```

NEW _build_acknowledgment():
```python
def _build_acknowledgment(self, query, risk_level, user):
    # Now handled by Response Quality Engine (Phase 2)
    tone_analysis = self.response_quality.tone_detector.detect(query)
    return self.response_quality.variation.get_acknowledgment(
        tone_analysis.tone,
        tone_analysis.distress_level
    )
```

OLD get_user_profile():
```python
def get_user_profile(self, user_id):
    return self.user_memory.get(user_id)
```

NEW get_user_profile():
```python
def get_user_profile(self, user_id):
    # Now includes conversation memory AND distress history
    conversation = self.memory.get_conversation(user_id)
    distress_analysis = self.distress_tracker.get_full_analysis(user_id)
    
    return {
        'conversation': conversation,
        'distress_analysis': distress_analysis,
        'safety_profile': self.safety_system.escalation_patterns.get(user_id)
    }
```
"""


# ================================================================
# STEP 5: CONVERSATION MANAGEMENT
# ================================================================

class ConversationManagement:
    """
    Methods for managing multi-turn conversations
    """
    
    @staticmethod
    def close_conversation(memory, distress_tracker, user_id):
        """
        Close a conversation and save long-term profile
        
        Called when user ends session
        """
        
        # Close conversation memory
        conversation = memory.close_conversation(user_id)
        
        if conversation:
            # Get final metrics
            metrics = memory.get_session_metrics(user_id)
            distress_analysis = distress_tracker.get_full_analysis(user_id)
            
            print(f"\n📊 Session Summary for {user_id}:")
            print(f"  Duration: {metrics.get('session_duration_minutes', 0):.1f} minutes")
            print(f"  Messages: {metrics.get('message_count', 0)}")
            print(f"  Avg Distress: {metrics.get('avg_distress', 0):.0%}")
            print(f"  Primary Topic: {metrics.get('primary_topic', 'varied')}")
            print(f"  Trend: {metrics.get('distress_trend', 'unknown')}")
            
            # Save to database (if you have one)
            # db.save_conversation_session(conversation.to_dict())


# ================================================================
# STEP 6: TESTING THE INTEGRATION
# ================================================================

"""
Test multi-turn conversations:

```python
from scripts.neuronix_core import NeuronixCorePhase3Integration

# Initialize
core = NeuronixCorePhase3Integration(vector_store, llm)
user_id = "test_user_123"

# Turn 1
result1 = core.handle_query_phase3(
    user_id,
    "I feel anxious all the time"
)
print(result1['response'])

# Turn 2 - System now has context
result2 = core.handle_query_phase3(
    user_id,
    "It's been happening for 2 weeks"
)
print(result2['response'])
# Now system knows this is ongoing, can escalate support

# Turn 3 - System detects escalation
result3 = core.handle_query_phase3(
    user_id,
    "It's getting worse, I can't sleep"
)
print(result3['response'])
# Now system has detected escalation and adds proactive message

# Check conversation
metrics = core.memory.get_session_metrics(user_id)
print(metrics)
# Shows escalation trend, can take action
```

Expected Output:
- Turn 1: Initial response with suggestions
- Turn 2: Response acknowledges prior context "I know you've been dealing with..."
- Turn 3: Detects escalation, adds proactive message suggesting professional help
"""


# ================================================================
# STEP 7: BACKEND API CHANGES
# ================================================================

"""
Update your chat endpoint to use Phase 3:

BEFORE (backend/api.py):
```python
@app.post("/chat")
def chat(request: ChatRequest):
    response = chat_engine.handle_query(request.message)
    return ChatResponse(response=response)
```

AFTER:
```python
@app.post("/chat")
def chat(request: ChatRequest):
    response = chat_engine.handle_query_phase3(
        user_id=request.user_id,
        query=request.message
    )
    
    return ChatResponse(
        response=response['response'],
        tone=response['tone_detected'],
        distress_level=response['distress_level'],
        distress_trend=response['distress_trend'],
        safety_level=response['safety_severity'],
        patterns=response['patterns_detected']
    )
```

Frontend Now Gets:
- response: The actual message
- tone: emotional/informational/neutral
- distress_level: 0-1 (for UI visualization)
- distress_trend: escalating/improving/stable
- safety_level: low/medium/high/critical
- patterns: [List of detected patterns]
"""


# ================================================================
# STEP 8: FRONTEND VISUALIZATION OPPORTUNITIES
# ================================================================

"""
With Phase 3 data, frontend can show:

1. Distress Trend Graph
   - Visual showing escalation/improvement over conversation
   - Helps user see their own pattern

2. Safety Level Indicator
   - Green (low), Yellow (medium), Orange (high), Red (critical)
   - Shows in conversation bubble

3. Detected Patterns
   - "I notice you've mentioned anxiety 3 times"
   - Helps user recognize their own patterns

4. Smart Suggestion Widgets
   - "Based on our conversation, you might find breathing exercises helpful"
   - Contextual, not generic

5. Session Summary
   - After session: "Timeline of your conversation"
   - What improved, what stayed same
   - When you should check in next
"""


# ================================================================
# CHECKLIST FOR IMPLEMENTATION
# ================================================================

"""
✅ Implementation Checklist

[ ] 1. Copy Phase 3 files:
    - scripts/conversation_memory.py
    - scripts/distress_tracker.py
    - scripts/contextual_followup_engine.py
    - scripts/proactive_safety.py

[ ] 2. Update scripts/neuronix_core.py:
    - Add imports
    - Add Phase 3 systems to __init__
    - Replace handle_query() with handle_query_phase3()
    - Update related methods

[ ] 3. Test with multi-turn conversation:
    - python scripts/PHASE3_TEST_MULTITURNS.py

[ ] 4. Update backend API:
    - Modify /chat endpoint
    - Return new fields

[ ] 5. Update frontend:
    - Display distress level
    - Show distress trend
    - Display safety indicators

[ ] 6. Monitor:
    - Watch for false positives in pattern detection
    - Gather user feedback
    - Iterate based on real usage

[ ] 7. Deploy:
    - Start with 10% of users
    - Monitor for 1 week
    - Full rollout if satisfied
"""

print(__doc__)
