# 1.2 — Create `piper_tts.py` backend

**Status**: ⬜ | **Deps**: 1.1 | **Agent**: any

## Do
Create `src/openjarvis/speech/piper_tts.py` following `cartesia_tts.py` pattern:

- `@TTSRegistry.register("piper")` class `PiperTTSBackend(TTSBackend)`
- `backend_id = "piper"`
- `__init__(self, *, model_path="", voice_name="en_US-lessac-medium", use_cuda=False, data_dir=None)`
- `_ensure_voice()` — lazy-load ONNX model: auto-download voice if not found, then `PiperVoice.load(path, use_cuda=use_cuda)`
- `synthesize(text, *, voice_id, speed, output_format)`:
  - Create `SynthesisConfig(length_scale=1.0/speed, ...)`
  - Iterate `voice.synthesize(text, syn_config)` → collect all `chunk.audio_int16_bytes` → decode int16 → numpy → `sf.write(buf, audio, sample_rate, format=output_format)` → return `TTSResult`
- `available_voices()` → `[self._voice_name]`
- `health()` → `self._voice is not None`
- `speed` maps to `length_scale` via `1.0 / max(speed, 0.1)`
- Handle import errors gracefully (return `health() == False`)

## Done when
- File exists, follows TTSBackend ABC
- `@TTSRegistry.register("piper")` decorator present
- No import errors when `piper-tts` is installed
