import { useState, useCallback, useRef, useEffect } from 'react';
import { transcribeAudio, fetchSpeechHealth, synthesizeSpeech } from '../lib/api';

export type SpeechState = 'idle' | 'waking' | 'recording' | 'transcribing' | 'sending' | 'playing';

const SILENCE_TIMEOUT_MS = 1500;
const SILENCE_THRESHOLD = 0.02;
const WAKE_SPEECH_MS = 600;   // how long speech must last before triggering wake
const WAKE_COOLDOWN_MS = 3000; // min time between wake-triggered conversations

export function useSpeech() {
  const [state, setState] = useState<SpeechState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [available, setAvailable] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  const [wakeMode, setWakeMode] = useState(false);
  const [level, setLevel] = useState(0);
  const voiceModeRef = useRef(false);
  const wakeModeRef = useRef(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const wakeSpeechTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wakeCooldownRef = useRef(false);
  const wakeStreamRef = useRef<MediaStream | null>(null);

  /** Callback: submit transcribed text to chat, returns assistant reply text. */
  const autoSubmitRef = useRef<((text: string) => Promise<string>) | null>(null);

  // Keep refs in sync with state for use in callbacks before re-render
  useEffect(() => {
    voiceModeRef.current = voiceMode;
  }, [voiceMode]);

  useEffect(() => {
    wakeModeRef.current = wakeMode;
  }, [wakeMode]);

  useEffect(() => {
    fetchSpeechHealth()
      .then((health) => setAvailable(health.available))
      .catch(() => setAvailable(false));
  }, []);

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
  }, []);

  const playTTS = useCallback(async (text: string): Promise<void> => {
    setState('playing');
    try {
      stopAudio();
      const blob = await synthesizeSpeech(text);
      const url = URL.createObjectURL(blob);
      audioUrlRef.current = url;
      const audio = new Audio(url);
      audioRef.current = audio;
      await new Promise<void>((resolve, reject) => {
        audio.onended = () => resolve();
        audio.onerror = () => reject(new Error('TTS playback failed'));
        audio.play().catch(reject);
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'TTS failed';
      setError(msg);
    } finally {
      if (state === 'playing') setState('idle');
    }
  }, [stopAudio]);

  /** Ref to avoid hoisting issues with startRecording. */
  const startRecordingRef = useRef<() => Promise<void>>(undefined);

  /** Start monitoring mic for wake word (speech-triggered activation). */
  const startWakeWatcher = useCallback(async () => {
    if (wakeStreamRef.current) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      wakeStreamRef.current = stream;

      const audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);

      const buffer = new Float32Array(analyser.fftSize);
      let speechStart: number | null = null;

      const poll = () => {
        if (!wakeModeRef.current) return;

        analyser.getFloatTimeDomainData(buffer);
        let sum = 0;
        for (let i = 0; i < buffer.length; i++) sum += buffer[i] * buffer[i];
        const rms = Math.sqrt(sum / buffer.length);

        const normalised = Math.min(rms / 0.5, 1);
        setLevel(normalised);

        if (rms >= SILENCE_THRESHOLD) {
          if (speechStart === null) {
            speechStart = Date.now();
          } else if (
            Date.now() - speechStart >= WAKE_SPEECH_MS &&
            !wakeCooldownRef.current &&
            !voiceModeRef.current
          ) {
            speechStart = null;
            wakeCooldownRef.current = true;
            setTimeout(() => { wakeCooldownRef.current = false; }, WAKE_COOLDOWN_MS);
            stopWakeWatcher();
            setState('idle');
            setVoiceMode(true);
            voiceModeRef.current = true;
            startRecordingRef.current?.();
            return;
          }
        } else {
          speechStart = null;
        }

        animFrameRef.current = requestAnimationFrame(poll);
      };
      poll();
    } catch {
      setWakeMode(false);
    }
  }, []);

  const stopWakeWatcher = useCallback(() => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    animFrameRef.current = null;
    if (wakeStreamRef.current) {
      wakeStreamRef.current.getTracks().forEach((t) => t.stop());
      wakeStreamRef.current = null;
    }
    setLevel(0);
  }, []);

  const startSilenceDetection = useCallback((stream: MediaStream) => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);

    const audioCtx = new AudioContext();
    const source = audioCtx.createMediaStreamSource(stream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    analyserRef.current = analyser;
    const buffer = new Float32Array(analyser.fftSize);

    const detect = () => {
      analyser.getFloatTimeDomainData(buffer);
      let sum = 0;
      for (let i = 0; i < buffer.length; i++) sum += buffer[i] * buffer[i];
      const rms = Math.sqrt(sum / buffer.length);

      // Normalise for UI feedback (clamp 0-1)
      const normalised = Math.min(rms / 0.5, 1);
      setLevel(normalised);

      if (rms < SILENCE_THRESHOLD) {
        if (!silenceTimerRef.current) {
          silenceTimerRef.current = setTimeout(() => {
            runVoiceLoopRef.current?.();
          }, SILENCE_TIMEOUT_MS);
        }
      } else {
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
      }
      animFrameRef.current = requestAnimationFrame(detect);
    };
    detect();
  }, []);

  const stopSilenceDetection = useCallback(() => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    animFrameRef.current = null;
    silenceTimerRef.current = null;
    analyserRef.current = null;
    setLevel(0);
  }, []);

  const startRecording = useCallback(async (): Promise<void> => {
    stopAudio();
    setError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Microphone not supported in this browser');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setState('recording');
      if (voiceModeRef.current) startSilenceDetection(stream);
    } catch (err) {
      setError('Microphone access denied');
      setState('idle');
    }
  }, [stopAudio, startSilenceDetection]);

  // Keep ref in sync for wake watcher
  startRecordingRef.current = startRecording;

  const stopRecording = useCallback(async (): Promise<string> => {
    return new Promise((resolve, reject) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state !== 'recording') {
        reject(new Error('Not recording'));
        return;
      }
      stopSilenceDetection();

      recorder.onstop = async () => {
        setState('transcribing');
        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        chunksRef.current = [];
        try {
          const result = await transcribeAudio(blob);
          setState('idle');
          resolve(result.text);
        } catch (err) {
          setState('idle');
          const msg = err instanceof Error ? err.message : 'Transcription failed';
          setError(msg);
          reject(err);
        }
      };
      recorder.stop();
    });
  }, [stopSilenceDetection]);

  const runVoiceLoopRef = useRef<(() => Promise<void>) | null>(null);

  const runVoiceLoop = useCallback(async () => {
    if (!voiceModeRef.current) return;
    try {
      const text = await stopRecording();
      if (!text) {
        if (voiceModeRef.current) startRecording();
        else if (wakeModeRef.current) startWakeWatcher();
        return;
      }
      setState('sending');
      const submit = autoSubmitRef.current;
      if (submit) {
        const reply = await submit(text);
        if (voiceModeRef.current && reply) {
          await playTTS(reply);
          if (voiceModeRef.current) startRecording();
          else if (wakeModeRef.current) startWakeWatcher();
        }
      }
    } catch {
      if (voiceModeRef.current) startRecording();
      else if (wakeModeRef.current) startWakeWatcher();
    }
  }, [stopRecording, startRecording, playTTS, startWakeWatcher]);

  runVoiceLoopRef.current = runVoiceLoop;

  const toggleVoiceMode = useCallback(() => {
    setVoiceMode((prev) => {
      if (prev) {
        const recorder = mediaRecorderRef.current;
        if (recorder && recorder.state === 'recording') recorder.stop();
        stopAudio();
        setState(wakeModeRef.current ? 'waking' : 'idle');
        if (wakeModeRef.current) startWakeWatcher();
        return false;
      } else {
        if (wakeModeRef.current) stopWakeWatcher();
        startRecording();
        return true;
      }
    });
  }, [startRecording, stopAudio, startWakeWatcher, stopWakeWatcher]);

  const toggleWakeMode = useCallback(() => {
    setWakeMode((prev) => {
      if (prev) {
        stopWakeWatcher();
        if (voiceModeRef.current) {
          const recorder = mediaRecorderRef.current;
          if (recorder && recorder.state === 'recording') recorder.stop();
          stopAudio();
          setState('idle');
          voiceModeRef.current = false;
        }
        return false;
      } else {
        startWakeWatcher();
        setState('waking');
        return true;
      }
    });
  }, [startWakeWatcher, stopWakeWatcher, stopAudio]);

  const abort = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state === 'recording') recorder.stop();
    stopAudio();
    stopWakeWatcher();
    setVoiceMode(false);
    setWakeMode(false);
    setState('idle');
  }, [stopAudio, stopWakeWatcher]);

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

  return {
    state,
    error,
    available,
    voiceMode,
    wakeMode,
    level,
    startRecording,
    stopRecording,
    runVoiceLoop,
    toggleVoiceMode,
    toggleWakeMode,
    abort,
    playTTS,
    stopAudio,
    autoSubmitRef,
    isRecording: state === 'recording',
    isTranscribing: state === 'transcribing',
    isPlaying: state === 'playing',
    isSending: state === 'sending',
    isWaking: state === 'waking',
  };
}
