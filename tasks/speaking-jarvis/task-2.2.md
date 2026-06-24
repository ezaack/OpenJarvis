# 2.2 — Voice mode state machine

**Status**: ⬜ | **Deps**: 2.1 | **File**: `frontend/src/hooks/useSpeech.ts`

## Do
Extend `useSpeech` hook with voice mode:

```
States: idle → listening → transcribing → sending → playing → listening (loop)
         ↑                                                         |
         └─────────────── (stop / timeout / error) ←──────────────┘
```

Add:
- `voiceMode: boolean` — is hands-free mode active?
- `toggleVoiceMode()` — enter/exit voice mode
- `autoSubmit: (text: string) => Promise<string>` — callback to submit to chat, returns assistant reply text
- `playTTS: (text: string) => Promise<void>` — calls `synthesizeSpeech`, plays audio
- On recording stop: auto-transcribe → call `autoSubmit` → call `playTTS` → restart recording
- `abort()` — stop recording + playback, reset to idle

Return from hook: `{ voiceMode, toggleVoiceMode, abort, state, error }`

## Done when
Hook exports voice mode API — actual integration tested in task 3.4.
