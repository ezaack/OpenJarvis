# 2.1 — Streaming TTS endpoint (deferred)

**Status**: ⬜ | **Deps**: 1.7 | **Agent**: any

## Do
Add `POST /v1/tts/synthesize/stream` in `src/openjarvis/server/api_routes.py`:

- Uses `StreamingResponse` with `text/event-stream`
- Iterates `backend.synthesize_stream(text)` (new method on `PiperTTSBackend`)
- Yields `data: <base64 int16_bytes>\n\n` per sentence chunk
- First event includes `sample_rate`, `sample_width`, `sample_channels` as JSON

Add `synthesize_stream()` to `PiperTTSBackend`:
```python
def synthesize_stream(self, text, *, voice_id, speed):
    syn_config = SynthesisConfig(length_scale=1.0/max(speed,0.1))
    for chunk in self._voice.synthesize(text, syn_config):
        yield chunk.audio_int16_bytes
```

## Done when
- `curl /v1/tts/synthesize/stream` returns SSE stream
- Each event contains valid int16 PCM chunk
