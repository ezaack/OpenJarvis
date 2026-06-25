# 1.6 — Remove `kokoro_tts.py`

**Status**: ⬜ | **Deps**: 1.5 | **Agent**: any

## Do
Delete `src/openjarvis/speech/kokoro_tts.py`.

## Done when
- File no longer exists
- No imports reference it (verified via grep: `kokoro_tts` yields no results outside uv.lock/tasks)
