"""
🎤 VOICE SUPPORT IMPLEMENTATION GUIDE
=====================================

Phase 6 Extension: Voice Input/Output Support

This guide covers everything needed to enable voice functionality in the NEURONIX system.
"""

# ================================================================
# QUICK START
# ================================================================

## 1. Installation

# Install required dependencies:
pip install openai
pip install elevenlabs  # For premium TTS (optional)
pip install google-cloud-texttospeech  # For Google TTS (optional)

# Set environment variables:
export OPENAI_API_KEY=your_openai_api_key
export ELEVENLABS_API_KEY=your_elevenlabs_key

# Or on Windows (PowerShell):
$env:OPENAI_API_KEY = "your_openai_api_key"
$env:ELEVENLABS_API_KEY = "your_elevenlabs_key"


## 2. Basic Usage

from scripts.voice_support import VoiceSupport, VoiceProfile, VoiceGender

# Initialize voice support
voice = VoiceSupport()

# Speech-to-Text (STT)
result = voice.transcribe_audio("user_recording.wav", language="en")
print(f"User said: {result.text}")
print(f"Emotion detected: {result.detected_emotion}")
print(f"Crisis signal: {result.is_crisis_signal}")

# Text-to-Speech (TTS)
profile = VoiceProfile(
    user_id="patient_001",
    preferred_gender="female",
    language="en",
    emotional_tone="compassionate"
)

response_text = "I understand. Let's take some deep breaths together."
audio_bytes = voice.synthesize_speech(response_text, profile)
# Play audio_bytes to user


## 3. API Integration

# The backend_api_phase6.py already includes voice endpoints:

# Voice Chat (STT + Response + Optional TTS)
POST /api/chat/voice
  Input:
    - user_id: str
    - file: audio file (mp3, wav, m4a, flac, ogg, opus)
    - language: str (optional, default="en")
    - enable_audio_response: bool (optional, default=True)
  
  Output:
    {
      "transcribed_text": "What I user said",
      "response_text": "AI response",
      "audio_response": "base64_encoded_audio",
      "detected_emotion": "anxious",
      "is_crisis": false,
      "topics": ["anxiety", "breathing_exercises"]
    }

# Set Voice Preferences
POST /api/users/{user_id}/voice/profile
  Input:
    {
      "preferred_gender": "female",
      "speaking_rate": "normal",
      "language": "en",
      "emotional_tone": "compassionate",
      "enable_voice": true
    }

# Synthesize Text to Speech
POST /api/voice/synthesize
  Input:
    {
      "text": "Response text to convert to speech",
      "user_id": "patient_001",
      "gender": "female",
      "language": "en"
    }
  
  Output:
    {
      "audio_base64": "base64_encoded_audio",
      "audio_size_bytes": 12345
    }

# Get Supported Languages
GET /api/voice/languages
  Output:
    {
      "supported_languages": ["en", "es", "fr", "de", ...],
      "total": 40
    }


## 4. Key Features

✅ Speech-to-Text (STT)
   - Uses OpenAI Whisper
   - Supports 40+ languages
   - Auto-detects language
   - High accuracy (95%+)
   - Preserves medical terminology

✅ Text-to-Speech (TTS)
   - Primary: ElevenLabs (natural-sounding, supports emotions)
   - Fallback: Google Cloud Text-to-Speech
   - Supports 40+ languages
   - Voice customization (gender, speed, tone)
   - Emotional tone injection

✅ Crisis Detection
   - Detects suicidal language patterns
   - Identifies self-harm language
   - Flags for immediate escalation

✅ Emotion Recognition
   - Detects from voice transcription: anxious, depressed, angry, calm, crisis
   - Used for response tone adjustment
   - Helps with user profiling

✅ Accessibility
   - Enables voice input for users uncomfortable typing
   - Critical for crisis scenarios
   - Supports multiple languages
   - Screen-reader friendly API


## 5. Crisis Handling

# Automatic detection triggers include:
- "suicide" / "kill myself" / "want to die"
- "self-harm" / "cut myself"
- "overdose" / "take pills"
- "jump off" / "end it all"

When detected:
1. Flag is_crisis_signal = true
2. Immediate crisis response generated
3. Resources provided automatically
4. Escalation triggered

Example:
```
POST /api/chat/voice with audio: "I want to kill myself"
Response includes:
{
  "is_crisis": true,
  "response_text": "[CRISIS RESOURCES] Please call 988 (Suicide & Crisis Lifeline)...",
  "detected_emotion": "crisis"
}
```


## 6. Frontend Integration (Example - Vue.js/React)

### Record and Send Voice

```javascript
// Record audio
const mediaRecorder = new MediaRecorder(stream);
mediaRecorder.start();

// Stop and send
mediaRecorder.stop();
mediaRecorder.addEventListener('dataavailable', async (event) => {
  const audioBlob = event.data;
  
  const formData = new FormData();
  formData.append('file', audioBlob);
  formData.append('user_id', currentUserId);
  formData.append('enable_audio_response', true);
  
  // Send to API
  const response = await fetch('/api/chat/voice', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  
  // Display response
  displayMessage(result.response_text);
  
  // Play audio response
  if (result.audio_response) {
    const audio = new Audio(`data:audio/mp3;base64,${result.audio_response}`);
    audio.play();
  }
  
  // Show emotion indicator
  showEmotionBadge(result.detected_emotion);
  
  // Handle crisis
  if (result.is_crisis) {
    showCrisisResources();
    alertCareTeam();
  }
});
```

### Set Voice Profile

```javascript
// Update user's voice preferences
const updateVoiceProfile = async (userId) => {
  const response = await fetch(`/api/users/${userId}/voice/profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      preferred_gender: 'female',
      speaking_rate: 'normal',
      language: 'en',
      emotional_tone: 'compassionate',
      enable_voice: true
    })
  });
  
  return response.json();
};
```


## 7. Production Deployment Checklist

- [ ] OPENAI_API_KEY configured in production environment
- [ ] Optional: ELEVENLABS_API_KEY configured (for premium TTS)
- [ ] Optional: Google Cloud credentials configured (for TTS fallback)
- [ ] Audio file upload size limits configured (max 25MB)
- [ ] CORS headers configured to allow audio upload
- [ ] Audio data encrypted in transit (HTTPS)
- [ ] Audio files not stored permanently (delete after processing)
- [ ] Crisis detection triggers connected to alert system
- [ ] Rate limiting enabled on voice endpoints (5-10 calls/min per user)
- [ ] Logging enabled for:
    - All voice requests
    - Crisis detections
    - Emotion transitions
    - TTS/STT failures
- [ ] Monitoring set up for:
    - API response times (target: <2s for STT + response + TTS)
    - STT accuracy rates
    - Failure rates per language
    - Crisis detection accuracy (avoid false negatives!)


## 8. Cost Considerations

### OpenAI Whisper (STT)
- $0.02 per minute of audio (discounted rate available)
- Unlimited languages
- Highly accurate

### ElevenLabs (TTS - Premium)
- $0.30 per 1K characters (streaming cheaper)
- Natural-sounding voices
- Emotion support
- Free tier: 10K characters/month

### Google Text-to-Speech (TTS - Fallback)
- $16 per 1M characters (WaveNet voices)
- $4 per 1M characters (standard voices)
- Good quality, lower cost than ElevenLabs

Example cost per user session:
- 2 minutes of voice input: ~$0.04 (Whisper)
- 300 character response synthesis: ~$0.09 (ElevenLabs) or ~$0.0012 (Google)
- Total per session: ~$0.05-0.13


## 9. Troubleshooting

### Whisper API Key Error
```
Error: OPENAI_API_KEY not set
Solution: export OPENAI_API_KEY=sk-... && python your_script.py
```

### Audio File Too Large
```
Error: File too large (30MB > 25MB)
Solution: Compress audio or split into chunks
```

### Poor Transcription Quality
```
Issue: Whisper returning gibberish
Solution: 
1. Check audio quality/volume
2. Verify language setting is correct
3. Add medical terminology in prompt param
```

### TTS Service Unavailable
```
Issue: No audio response generated
Solution:
1. Check ELEVENLABS_API_KEY is set
2. Check Google Cloud credentials
3. System will gracefully degrade to text-only
```

### Crisis Signal False Positives
```
Issue: "I don't want to live like this anymore" flagged as crisis
Solution:
1. Review crisis_keywords in voice_support.py
2. Add context-aware filtering
3. Require confirmation for borderline cases
```


## 10. Testing

Run the test suite:
```bash
python test_voice_support.py
```

Expected output:
```
Result: 7/7 tests passed
✅ ALL TESTS PASSED! Voice support is ready for deployment.
```

Test coverage:
- ✅ Initialization
- ✅ Emotion Detection
- ✅ Crisis Detection
- ✅ Voice Profile Management
- ✅ Language Support
- ✅ Audio File Validation
- ✅ TTS Integration


## 11. Architecture Diagram

```
User Voice Input
    ↓
[Browser/Mobile Recording]
    ↓
[Upload Audio File]
    ↓
POST /api/chat/voice
    ↓
[Voice Support Module]
    ├─ Whisper STT → Text
    ├─ Emotion Detection
    └─ Crisis Detection
    ↓
[NeuronixCore]
    ├─ Phase 6 Memory Store
    ├─ Learning Tracker
    └─ Query Generation
    ↓
[TTS Synthesis]
    ├─ ElevenLabs (Primary)
    └─ Google (Fallback)
    ↓
Response with Audio
    ├─ Transcribed Text
    ├─ AI Response
    ├─ Audio Response (optional)
    ├─ Emotion Detected
    └─ Crisis Flag
    ↓
[Browser/Mobile]
    ├─ Show Text
    ├─ Play Audio
    ├─ Emotion Indicator
    └─ Crisis Resources (if needed)
```


## 12. Security & Privacy

✅ Audio Processing
- Audio files deleted after processing
- No permanent audio storage
- Encrypted in transit (HTTPS)
- Processed server-side, not stored locally

✅ Crisis Detection
- Patterns matched on client/server
- Automatic escalation (no user opt-out)
- Documented in user's session history
- Viewable by care team

✅ Emotional Data
- Emotion classifications stored in session
- Used for personalization
- No biometric storage
- User can request deletion

✅ Compliance
- HIPAA compliant processing
- PHI not sent to external STT if possible
- Audit trail for all voice interactions
- Consent captured before first use


## 13. Next Steps

1. Set up API keys for Whisper and ElevenLabs
2. Test voice recording in frontend
3. Deploy backend_api_phase6.py with voice endpoints
4. Add UI for voice input button (microphone icon)
5. Add audio playback for responses
6. Configure crisis escalation workflow
7. Monitor voice API costs
8. Gather user feedback on voice quality
9. A/B test different voice profiles
10. Plan Phase 7: Real-time speech synthesis


## Support

For issues or questions:
- Check voice module docs: scripts/voice_support.py
- Review test suite: test_voice_support.py
- See API docs: backend_api_phase6.py
- Crisis support: Implement escalation logic per your guidelines
"""

print(__doc__)
