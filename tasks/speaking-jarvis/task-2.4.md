# 2.4 — Voice mode UI indicator

**Status**: ⬜ | **Deps**: 2.2 | **File**: `frontend/src/components/` (modify chat input area)

## Do
In the chat input component, when `voiceMode === true`:
- Show pulsing/animated mic icon (CSS animation: pulse + color shift)
- Show "Listening..." text below the input area
- Disable text input (or switch to voice-only)
- Show "Press Ctrl+Space to stop" hint

When `state === 'transcribing'`: show "Transcribing..."
When `state === 'playing'`: show "Speaking..."

## Done when
Visual feedback clearly indicates voice mode state in the UI.
