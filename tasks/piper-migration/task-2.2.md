# 2.2 — Frontend progressive playback (deferred)

**Status**: ⬜ | **Deps**: 2.1 | **Agent**: any

## Do
1. Add `synthesizeSpeechStream()` to `frontend/src/lib/api.ts`:
   - Fetches `POST /v1/tts/synthesize/stream` (SSE)
   - Returns `AsyncGenerator<AudioChunk>` with `sample_rate`, `bytes`

2. Update `useSpeech.ts` `playTTS()`:
   - Use `new AudioContext()` + buffer scheduling
   - First chunk sets sample rate, creates `AudioBufferSourceNode`
   - Append subsequent chunks to a play queue
   - Start playback immediately after first chunk arrives

## Done when
- First sentence audio plays within ~200ms of TTS request
- Remaining sentences play seamlessly
