"""
🎤 Phase 6: Voice Support System
=================================
Speech-to-Text (STT) + Text-to-Speech (TTS) Integration

Features:
- OpenAI Whisper for accurate speech recognition (40+ languages)
- ElevenLabs for natural sounding voice responses
- Fallback to Google Text-to-Speech if ElevenLabs unavailable
- Support for crisis scenarios (emotional tone detection)
- Audio file upload/streaming
- Volume/speed control for responses

Example:
  voice = VoiceSupport()
  
  # User speaks their query
  user_text = voice.transcribe_audio("user_audio.wav")
  # "I'm feeling really anxious right now"
  
  # System generates response
  response_text = "Let's try some breathing exercises..."
  
  # System speaks back
  audio_bytes = voice.synthesize_speech(response_text)
  # Play audio_bytes to user
"""

import io
import logging
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# ================================================================
# VOICE ENUMS & DATA MODELS
# ================================================================

class VoiceGender(Enum):
    """Voice gender preferences"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class SpeakingRate(Enum):
    """Speaking rate options"""
    SLOW = 0.8
    NORMAL = 1.0
    FAST = 1.2


@dataclass
class VoiceProfile:
    """User's voice preferences"""
    user_id: str
    preferred_gender: VoiceGender = VoiceGender.NEUTRAL
    speaking_rate: SpeakingRate = SpeakingRate.NORMAL
    language: str = "en"  # ISO 639-1 code
    emotional_tone: str = "compassionate"  # compassionate/clinical/supportive
    volume: float = 1.0  # 0.0 - 1.0
    enable_voice: bool = True


@dataclass
class TranscriptionResult:
    """Result from speech-to-text"""
    text: str
    confidence: float  # 0-1
    language: str
    duration_seconds: float
    detected_emotion: Optional[str] = None  # angry/sad/anxious/calm/happy
    is_crisis_signal: bool = False


@dataclass
class SynthesisRequest:
    """Request for text-to-speech"""
    text: str
    voice_profile: VoiceProfile
    include_emotion_markers: bool = True  # e.g., [pause], [calm tone]


# ================================================================
# VOICE SUPPORT SYSTEM
# ================================================================

class VoiceSupport:
    """
    Complete voice support with STT/TTS
    
    Handles:
    - Audio file upload & validation
    - Speech-to-text using OpenAI Whisper
    - Emotion detection from speech
    - Crisis signal detection
    - Text-to-speech synthesis
    - Audio streaming
    """
    
    def __init__(self):
        """Initialize voice support system"""
        self.whisper_available = False
        self.elevenlabs_available = False
        self.google_tts_available = False
        self.detected_emotions = {}
        
        self._init_whisper()
        self._init_tts()
    
    def _init_whisper(self):
        """Initialize OpenAI Whisper"""
        try:
            import openai
            self.openai_client = openai.Client()
            self.whisper_available = True
            logger.info("✅ OpenAI Whisper (STT) available")
        except Exception as e:
            logger.warning(f"⚠️  Whisper not available: {str(e)[:80]}")
            self.whisper_available = False
    
    def _init_tts(self):
        """Initialize Text-to-Speech options"""
        # Try ElevenLabs first
        try:
            from elevenlabs import ElevenLabs
            self.elevenlabs_available = True
            self.elevenlabs_client = ElevenLabs(api_key=self._get_elevenlabs_key())
            logger.info("✅ ElevenLabs (TTS) available")
        except Exception as e:
            logger.warning(f"⚠️  ElevenLabs not available: {e}")
        
        # Fallback to Google Text-to-Speech
        try:
            from google.cloud import texttospeech
            self.google_tts_available = True
            self.google_tts_client = texttospeech.TextToSpeechClient()
            logger.info("✅ Google Text-to-Speech (TTS) available")
        except Exception as e:
            logger.warning(f"⚠️  Google TTS not available: {e}")
    
    def _get_elevenlabs_key(self) -> str:
        """Get ElevenLabs API key from environment"""
        import os
        return os.getenv("ELEVENLABS_API_KEY", "")
    
    # ================================================================
    # SPEECH-TO-TEXT (STT)
    # ================================================================
    
    def transcribe_audio(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text using OpenAI Whisper
        
        Args:
            audio_file_path: Path to audio file (mp3, wav, m4a, etc)
            language: ISO 639-1 language code (auto-detected if None)
        
        Returns:
            TranscriptionResult with text and metadata
        """
        if not self.whisper_available:
            logger.error("Whisper not available")
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language="unknown",
                duration_seconds=0.0,
                is_crisis_signal=False
            )
        
        try:
            import openai
            
            logger.info(f"🎤 Transcribing: {audio_file_path}")
            
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    prompt="This is a healthcare conversation. Preserve medical terminology and emotional context.",
                    response_format="verbose_json"  # Returns confidence scores
                )
            
            text = transcript.text
            
            # Detect emotion from transcription
            detected_emotion = self._detect_emotion_from_text(text)
            
            # Check for crisis signals
            is_crisis = self._check_crisis_signals(text)
            
            result = TranscriptionResult(
                text=text,
                confidence=getattr(transcript, 'confidence', 0.95),
                language=getattr(transcript, 'language', language or 'en'),
                duration_seconds=getattr(transcript, 'duration', 0.0),
                detected_emotion=detected_emotion,
                is_crisis_signal=is_crisis
            )
            
            logger.info(f"✅ Transcribed: {text[:80]}...")
            if is_crisis:
                logger.warning(f"🚨 CRISIS SIGNAL DETECTED in voice")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language=language or "unknown",
                duration_seconds=0.0,
                is_crisis_signal=False
            )
    
    def transcribe_stream(
        self,
        audio_stream,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio stream in real-time
        
        Args:
            audio_stream: Audio stream (bytes or file-like object)
            language: ISO 639-1 language code
        
        Returns:
            TranscriptionResult
        """
        # Convert stream to file for Whisper
        if isinstance(audio_stream, bytes):
            audio_file = io.BytesIO(audio_stream)
        else:
            audio_file = audio_stream
        
        # Save temporarily and transcribe
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_file.read() if hasattr(audio_file, 'read') else audio_stream)
            tmp_path = tmp.name
        
        try:
            result = self.transcribe_audio(tmp_path, language)
            return result
        finally:
            import os
            os.unlink(tmp_path)
    
    def _detect_emotion_from_text(self, text: str) -> str:
        """Detect emotional tone from transcribed text"""
        text_lower = text.lower()
        
        # Crisis/urgent emotions
        if any(word in text_lower for word in ["suicide", "kill myself", "want to die", "hopeless", "worthless", "end it all", "don't want to live", "harm myself"]):
            return "crisis"
        
        # Anxiety/fear
        if any(word in text_lower for word in ["anxiety", "anxious", "panic", "scared", "terrified", "afraid"]):
            return "anxious"
        
        # Depression/sadness
        if any(word in text_lower for word in ["depressed", "depressing", "sad", "crying", "lonely", "empty"]):
            return "depressed"
        
        # Anger/frustration
        if any(word in text_lower for word in ["angry", "angry about", "frustrated", "furious", "hate", "resentment"]):
            return "angry"
        
        # Calm/stable
        if any(word in text_lower for word in ["better", "calm", "relaxed", "managed", "okay", "fine", "good"]):
            return "calm"
        
        return "neutral"
    
    def _check_crisis_signals(self, text: str) -> bool:
        """Check if text contains crisis signals"""
        crisis_keywords = [
            "suicide", "kill myself", "want to die", "don't want to live",
            "end it all", "don't care anymore", "nothing matters",
            "harm myself", "self-harm", "cut myself",
            "overdose", "take pills", "jump off"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in crisis_keywords)
    
    # ================================================================
    # TEXT-TO-SPEECH (TTS)
    # ================================================================
    
    def synthesize_speech(
        self,
        text: str,
        voice_profile: VoiceProfile,
        output_format: str = "mp3"
    ) -> bytes:
        """
        Synthesize text to speech
        
        Args:
            text: Text to synthesize
            voice_profile: User's voice preferences
            output_format: Audio format (mp3, wav, opus, aac)
        
        Returns:
            Audio bytes
        """
        if not voice_profile.enable_voice:
            return b""
        
        # Try ElevenLabs first (more natural)
        if self.elevenlabs_available:
            return self._synthesize_elevenlabs(text, voice_profile, output_format)
        
        # Fallback to Google
        if self.google_tts_available:
            return self._synthesize_google(text, voice_profile, output_format)
        
        logger.warning("No TTS available")
        return b""
    
    def _synthesize_elevenlabs(
        self,
        text: str,
        voice_profile: VoiceProfile,
        output_format: str
    ) -> bytes:
        """Synthesize using ElevenLabs (premium quality)"""
        try:
            from elevenlabs import Voice, VoiceSettings
            from elevenlabs.client import ElevenLabs
            
            logger.info(f"🎤 ElevenLabs synthesis: {text[:50]}...")
            
            # Map voice preferences to ElevenLabs voices
            voice_map = {
                ("male", "en"): "Adam",  # Professional male
                ("female", "en"): "Sarah",  # Professional female
                ("neutral", "en"): "Rachel",  # Neutral voice
            }
            
            voice_name = voice_map.get(
                (voice_profile.preferred_gender.value, voice_profile.language),
                "Rachel"
            )
            
            # Create voice with settings
            voice = Voice(
                voice_id=voice_name,
                settings=VoiceSettings(
                    stability=0.71,  # 0-1: higher = more consistent
                    similarity_boost=0.75  # 0-1: higher = matches voice better
                )
            )
            
            # Add emotional markers if needed
            enhanced_text = text
            if voice_profile.emotional_tone == "compassionate":
                enhanced_text = f"[Speak gently and compassionately] {text}"
            elif voice_profile.emotional_tone == "supportive":
                enhanced_text = f"[Speak in a supportive tone] {text}"
            
            # Synthesize
            audio = self.elevenlabs_client.generate(
                text=enhanced_text,
                voice=voice,
                model="eleven_monolingual_v1",
                stream=False
            )
            
            # Convert to bytes
            audio_bytes = b"".join(audio)
            logger.info(f"✅ ElevenLabs synthesis complete ({len(audio_bytes)} bytes)")
            return audio_bytes
        
        except Exception as e:
            logger.error(f"❌ ElevenLabs synthesis failed: {e}")
            return b""
    
    def _synthesize_google(
        self,
        text: str,
        voice_profile: VoiceProfile,
        output_format: str
    ) -> bytes:
        """Synthesize using Google Cloud Text-to-Speech (fallback)"""
        try:
            from google.cloud import texttospeech
            
            logger.info(f"🎤 Google TTS synthesis: {text[:50]}...")
            
            # Set up TTS request
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Map preferences
            gender_map = {
                "male": texttospeech.SsmlVoiceGender.MALE,
                "female": texttospeech.SsmlVoiceGender.FEMALE,
                "neutral": texttospeech.SsmlVoiceGender.NEUTRAL,
            }
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_profile.language,
                gender=gender_map.get(voice_profile.preferred_gender.value,
                                     texttospeech.SsmlVoiceGender.NEUTRAL),
                name=f"en-US-Neural2-{voice_profile.preferred_gender.value[0].upper()}"
                if voice_profile.language == "en" else None
            )
            
            # Audio config
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=voice_profile.speaking_rate.value,
                pitch=0.0
            )
            
            # Synthesize
            response = self.google_tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            logger.info(f"✅ Google TTS complete ({len(response.audio_content)} bytes)")
            return response.audio_content
        
        except Exception as e:
            logger.error(f"❌ Google TTS failed: {e}")
            return b""
    
    # ================================================================
    # UTILITY METHODS
    # ================================================================
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return [
            "en", "es", "fr", "de", "it", "pt", "nl", "ru", "ja", "ko",
            "zh", "ar", "hi", "tr", "pl", "uk", "vi", "th", "id", "el"
        ]
    
    def validate_audio_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate audio file before processing
        
        Returns:
            (is_valid, error_message)
        """
        import os
        
        # Check file exists
        if not os.path.exists(file_path):
            return False, "File not found"
        
        # Check file size (max 25MB for Whisper)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 25:
            return False, f"File too large ({file_size_mb:.1f}MB > 25MB)"
        
        # Check file extension
        valid_extensions = [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus"]
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in valid_extensions:
            return False, f"Invalid format ({ext}). Supported: {', '.join(valid_extensions)}"
        
        return True, ""
    
    def set_voice_profile(self, profile: VoiceProfile):
        """Update user's voice preferences"""
        self.voice_profiles = getattr(self, 'voice_profiles', {})
        self.voice_profiles[profile.user_id] = profile
        logger.info(f"✅ Voice profile updated for {profile.user_id}")
    
    def get_voice_profile(self, user_id: str) -> VoiceProfile:
        """Get user's voice preferences"""
        self.voice_profiles = getattr(self, 'voice_profiles', {})
        return self.voice_profiles.get(
            user_id,
            VoiceProfile(user_id=user_id)
        )


# ================================================================
# EXAMPLE USAGE
# ================================================================

if __name__ == "__main__":
    print("🎤 Voice Support Demo\n")
    
    voice = VoiceSupport()
    
    # Example 1: Speech-to-Text
    print("=" * 60)
    print("Example 1: Speech-to-Text (STT)")
    print("=" * 60)
    print("(Requires audio file - this is a demo)")
    print("voice.transcribe_audio('user_voice.mp3')")
    print("# Returns: TranscriptionResult with text, emotion, crisis signals\n")
    
    # Example 2: Text-to-Speech
    print("=" * 60)
    print("Example 2: Text-to-Speech (TTS)")
    print("=" * 60)
    
    # Create voice profile
    profile = VoiceProfile(
        user_id="patient_001",
        preferred_gender="female",
        speaking_rate="normal",
        language="en",
        emotional_tone="compassionate"
    )
    
    voice.set_voice_profile(profile)
    
    # Synthesize speech
    response_text = "I hear you. Let's take some deep breaths together. In for 4 counts, hold for 4, out for 4."
    
    print(f"Text: {response_text}\n")
    print("Synthesizing with voice profile:")
    print(f"  • Gender: {profile.preferred_gender.value}")
    print(f"  • Language: {profile.language}")
    print(f"  • Tone: {profile.emotional_tone}")
    
    audio_bytes = voice.synthesize_speech(response_text, profile)
    
    if audio_bytes:
        print(f"\n✅ Audio synthesized ({len(audio_bytes)} bytes)")
        print("   Ready to play to user")
    else:
        print("\n⚠️  Audio synthesis not available (demo mode)")
    
    # Example 3: Supported languages
    print("\n" + "=" * 60)
    print("Example 3: Supported Languages")
    print("=" * 60)
    langs = voice.get_supported_languages()
    print(f"Supported: {', '.join(langs[:10])}... ({len(langs)} total)")
    
    print("\n✅ Voice Support Ready for Integration!")
