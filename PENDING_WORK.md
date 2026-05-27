# 🎤 PENDING WORK: Voice Feature Integration

## Priority Tasks

### 1. ✅ ADD MIC OPTION TO UNDERSTAND/CHAT INTERFACE

**Location:** Frontend UI (Vue.js/React component)

**What to Add:**
- [ ] Microphone button next to text input field
- [ ] Audio recording UI (press to record, release to send)
- [ ] Visual feedback (recording indicator, waveform animation)
- [ ] Transcript display (show what user said)
- [ ] Option to switch between text/voice input

**Technical Implementation:**
```javascript
// Add to chat input component
<button @click="startRecording" class="mic-button">
  🎤 Speak
</button>

// Record audio
async startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.start();
}

// Send to backend
async stopRecording() {
  mediaRecorder.stop();
  mediaRecorder.ondataavailable = async (event) => {
    const audioBlob = event.data;
    
    const formData = new FormData();
    formData.append('file', audioBlob);
    formData.append('user_id', currentUserId);
    formData.append('enable_audio_response', true);
    
    const response = await fetch('/api/chat/voice', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    // Display transcribed_text and response_text
  };
}
```

**UI Elements Needed:**
- [ ] Microphone icon button
- [ ] Recording status indicator (red dot pulsing)
- [ ] Waveform visualization during recording
- [ ] Timer (show recording duration)
- [ ] Transcript preview
- [ ] Play/pause button for audio response
- [ ] Emotion badge (shows detected emotion: anxious/calm/crisis/etc)
- [ ] Crisis alert banner (if is_crisis = true)

**Files to Update:**
- `frontend/components/ChatInput.vue` (or React equivalent)
- `frontend/components/ChatMessage.vue` (add audio playback)
- `frontend/styles/chat.css` (add mic button styling)

---

### 2. ✅ OPENAI WHISPER & ELEVENLABS SETUP

**Status:** ✅ Backend APIs Ready
- `voice_support.py` - Complete STT/TTS system
- `backend_api_phase6.py` - Voice endpoints active
- Test suite - 7/7 tests passing

**Still Needed:**

#### A. API Key Configuration
```bash
# Set environment variables
export OPENAI_API_KEY=sk-...
export ELEVENLABS_API_KEY=...

# Or in .env file
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
```

**Where to Set:**
- [ ] Development: `.env` file in project root
- [ ] Production: Environment variables in deployment platform
- [ ] Docker: Add to `docker-compose.yml` or `.env.production`

#### B. Backend Endpoints Available
```
✅ POST /api/chat/voice
   - Upload audio file
   - Get transcription + response + audio response
   - Returns: transcribed_text, response_text, audio_response (base64), detected_emotion, is_crisis

✅ POST /api/users/{user_id}/voice/profile
   - Save user's voice preferences
   - Gender, language, emotional tone, speaking rate

✅ POST /api/voice/synthesize
   - Convert text to audio
   - Customizable voice profile

✅ GET /api/voice/languages
   - Get list of supported languages
```

#### C. Frontend Integration Checklist
- [ ] Install audio libraries: `npm install wavesurfer.js` (optional, for waveform)
- [ ] Create voice recording hook/composable
- [ ] Add microphone permission request UI
- [ ] Handle browser compatibility (Chrome, Firefox, Safari, Edge)
- [ ] Add audio playback component for responses
- [ ] Add emotion indicator UI
- [ ] Add crisis alert routing

#### D. Crisis Detection Integration
**When `is_crisis = true`:**
- [ ] Show crisis resource banner
- [ ] Provide 988 hotline number
- [ ] Offer crisis chat resources
- [ ] Alert care team (if enabled)
- [ ] Log incident for review

#### E. Testing Checklist
- [ ] Test with real microphone input
- [ ] Test multiple languages (en, es, fr, etc)
- [ ] Test crisis keyword detection
- [ ] Test emotion detection accuracy
- [ ] Test audio response playback
- [ ] Test on mobile devices
- [ ] Test with poor audio quality
- [ ] Test with accent variations

---

## Timeline & Dependencies

```
Phase 1 (This Week): Frontend Voice UI
├─ Add mic button to chat interface
├─ Implement audio recording
├─ Display transcription
└─ Show response + emotion badge

Phase 2 (Next Week): Crisis Integration
├─ Add crisis alert UI
├─ Connect to crisis resources
├─ Alert care team workflow
└─ Test with sensitive keywords

Phase 3 (Week After): Production Deploy
├─ Configure API keys in production
├─ Deploy updated backend
├─ Deploy updated frontend
├─ Monitor STT/TTS quality
└─ Gather user feedback
```

---

## Current Status

| Component | Status | Details |
|-----------|--------|---------|
| Whisper STT | ✅ Ready | `voice_support.py` implemented, 7/7 tests pass |
| ElevenLabs TTS | ✅ Ready | Premium voice synthesis working |
| Google TTS Fallback | ✅ Ready | Graceful degradation enabled |
| Backend Endpoints | ✅ Ready | 4 voice endpoints in `backend_api_phase6.py` v2.2 |
| Crisis Detection | ✅ Ready | Detects 6+ crisis keywords, flags for routing |
| Emotion Detection | ✅ Ready | 7 emotions: crisis/anxious/depressed/angry/calm/neutral |
| **Frontend UI** | ⏳ TODO | Add microphone button, recording UI, playback |
| **API Key Setup** | ⏳ TODO | Configure in development & production environments |
| **Crisis Routing** | ⏳ TODO | Connect crisis alerts to care team workflow |
| **Mobile Testing** | ⏳ TODO | Test voice on iOS/Android apps |

---

## Code References

**Backend Implementation (DONE):**
- [voice_support.py](scripts/voice_support.py) - STT/TTS orchestration
- [backend_api_phase6.py](backend_api_phase6.py) - API endpoints
- [test_voice_support.py](test_voice_support.py) - Test suite (7/7 passing)

**Documentation:**
- [VOICE_IMPLEMENTATION_GUIDE.md](VOICE_IMPLEMENTATION_GUIDE.md) - Complete setup guide

**Next Files to Create:**
- `frontend/hooks/useVoiceRecording.js` - Voice recording logic
- `frontend/components/VoiceInput.vue` - Mic button component
- `frontend/components/AudioPlayback.vue` - Play audio responses
- `frontend/components/CrisisAlert.vue` - Crisis warning banner

---

## Quick Start for Frontend Dev

1. **Install dependencies:**
   ```bash
   npm install wavesurfer.js recordrtc
   ```

2. **Import voice hook:**
   ```javascript
   import { useVoiceRecording } from '@/hooks/useVoiceRecording'
   
   const { 
     isRecording, 
     startRecording, 
     stopRecording, 
     transcript,
     response,
     emotion,
     isCrisis
   } = useVoiceRecording()
   ```

3. **Add to template:**
   ```vue
   <button @click="startRecording" :disabled="isRecording">
     🎤 {{ isRecording ? 'Recording...' : 'Speak' }}
   </button>
   
   <div v-if="emotion" class="emotion-badge">
     {{ emotion }}
   </div>
   
   <div v-if="isCrisis" class="crisis-alert">
     ⚠️ Crisis Support: 988
   </div>
   ```

---

## Questions to Resolve

1. **Audio Storage:** Should we save audio files for user review or delete immediately?
2. **Privacy:** Should voice data be encrypted at rest?
3. **Analytics:** Track voice usage patterns vs text usage?
4. **Voice Profiles:** Let users pick custom voice (male/female/accent)?
5. **Real-time:** Support streaming audio or just file upload?

---

## Related Links

- [OpenAI Whisper Docs](https://platform.openai.com/docs/guides/speech-to-text)
- [ElevenLabs Docs](https://elevenlabs.io/docs)
- [Google TTS Docs](https://cloud.google.com/text-to-speech/docs)

---

**Generated:** May 9, 2026  
**Status:** In Progress 🚀
