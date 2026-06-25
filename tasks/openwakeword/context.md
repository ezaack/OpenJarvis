# OpenWakeWord — Shared Context

## Decisions
- **Approach**: Option A — Python backend (server-side detection) with WebSocket bridge.
- **Wake word**: "hey_jarvis" (OpenWakeWord pre-trained model; activate with "Hey Ada").
- **Fallback**: Energy-based VAD remains as fallback when wake word model is unavailable.
- **Audio format**: 16-bit 16kHz mono PCM streamed from browser → server over WebSocket.
- **Cooldown**: 3s debounce between activations (existing `WAKE_COOLDOWN_MS` preserved).
- **Threshold**: Default 0.5, configurable via `speech.wakeword.threshold`.

## Key Files

| File | Role |
|------|------|
| `src/openjarvis/speech/openwakeword.py` | New `OpenWakeWordDetector` class |
| `src/openjarvis/speech/__init__.py` | Register module for auto-import |
| `src/openjarvis/core/config.py` | `SpeechConfig.wakeword` sub-section |
| `src/openjarvis/server/api_routes.py` | WebSocket route `/v1/speech/wakeword/stream` |
| `src/openjarvis/cli/serve.py` | Wire wake word detector at startup (~L464) |
| `frontend/src/hooks/useSpeech.ts` | `startWakeWatcher()` → WebSocket streaming |
| `frontend/src/lib/api.ts` | `createWakeWordStream()` WebSocket helper |
| `frontend/src/components/Chat/InputArea.tsx` | Wake word UI indicator + toggle |
| `src/pyproject.toml` | Add `openwakeword` to `speech` extra |

## OpenWakeWord API Reference

```python
import openwakeword
from openwakeword.model import Model

# One-time download of all pre-trained models
openwakeword.utils.download_models()

# Instantiate model(s)
model = Model(wakeword_models=["hey_jarvis.onnx"])

# Predict on a single 16kHz 16-bit PCM audio frame (multiples of 1280 samples = 80ms)
prediction = model.predict(frame)
# Returns {"hey_jarvis": 0.85} — score 0.0–1.0

# Optional: enable Silero VAD as second-stage filter
model = Model(wakeword_models=["hey_jarvis.onnx"], vad_threshold=0.5)

# Optional: Speex noise suppression (Linux only)
model = Model(wakeword_models=["hey_jarvis.onnx"], enable_speex_noise_suppression=True)
```

## Audio Processing Chain (Browser → Server)

```
Browser mic → AudioContext({sampleRate: 16000}) → ScriptProcessorNode
  → 16-bit PCM Int16Array → WebSocket binary frames
  → Server reads binary frame → OpenWakeWordModel.predict(frame)
  → If score >= threshold → send {"event": "wakeword", "keyword": "hey_jarvis"}
  → Frontend receives → startRecording()
```

## Conventions
- Follow existing patterns in `speech/_discovery.py` for backend registration.
- Follow existing route patterns in `api_routes.py` (see `/v1/speech/transcribe` for reference).
- Models downloaded at first run to `~/.cache/openwakeword/` automatically.
