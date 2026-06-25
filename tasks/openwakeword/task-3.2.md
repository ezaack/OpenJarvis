# 3.2 — Replace energy VAD in `useSpeech.ts` with OpenWakeWord WS stream

**Status**: ⬜ | **Deps**: 3.1 | **File**: `frontend/src/hooks/useSpeech.ts`

## Do
Replace the energy-based `startWakeWatcher()` with a real OpenWakeWord WebSocket streaming implementation.

### What to change

**Replace `startWakeWatcher()`** — instead of polling RMS energy, do:

```typescript
import { createWakeWordStream } from '../lib/api';

const wakeStreamRef = useRef<ReturnType<typeof createWakeWordStream> | null>(null);
const audioCtxRef = useRef<AudioContext | null>(null);
const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

const startWakeWatcher = useCallback(async () => {
  if (wakeStreamRef.current) return;
  if (wakeStreamRef.current) wakeStreamRef.current.close();

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    wakeStreamRef.current = stream;  // keep for cleanup

    // Create AudioContext at 16kHz for OpenWakeWord
    const audioCtx = new AudioContext({ sampleRate: 16000 });
    audioCtxRef.current = audioCtx;
    const source = audioCtx.createMediaStreamSource(stream);
    sourceRef.current = source;

    // Processor node: chunk audio into 80ms frames (1280 samples)
    const processor = audioCtx.createScriptProcessor(4096, 1, 1);
    const ws = createWakeWordStream({
      onWakeWord: (keyword, confidence) => {
        if (!wakeCooldownRef.current && !voiceModeRef.current) {
          wakeCooldownRef.current = true;
          setTimeout(() => { wakeCooldownRef.current = false; }, WAKE_COOLDOWN_MS);
          stopWakeWatcher();
          setState('idle');
          setVoiceMode(true);
          voiceModeRef.current = true;
          startRecordingRef.current?.();
        }
      },
      onError: (err) => {
        console.error('Wake word stream error:', err);
        setError(err);
      },
      onClose: () => {
        setLevel(0);
      },
    });

    wakeStreamRef.current = ws;  // store WS controller

    // Chunk mic audio into 80ms frames and send over WebSocket
    processor.onaudioprocess = (e) => {
      if (!wakeModeRef.current) return;
      const input = e.inputBuffer.getChannelData(0);  // Float32Array

      // Convert Float32 → Int16 (16-bit PCM)
      const pcm = new Int16Array(input.length);
      for (let i = 0; i < input.length; i++) {
        const s = Math.max(-1, Math.min(1, input[i]));
        pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }

      ws.sendFrame(pcm.buffer);

      // Update level meter for UI
      let sum = 0;
      for (let i = 0; i < input.length; i++) sum += input[i] * input[i];
      const rms = Math.sqrt(sum / input.length);
      setLevel(Math.min(rms / 0.5, 1));
    };

    source.connect(processor);
    processor.connect(audioCtx.destination);

  } catch {
    setWakeMode(false);
  }
}, []);
```

**Replace `stopWakeWatcher()`**:

```typescript
const stopWakeWatcher = useCallback(() => {
  wakeStreamRef.current?.close();
  wakeStreamRef.current = null;
  sourceRef.current?.disconnect();
  audioCtxRef.current?.close();
  audioCtxRef.current = null;
  if (wakeStreamRef.current) {  // legacy MediaStream ref
    (wakeStreamRef.current as any)?.getTracks?.()?.forEach?.((t: MediaStreamTrack) => t.stop());
  }
  setLevel(0);
}, []);
```

### Ref changes needed
- Remove `animFrameRef`, `wakeSpeechTimerRef` from wake watcher (energy VAD no longer needed for wake word).
- Keep `silenceTimerRef` and `animFrameRef` for the recording-phase silence detection (unchanged).
- Keep `WAKE_SPEECH_MS`, `SILENCE_THRESHOLD`, `SILENCE_TIMEOUT_MS` constants (silence detection still used during recording).
- The `wakeModeRef` and `wakeCooldownRef` logic stays the same.

## Done when
Enabling wake mode starts listening for "Hey Ada" specifically, not any sound. Saying "Hey Ada" triggers recording.
