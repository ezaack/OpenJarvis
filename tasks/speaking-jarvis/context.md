# Speaking Jarvis — Shared Context

## Decisions
- **Wake word**: ACTIVE. Use a wake word (e.g. "Hey Ada") to trigger listening. Continuous local audio monitoring detects the wake word and starts recording. Keyboard shortcut (Ctrl+Space) remains as a secondary toggle.
- **TTS backend**: Kokoro (local, open-source, no API key).
- **No streaming TTS**: Generate full audio before playback (Kokoro limitation).
- **Auto-send**: After recording stops, auto-transcribe → auto-submit to chat.

## Key Files
| File | Role |
|------|------|
| `src/openjarvis/server/api_routes.py` | TTS route `POST /v1/tts/synthesize` |
| `src/openjarvis/speech/_discovery.py` | `get_tts_backend()` discovery |
| `src/openjarvis/cli/serve.py` | Wire TTS backend (~L464, next to speech) |
| `src/openjarvis/speech/kokoro_tts.py` | Existing Kokoro backend |
| `src/openjarvis/speech/tts.py` | TTSBackend ABC, TTSResult |
| `frontend/src/hooks/useSpeech.ts` | Voice mode state, auto-send, TTS loop |
| `frontend/src/lib/api.ts` | `synthesizeSpeech()` client |
| `frontend/src/components/` | Voice mode UI indicator |
| `src/pyproject.toml` | Add `kokoro` to `speech` extra |

## Conventions
- Follow existing patterns in `_discovery.py` for TTS (mirror speech discovery).
- Follow existing route patterns in `api_routes.py` (see `/v1/speech/transcribe` for reference).
- TTS route returns `Response(content=audio_bytes, media_type="audio/wav")`.
- Frontend: use `new Audio(URL.createObjectURL(blob)).play()` for TTS playback.

## Server Status
- Running at `http://127.0.0.1:8000`
- STT: faster-whisper ✓
- Engine: ollama / gemma3:4b
- Speech extra installed (faster-whisper + deps)

## Frontend Status
- Running at `http://localhost:5173`
- `VITE_SUPABASE_ANON_KEY` error fixed (made optional in supabase.ts)
- `faster_whisper.py` tempfile fix applied (delete=False for Windows)
