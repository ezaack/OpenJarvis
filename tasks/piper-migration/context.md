# Piper Migration — Shared Context

## Decisions
- **Drop Kokoro entirely** — Piper is faster (ONNX), lighter (15MB voice vs 300MB), no API key
- **Default voice**: `en_US-lessac-medium` (~15MB, natural female)
- **Lazy download**: Auto-download voice on first use via `piper.download_voices`
- **Speed mapping**: `speed=1.0` → `length_scale=1.0`, `speed=2.0` → `length_scale=0.5` (inverse)
- **No streaming yet**: Same Kokoro pattern (collect all → WAV). Streaming is Phase 2
- **GPLv3**: Piper is GPLv3 — verify license compatibility

## Key Files
| File | Action | Role |
|------|--------|------|
| `src/openjarvis/speech/piper_tts.py` | **CREATE** | Piper TTSBackend impl |
| `src/openjarvis/speech/__init__.py` | Modify | Swap kokoro_tts → piper_tts |
| `src/openjarvis/speech/_discovery.py` | Modify | Replace kokoro with piper |
| `src/openjarvis/cli/serve.py` | Modify | Remove kokoro import |
| `src/pyproject.toml` | Modify | kokoro → piper-tts |
| `tests/speech/test_tts_backends.py` | Modify | kokoro tests → piper tests |
| `src/openjarvis/speech/kokoro_tts.py` | **DELETE** | Removed |
| `src/openjarvis/speech/tts.py` | Reference | TTSBackend ABC, TTSResult |
| `src/openjarvis/core/registry.py` | Reference | TTSRegistry decorator |

## Conventions
- Follow `cartesia_tts.py` pattern for backend structure
- `@TTSRegistry.register("piper")` decorator
- `health()` returns True if ONNX model loaded
- `synthesize()` matches existing signature: `(text, voice_id, speed, output_format) → TTSResult`
- Tests mock `PiperVoice.load` + `voice.synthesize()`; no real model needed

## Server Status
- Running at `http://127.0.0.1:8000`
- STT: faster-whisper ✓
- Engine: ollama / gemma3:4b
- Current TTS: kokoro

## Piper API Reference
```python
from piper import PiperVoice, SynthesisConfig
from piper.download_voices import download_voice

# Download
download_voice("en_US-lessac-medium", data_dir="/path/to/voices")

# Load
voice = PiperVoice.load("/path/to/en_US-lessac-medium.onnx", use_cuda=False)

# Synthesize (sentence-by-sentence generator)
syn_config = SynthesisConfig(length_scale=1.0, noise_scale=0.667)
for chunk in voice.synthesize("Hello world. This is a test.", syn_config):
    # chunk.audio_int16_bytes — ready to play
    # chunk.sample_rate, chunk.sample_width, chunk.sample_channels
    pass
```
