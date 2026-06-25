# Voice Conversation Rewrite — Context (Backend-Only)

## Current State (2026-06-25)

The voice loop is **implemented and running** in `voice_loop.py` with the following status:

### Working
- `voice_loop.py` — state machine (IDLE → GREETING → LISTENING → IDLE)
- `vad.py` — Silero VAD wrapper (extracted from old `openwakeword.py`)
- Adaptive noise floor tracking (running RMS estimator, gate ratio 1.5x)
- Console status display: emoji status line + `[YOU]` / `[OLLAMA]` transcript lines
- `/v1/voice/status` WebSocket endpoint — broadcasts state changes
- `ConfigPage.tsx` + `useVoiceStatus.ts` — frontend status indicator
- Uvicorn access/WS logs suppressed — no `INFO: connection open/closed` noise
- `openwakeword.py` removed (only `vad.py` remains from that module)

### Current Configuration
- `_discovery.py` passes `require_wake_word=False` — listens continuously, no wake word needed
- Mic opens via pyaudio default input device at 16kHz
- `MIN_SIGNAL_RATIO = 1.5` — noise gate passes audio when RMS > 1.5× ambient floor
- `_vad_threshold = 0.6` — VAD probability threshold
- `SILENCE_BEFORE_TRANSCRIBE_MS = 800` — idle silence timeout
- `LISTEN_SILENCE_TIMEOUT_MS = 1500` — listening silence timeout

### Known Issues
- **Mic capture not working** on this machine — noise floor RMS ~0.000075, speech also at ~0.00007. Audio barely registers. Possible causes:
  - Wrong default pyaudio input device
  - Mic gain too low
  - USB mic device not selected
  - See diagnostic below

## How to Re-enable Wake Word Later

In `src/src/openjarvis/speech/_discovery.py` (around line 187):

```python
return VoiceLoop(
    stt_backend=stt_backend,
    tts_backend=tts_backend,
    engine=engine,
    model=model,
    require_wake_word=False,   # ← change to True
    wake_phrases=["hey jarvis", "hey ada", "jarvis"],
)
```

Set `require_wake_word=True`. The loop will then only transition from IDLE → GREETING when the transcribed text contains one of the wake phrases. Also update the `_STATUS_LABELS["idle"]` back to `"🎤  Waiting for wake word…"` if desired.

## Analysis

The original voice implementation had become overly complex with layers of workarounds:

1. **OpenWakeWord ONNX model abandoned** — the `hey_jarvis_v0.1` model produces "unusable scores" on this platform.
2. **Dual wake-word paths**: Server WebSocket stream + client-side "legacy VAD" fallback.
3. **8+ state refs in frontend**: Multiple refs for voice/wake/audio state management.
4. **Browser AudioContext chaos**: Multiple AudioContexts with race conditions.
5. **No wake-word feedback**: No audio confirmation when "Hey Jarvis" detected.

## Decision: Backend-Only

All voice processing moved to the Python server. Frontend is a trivial status display.

## Architecture

```
IDLE → GREETING → LISTENING → IDLE
```

- **IDLE**: pyaudio mic open, Silero VAD monitors. When speech detected → buffer audio → on silence (800ms) → transcribe via STT backend → [optional wake check] → GREETING
- **GREETING**: Send utterance to Ollama → play TTS response → LISTENING
- **LISTENING**: Record via pyaudio → on silence (1.5s) → transcribe → send to Ollama → play TTS reply → loop. Extended silence (5s) → IDLE
- Broadcasts state changes via `/v1/voice/status` WebSocket

## Console Output Format

```
🎤  Waiting for wake word…      ← status line (updates in-place)
  [YOU] hello how are you        ← transcribed user speech
  [OLLAMA] I'm doing great!      ← LLM response
  🎙️  Listening…                 ← state changed
```

## Files

### Backend (Python)
- `src/src/openjarvis/speech/voice_loop.py` — state machine + console display
- `src/src/openjarvis/speech/vad.py` — Silero VAD wrapper
- `src/src/openjarvis/speech/_discovery.py` — factory function with `require_wake_word` toggle
- `src/src/openjarvis/server/api_routes.py` — WebSocket endpoint `/v1/voice/status`
- `src/src/openjarvis/server/app.py` — wires voice loop startup/shutdown
- `src/src/openjarvis/cli/serve.py` — `access_log=False`, loggers set to WARNING

### Frontend (TypeScript/React)
- `src/frontend/src/pages/ConfigPage.tsx` — status indicator + settings
- `src/frontend/src/hooks/useVoiceStatus.ts` — WebSocket hook

## Mic Diagnostic

If the mic level stays flat when speaking, test the default input device:

```powershell
cd src
uv run python -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'dev[{i}] {info[\"name\"]}  rate={info[\"defaultSampleRate\"]}')
p.terminate()
"
```

Then force a specific device in `voice_loop.py` `_ensure_audio()` by passing `input_device_index=N` to `p.open(...)`.
