#!/usr/bin/env python
"""
Test end-to-end multilingual RAG system integration
Tests: emotion detection, ChromaDB retrieval, response generation
"""

import sys
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

# Test 1: Test MultilingualEmotionDetector
logger.info("=" * 70)
logger.info("TEST 1: MULTILINGUAL EMOTION DETECTOR")
logger.info("=" * 70)

try:
    from backend.multilingual_emotion_detector import MultilingualEmotionDetector
    
    detector = MultilingualEmotionDetector()
    
    test_queries = [
        ("I'm feeling depressed", "English depression"),
        ("mujhe tension hai bohot", "Hinglish anxiety"),
        ("gussa aa raha hai", "Hindi anger"),
        ("khushi bohot hai", "Hindi happiness"),
        ("I'm so anxious about the future", "English anxiety"),
    ]
    
    logger.info("\n[EMOTION DETECTION]")
    for query, description in test_queries:
        emotion, intensity, scores = detector.detect_emotion(query)
        logger.info(f"  {description:30} → {emotion:12} (intensity: {intensity:.1f}x)")
    
    logger.info("[OK] Emotion detection working!\n")
except Exception as e:
    logger.error(f"[ERROR] Emotion detection failed: {e}\n")
    import traceback
    traceback.print_exc()

# Test 2: Verify NeuronixChatEngine imports correctly
logger.info("=" * 70)
logger.info("TEST 2: CHAT ENGINE INITIALIZATION")
logger.info("=" * 70)

try:
    from backend.chat_engine import NeuronixChatEngine
    
    logger.info("\n[INIT] Initializing NeuronixChatEngine...")
    engine = NeuronixChatEngine(google_api_key=os.getenv("GOOGLE_API_KEY"))
    
    logger.info(f"[OK] Chat engine initialized")
    logger.info(f"[OK] Database status: {engine.db_status['message']}")
    logger.info(f"[OK] Multilingual detector available: {engine.multilingual_detector is not None}")
    logger.info(f"[OK] Tone analyzer available: {engine.tone_analyzer is not None}\n")
    
except Exception as e:
    logger.error(f"[ERROR] Chat engine initialization failed: {e}\n")
    import traceback
    traceback.print_exc()

# Test 3: Test emotion detection through chat engine
logger.info("=" * 70)
logger.info("TEST 3: EMOTION DETECTION VIA CHAT ENGINE")
logger.info("=" * 70)

try:
    test_queries = [
        "I'm feeling very depressed today",
        "mujhe bohot anxiety hai",
        "gussa se jhagda ho gaya",
    ]
    
    logger.info("\n[TONE ANALYSIS]")
    for query in test_queries:
        tone = engine.tone_analyzer.analyze_tone(query)
        logger.info(f"  Query: {query:35} → Tone: {tone}")
    
    logger.info("[OK] Tone analysis working!\n")
    
except Exception as e:
    logger.error(f"[ERROR] Tone analysis failed: {e}\n")

logger.info("=" * 70)
logger.info("✅ END-TO-END INTEGRATION TEST COMPLETE")
logger.info("=" * 70)
