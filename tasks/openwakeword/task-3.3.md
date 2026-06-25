# 3.3 — Add wake word UI indicator (waiting for "Hey Ada")

**Status**: ⬜ | **Deps**: 3.2 | **File**: `frontend/src/components/Chat/InputArea.tsx`

## Do
Update the wake word indicator in `InputArea.tsx` to show the specific wake phrase being listened for.

### Changes in the wake word mode indicator (~L739–763)

Update the `isWaking` state text from generic `"Waiting for wake word..."` to `'Waiting for "Hey Ada"...'`:

```tsx
{isWaking && (
  <>
    Waiting for &ldquo;Hey Ada&rdquo; &middot;{' }
    <kbd className="font-mono" style={{ fontWeight: 600 }}>Ctrl+Space</kbd> to toggle
  </>
)}
```

### Wake word button tooltip (~L665)

Update the wake word toggle button title to be more specific:

```tsx
title={wakeMode ? 'Listening for "Hey Ada"' : 'Wake word: off'}
```

Optionally, pass the configured wake word phrase as a prop from the parent (or read from a hook) so it's not hardcoded.

## Done when
Wake mode indicator says `Waiting for "Hey Ada"...` instead of `Waiting for wake word...`.
