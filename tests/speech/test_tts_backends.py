"""Tests for TTS backend infrastructure."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from openjarvis.core.registry import TTSRegistry
from openjarvis.speech.tts import TTSResult

# ---------------------------------------------------------------------------
# TTSResult tests
# ---------------------------------------------------------------------------


def test_tts_result_dataclass():
    result = TTSResult(
        audio=b"fake-audio-bytes",
        format="mp3",
        duration_seconds=3.5,
        voice_id="jarvis-v1",
    )
    assert result.audio == b"fake-audio-bytes"
    assert result.format == "mp3"
    assert result.duration_seconds == 3.5


def test_tts_result_save(tmp_path):
    result = TTSResult(audio=b"fake-mp3-data", format="mp3")
    out = result.save(tmp_path / "test.mp3")
    assert out.exists()
    assert out.read_bytes() == b"fake-mp3-data"


# ---------------------------------------------------------------------------
# Cartesia backend tests
# ---------------------------------------------------------------------------


def test_cartesia_registered():
    from openjarvis.speech.cartesia_tts import CartesiaTTSBackend

    TTSRegistry.register_value("cartesia", CartesiaTTSBackend)
    assert TTSRegistry.contains("cartesia")


def test_cartesia_synthesize():
    from openjarvis.speech.cartesia_tts import CartesiaTTSBackend

    backend = CartesiaTTSBackend(api_key="fake-key")

    with patch(
        "openjarvis.speech.cartesia_tts._cartesia_synthesize",
        return_value=b"fake-audio-mp3-bytes",
    ):
        result = backend.synthesize("Hello world", voice_id="test-voice")

    assert result.audio == b"fake-audio-mp3-bytes"
    assert result.format == "mp3"
    assert result.voice_id == "test-voice"


# ---------------------------------------------------------------------------
# Piper backend tests
# ---------------------------------------------------------------------------


def test_piper_registered():
    from openjarvis.speech.piper_tts import PiperTTSBackend

    TTSRegistry.register_value("piper", PiperTTSBackend)
    assert TTSRegistry.contains("piper")


def test_piper_health_mocked():
    from openjarvis.speech.piper_tts import PiperTTSBackend

    # Mock _ensure_voice (no download) and PiperVoice (no load)
    with patch("openjarvis.speech.piper_tts._ensure_voice") as mock_ev:
        mock_ev.return_value = "fake_model.onnx"
        with patch("piper.PiperVoice") as mock_pv_cls:
            mock_pv_cls.load.return_value = MagicMock()
            backend = PiperTTSBackend()
            assert backend.health() is True

    # Raise ImportError from the import inside _ensure_loaded
    original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

    def _mock_import(name, *args, **kwargs):
        if name == "piper":
            raise ImportError("No module named 'piper'")
        return original_import(name, *args, **kwargs)

    backend2 = PiperTTSBackend()
    backend2._voice = None
    with patch("builtins.__import__", side_effect=_mock_import):
        assert backend2.health() is False


# ---------------------------------------------------------------------------
# OpenAI TTS backend tests
# ---------------------------------------------------------------------------


def test_openai_tts_registered():
    from openjarvis.speech.openai_tts import OpenAITTSBackend

    TTSRegistry.register_value("openai_tts", OpenAITTSBackend)
    assert TTSRegistry.contains("openai_tts")


def test_openai_tts_synthesize():
    from openjarvis.speech.openai_tts import OpenAITTSBackend

    backend = OpenAITTSBackend(api_key="fake-key")

    with patch(
        "openjarvis.speech.openai_tts._openai_tts_request",
        return_value=b"fake-openai-audio",
    ):
        result = backend.synthesize("Hello", voice_id="nova")

    assert result.audio == b"fake-openai-audio"
    assert result.voice_id == "nova"
