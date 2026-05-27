#!/usr/bin/env python3
"""
Lightweight Multilingual Emotion Detection
Supports: English, Hindi, Hinglish (mixed English-Hindi)
Uses keyword-based detection with optional transformer support
"""

import logging
import re
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class MultilingualEmotionDetector:
    """
    Lightweight multilingual emotion detection using keyword matching + optional transformers.
    Supports English, Hindi, Hinglish, and other languages.
    """
    
    def __init__(self, use_transformers=False):
        """
        Initialize emotion detector.
        
        Args:
            use_transformers: If True, load transformer models (slower but more accurate).
                            If False (default), use lightweight keyword matching.
        """
        logger.info("[INIT] Initializing MultilingualEmotionDetector...")
        
        self.use_transformers = use_transformers
        self.classifier = None
        
        # Optionally load transformer for zero-shot classification
        if use_transformers:
            try:
                from transformers import pipeline
                logger.info("[INIT] Loading transformer pipeline... (this may take a minute on first run)")
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bert-base-multilingual-uncased",  # Smaller model (~600MB)
                    device=-1  # CPU
                )
                logger.info("[OK] Transformer pipeline loaded")
            except Exception as e:
                logger.warning(f"[WARN] Could not load transformers: {e}. Using keyword-based detection.")
                self.classifier = None
        
        # Language detection patterns
        self.devanagari_pattern = re.compile(r'[\u0900-\u097F]')  # Hindi/Devanagari
        self.latin_pattern = re.compile(r'[a-zA-Z]')
        
        # Comprehensive emotion keywords in English and Hindi/Hinglish
        self.emotion_keywords = {
            "happy": [
                "happy", "joyful", "excited", "cheerful", "delighted", "wonderful",
                "fantastic", "amazing", "great", "awesome", "excellent", "thrilled",
                "khushi", "happy", "joyful", "excited", "mast", "badiya", "badhiya",
                "mazza", "fun", "enjoying", "satisfied", "proud", "loved", "blessed",
                "lucky", "celebrate", "celebration", "khush", "shukriya", "dhanyavaad"
            ],
            "sad": [
                "sad", "unhappy", "depressed", "down", "dejected", "lonely",
                "isolated", "miserable", "wretched", "sorrowful", "heartbroken",
                "udaas", "udaasi", "depressed", "dukhi", "dukh", "unhappy",
                "alone", "overwhelmed", "hopeless", "worthless", "broken",
                "suffering", "pain", "hurt", "grief", "mourn", "loss", "lost",
                "depression", "ghabra", "bura lag", "akela", "abandoned"
            ],
            "angry": [
                "angry", "furious", "mad", "rage", "upset", "annoyed",
                "irritated", "frustrated", "exasperated", "livid", "seething",
                "gussa", "naraz", "gussail", "krodh", "raged",
                "pissed", "seething", "riled", "bitter", "hostile", "aggressive",
                "bakwaas", "bekar", "thak", "fed up", "sick of", "chutyya",
                "jhagda", "larai", "dushman", "dron"
            ],
            "anxious": [
                "anxiety", "anxious", "worried", "concerned", "nervous",
                "uneasy", "restless", "tense", "panicked", "fearful",
                "tension", "stress", "tensio", "dar", "bhay", "ghabrana",
                "panic", "fear", "scared", "frightened", "afraid",
                "overthinking", "overwhelmed", "haunted", "troubled", "neend"
            ],
            "confused": [
                "confused", "bewildered", "puzzled", "perplexed", "lost",
                "disoriented", "muddled", "baffled", "uncertain", "unsure",
                "confusion", "lost", "samjh", "nahi", "samjh nahi aa raha",
                "unclear", "foggy", "hazy", "chaotic", "samjhta nahi",
                "unclear", "uncertain", "doubt", "doubt"
            ],
            "stressed": [
                "stressed", "stressed out", "pressure", "overwhelmed",
                "burned out", "exhausted", "drained", "fatigued", "tired",
                "stress", "thak", "bakwaas", "bekar", "useless",
                "frustrated", "at wits end", "spent", "worn out", "done",
                "takraar", "takleef"
            ],
            "calm": [
                "calm", "peaceful", "relaxed", "tranquil", "serene",
                "composed", "collected", "cool", "unruffled",
                "shanti", "shaant", "sukoon", "peaceful", "meditative",
                "zen", "balanced", "grounded", "patient", "tolerant"
            ],
            "disappointed": [
                "disappointed", "letdown", "let down", "dismayed",
                "disheartened", "demoralized", "crestfallen",
                "failed", "loss", "waste", "ruined", "destroyed"
            ]
        }
        
        # Hinglish typo corrections
        self.typo_corrections = {
            "mje": "mujhe", "mjhe": "mujhe", "depresun": "depression",
            "gussa": "gussa", "neend": "neend", "tensio": "tension",
            "dar": "dar", "akela": "akela", "khushi": "khushi",
            "udaas": "udaas", "thak": "thak", "bakwaas": "bakwaas",
            "bokwaas": "bakwaas", "bekar": "bekar", "bohot": "bohot",
            "bahut": "bohot", "zyada": "zyada", "bilkul": "bilkul",
            "thoda": "thoda", "shanti": "shanti", "sukoon": "sukoon",
            "ghabrana": "ghabrana", "nahi": "nahi", "samjh": "samjh"
        }
        
        # Intensity modifiers (Hindi/Hinglish)
        self.intensity_modifiers = {
            "bohot": 2.0, "bahut": 2.0, "zyada": 2.0, "bilkul": 2.0,
            "very": 1.8, "so": 1.7, "extremely": 1.9, "absolutely": 2.0,
            "totally": 1.8, "completely": 1.9, "quite": 1.4, "really": 1.5,
            "fairly": 1.3, "rather": 1.4, "itna": 1.5,
            "thoda": 0.7, "slightly": 0.7, "bit": 0.7, "little": 0.7,
            "somewhat": 0.9, "kind": 0.9, "of": 0.9,
            "kabhi": 0.5, "sirf": 0.5, "bus": 0.5, "only": 0.5, "just": 0.5
        }
        
        logger.info("[OK] MultilingualEmotionDetector initialized")
    
    def detect_language(self, text: str) -> str:
        """Detect language: English, Hindi, Hinglish, or unknown"""
        if not text:
            return "unknown"
        
        devanagari_count = len(self.devanagari_pattern.findall(text))
        latin_count = len(self.latin_pattern.findall(text))
        
        if devanagari_count > 0 and latin_count > 0:
            return "hinglish"
        elif devanagari_count > latin_count:
            return "hindi"
        else:
            return "english"
    
    def normalize_hinglish(self, text: str) -> str:
        """Normalize Hinglish text: fix typos and expand abbreviations"""
        normalized = text.lower()
        
        for typo, correct in self.typo_corrections.items():
            normalized = re.sub(r'\b' + re.escape(typo) + r'\b', correct, normalized)
        
        return normalized
    
    def detect_emotion(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Detect emotion from text.
        
        Args:
            text: Input text in English, Hindi, or Hinglish
            
        Returns:
            (emotion_label, intensity_multiplier, confidence_scores)
        """
        if not text:
            return "neutral", 1.0, {}
        
        language = self.detect_language(text)
        
        # Normalize text if needed
        if language in ["hinglish", "hindi"]:
            text_processed = self.normalize_hinglish(text)
        else:
            text_processed = text.lower()
        
        # Try transformer classification
        emotion = None
        scores = {}
        
        if self.use_transformers and self.classifier is not None:
            try:
                emotion, scores = self._classify_with_transformer(text_processed)
            except Exception as e:
                logger.debug(f"Transformer classification failed: {e}")
                emotion = None
        
        # Fallback to keyword matching
        if emotion is None:
            emotion, scores = self._keyword_matching(text_processed)
        
        # Calculate intensity
        intensity = self._get_intensity(text_processed)
        
        logger.debug(f"[EMOTION] {language}: '{text[:40]}...' → {emotion} (intensity: {intensity:.2f}x)")
        
        return emotion, intensity, scores
    
    def _classify_with_transformer(self, text: str) -> Tuple[str, Dict]:
        """Use transformer for zero-shot classification"""
        if self.classifier is None:
            return None, {}
        
        candidate_labels = list(self.emotion_keywords.keys())
        
        try:
            result = self.classifier(text, candidate_labels, multi_class=True)
            scores = {label: float(score) for label, score in zip(result["labels"], result["scores"])}
            top_emotion = result["labels"][0]
            top_score = result["scores"][0]
            
            if top_score > 0.3:
                return top_emotion, scores
            return None, {}
        except Exception as e:
            logger.debug(f"Transformer error: {e}")
            return None, {}
    
    def _keyword_matching(self, text: str) -> Tuple[str, Dict[str, float]]:
        """Keyword-based emotion detection fallback"""
        scores = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            match_count = sum(1 for keyword in keywords if keyword in text)
            if match_count > 0:
                scores[emotion] = min(match_count / len(keywords), 1.0)
        
        if not scores:
            return "neutral", {}
        
        top_emotion = max(scores.items(), key=lambda x: x[1])[0]
        return top_emotion, scores
    
    def _get_intensity(self, text: str) -> float:
        """Calculate emotion intensity (0.5 to 2.5) from linguistic markers"""
        intensity = 1.0
        
        # Check for intensity modifiers
        words = text.split()
        for word in words:
            if word in self.intensity_modifiers:
                intensity = self.intensity_modifiers[word]
                break
        
        # Adjust for punctuation
        intensity += (text.count("!") * 0.2)
        intensity += (text.count("?") * 0.15)
        
        # Clamp to 0.5-2.5
        return max(0.5, min(2.5, intensity))
    
    def get_emotion_response_tone(self, emotion: str, intensity: float) -> Dict:
        """Get response tone parameters based on emotion and intensity"""
        tone = {
            "empathy": "MEDIUM",
            "pace": "normal",
            "language": "english",
            "response_length": "medium",
            "tone_keywords": []
        }
        
        emotion_tones = {
            "depressed": {
                "empathy": "VERY_HIGH" if intensity > 1.5 else "HIGH",
                "pace": "slow",
                "tone_keywords": ["supportive", "compassionate", "understanding"]
            },
            "angry": {
                "empathy": "MEDIUM",
                "pace": "calm",
                "tone_keywords": ["validating", "non-judgmental", "grounding"]
            },
            "anxious": {
                "empathy": "HIGH",
                "pace": "slow",
                "tone_keywords": ["soothing", "reassuring", "grounding"]
            },
            "happy": {
                "empathy": "LOW",
                "pace": "upbeat",
                "tone_keywords": ["celebratory", "positive", "engaging"]
            },
            "confused": {
                "empathy": "MEDIUM",
                "pace": "slow",
                "tone_keywords": ["clarifying", "patient", "structured"]
            },
            "stressed": {
                "empathy": "HIGH",
                "pace": "calm",
                "tone_keywords": ["grounding", "practical", "supportive"]
            },
            "calm": {
                "empathy": "MEDIUM",
                "pace": "normal",
                "tone_keywords": ["balanced", "thoughtful", "measured"]
            }
        }
        
        if emotion in emotion_tones:
            tone.update(emotion_tones[emotion])
        
        return tone


# Quick test
if __name__ == "__main__":
    detector = MultilingualEmotionDetector(use_transformers=False)  # Start with keyword-based
    
    tests = [
        "I'm so depressed",
        "mujhe gussa aa raha hai",
        "bohot anxiety hai yaar",
        "I'm happy!!!!",
    ]
    
    for query in tests:
        emotion, intensity, scores = detector.detect_emotion(query)
        print(f"{query:40} → {emotion} (intensity: {intensity:.2f}x)")
