# OpenWakeWord — Task Index

Status: ⬜ not-started | 🔵 in-progress | ✅ done | ❌ blocked

> Real "Hey Ada" wake word detection via OpenWakeWord (Python backend + WebSocket bridge).

## Phase 1: Python Backend — Wake Word Detector

| # | Task | Status | Deps |
|---|------|--------|------|
| 1.1 | Install openwakeword + onnxruntime | ⬜ | — |
| 1.2 | Create `OpenWakeWordDetector` class | ⬜ | 1.1 |
| 1.3 | Add `wakeword` section to `SpeechConfig` | ⬜ | — |
| 1.4 | Register detector in `speech/__init__.py` | ⬜ | 1.2 |

## Phase 2: Server — WebSocket Endpoint

| # | Task | Status | Deps |
|---|------|--------|------|
| 2.1 | Add WebSocket route `/v1/speech/wakeword/stream` | ⬜ | 1.2 |
| 2.2 | Wire wake word into `cli/serve.py` startup | ⬜ | 2.1, 1.3 |
| 2.3 | Add wake word health endpoint | ⬜ | 1.2 |

## Phase 3: Frontend — Real Wake Word

| # | Task | Status | Deps |
|---|------|--------|------|
| 3.1 | Add WebSocket client helper to `api.ts` | ⬜ | 2.1 |
| 3.2 | Replace energy VAD in `useSpeech.ts` with OpenWakeWord WS stream | ⬜ | 3.1 |
| 3.3 | Add wake word UI indicator (waiting for "Hey Ada") | ⬜ | 3.2 |
| 3.4 | End-to-end test: toggle wake word → say "Hey Ada" → transcribe → reply | ⬜ | 3.3 |

## Progress Log

<!-- Append entries: [YYYY-MM-DD HH:MM] <task#> — <note> -->
...l — Implemented all phases. Phase 1: added openwakeword+onnxruntime dep, created `OpenWakeWordDetector` class with `SpeechRegistry` registration, added `WakeWordConfig` to `SpeechConfig`. Phase 2: added WebSocket route `/v1/speech/wakeword/stream` + health endpoint, wired detector into `serve.py` and `create_app`. Phase 3: added `connectWakeWordStream` + `fetchWakeWordHealth` helpers to `api.ts`, replaced energy VAD in `useSpeech.ts` with OWW WebSocket stream (with legacy fallback), added "Say 'Hey Ada'" UI indicator in `InputArea.tsx`.
