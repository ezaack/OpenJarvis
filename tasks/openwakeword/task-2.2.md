# 2.2 — Wire wake word into `cli/serve.py` startup

**Status**: ⬜ | **Deps**: 2.1, 1.3 | **File**: `src/openjarvis/cli/serve.py`

## Do
In `cli/serve.py`, near where `speech_backend` is initialized (~L464), add wake word detector initialization.

Find the block that looks like:

```python
# Speech backend
speech_backend = get_speech_backend(config)
app.state.speech_backend = speech_backend
if speech_backend:
    logger.info("Speech backend: %s", speech_backend.backend_id)
```

Add after it:

```python
# Wake word detector
wakeword_detector = None
if config.speech.wakeword.enabled:
    try:
        from openjarvis.speech.openwakeword import OpenWakeWordDetector
        wakeword_detector = OpenWakeWordDetector(
            wakeword=config.speech.wakeword.model,
            threshold=config.speech.wakeword.threshold,
            vad_threshold=config.speech.wakeword.vad_threshold or None,
        )
        if wakeword_detector.health():
            app.state.wakeword_detector = wakeword_detector
            logger.info(
                "Wake word detector: %s (threshold=%.2f)",
                config.speech.wakeword.model,
                config.speech.wakeword.threshold,
            )
        else:
            logger.warning("Wake word detector health check failed")
            wakeword_detector = None
    except Exception as exc:
        logger.warning("Failed to initialize wake word detector: %s", exc)
```

If a separate `ws_routes.py` was created in 2.1, also import and include that router here.

## Done when
Running `jarvis serve` with `[speech.wakeword] enabled = true` in config logs `"Wake word detector: hey_jarvis"`.
