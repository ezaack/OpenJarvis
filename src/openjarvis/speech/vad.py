"""Silero VAD wrapper — voice activity detection using the Silero model.

Extracted from the old openwakeword.py to be shared between voice_loop.py
and any other module that needs speech/non-speech classification.
"""

from __future__ import annotations

import logging
import struct
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
VAD_FRAME_MS = 30
VAD_FRAME_SIZE = int(SAMPLE_RATE * VAD_FRAME_MS / 1000)  # 480 samples


def pcm16_to_float32(audio_bytes: bytes) -> Optional[np.ndarray]:
    """Convert raw 16-bit PCM bytes to float32 numpy array (-1..1)."""
    count = len(audio_bytes) // 2
    raw = struct.unpack_from(f"<{count}h", audio_bytes, 0)
    return np.array(raw, dtype=np.float32) / 32768.0


class SileroVAD:
    """Thin wrapper around the Silero VAD model from openwakeword.

    Usage::

        vad = SileroVAD()
        prob = vad.predict(float32_audio)
        is_speech = prob > 0.5
    """

    def __init__(self) -> None:
        self._model: Optional["VAD"] = None  # type: ignore[name-defined]

    def _ensure(self):
        if self._model is not None:
            return self._model
        try:
            from openwakeword.vad import VAD as SileroVAD

            self._model = SileroVAD()
        except ImportError:
            raise ImportError(
                "Silero VAD requires the 'openwakeword' package. "
                "Install it with: uv sync --extra speech-openwakeword"
            ) from None
        return self._model

    def predict(self, audio: np.ndarray) -> float:
        """Run VAD on float32 audio and return speech probability (0–1)."""
        if len(audio) == 0:
            return 0.0
        model = self._ensure()
        try:
            int16_audio = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
            frame_size = VAD_FRAME_SIZE
            remainder = len(int16_audio) % frame_size
            if remainder:
                pad_len = frame_size - remainder
                int16_audio = np.pad(int16_audio, (0, pad_len))
            return float(model.predict(int16_audio))
        except Exception as exc:
            logger.debug("VAD prediction error: %s", exc)
            return 0.0

    def reset_states(self) -> None:
        """Reset VAD internal state (call between independent utterances)."""
        if self._model is not None:
            try:
                self._model.reset_states()
            except Exception:
                pass
