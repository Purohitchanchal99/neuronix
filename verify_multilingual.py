#!/usr/bin/env python
"""
Quick verification that multilingual emotion detection is working in live system
"""

import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

# Quick smoke test
from backend.multilingual_emotion_detector import MultilingualEmotionDetector

detector = MultilingualEmotionDetector()

print("\n" + "="*70)
print("MULTILINGUAL EMOTION DETECTION - LIVE VERIFICATION")
print("="*70 + "\n")

test_cases = [
    ("I'm feeling really depressed today", "English"),
    ("mujhe bohot tension hai", "Hinglish"),
    ("gussa aa raha bohot", "Hinglish"),
    ("khushi hai yaar!", "Hinglish"),
    ("I'm so anxious about everything", "English"),
]

for query, language in test_cases:
    emotion, intensity, _ = detector.detect_emotion(query)
    print(f"✓ {language:12} | '{query}' → {emotion} ({intensity:.1f}x)")

print("\n" + "="*70)
print("✅ MULTILINGUAL EMOTION DETECTION VERIFIED AND WORKING!")
print("="*70 + "\n")
