# Voice Conversation Rewrite — Index (Backend-Only)

## Overview

Replace the tangled dual-path wake-word + voice-loop implementation with a single, explicit state machine running entirely in the Python server. The frontend becomes a trivial status display. Uses `pyaudio` for mic access (proven working) and Silero VAD for voice activity detection.

## Phases

### Phase 1: Remove Old Wake Word Code
- [ ] 1.1 — Remove wake word routes from `api_routes.py`
- [ ] 1.2 — Remove `wakeword_detector` from `app.py`
- [ ] 1.3 — Remove `openwakeword` from `speech/__init__.py`
- [ ] 1.4 — Remove `get_wakeword_detector` from `_discovery.py`
- [ ] 1.5 — Delete `openwakeword.py`

### Phase 2: Simplify Frontend to Config-Only Page
- [ ] 2.1 — Remove wake word types/functions from `api.ts`
- [ ] 2.2 — Delete `useSpeech`, `InputArea`, `ChatArea`, `MicButton`, all chat components
- [ ] 2.3 — Create new `ConfigPage` — settings form + voice status indicator
- [ ] 2.4 — Create lightweight `useVoiceStatus` hook (WebSocket listener, no audio)
- [ ] 2.5 — Update `App.tsx` — render ConfigPage instead of ChatArea

### Phase 3: Create Backend Voice Loop (Python)
- [ ] 3.1 — Create `vad.py` — Silero VAD wrapper
- [ ] 3.2 — Create `voice_loop.py` — state machine (IDLE / GREETING / LISTENING)
- [ ] 3.3 — Create `/v1/voice/status` WebSocket endpoint
- [ ] 3.4 — Wire voice loop into `jarvis serve` startup

### Phase 4: Verify
- [ ] 4.1 — Remove `test_wakeword.py`
- [ ] 4.2 — TypeScript compilation check
- [ ] 4.3 — Server smoke test (voice loop starts, responds to wake word)
- [ ] 4.4 — Frontend displays status correctly
