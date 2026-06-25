# Phase 1: Remove Old Wake Word Code

## Task 1.1 — Remove wake word routes from `api_routes.py`

**Files**: `src/src/openjarvis/server/api_routes.py`

Remove:
- `wakeword_router` definition (line ~969)
- `wakeword_health` endpoint (lines ~972-982)
- `wakeword_stream` WebSocket endpoint (lines ~998-1040)
- `app.include_router(wakeword_router)` line (~1165)

## Task 1.2 — Remove `wakeword_detector` from server app state

**Files**: `src/src/openjarvis/server/app.py`

Remove:
- `wakeword_detector=None` parameter from state/init
- `app.state.wakeword_detector = wakeword_detector` assignment
- Any wakeword detector creation/import code

## Task 1.3 — Remove `openwakeword` from speech module imports

**Files**: `src/src/openjarvis/speech/__init__.py`

Remove `"openwakeword"` from the STT backend import loop.

## Task 1.4 — Remove `get_wakeword_detector` from discovery

**Files**: `src/src/openjarvis/speech/_discovery.py`

Remove:
- `get_wakeword_detector()` function
- Any imports of `OpenWakeWordDetector`

## Task 1.5 — Delete `openwakeword.py`

**Files**: `src/src/openjarvis/speech/openwakeword.py`

Delete the entire file. The VAD logic will be recreated cleanly in new `vad.py`.
