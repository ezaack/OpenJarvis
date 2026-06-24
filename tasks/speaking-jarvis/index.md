# Speaking Jarvis — Task Index

Status: ⬜ not-started | 🔵 in-progress | ✅ done | ❌ blocked

## Phase 1: Server TTS

| # | Task | Status | Deps |
|---|------|--------|------|
| 1.1 | Add kokoro to speech extra + install | ⬜ | — |
| 1.2 | Add `get_tts_backend()` to `_discovery.py` | ⬜ | 1.1 |
| 1.3 | Add `POST /v1/tts/synthesize` route | ⬜ | 1.2 |
| 1.4 | Wire TTS into `cli/serve.py` | ⬜ | 1.2 |

## Phase 2: Frontend Voice Mode

| # | Task | Status | Deps |
|---|------|--------|------|
| 2.1 | Add `synthesizeSpeech()` to `api.ts` | ⬜ | 1.3 |
| 2.2 | Extend `useSpeech.ts` with voice mode state machine | ⬜ | 2.1 |
| 2.3 | Add Ctrl+Space keyboard shortcut | ⬜ | 2.2 |
| 2.4 | Add voice mode UI indicator | ⬜ | 2.2 |

## Phase 3: TTS Playback + Loop

| # | Task | Status | Deps |
|---|------|--------|------|
| 3.1 | Auto-play TTS for assistant msgs in voice mode | ⬜ | 2.2 |
| 3.2 | Speaker replay button on msgs | ⬜ | 3.1 |
| 3.3 | Interrupt TTS on new recording | ⬜ | 3.1 |
| 3.4 | End-to-end test: Ctrl+Space → speak → reply → loop | ⬜ | 3.3 |

## Progress Log

<!-- Append entries: [YYYY-MM-DD HH:MM] <task#> — <note> -->
