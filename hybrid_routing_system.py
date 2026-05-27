"""
🚀 HYBRID ROUTING SYSTEM FOR NEURONIX
======================================
Primary: Gemini (gemini-1.5-pro) for high-quality answers
Fallback: HuggingFace (all-MiniLM-L6-v2) when Gemini quota exhausted
Automatic failover + graceful degradation
"""

import logging
from typing import Dict, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ROUTING MODELS
# ============================================================================

class ModelType(Enum):
    """Available models"""
    GEMINI_PRO = "gemini-1.5-pro"
    HUGGINGFACE_MINILM = "all-MiniLM-L6-v2"


class RoutingPriority(Enum):
    """Routing priority levels"""
    PRIMARY = "primary"  # Gemini
    FALLBACK = "fallback"  # HuggingFace
    EMERGENCY = "emergency"  # Local fallback


class RouteStatus(Enum):
    """Status of routing endpoints"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    QUOTA_EXCEEDED = "quota_exceeded"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


# ============================================================================
# HYBRID ROUTING ENGINE
# ============================================================================

class HybridRouter:
    """
    Intelligent hybrid routing system
    
    Strategy:
    1. Try Gemini (primary) → High quality, better context
    2. If quota exceeded → Route to HuggingFace (fallback)
    3. Fallback to local processing (emergency)
    4. Log all routing decisions for debugging
    """
    
    def __init__(self):
        self.primary_model = None  # Gemini
        self.fallback_model = None  # HuggingFace
        self.emergency_model = None  # Local
        
        self.routing_log = []
        self.model_stats = {
            ModelType.GEMINI_PRO.value: {
                "calls": 0,
                "successful": 0,
                "failed": 0,
                "quota_errors": 0,
                "avg_latency": 0,
                "status": RouteStatus.HEALTHY.value
            },
            ModelType.HUGGINGFACE_MINILM.value: {
                "calls": 0,
                "successful": 0,
                "failed": 0,
                "quota_errors": 0,
                "avg_latency": 0,
                "status": RouteStatus.HEALTHY.value
            }
        }
        
        # Rate limiting & quota tracking
        self.quota_reset_time = None
        self.quota_remaining = 10000  # Gemini daily limit
        
        logger.info("✅ HybridRouter initialized")
    
    def route_query(self, query: str, context: str, 
                   system_prompt: str) -> Dict:
        """
        Route query through hybrid system
        
        Returns:
        {
            "response": str,
            "model_used": str,
            "routing_decision": Dict,
            "metadata": {
                "latency_ms": float,
                "model_status": str,
                "fallback_used": bool
            }
        }
        """
        
        start_time = datetime.now()
        routing_decision = {}
        
        # Step 1: Try primary (Gemini)
        logger.info("🔄 Step 1: Attempting Gemini (Primary)")
        gemini_response = self._try_gemini(query, context, system_prompt)
        
        if gemini_response["success"]:
            latency = (datetime.now() - start_time).total_seconds() * 1000
            routing_decision = {
                "route": "primary",
                "model": ModelType.GEMINI_PRO.value,
                "status": "success"
            }
            
            self._log_routing_decision(query, routing_decision, latency)
            
            return {
                "response": gemini_response["response"],
                "model_used": ModelType.GEMINI_PRO.value,
                "routing_decision": routing_decision,
                "metadata": {
                    "latency_ms": latency,
                    "model_status": "healthy",
                    "fallback_used": False,
                    "confidence": 0.95
                }
            }
        
        # Step 2: Check if quota exceeded
        if gemini_response.get("quota_exceeded"):
            logger.warning("⚠️ Gemini quota exceeded. Routing to HuggingFace")
            routing_decision["quota_exceeded"] = True
            self.model_stats[ModelType.GEMINI_PRO.value]["quota_errors"] += 1
        
        # Step 3: Try fallback (HuggingFace)
        logger.info("🔄 Step 2: Attempting HuggingFace (Fallback)")
        hf_response = self._try_huggingface(query, context, system_prompt)
        
        if hf_response["success"]:
            latency = (datetime.now() - start_time).total_seconds() * 1000
            routing_decision = {
                "route": "fallback",
                "model": ModelType.HUGGINGFACE_MINILM.value,
                "reason": "gemini_quota_exceeded" if gemini_response.get("quota_exceeded") else "gemini_failed",
                "status": "success"
            }
            
            self._log_routing_decision(query, routing_decision, latency)
            
            return {
                "response": hf_response["response"],
                "model_used": ModelType.HUGGINGFACE_MINILM.value,
                "routing_decision": routing_decision,
                "metadata": {
                    "latency_ms": latency,
                    "model_status": "fallback_active",
                    "fallback_used": True,
                    "confidence": 0.75,
                    "note": "Using faster model due to primary quota exhaustion"
                }
            }
        
        # Step 4: Emergency fallback (local processing)
        logger.warning("⚠️ Both Gemini and HuggingFace failed. Using emergency fallback")
        latency = (datetime.now() - start_time).total_seconds() * 1000
        
        routing_decision = {
            "route": "emergency",
            "status": "degraded",
            "reason": "both_models_failed"
        }
        
        self._log_routing_decision(query, routing_decision, latency)
        
        return {
            "response": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
            "model_used": "emergency_fallback",
            "routing_decision": routing_decision,
            "metadata": {
                "latency_ms": latency,
                "model_status": "emergency_mode",
                "fallback_used": True,
                "confidence": 0.3,
                "warning": "System in emergency mode - limited functionality"
            }
        }
    
    def _try_gemini(self, query: str, context: str, system_prompt: str) -> Dict:
        """
        Attempt to call Gemini API
        Returns: {"success": bool, "response": str, "quota_exceeded": bool}
        """
        
        try:
            # Check quota locally first
            if self.quota_remaining <= 0:
                logger.warning("⚠️ Gemini quota exhausted")
                return {
                    "success": False,
                    "quota_exceeded": True,
                    "response": None
                }
            
            # Simulate Gemini call
            # In production: use google.generativeai library
            response = self._simulate_gemini_call(query, context, system_prompt)
            
            # Update stats
            self.model_stats[ModelType.GEMINI_PRO.value]["calls"] += 1
            self.model_stats[ModelType.GEMINI_PRO.value]["successful"] += 1
            self.quota_remaining -= 1
            
            logger.info(f"✅ Gemini succeeded (Quota remaining: {self.quota_remaining})")
            
            return {
                "success": True,
                "quota_exceeded": False,
                "response": response
            }
        
        except Exception as e:
            logger.error(f"❌ Gemini error: {e}")
            self.model_stats[ModelType.GEMINI_PRO.value]["failed"] += 1
            
            # Check if quota error
            quota_exceeded = "quota" in str(e).lower() or "rate_limit" in str(e).lower()
            
            return {
                "success": False,
                "quota_exceeded": quota_exceeded,
                "response": None,
                "error": str(e)
            }
    
    def _try_huggingface(self, query: str, context: str, system_prompt: str) -> Dict:
        """
        Attempt to call HuggingFace embeddings
        Returns: {"success": bool, "response": str}
        """
        
        try:
            # Simulate HuggingFace call
            # In production: use sentence_transformers library
            response = self._simulate_huggingface_call(query, context, system_prompt)
            
            # Update stats
            self.model_stats[ModelType.HUGGINGFACE_MINILM.value]["calls"] += 1
            self.model_stats[ModelType.HUGGINGFACE_MINILM.value]["successful"] += 1
            
            logger.info("✅ HuggingFace succeeded (Fallback model)")
            
            return {
                "success": True,
                "response": response
            }
        
        except Exception as e:
            logger.error(f"❌ HuggingFace error: {e}")
            self.model_stats[ModelType.HUGGINGFACE_MINILM.value]["failed"] += 1
            
            return {
                "success": False,
                "response": None,
                "error": str(e)
            }
    
    @staticmethod
    def _simulate_gemini_call(query: str, context: str, system_prompt: str) -> str:
        """Simulate Gemini API call"""
        # In production: actual Gemini API call
        return f"Gemini Response: {query[:50]}..."
    
    @staticmethod
    def _simulate_huggingface_call(query: str, context: str, system_prompt: str) -> str:
        """Simulate HuggingFace API call"""
        # In production: actual HuggingFace API call
        return f"HuggingFace Response: {query[:50]}..."
    
    def _log_routing_decision(self, query: str, routing_decision: Dict, latency_ms: float):
        """Log routing decision for debugging"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query[:100],  # First 100 chars
            "routing_decision": routing_decision,
            "latency_ms": latency_ms
        }
        self.routing_log.append(log_entry)
    
    def get_routing_stats(self) -> Dict:
        """Get current routing statistics"""
        total_calls = sum(m["calls"] for m in self.model_stats.values())
        total_successful = sum(m["successful"] for m in self.model_stats.values())
        
        return {
            "total_calls": total_calls,
            "total_successful": total_successful,
            "success_rate": (total_successful / total_calls * 100) if total_calls > 0 else 0,
            "gemini_stats": self.model_stats[ModelType.GEMINI_PRO.value],
            "huggingface_stats": self.model_stats[ModelType.HUGGINGFACE_MINILM.value],
            "gemini_quota_remaining": self.quota_remaining,
            "recent_decisions": self.routing_log[-5:]  # Last 5 routing decisions
        }


# ============================================================================
# QUOTA MANAGEMENT
# ============================================================================

class QuotaManager:
    """Manages API quotas and rate limits"""
    
    def __init__(self):
        self.gemini_daily_limit = 10000
        self.gemini_quota_used = 0
        self.quota_reset_time = datetime.now() + timedelta(hours=24)
        
        logger.info("✅ QuotaManager initialized")
    
    def check_quota(self, model_type: ModelType) -> Tuple[bool, int]:
        """
        Check if quota is available
        Returns: (available: bool, remaining: int)
        """
        
        # Reset quota if 24 hours have passed
        if datetime.now() >= self.quota_reset_time:
            self._reset_quota()
        
        if model_type == ModelType.GEMINI_PRO:
            remaining = self.gemini_daily_limit - self.gemini_quota_used
            available = remaining > 0
            
            return available, remaining
        
        # HuggingFace has no daily limit (local model)
        return True, -1
    
    def consume_quota(self, model_type: ModelType, amount: int = 1):
        """Consume quota"""
        if model_type == ModelType.GEMINI_PRO:
            self.gemini_quota_used += amount
            logger.info(f"📊 Gemini quota used: {self.gemini_quota_used}/{self.gemini_daily_limit}")
    
    def _reset_quota(self):
        """Reset daily quota"""
        self.gemini_quota_used = 0
        self.quota_reset_time = datetime.now() + timedelta(hours=24)
        logger.info("🔄 Gemini quota reset for new day")


# ============================================================================
# FAILOVER LOGIC
# ============================================================================

class FailoverStrategy:
    """Implements failover strategies"""
    
    @staticmethod
    def should_failover(primary_error: Exception) -> bool:
        """Determine if failover should be triggered"""
        error_msg = str(primary_error).lower()
        
        failover_triggers = [
            "quota",
            "rate_limit",
            "429",  # Too many requests
            "503",  # Service unavailable
            "timeout",
            "connection_error"
        ]
        
        return any(trigger in error_msg for trigger in failover_triggers)
    
    @staticmethod
    def get_failover_model(primary_error: Exception) -> ModelType:
        """Get appropriate failover model based on error"""
        
        error_msg = str(primary_error).lower()
        
        # Quota/rate limit errors → go to HuggingFace
        if any(x in error_msg for x in ["quota", "rate_limit", "429"]):
            return ModelType.HUGGINGFACE_MINILM
        
        # Availability errors → try HuggingFace first
        if any(x in error_msg for x in ["503", "unavailable", "timeout"]):
            return ModelType.HUGGINGFACE_MINILM
        
        # Default fallback
        return ModelType.HUGGINGFACE_MINILM


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Initialize router
    router = HybridRouter()
    
    # Example query
    query = "What is anxiety disorder?"
    context = "...relevant clinical context..."
    system_prompt = "You are a clinical mental health expert..."
    
    # Route the query
    result = router.route_query(query, context, system_prompt)
    
    print(f"\n✅ Response: {result['response']}")
    print(f"🔄 Model Used: {result['model_used']}")
    print(f"📊 Routing Decision: {result['routing_decision']}")
    print(f"⏱️ Latency: {result['metadata']['latency_ms']}ms")
    
    # Get statistics
    stats = router.get_routing_stats()
    print(f"\n📊 Routing Statistics:")
    print(f"Total Calls: {stats['total_calls']}")
    print(f"Success Rate: {stats['success_rate']:.2f}%")
    print(f"Gemini Quota Remaining: {stats['gemini_quota_remaining']}")
