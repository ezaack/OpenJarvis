# 3.3 — Interrupt TTS on new recording

**Status**: ⬜ | **Deps**: 3.1 | **File**: `frontend/src/hooks/useSpeech.ts`

## Do
- Track currently playing Audio element in a ref.
- When `startRecording()` is called, if audio is playing: `audio.pause(); audio.currentTime = 0;` and revoke blob URL.
- This allows natural conversation: speak over Jarvis to interrupt.

## Done when
Starting a new recording while TTS is playing stops the audio immediately.
