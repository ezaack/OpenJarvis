# 1.1 — Update deps: kokoro → piper-tts

**Status**: ⬜ | **Deps**: none | **Agent**: any

## Do
1. In `src/pyproject.toml`, change line `speech = ["faster-whisper>=1.0", "kokoro>=0.1"]` → `speech = ["faster-whisper>=1.0", "piper-tts>=1.4"]`
2. Run `uv sync --extra speech` from `src/`
3. Verify: `.venv\Scripts\python -c "from piper import PiperVoice; print('ok')"`

## Done when
- `uv sync` succeeds with piper-tts installed
- Piper imports without error
