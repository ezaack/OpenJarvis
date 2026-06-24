# 3.4 — End-to-end voice conversation test

**Status**: ⬜ | **Deps**: 3.3 | **Manual test**

## Do
1. Start server: `jarvis serve --model gemma3:4b` (TTS: kokoro)
2. Start frontend: `npm run dev`
3. Open http://localhost:5173
4. Press Ctrl+Space → verify "Listening..." UI + mic starts
5. Speak a short sentence → verify auto-transcribe → auto-send to chat
6. Wait for response → verify TTS plays automatically
7. While TTS plays, press Ctrl+Space or click mic → verify interrupt + new recording starts
8. Press Ctrl+Space again → verify exit voice mode

## Done when
Full loop works: Ctrl+Space → speak → auto-send → TTS reply → loop, with interrupt support.
