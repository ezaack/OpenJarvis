# 1.1 — Install kokoro

**Status**: ⬜ | **Deps**: none | **Agent**: any

## Do
1. Add `"kokoro>=0.1"` to `speech` extra in `src/pyproject.toml` (line with `speech = ["faster-whisper>=1.0"]`)
2. Run `uv sync --extra speech`
3. Verify: `.venv\Scripts\python -c "from kokoro import KPipeline; print('ok')"`

## Done when
Kokoro imports without error in project venv.
