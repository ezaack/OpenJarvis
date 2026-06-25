# Phase 2: Simplify Frontend to Config-Only Page

## Task 2.1 — Remove wake word types and functions from `api.ts`

**Files**: `src/frontend/src/lib/api.ts`

Remove:
- `connectWakeWordStream()` function
- `fetchWakeWordHealth()` function
- `WakeWordHealth` interface
- `WakeWordDetectionEvent` interface
- `WakeWordEvent` type
- All chat-related API functions (chat streaming, message sending) — server handles voice internally

Add:
- `connectVoiceStatus()` — WebSocket connection to new `/v1/voice/status` endpoint
- `VoiceStatusEvent` type: `{ state: 'idle' | 'greeting' | 'listening', ... }`
- `startVoice()` / `stopVoice()` — REST calls to start/stop the server voice loop

## Task 2.2 — Delete all chat components and audio hooks

**Files to delete**:
- `src/frontend/src/hooks/usespeech.ts`
- `src/frontend/src/components/Chat/ChatArea.tsx`
- `src/frontend/src/components/Chat/InputArea.tsx`
- `src/frontend/src/components/Chat/MicButton.tsx`
- `src/frontend/src/components/Chat/` — entire directory (MessageBubble, etc.)
- Any other chat-related components

## Task 2.3 — Create `ConfigPage` component

**Files**: `src/frontend/src/components/ConfigPage.tsx` (new)

Single-page configuration UI:
```tsx
export function ConfigPage() {
  // Voice status from WebSocket
  const { voiceState, level } = useVoiceStatus();

  return (
    <div>
      {/* Voice status indicator */}
      <VoiceStatusIndicator state={voiceState} level={level} />

      {/* Start/Stop button */}
      <button onClick={voiceState === 'idle' ? startVoice : stopVoice}>
        {voiceState === 'idle' ? 'Start Voice' : 'Stop Voice'}
      </button>

      {/* Settings form */}
      <SettingsForm />
    </div>
  );
}
```

`SettingsForm` includes:
- STT backend selector (faster-whisper / openai / deepgram)
- TTS backend selector (piper / cartesia / openai_tts)
- Model selector
- Voice ID input
- Speed slider
- Saves via existing config API endpoints

## Task 2.4 — Create `useVoiceStatus` hook

**Files**: `src/frontend/src/hooks/useVoiceStatus.ts` (new)

Lightweight hook — no audio processing at all:
```typescript
export function useVoiceStatus() {
  // Connects to /v1/voice/status WebSocket
  // Listens for { type: "state", state: "idle"|"greeting"|"listening" }
  // Exposes: { voiceState, level, lastTranscript, lastReply }
}
```

## Task 2.5 — Update `App.tsx`

**Files**: `src/frontend/src/App.tsx`

- Remove all chat-related imports and routes
- Render `<ConfigPage />` as the main (only) view
- Remove model selector, conversation list, chat history
- Keep the app shell (header, theme, etc.)
