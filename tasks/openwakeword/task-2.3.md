# 2.3 — Add wake word health endpoint

**Status**: ⬜ | **Deps**: 1.2 | **File**: `src/openjarvis/server/api_routes.py`

## Do
Add a GET endpoint to the `speech_router` (or a new `wakeword_router`) that reports wake word detector status.

```python
@speech_router.get("/wakeword/health")
async def wakeword_health(request: Request):
    """Check if a wake word detector is available."""
    detector = getattr(request.app.state, "wakeword_detector", None)
    if detector is None:
        return {"available": False, "reason": "No wake word detector configured"}
    try:
        available = detector.health()
        reason = None
    except Exception as exc:
        available = False
        reason = str(exc)

    return {
        "available": available,
        "backend": getattr(detector, "backend_id", "openwakeword"),
        "wakeword": getattr(detector, "_wakeword", "unknown"),
        "threshold": getattr(detector, "_threshold", 0.5),
        **({"reason": reason} if reason else {}),
    }
```

## Done when
`GET /v1/speech/wakeword/health` returns `{"available": true, "backend": "openwakeword", "wakeword": "hey_jarvis"}`.
