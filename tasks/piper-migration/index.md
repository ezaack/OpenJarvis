# Piper TTS Migration — Task Index

Status: ⬜ not-started | 🔵 in-progress | ✅ done | ❌ blocked

## Phase 1: Backend

| # | Task | Status | Deps |
|---|------|--------|------|
| 1.1 | Update deps: kokoro → piper-tts | ⬜ | — |
| 1.2 | Create `piper_tts.py` backend | ⬜ | 1.1 |
| 1.3 | Update `__init__.py` + `_discovery.py` | ⬜ | 1.2 |
| 1.4 | Cleanup `serve.py` stale import | ⬜ | 1.3 |
| 1.5 | Update TTS tests | ⬜ | 1.2 |
| 1.6 | Remove `kokoro_tts.py` | ⬜ | 1.5 |
| 1.7 | End-to-end verification | ⬜ | 1.6 |

## Phase 2: Follow-up (deferred)

| # | Task | Status | Deps |
|---|------|--------|------|
| 2.1 | Streaming TTS endpoint | ⬜ | 1.7 |
| 2.2 | Frontend progressive playback | ⬜ | 2.1 |
