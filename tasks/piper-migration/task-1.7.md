# 1.7 — End-to-end verification

**Status**: ⬜ | **Deps**: 1.6 | **Agent**: any

## Do
1. Start server: `jarvis serve --model gemma3:4b` — console shows `TTS: piper`
2. Test TTS endpoint:
   ```
   curl -X POST http://127.0.0.1:8000/v1/tts/synthesize \
     -H "Content-Type: application/json" \
     -d '{"text":"Hello world. This is a test."}' \
     --output test.wav
   ```
3. Verify `test.wav` is valid audio (playable, non-zero size)
4. Test voice mode: Ctrl+Space → speak → transcribe → LLM reply → TTS playback

## Done when
- Server shows `TTS: piper`
- `curl /v1/tts/synthesize` returns valid WAV
- Voice mode works end-to-end
