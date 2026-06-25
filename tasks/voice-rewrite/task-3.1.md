# Phase 3: Create Backend Voice Loop (Python)

## Task 3.1 — Create `vad.py` — Silero VAD wrapper

**Files**: `src/src/openjarvis/speech/vad.py` (new)

Clean VAD wrapper, extracted from the VAD logic in the old `openwakeword.py`.

```python
# vad.py - Silero VAD wrapper
import numpy as np
from openwakeword.vad import VAD as SileroVAD

SAMPLE_RATE = 16000
VAD_FRAME_MS = 30
VAD_FRAME_SIZE = int(SAMPLE_RATE * VAD_FRAME_MS / 1000)  # 480

class VoiceActivityDetector:
    """Wrapper around Silero VAD for speech detection."""

    def __init__(self, threshold: float = 0.5):
        self._vad = SileroVAD()
        self._threshold = threshold

    def is_speech(self, pcm16_bytes: bytes) -> bool:
        """Return True if the audio chunk contains speech."""
        samples = np.frombuffer(pcm16_bytes, dtype=np.int16)
        # Pad to multiple of frame size
        remainder = len(samples) % VAD_FRAME_SIZE
        if remainder:
            samples = np.pad(samples, (0, VAD_FRAME_SIZE - remainder))
        try:
            return float(self._vad.predict(samples)) >= self._threshold
        except Exception:
            return False

    def reset(self) -> None:
        self._vad.reset_states()
```

## Task 3.2 — Create `voice_loop.py` — state machine

**Files**: `src/src/openjarvis/speech/voice_loop.py` (new)

Core voice conversation state machine. Runs as an `asyncio` task during `jarvis serve`.

### API

```python
class VoiceLoop:
    """State machine: IDLE -> GREETING -> LISTENING -> IDLE."""

    def __init__(
        self,
        stt_backend,      # SpeechBackend for transcription
        tts_backend,       # TTSBackend for synthesis
        engine,            # LLM engine for Ollama responses
        status_callback,   # async fn to broadcast state to frontend
    ): ...

    async def start(self) -> None: ...   # Opens mic, enters IDLE
    async def stop(self) -> None: ...    # Closes mic, stops loop
```

### State Machine Logic

**IDLE**:
- Open pyaudio mic (mono, 16kHz, int16)
- Read chunks of ~480 samples (30ms frames for VAD)
- Run Silero VAD on each chunk
- When speech detected: start buffering chunks
- When silence resumes for 800ms:
  - Convert buffered chunks to WAV
  - Call `stt_backend.transcribe(wav)`
  - If transcript contains "hey jarvis" → GREETING
  - Otherwise discard buffer, stay in IDLE
- Broadcast: `{"state": "idle"}`

**GREETING**:
- Send "hey jarvis" to engine (Ollama) as a chat message
- Get response → synthesize via TTS → play via `pyaudio` output
- Broadcast: `{"state": "greeting", "text": "..."}`
- Transition to LISTENING

**LISTENING**:
- Record audio continuously
- On each chunk, check for silence via VAD
- After 1.5s of continuous silence:
  - Stop recording
  - Convert to WAV → transcribe via STT
  - If transcript is empty → loop back to recording
  - Send transcript to engine (Ollama) → get response → TTS → play
  - Restart recording
- On 5s total silence with no speech → IDLE
- Broadcast: `{"state": "listening", "transcript": "...", "reply": "..."}`

### Audio I/O

- **Input**: `pyaudio.PyAudio().open(format=paInt16, channels=1, rate=16000, input=True, frames_per_buffer=480)`
- **Output (TTS)**: TTS synthesizes → get WAV bytes → play via `pyaudio` output stream
- Run audio I/O in `asyncio` via `loop.run_in_executor` to avoid blocking the event loop

## Task 3.3 — Create `/v1/voice/status` WebSocket endpoint

**Files**: `src/src/openjarvis/server/api_routes.py`

New WebSocket endpoint that broadcasts voice state to the frontend:

```python
@voice_router.websocket("/status")
async def voice_status(websocket: WebSocket):
    await websocket.accept()
    # Register this client
    voice_loop = websocket.app.state.voice_loop
    # ... subscribe to state changes, forward to client
```

Events sent to frontend:
- `{"type": "state", "state": "idle"}`
- `{"type": "state", "state": "greeting", "text": "Yes, sir?"}`
- `{"type": "state", "state": "listening"}`
- `{"type": "transcript", "text": "what's the weather"}`
- `{"type": "reply", "text": "It's sunny today."}`

## Task 3.4 — Wire voice loop into `jarvis serve`

**Files**: `src/src/openjarvis/server/app.py`, `src/src/openjarvis/cli/serve.py`

- On server startup, if STT and TTS backends are available, create a `VoiceLoop` instance
- Store it in `app.state.voice_loop`
- Start it as a background `asyncio.Task`
- On server shutdown, stop the voice loop
- Expose `--no-voice` flag to `jarvis serve` to disable voice mode
