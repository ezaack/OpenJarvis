"""Voice conversation loop — a clean state machine running entirely in Python.

States::

    IDLE → GREETING → LISTENING → IDLE (or loop)

- IDLE: pyaudio mic open, Silero VAD monitors. When speech detected → buffer
  audio → on silence (800ms) → transcribe via STT backend → if "hey jarvis"
  found → GREETING
- GREETING: Send prompt to Ollama → play TTS response as audio feedback →
  LISTENING
- LISTENING: Record via pyaudio → on silence (1.5s) → transcribe → send to
  Ollama → play TTS reply → loop. On extended silence (5s) → IDLE

Broadcasts state changes to frontend via a list of WebSocket callbacks.
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

from openjarvis.core.types import Message, Role
from openjarvis.speech._stubs import SpeechBackend, TranscriptionResult
from openjarvis.speech.tts import TTSBackend
from openjarvis.speech.vad import SileroVAD, pcm16_to_float32

# File logger for troubleshooting — writes to a rotating log in the config dir
_VOICE_LOG_PATH = None
try:
    from openjarvis.core.paths import get_config_dir
    _VOICE_LOG_PATH = str(get_config_dir() / "voice.log")
    _fh = logging.FileHandler(_VOICE_LOG_PATH, mode="a", encoding="utf-8")
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    _voice_logger = logging.getLogger(__name__)
    _voice_logger.setLevel(logging.DEBUG)      # Allow DEBUG+ through the logger
    _voice_logger.addHandler(_fh)
except Exception:
    pass

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CHUNK_SIZE = 1024  # pyaudio frames per buffer
SILENCE_BEFORE_TRANSCRIBE_MS = 800  # ms of silence before triggering transcription
LISTEN_SILENCE_TIMEOUT_MS = 1500  # ms of silence during LISTENING
EXTENDED_SILENCE_MS = 5000  # ms of extended silence → back to IDLE
SPEECH_MIN_DURATION_MS = 500  # minimum speech duration to transcribe
MAX_BUFFER_SECONDS = 10  # max audio buffer duration to prevent unbounded growth
GREETING_PROMPT = "The user just said 'Hey Jarvis' to wake you. Respond briefly with a greeting (one sentence)."

# Console status symbols
_CONSOLE_CLEAR = "\033[K"  # Clear to end of line (for overwriting status lines)
_STATUS_LABELS: dict[str, str] = {
    "idle":      "\U0001f3a4  Waiting for wake word\u2026",
    "greeting":  "\U0001f44b  Speaking greeting\u2026",
    "listening": "\U0001f399\ufe0f  Listening\u2026",
}
_SUB_LABELS: dict[str, str] = {
    "transcribing":     "\U0001f50d  Transcribing\u2026",
    "sending":          "\U0001f4e1  Sending to AI\u2026",
    "speaking":         "\U0001f399\ufe0f  Speaking\u2026",
    "wake_detected":    "\u2728  Wake word detected!",
    "idle_sub":         "\U0001f3a4  Waiting for wake word\u2026",
}
_CACHED_STATUS_LINE = ""


class VoiceState(str, Enum):
    IDLE = "idle"
    GREETING = "greeting"
    LISTENING = "listening"


class VoiceLoop:
    """Background voice conversation loop.

    Call ``start()`` to begin the loop in a background task. The loop runs
    continuously until ``stop()`` is called.

    Register a ``status_callback`` to receive state-change notifications
    (typically forwarded to a WebSocket).
    """

    def __init__(
        self,
        stt_backend: SpeechBackend,
        tts_backend: TTSBackend,
        engine: Any,  # The inference engine (for chat completions)
        model: str = "",
        *,
        wake_phrases: Optional[list[str]] = None,
        require_wake_word: bool = True,
        greeting_prompt: str = GREETING_PROMPT,
        system_prompt: str = "You are a helpful voice assistant. Keep responses brief and conversational.",
    ) -> None:
        self._stt = stt_backend
        self._tts = tts_backend
        self._engine = engine
        self._model = model
        self._require_wake_word = require_wake_word
        self._wake_phrases = wake_phrases or ["hey jarvis", "hey ada", "jarvis"]
        self._greeting_prompt = greeting_prompt
        self._system_prompt = system_prompt

        self._vad = SileroVAD()
        logger.info(
            "VoiceLoop initialized: stt=%s tts=%s model=%r wake=%s require_wake=%s log=%s",
            stt_backend.backend_id if stt_backend else "none",
            tts_backend.backend_id if tts_backend else "none",
            model,
            self._wake_phrases,
            self._require_wake_word,
            _VOICE_LOG_PATH or "(console only)",
        )
        self._state = VoiceState.IDLE
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Audio buffer for current utterance
        self._buffer: list[np.ndarray] = []
        self._speech_start: Optional[float] = None
        self._last_speech_time: Optional[float] = None

        # Adaptive noise floor tracking
        self._noise_floor: float = 0.001  # running estimate of ambient RMS (starts low)
        self._noise_samples: int = 0
        self._vad_threshold: float = 0.3  # VAD probability threshold

        # Registered callbacks (e.g. WebSocket connections)
        self._status_callbacks: list[Callable[[dict[str, Any]], None]] = []

        # pyaudio handle
        self._pyaudio: Any = None
        self._stream: Any = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> VoiceState:
        return self._state

    def add_status_callback(self, cb: Callable[[dict[str, Any]], None]) -> None:
        """Register a callback that receives state-change dicts.

        The dict has at least ``{"state": <str>}`` and may include
        extra fields like ``{"state": "listening", "silence_timeout_ms": 1500}``.
        """
        self._status_callbacks.append(cb)

    def remove_status_callback(self, cb: Callable[[dict[str, Any]], None]) -> None:
        if cb in self._status_callbacks:
            self._status_callbacks.remove(cb)

    async def start(self) -> None:
        """Start the voice loop in a background asyncio task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Voice loop started")

    async def stop(self) -> None:
        """Stop the voice loop and clean up resources."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._cleanup_audio()
        logger.info("Voice loop stopped")

    # ------------------------------------------------------------------
    # Console status display
    # ------------------------------------------------------------------

    @staticmethod
    def _write_status(label: str) -> None:
        """Write a status line to stderr, overwriting the previous one."""
        global _CACHED_STATUS_LINE
        if _CACHED_STATUS_LINE == label:
            return
        # Move to a new line first if there was any previous status
        if _CACHED_STATUS_LINE:
            print(file=sys.stderr, flush=True)
        _CACHED_STATUS_LINE = label
        print(f"\r{_CONSOLE_CLEAR}{label}", file=sys.stderr, end="", flush=True)

    @staticmethod
    def _write_sub_status(label: str) -> None:
        """Write a secondary status line (below the main one)."""
        global _CACHED_STATUS_LINE
        if not _CACHED_STATUS_LINE:
            return
        print(f"\r{_CONSOLE_CLEAR}  {label}", file=sys.stderr, end="", flush=True)

    @staticmethod
    def _write_done() -> None:
        """Finish the status line and move to next line."""
        global _CACHED_STATUS_LINE
        if _CACHED_STATUS_LINE:
            print(file=sys.stderr, flush=True)
            _CACHED_STATUS_LINE = ""

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def _set_state(self, new_state: VoiceState, **extra: Any) -> None:
        old = self._state
        self._state = new_state
        payload: dict[str, Any] = {"state": new_state.value}
        if new_state == VoiceState.IDLE:
            payload["silence_timeout_ms"] = SILENCE_BEFORE_TRANSCRIBE_MS
        elif new_state == VoiceState.LISTENING:
            payload["silence_timeout_ms"] = LISTEN_SILENCE_TIMEOUT_MS
        payload.update(extra)
        label = _STATUS_LABELS.get(new_state.value, new_state.value)
        self._write_status(label)
        logger.info("Voice state: %s -> %s%s", old.value, new_state.value,
                     f" ({extra})" if extra else "")
        for cb in self._status_callbacks:
            try:
                cb(payload)
            except Exception:
                logger.debug("Status callback failed", exc_info=True)

    # ------------------------------------------------------------------
    # Audio I/O
    # ------------------------------------------------------------------

    def _ensure_audio(self) -> None:
        """Open pyaudio stream if not already open."""
        if self._stream is not None:
            return
        import pyaudio

        self._pyaudio = pyaudio.PyAudio()
        # Log available input devices for debugging
        try:
            for i in range(self._pyaudio.get_device_count()):
                info = self._pyaudio.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    logger.info(
                        "Mic device [%d]: %s (channels=%d, rate=%.0f)",
                        i,
                        info.get("name", "unknown"),
                        info["maxInputChannels"],
                        info.get("defaultSampleRate", 0),
                    )
        except Exception:
            pass
        try:
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
            )
            logger.info(
                "Microphone opened: rate=%d channels=1 format=int16 bufsize=%d",
                int(self._stream._rate) if hasattr(self._stream, '_rate') else SAMPLE_RATE,
                CHUNK_SIZE,
            )
        except Exception as exc:
            logger.error("Failed to open microphone: %s", exc)
            raise

    def _cleanup_audio(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._pyaudio is not None:
            try:
                self._pyaudio.terminate()
            except Exception:
                pass
            self._pyaudio = None

    def _read_audio(self) -> Optional[np.ndarray]:
        """Read one chunk of audio from mic, return float32 or None."""
        try:
            self._ensure_audio()
            raw = self._stream.read(CHUNK_SIZE, exception_on_overflow=False)
            return pcm16_to_float32(raw)
        except Exception as exc:
            logger.debug("Audio read error: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Transcription helpers
    # ------------------------------------------------------------------

    def _concatenate_buffer(self) -> np.ndarray:
        return np.concatenate(self._buffer) if self._buffer else np.array([], dtype=np.float32)

    def _buffer_to_wav(self, audio: np.ndarray) -> bytes:
        """Convert float32 audio to WAV bytes for the STT backend."""
        import wave

        int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(int16.tobytes())
        return buf.getvalue()

    async def _transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio via the STT backend. Returns empty string on failure."""
        wav_bytes = self._buffer_to_wav(audio)
        try:
            loop = asyncio.get_event_loop()
            result: TranscriptionResult = await loop.run_in_executor(
                None, self._stt.transcribe, wav_bytes
            )
            return (result.text or "").strip()
        except Exception as exc:
            logger.debug("Transcription failed: %s", exc)
            return ""

    def _check_wake_phrase(self, text: str) -> bool:
        t = text.lower()
        for phrase in self._wake_phrases:
            if phrase in t:
                return True
        return False

    async def _llm_chat(self, text: str) -> str:
        """Send user text to the LLM and return the response text."""
        self._write_sub_status(_SUB_LABELS["sending"])
        try:
            messages = [
                Message(role=Role.SYSTEM, content=self._system_prompt),
                Message(role=Role.USER, content=text),
            ]
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._engine.generate(
                    messages=messages,
                    model=self._model or "",
                ),
            )
            content = ""
            if isinstance(result, dict):
                content = result.get("content", result.get("text", ""))
            elif hasattr(result, "content"):
                content = result.content
            return str(content).strip() if content else ""
        except Exception as exc:
            logger.debug("LLM chat failed: %s", exc)
            return "I'm sorry, I couldn't process that."

    async def _speak(self, text: str) -> None:
        """Synthesize text to speech and play through speakers."""
        if not text:
            logger.warning("_speak called with empty text, skipping")
            return
        if self._tts is None:
            logger.warning("TTS backend not available, skipping speech")
            return
        self._write_sub_status(_SUB_LABELS["speaking"])
        logger.info("TTS synthesizing %d chars: %r", len(text), text[:80])
        try:
            loop = asyncio.get_event_loop()
            tts_result = await loop.run_in_executor(
                None,
                lambda: self._tts.synthesize(text, output_format="wav"),
            )
            logger.info("TTS synthesized %d bytes (fmt=%s)", len(tts_result.audio), tts_result.format)
            # Play audio through pyaudio
            import pyaudio as pa

            wav_bytes = tts_result.audio

            # Parse WAV header to get playback parameters
            import wave

            with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                p = pa.PyAudio()
                out_stream = p.open(
                    format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                )
                data = wf.readframes(wf.getnframes())
                out_stream.write(data)
                out_stream.close()
            p.terminate()
        except Exception as exc:
            logger.debug("TTS playback failed: %s", exc)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def _run(self) -> None:
        """Main async loop — never returns until ``stop()`` is called."""
        print("\n[Voice Loop] Starting\u2026", file=sys.stderr, flush=True)
        global _CACHED_STATUS_LINE
        _CACHED_STATUS_LINE = ""
        self._set_state(VoiceState.IDLE)
        print("\n[Voice Loop] Current state: "f"{self._state.value}\n", file=sys.stderr, flush=True)
        consecutive_errors = 0

        while self._running:
            try:
                if self._state == VoiceState.IDLE:
                    await self._tick_idle()
                elif self._state == VoiceState.GREETING:
                    await self._tick_greeting()
                elif self._state == VoiceState.LISTENING:
                    await self._tick_listening()
                consecutive_errors = 0
            except asyncio.CancelledError:
                break
            except ImportError as exc:
                consecutive_errors += 1
                if consecutive_errors == 1:
                    logger.error("Voice loop missing dependency: %s", exc)
                if consecutive_errors >= 5:
                    logger.critical(
                        "Voice loop disabled: persistent ImportError after %d attempts. "
                        "Install missing dependencies and restart.",
                        consecutive_errors,
                    )
                    self._running = False
                    break
                await asyncio.sleep(1.0)
            except Exception:
                logger.exception("Voice loop tick error — resetting to IDLE")
                self._reset_buffer()
                self._set_state(VoiceState.IDLE)

            # Small sleep to prevent busy-waiting
            await asyncio.sleep(0.05)

        self._cleanup_audio()

    # ------------------------------------------------------------------
    # IDLE state
    # ------------------------------------------------------------------

    async def _tick_idle(self) -> None:
        """IDLE: Monitor mic via VAD. Buffer speech. On silence → transcribe → check wake phrase."""
        chunk = self._read_audio()
        if chunk is None:
            return

        now = time.time()
        rms = float(np.sqrt(np.mean(chunk ** 2))) if len(chunk) > 0 else 0.0

        # Adaptive noise floor: continuous running estimate of ambient RMS.
        # Only update during non-speech periods so we don't learn speech as noise.
        # Uses exponential moving average for smoothness.
        # Floor is clamped to a minimum of 1e-6 and a maximum of 0.005 to
        # prevent collapse to zero (impassable gate) and to prevent drift
        # too high in moderately noisy environments (which would gate out
        # quiet speech).
        if self._speech_start is None:
            if self._noise_samples < 20:
                self._noise_floor = 0.7 * self._noise_floor + 0.3 * rms
            else:
                self._noise_floor = 0.99 * self._noise_floor + 0.01 * rms
            self._noise_floor = np.clip(self._noise_floor, 1e-6, 0.005)
            self._noise_samples += 1

        # Dynamic noise gate: require RMS >= noise_floor * MIN_SIGNAL_RATIO
        MIN_SIGNAL_RATIO = 1.2
        threshold = self._noise_floor * MIN_SIGNAL_RATIO
        is_loud_enough = rms >= threshold

        # Skip VAD when audio is just ambient noise and we're not already tracking speech
        if not is_loud_enough and self._speech_start is None:
            logger.debug("Noise gate: rms=%.6f < threshold=%.6f (floor=%.6f)",
                         rms, threshold, self._noise_floor)
            # Print live RMS level every ~100 frames to diagnose mic issues
            if self._noise_samples % 100 == 0:
                print(f"\r  \U0001f399\ufe0f  Mic level: {rms:.6f}  (threshold: {threshold:.6f})  {_CONSOLE_CLEAR}",
                      file=sys.stderr, end="", flush=True)
            return

        if is_loud_enough:
            speech_prob = self._vad.predict(chunk)
        else:
            speech_prob = 0.0
        is_speech = speech_prob > self._vad_threshold and is_loud_enough
        logger.debug("VAD: prob=%.4f rms=%.5f floor=%.5f speech=%s buf=%d chunks",
                     speech_prob, rms, self._noise_floor, is_speech, len(self._buffer))

        # Only buffer when speech is active or within trailing-silence window.
        # This prevents unbounded growth during continuous silence (see #1).
        if is_speech or self._speech_start is not None:
            self._buffer.append(chunk)
            # Cap buffer to MAX_BUFFER_SECONDS — discard oldest chunks
            max_samples = SAMPLE_RATE * MAX_BUFFER_SECONDS
            total = sum(len(c) for c in self._buffer)
            while total > max_samples and self._buffer:
                dropped = self._buffer.pop(0)
                total -= len(dropped)
                logger.debug("Dropped %d samples from buffer (total=%d)", len(dropped), total)

        if is_speech:
            self._last_speech_time = now
            if self._speech_start is None:
                self._speech_start = now
                logger.info("Speech started (VAD=%.3f rms=%.5f floor=%.5f)", speech_prob, rms, self._noise_floor)

        # Extended silence reset (stale buffer)
        if (
            not is_speech
            and self._speech_start is not None
            and self._last_speech_time is not None
            and (now - self._last_speech_time) > 3.0
        ):
            logger.debug("Stale buffer reset after %.1fs silence", now - self._last_speech_time)
            self._reset_buffer()
            return

        # Speech ended → transcribe and check wake phrase
        if (
            self._speech_start is not None
            and self._last_speech_time is not None
            and (now - self._last_speech_time) > (SILENCE_BEFORE_TRANSCRIBE_MS / 1000)
        ):
            duration_ms = (now - self._speech_start) * 1000
            logger.debug("Speech ended: dur=%.0fms buffer=%d chunks", duration_ms, len(self._buffer))
            if duration_ms >= SPEECH_MIN_DURATION_MS:
                self._write_sub_status(_SUB_LABELS["transcribing"])
                audio = self._concatenate_buffer()
                self._reset_buffer()
                text = await self._transcribe(audio)
                self._write_status(_STATUS_LABELS["idle"])
                if text:
                    logger.info("IDLE transcribed: %r (dur=%.0fms)", text, duration_ms)
                    self._write_done()
                    print(f"  [YOU] {text}", file=sys.stderr, flush=True)
                    if not self._require_wake_word or self._check_wake_phrase(text):
                        if self._require_wake_word:
                            logger.info("Wake phrase DETECTED in: %r", text)
                            self._write_sub_status(_SUB_LABELS["wake_detected"])
                        else:
                            logger.info("Always-listen mode: transcribing and responding")
                        self._set_state(VoiceState.GREETING, detected=text)
                        return
                    else:
                        logger.debug("No wake phrase in: %r", text)
                else:
                    logger.debug("Empty transcription (dur=%.0fms)", duration_ms)
            else:
                logger.debug("Speech too short (%.0fms < %dms), discarding", duration_ms, SPEECH_MIN_DURATION_MS)
                self._reset_buffer()

        # Safety: force check on very long speech
        if (
            self._speech_start is not None
            and (now - self._speech_start) > 5.0
            and self._last_speech_time is not None
            and (now - self._last_speech_time) < 2.0
        ):
            logger.debug("Safety force-check after %.1fs of continuous speech", now - self._speech_start)
            self._write_sub_status(_SUB_LABELS["transcribing"])
            audio = self._concatenate_buffer()
            self._reset_buffer()
            text = await self._transcribe(audio)
            self._write_status(_STATUS_LABELS["idle"])
            if text:
                logger.info("Safety transcribe: %r", text[:120])
                self._write_done()
                print(f"  [YOU] {text}", file=sys.stderr, flush=True)
                if not self._require_wake_word or self._check_wake_phrase(text):
                    if self._require_wake_word:
                        logger.info("Wake phrase DETECTED via safety check: %r", text)
                        self._write_sub_status(_SUB_LABELS["wake_detected"])
                    else:
                        logger.info("Always-listen mode: transcribing and responding (safety)")
                    self._set_state(VoiceState.GREETING, detected=text)
            else:
                logger.debug("Safety transcribe: empty result")

    # ------------------------------------------------------------------
    # GREETING state
    # ------------------------------------------------------------------

    async def _tick_greeting(self) -> None:
        """GREETING: Send greeting prompt to LLM → play TTS → go to LISTENING."""
        self._set_state(VoiceState.GREETING)
        logger.info("GREETING: sending prompt to LLM")
        self._write_sub_status(_SUB_LABELS["sending"])
        reply = await self._llm_chat(self._greeting_prompt)
        logger.info("GREETING: LLM replied: %r", reply[:100] if reply else "(empty)")
        if reply:
            self._write_done()
            print(f"  [OLLAMA] {reply}", file=sys.stderr, flush=True)
            logger.info("GREETING: speaking TTS response")
            self._write_sub_status(_SUB_LABELS["speaking"])
            await self._speak(reply)
        else:
            logger.warning("GREETING: empty LLM reply, skipping TTS")
        self._set_state(VoiceState.LISTENING)

    # ------------------------------------------------------------------
    # LISTENING state
    # ------------------------------------------------------------------

    async def _tick_listening(self) -> None:
        """LISTENING: Record utterance → transcribe → LLM → TTS → loop/IDLE."""
        logger.info("LISTENING: starting listening loop")
        self._reset_buffer()
        utterance_audio: list[np.ndarray] = []
        last_speech: Optional[float] = None
        speech_start: Optional[float] = None
        utterance_start = time.time()
        transcribed_count = 0

        while self._running and self._state == VoiceState.LISTENING:
            chunk = self._read_audio()
            if chunk is None:
                await asyncio.sleep(0.05)
                continue

            utterance_audio.append(chunk)
            now = time.time()

            rms = float(np.sqrt(np.mean(chunk ** 2))) if len(chunk) > 0 else 0.0
            MIN_SIGNAL_RATIO = 1.2
            is_loud_enough = rms >= (self._noise_floor * MIN_SIGNAL_RATIO)
            if is_loud_enough:
                speech_prob = self._vad.predict(chunk)
            else:
                speech_prob = 0.0
            is_speech = speech_prob > self._vad_threshold and is_loud_enough
            logger.debug("LISTENING VAD: prob=%.4f rms=%.5f floor=%.5f speech=%s buf=%d chunks",
                         speech_prob, rms, self._noise_floor, is_speech, len(utterance_audio))

            if is_speech:
                last_speech = now
                if speech_start is None:
                    speech_start = now
                    logger.info("LISTENING: user started speaking")

            silence_duration = (now - last_speech) if last_speech is not None else 0.0

            # Extended silence → back to IDLE
            if last_speech is not None and silence_duration > (EXTENDED_SILENCE_MS / 1000):
                logger.info("LISTENING: extended silence (%.1fs), returning to IDLE", silence_duration)
                self._write_done()
                self._set_state(VoiceState.IDLE)
                return

            # Normal silence → transcribe and respond
            if (
                speech_start is not None
                and last_speech is not None
                and silence_duration > (LISTEN_SILENCE_TIMEOUT_MS / 1000)
            ):
                logger.info("LISTENING: silence timeout (%.1fs), transcribing %d chunks",
                            silence_duration, len(utterance_audio))
                self._write_sub_status(_SUB_LABELS["transcribing"])
                audio = np.concatenate(utterance_audio) if utterance_audio else np.array([], dtype=np.float32)
                text = await self._transcribe(audio)

                if not text:
                    logger.debug("LISTENING: empty transcription, continuing to listen")
                    self._write_status(_STATUS_LABELS["listening"])
                    # Empty transcription — keep listening
                    self._reset_buffer()
                    utterance_audio.clear()
                    last_speech = None
                    speech_start = None
                    utterance_start = time.time()
                    continue

                transcribed_count += 1
                logger.info("LISTENING transcribed: %r", text)
                self._write_done()
                print(f"  [YOU] {text}", file=sys.stderr, flush=True)
                self._write_sub_status(_SUB_LABELS["sending"])
                reply = await self._llm_chat(text)
                logger.info("LISTENING LLM reply: %r", reply[:100] if reply else "(empty)")
                if reply:
                    self._write_done()
                    print(f"  [OLLAMA] {reply}", file=sys.stderr, flush=True)
                    self._write_sub_status(_SUB_LABELS["speaking"])
                    await self._speak(reply)
                self._write_status(_STATUS_LABELS["listening"])

                # Reset for next utterance
                utterance_audio.clear()
                last_speech = None
                speech_start = None
                utterance_start = time.time()

            await asyncio.sleep(0.05)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _reset_buffer(self) -> None:
        self._buffer.clear()
        self._speech_start = None
        self._last_speech_time = None
