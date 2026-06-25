# 3.1 — Add WebSocket client helper to `api.ts`

**Status**: ⬜ | **Deps**: 2.1 | **File**: `frontend/src/lib/api.ts`

## Do
Add a function that creates a WebSocket connection for streaming microphone audio to the wake word detector.

```typescript
// ---------------------------------------------------------------------------
// Wake word detection (WebSocket streaming)
// ---------------------------------------------------------------------------

export type WakeWordEvent =
  | { event: 'wakeword'; keyword: string; confidence: number }
  | { event: 'error'; error: string };

export interface WakeWordStreamCallbacks {
  onWakeWord: (keyword: string, confidence: number) => void;
  onError: (error: string) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

/**
 * Open a WebSocket to stream 16kHz 16-bit PCM audio for wake word detection.
 * Returns a controller with `sendFrame()` and `close()` methods.
 */
export function createWakeWordStream(
  callbacks: WakeWordStreamCallbacks,
): { sendFrame: (data: ArrayBuffer) => boolean; close: () => void } {
  const ws = new WebSocket(
    `${getBase().replace(/^http/, 'ws')}/v1/speech/wakeword/stream`,
  );

  ws.binaryType = 'arraybuffer';

  ws.onopen = () => callbacks.onOpen?.();
  ws.onclose = () => callbacks.onClose?.();

  ws.onmessage = (event: MessageEvent) => {
    try {
      const msg: WakeWordEvent = JSON.parse(event.data as string);
      if (msg.event === 'wakeword') {
        callbacks.onWakeWord(msg.keyword, msg.confidence);
      } else if (msg.event === 'error') {
        callbacks.onError(msg.error);
      }
    } catch {
      callbacks.onError('Failed to parse wake word server message');
    }
  };

  ws.onerror = () => callbacks.onError('WebSocket connection failed');

  let closed = false;
  ws.onclose = () => { closed = true; };

  return {
    sendFrame(data: ArrayBuffer): boolean {
      if (closed || ws.readyState !== WebSocket.OPEN) return false;
      ws.send(data);
      return true;
    },
    close() {
      closed = true;
      ws.close();
    },
  };
}
```

## Done when
Calling `createWakeWordStream({ onWakeWord: (k, c) => console.log(k, c) })` from browser console connects to the server WebSocket.
