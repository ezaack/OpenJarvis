# 3.2 — Speaker replay button

**Status**: ⬜ | **Deps**: 3.1 | **File**: Chat message component

## Do
Add a small speaker icon button next to each assistant message.
- On click: fetch TTS audio for that message text and play it.
- Show loading spinner while fetching/playing.
- Reuse `synthesizeSpeech()` from api.ts.

## Done when
Clicking speaker icon on any assistant message plays its TTS audio.
