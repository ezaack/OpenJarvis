# Phase 4: Verify

## Task 4.1 — Remove `test_wakeword.py`

**Files**: `test_wakeword.py` (workspace root)

Delete this file — it uses the old server WebSocket approach and direct openwakeword model calls.

## Task 4.2 — TypeScript Compilation Check

Run `npx tsc --noEmit` from `src/frontend/` and fix any type errors introduced by:
- Removing all chat components (ChatArea, InputArea, MicButton, etc.)
- Removing `useSpeech` hook
- Adding `ConfigPage` and `useVoiceStatus`

## Task 4.3 — Server Smoke Test

Run the server: `Push-Location "c:\Users\drm26\AppData\Local\OpenJarvis\src"; uv run python -m openjarvis.cli.serve --host 127.0.0.1 --port 8000`

Verify:
- Server starts without errors
- Voice loop starts and enters IDLE (check logs: "Voice loop: IDLE")
- STT, TTS, Ollama chat endpoints all work
- `/v1/voice/status` WebSocket is reachable
- Say "Hey Jarvis" — check logs for wake word detection, greeting response, TTS playback

## Task 4.4 — End-to-End Voice Test

1. Start server with voice enabled: `uv run python -m openjarvis.cli.serve`
2. Server enters IDLE — log confirms VAD is monitoring
3. Say "Hey Jarvis" → server detects wake word → Ollama responds → TTS plays greeting
4. Say "What time is it?" → server transcribes → Ollama responds → TTS plays reply
5. Stay silent 5s → server returns to IDLE
6. Say "Hey Jarvis" again → works again
7. Open `http://127.0.0.1:5173` → ConfigPage loads, shows voice status indicator
8. Voice status WS shows `{"state": "idle"}` / `{"state": "listening"}` correctly
9. Settings form works — changing STT/TTS/model persists correctly
