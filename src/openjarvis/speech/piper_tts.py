"""Piper TTS backend — fast local ONNX text-to-speech.

Runs entirely offline with no API key. Voice model is auto-downloaded
on first use via ``piper.download_voices``.

Requires: pip install piper-tts
"""

from __future__ import annotations

import io
import tempfile
import wave
from pathlib import Path
from typing import List

import numpy as np

from openjarvis.core.registry import TTSRegistry
from openjarvis.speech.tts import TTSBackend, TTSResult

_DEFAULT_VOICE = "en_US-lessac-medium"
_VOICES_DIR = Path(tempfile.gettempdir()) / "piper-voices"


def _ensure_voice(voice_id: str) -> Path:
    """Download voice model if not already cached, return model path."""
    from piper.download_voices import download_voice

    _VOICES_DIR.mkdir(parents=True, exist_ok=True)
    download_voice(voice_id, download_dir=_VOICES_DIR)
    return _VOICES_DIR / f"{voice_id}.onnx"


@TTSRegistry.register("piper")
class PiperTTSBackend(TTSBackend):
    """Piper TTS — fast local ONNX voice synthesis."""

    backend_id = "piper"

    def __init__(self, *, voice_id: str = "", use_cuda: bool = False) -> None:
        self._voice_id = voice_id or _DEFAULT_VOICE
        self._use_cuda = use_cuda
        self._voice: object | None = None

    def _ensure_loaded(self) -> None:
        if self._voice is not None:
            return
        try:
            from piper import PiperVoice

            model_path = _ensure_voice(self._voice_id)
            self._voice = PiperVoice.load(
                str(model_path),
                use_cuda=self._use_cuda,
                download_dir=_VOICES_DIR,
            )
        except ImportError:
            raise RuntimeError(
                "piper-tts package not installed. Install with: pip install piper-tts"
            )

    def synthesize(
        self,
        text: str,
        *,
        voice_id: str = "",
        speed: float = 1.0,
        output_format: str = "wav",
    ) -> TTSResult:
        self._ensure_loaded()
        from piper import SynthesisConfig

        vid = voice_id or self._voice_id

        # Speed → length_scale (inverse relationship)
        length_scale = 1.0 / max(speed, 0.1)

        syn_config = SynthesisConfig(length_scale=length_scale, noise_scale=0.667)
        voice = self._voice

        if output_format == "wav":
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wav_file:
                voice.synthesize_wav(text, wav_file, syn_config=syn_config)
            buf.seek(0)
            audio_bytes = buf.read()
            # Get sample rate from the WAV header
            with wave.open(io.BytesIO(audio_bytes), "rb") as wav_read:
                sample_rate = wav_read.getframerate()
                duration = wav_read.getnframes() / sample_rate
        else:
            samples: list[np.ndarray] = []
            sample_rate = 22050
            for chunk in voice.synthesize(text, syn_config):
                samples.append(chunk.audio_float_array)
                sample_rate = chunk.sample_rate

            if not samples:
                return TTSResult(audio=b"", format=output_format, voice_id=vid)

            combined = np.concatenate(samples)
            # Raw PCM16 for non-WAV (streaming-ready)
            audio_bytes = (combined * 32767).astype(np.int16).tobytes()
            duration = len(combined) / sample_rate

        return TTSResult(
            audio=audio_bytes,
            format=output_format,
            voice_id=vid,
            sample_rate=sample_rate,
            duration_seconds=duration,
            metadata={"backend": "piper", "voice": vid},
        )

    def available_voices(self) -> List[str]:
        return [
            "en_US-lessac-medium",
            "en_US-lessac-low",
            "en_GB-alan-medium",
            "en_GB-semaine-medium",
        ]

    def health(self) -> bool:
        try:
            self._ensure_loaded()
            return True
        except (RuntimeError, ImportError, OSError, ValueError):
            return False
