# 3.1 — Auto-play TTS in voice mode

**Status**: ⬜ | **Deps**: 2.2 | **File**: Chat component (find msg rendering) + useSpeech hook

## Do
- When an assistant message arrives AND `voiceMode === true`, call `playTTS(messageText)`.
- Ensure playback doesn't overlap — queue if already playing.
- Use `new Audio(URL.createObjectURL(blob))` for playback.
- Handle browser autoplay policy: first user gesture (Ctrl+Space) unlocks audio context.

## Done when
Speaking a message and getting TTS reply that plays automatically.
