# 1.5 — Update TTS tests

**Status**: ⬜ | **Deps**: 1.2 | **Agent**: any

## Do
In `tests/speech/test_tts_backends.py`, replace the two kokoro tests with piper equivalents:

### Replace `test_kokoro_registered` → `test_piper_registered`
```python
def test_piper_registered():
    from openjarvis.speech.piper_tts import PiperTTSBackend
    TTSRegistry.register_value("piper", PiperTTSBackend)
    assert TTSRegistry.contains("piper")
```

### Replace `test_kokoro_health_false_without_package` → `test_piper_health_false_without_model`
```python
def test_piper_health_false_without_model():
    from openjarvis.speech.piper_tts import PiperTTSBackend
    backend = PiperTTSBackend()
    assert backend.health() is False
```

### Add `test_piper_synthesize` (mocked)
```python
def test_piper_synthesize():
    from openjarvis.speech.piper_tts import PiperTTSBackend
    backend = PiperTTSBackend()
    # Mock voice.synthesize to return a single AudioChunk with silence
    fake_chunk = MagicMock()
    fake_chunk.audio_int16_bytes = bytes(44100)  # 1s silence @ 22050Hz
    fake_chunk.sample_rate = 22050
    fake_chunk.sample_width = 2
    fake_chunk.sample_channels = 1
    backend._voice = MagicMock()
    backend._voice.config.sample_rate = 22050
    backend._voice.synthesize.return_value = [fake_chunk]
    result = backend.synthesize("Hello", voice_id="test", output_format="wav")
    assert result.audio  # non-empty WAV bytes
    assert result.format == "wav"
```

## Done when
- `pytest tests/speech/test_tts_backends.py -v` passes all TTS tests
- No kokoro references remain in test file
