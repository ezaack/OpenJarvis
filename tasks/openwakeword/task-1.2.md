# 1.2 — Create `OpenWakeWordDetector` class

**Status**: ⬜ | **Deps**: 1.1 | **File**: `src/openjarvis/speech/openwakeword.py`

## Do
Create `src/openjarvis/speech/openwakeword.py` with:

```python
"""OpenWakeWord-based wake word detection backend."""
from __future__ import annotations

import logging
from typing import Optional

from openjarvis.core.registry import SpeechRegistry

try:
    import openwakeword
    from openwakeword.model import Model
except ImportError:
    Model = None  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)


@SpeechRegistry.register("openwakeword")
class OpenWakeWordDetector:
    """Wake word detection using OpenWakeWord (ONNX-based)."""

    backend_id = "openwakeword"

    def __init__(
        self,
        wakeword: str = "hey_jarvis",
        threshold: float = 0.5,
        vad_threshold: Optional[float] = None,
    ) -> None:
        self._wakeword = wakeword
        self._threshold = threshold
        self._vad_threshold = vad_threshold
        self._model: Optional[Model] = None
        self._last_error: Optional[str] = None

    def _ensure_model(self) -> Model:
        if self._model is None:
            if Model is None:
                raise ImportError(
                    "openwakeword is not installed. "
                    "Install with: uv sync --extra speech"
                )
            openwakeword.utils.download_models()
            kwargs = {"wakeword_models": [f"{self._wakeword}.onnx"]}
            if self._vad_threshold is not None:
                kwargs["vad_threshold"] = self._vad_threshold
            self._model = Model(**kwargs)
        return self._model

    def process_frame(self, audio_frame: bytes) -> tuple[bool, float]:
        """Process a 16kHz 16-bit PCM audio frame.

        Returns (detected: bool, confidence: float).
        Frame should be a multiple of 1280 samples (80ms).
        """
        try:
            model = self._ensure_model()
            prediction = model.predict(audio_frame)
            score = prediction.get(self._wakeword, 0.0)
            return score >= self._threshold, score
        except Exception as exc:
            self._last_error = str(exc)
            logger.debug("Wake word detection failed: %s", exc)
            return False, 0.0

    def health(self) -> bool:
        """Check if the model is loadable."""
        try:
            self._ensure_model()
            return True
        except Exception as exc:
            self._last_error = str(exc)
            return False

    def last_error(self) -> Optional[str]:
        return self._last_error
```

## Key details
- The `wakeword` param is the model stem name (e.g. `"hey_jarvis"` for `hey_jarvis.onnx`).
- `threshold` controls sensitivity (default 0.5, tune per environment).
- `vad_threshold` enables Silero VAD second-stage filter (optional, 0.0–1.0).
- `process_frame()` accepts raw 16kHz 16-bit PCM bytes.
- Uses `@SpeechRegistry.register("openwakeword")` for auto-discovery.

## Done when
`OpenWakeWordDetector().health()` returns `True` and `process_frame(silence)` returns `(False, < 0.5)`.
