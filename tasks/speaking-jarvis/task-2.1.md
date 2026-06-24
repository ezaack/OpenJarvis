# 2.1 — TTS client in api.ts

**Status**: ⬜ | **Deps**: 1.3 | **File**: `frontend/src/lib/api.ts`

## Do
Add function at end of api.ts:
```ts
export async function synthesizeSpeech(text: string, voiceId = 'af_heart', speed = 1.0): Promise<Blob> {
  const res = await fetch(`${getBase()}/v1/tts/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice_id: voiceId, speed }),
  });
  if (!res.ok) throw new Error('TTS failed');
  return res.blob();
}
```

## Done when
Can call `synthesizeSpeech("hello")` from browser console and get a playable audio blob.
