# 1.2 — TTS discovery

**Status**: ⬜ | **Deps**: 1.1 | **File**: `src/openjarvis/speech/_discovery.py`

## Do
Add `get_tts_backend(config)` function that mirrors `get_speech_backend()`:
- Priority order: `["kokoro", "cartesia", "openai_tts"]`
- For kokoro: instantiate with defaults (no extra config needed)
- For cartesia: needs `CARTESIA_API_KEY` env var, skip if missing
- For openai_tts: needs `OPENAI_API_KEY` env var, skip if missing
- Return first healthy backend or `None`
- Health check: call `backend.health()` (already exists on TTSBackend ABC)

## Done when
`get_tts_backend(config)` returns Kokoro backend with `health() == True`.
