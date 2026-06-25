# 2.1 — Add WebSocket route `/v1/speech/wakeword/stream`

**Status**: ⬜ | **Deps**: 1.2 | **File**: `src/openjarvis/server/api_routes.py` (or new `ws_routes.py`)

## Do
Add a WebSocket endpoint that accepts streaming 16kHz 16-bit mono PCM audio frames and returns wake word detection events.

### Option A (recommended): Add to `api_routes.py`

Add to the `speech_router` or create a new `wakeword_router`:

```python
from fastapi import WebSocket, WebSocketDisconnect

@speech_router.websocket("/wakeword/stream")
async def wakeword_stream(websocket: WebSocket):
    await websocket.accept()
    detector = getattr(websocket.app.state, "wakeword_detector", None)
    if detector is None:
        await websocket.send_json({"error": "Wake word detector not configured"})
        await websocket.close()
        return

    try:
        while True:
            # Receive binary audio frame (16kHz 16-bit PCM)
            data = await websocket.receive_bytes()
            detected, confidence = detector.process_frame(data)
            if detected:
                await websocket.send_json({
                    "event": "wakeword",
                    "keyword": detector._wakeword,
                    "confidence": round(confidence, 4),
                })
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.exception("Wake word WebSocket error")
        try:
            await websocket.send_json({"error": str(exc)})
        except Exception:
            pass
```

### Option B: Create `src/openjarvis/server/ws_routes.py`
If the API routes file is getting large, create a separate `ws_routes.py` that registers its own router and include it in the main app in `serve.py`.

### Frame size guidance
- 80ms at 16kHz = 1280 samples = 2560 bytes (16-bit)
- Frontend should chunk audio into multiples of 1280 samples
- OpenWakeWord handles variable frame sizes internally

## Done when
Connecting to `ws://127.0.0.1:8000/v1/speech/wakeword/stream` and sending PCM frames returns `{"event": "wakeword"}` on detection.
