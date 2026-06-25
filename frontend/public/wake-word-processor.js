/**
 * AudioWorkletProcessor for wake-word detection.
 *
 * Captures raw PCM from the microphone, downsamples to 16 kHz,
 * converts to 16-bit signed integer (PCM16), and posts the buffer
 * to the main thread when enough samples have accumulated.
 *
 * OpenWakeWord / the server expects 16-bit PCM mono at 16 kHz with
 * chunks of ~20480 samples (1280 ms).
 */

const OWW_SAMPLE_RATE = 16000;
const CHUNK_DURATION_MS = 1280;
const TARGET_SAMPLES = Math.floor(OWW_SAMPLE_RATE * CHUNK_DURATION_MS / 1000); // 20480

class WakeWordProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    /** @type {number[]} */
    this._buffer = [];
    this._sampleRate = sampleRate; // provided by AudioWorklet global scope

    // Compute downsampling step: e.g. 48000/16000 = 3, 44100/16000 ≈ 3
    this._step = Math.max(1, Math.round(this._sampleRate / OWW_SAMPLE_RATE));
  }

  /**
   * @param {Float32Array[][]} inputs
   * @param {Float32Array[][]} outputs
   * @param {Record<string, Float32Array>} parameters
   * @returns {boolean}
   */
  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || !input[0] || input[0].length === 0) {
      return true; // keep alive
    }

    const channel = input[0];

    // Downsample and accumulate
    for (let i = 0; i < channel.length; i += this._step) {
      this._buffer.push(channel[i]);
    }

    // Emit chunks as they fill up
    while (this._buffer.length >= TARGET_SAMPLES) {
      const chunk = this._buffer.splice(0, TARGET_SAMPLES);
      const pcm16 = new Int16Array(chunk.length);
      for (let i = 0; i < chunk.length; i++) {
        const s = Math.max(-1, Math.min(1, chunk[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }
      // Transfer the ArrayBuffer to avoid copying
      this.port.postMessage(
        { type: 'audio', pcm16: pcm16.buffer },
        [pcm16.buffer]
      );
    }

    return true; // keep the processor alive
  }
}

registerProcessor('wake-word-processor', WakeWordProcessor);
