# 1.4 — Cleanup `serve.py`

**Status**: ⬜ | **Deps**: 1.3 | **Agent**: any

## Do
In `src/openjarvis/cli/serve.py`, find the `get_tts_backend` block (~L476-484). The discovery module now handles piper import internally. Remove any stale explicit kokoro import if present (e.g. `import openjarvis.speech.kokoro_tts`).

If no stale import exists, no changes needed — verify the `get_tts_backend(config)` call still works.

## Done when
- Server starts with `TTS: piper` in console output
- No kokoro references in serve.py
