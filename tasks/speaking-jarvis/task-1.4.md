# 1.4 — Wire TTS into serve.py

**Status**: ⬜ | **Deps**: 1.2 | **File**: `src/openjarvis/cli/serve.py`

## Do
Next to where speech backend is wired (search for `speech_backend = None`, ~L464), add:
```python
tts_backend = None
try:
    from openjarvis.speech._discovery import get_tts_backend
    tts_backend = get_tts_backend(config)
    if tts_backend:
        console.print(f"  TTS: [cyan]{tts_backend.backend_id}[/cyan]")
except Exception as exc:
    logger.debug("TTS backend discovery failed: %s", exc)
```

Then pass `tts_backend` through to `create_app()` and set `app.state.tts_backend = tts_backend`.

## Done when
Server startup prints `TTS: kokoro` next to `Speech: faster-whisper`.
