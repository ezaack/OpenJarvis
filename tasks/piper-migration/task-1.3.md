# 1.3 — Update `__init__.py` + `_discovery.py`

**Status**: ⬜ | **Deps**: 1.2 | **Agent**: any

## Do

### `src/openjarvis/speech/__init__.py`
- Change `"kokoro_tts"` → `"piper_tts"` in TTS import loop (line ~13)

### `src/openjarvis/speech/_discovery.py`
- Change `TTS_DISCOVERY_ORDER`: `"kokoro"` → `"piper"` (keep `"piper"` first)
- In `_create_tts_backend()`: replace kokoro branch (`if key == "kokoro": return backend_cls()`) with piper branch:
  ```python
  if key == "piper":
      voice_name = getattr(config.tts, "voice_name", "en_US-lessac-medium")
      use_cuda = getattr(config.tts, "use_cuda", False)
      return backend_cls(voice_name=voice_name, use_cuda=use_cuda)
  ```
- In `get_tts_backend()`: change `import openjarvis.speech.kokoro_tts` → `import openjarvis.speech.piper_tts`

## Done when
- Imports piper_tts instead of kokoro_tts
- `TTS_DISCOVERY_ORDER = ["piper", "cartesia", "openai_tts"]`
- `get_tts_backend(config)` returns Piper when piper-tts installed
