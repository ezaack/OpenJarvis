# 1.4 — Register detector in `speech/__init__.py`

**Status**: ⬜ | **Deps**: 1.2 | **File**: `src/openjarvis/speech/__init__.py`

## Do
Add `"openwakeword"` to the import list so the `@SpeechRegistry.register("openwakeword")` decorator fires at import time.

```python
# Optional wake word backends
for _mod in ("openwakeword",):
    try:
        importlib.import_module(f".{_mod}", __name__)
    except ImportError:
        pass
```

Place this after the existing STT and TTS import blocks, or merge it into the STT block.

## Done when
`import openjarvis.speech` loads `OpenWakeWordDetector` into `SpeechRegistry` without error when `openwakeword` is installed.
