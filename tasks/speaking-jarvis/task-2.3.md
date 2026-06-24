# 2.3 — Ctrl+Space shortcut

**Status**: ⬜ | **Deps**: 2.2 | **File**: `frontend/src/hooks/useSpeech.ts` or new hook

## Do
Add `useEffect` in the speech hook that listens for Ctrl+Space (or Cmd+Space on Mac):
```ts
useEffect(() => {
  const handler = (e: KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.code === 'Space') {
      e.preventDefault();
      toggleVoiceMode();
    }
  };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}, [toggleVoiceMode]);
```

## Done when
Ctrl+Space toggles voice mode on/off in the browser.
