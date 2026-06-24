# 1.3 — TTS API route

**Status**: ⬜ | **Deps**: 1.2 | **File**: `src/openjarvis/server/api_routes.py`

## Do
Add after speech routes (~L920):

```python
tts_router = APIRouter(prefix="/v1/tts", tags=["tts"])

@tts_router.post("/synthesize")
async def synthesize_speech(request: Request, body: dict):
    backend = getattr(request.app.state, "tts_backend", None)
    if backend is None:
        raise HTTPException(501, "TTS backend not configured")
    text = body.get("text", "")
    voice_id = body.get("voice_id", "af_heart")
    speed = body.get("speed", 1.0)
    result = backend.synthesize(text, voice_id=voice_id, speed=speed)
    return Response(content=result.audio, media_type=f"audio/{result.format}")
```

Also register `tts_router` in `app.py` where speech_router is registered.

## Done when
`curl -X POST http://localhost:8000/v1/tts/synthesize -H "Content-Type: application/json" -d '{"text":"hello"}' --output t.wav && ffplay t.wav` produces audible speech.
