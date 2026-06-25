# 1.3 — Add `wakeword` section to `SpeechConfig`

**Status**: ⬜ | **Deps**: none | **File**: `src/openjarvis/core/config.py`

## Do
Add a `WakeWordConfig` dataclass and a `wakeword` field to `SpeechConfig`.

1. Add this dataclass near `SpeechConfig` (~L1432):

```python
@dataclass(slots=True)
class WakeWordConfig:
    """Wake word detection settings."""

    enabled: bool = False
    backend: str = "openwakeword"   # "openwakeword", "none"
    model: str = "hey_jarvis"       # model stem name
    threshold: float = 0.5          # detection threshold 0.0–1.0
    vad_threshold: float = 0.0      # 0.0 = disabled; 0.0–1.0 enables Silero VAD
```

2. Add `wakeword: WakeWordConfig = field(default_factory=WakeWordConfig)` to `SpeechConfig`:

```python
@dataclass(slots=True)
class SpeechConfig:
    """Speech-to-text settings."""

    backend: str = "auto"
    model: str = "base"
    language: str = ""
    device: str = "auto"
    compute_type: str = "float16"
    wakeword: WakeWordConfig = field(default_factory=WakeWordConfig)
```

3. Check `_parse_speech_section` in `load_config()` (or wherever TOML → dataclass mapping happens) to ensure `[speech.wakeword]` table values are read correctly. If the parser uses recursive dataclass population from nested TOML tables, it should work automatically. If not, add explicit mapping.

## Config TOML example

```toml
[speech]
backend = "faster-whisper"

[speech.wakeword]
enabled = true
backend = "openwakeword"
model = "hey_jarvis"
threshold = 0.5
vad_threshold = 0.3
```

## Done when
Config can be loaded with `[speech.wakeword]` section and `config.speech.wakeword.enabled == True`.
