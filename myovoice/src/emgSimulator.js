/**
 * MyoVoice sEMG Signal Simulator & DSP Library
 * This file simulates a 4-channel throat sEMG system and implements
 * real-time digital signal processing (DSP) filters.
 */

// Define standard vocabulary and their muscle activation profiles (envelopes)
// 4 Channels: L1 (Laryngeal Left), L2 (Laryngeal Right), T1 (Thyrohyoid), S1 (Sternohyoid)
export const VOCABULARY = {
  HELLO: {
    word: "Hello",
    durationMs: 1200,
    envelopes: [
      // Channel 1: Laryngeal Left - Two syllable peaks
      (t) => 0.1 * Math.sin(t * Math.PI) + (t > 0.1 && t < 0.4 ? 0.8 : 0) + (t > 0.6 && t < 1.0 ? 0.9 : 0),
      // Channel 2: Laryngeal Right - Symmetrical to Left with slight lag
      (t) => 0.15 * Math.sin(t * Math.PI) + (t > 0.15 && t < 0.45 ? 0.75 : 0) + (t > 0.65 && t < 1.05 ? 0.85 : 0),
      // Channel 3: Thyrohyoid - Swallowing/tongue elevation on second syllable
      (t) => (t > 0.5 && t < 0.95 ? 0.7 : 0.05),
      // Channel 4: Sternohyoid - Stabilizing anchor muscle
      (t) => (t > 0.1 && t < 1.1 ? 0.3 : 0.02)
    ],
    audioUrl: null // Generated via browser Web Speech API
  },
  HELP: {
    word: "Help",
    durationMs: 800,
    envelopes: [
      (t) => (t > 0.1 && t < 0.6 ? 1.0 : 0.05), // Sharp, fast burst
      (t) => (t > 0.12 && t < 0.58 ? 0.95 : 0.05),
      (t) => (t > 0.05 && t < 0.5 ? 0.4 : 0.05),
      (t) => (t > 0.1 && t < 0.7 ? 0.8 : 0.02)
    ]
  },
  YES: {
    word: "Yes",
    durationMs: 600,
    envelopes: [
      (t) => (t > 0.1 && t < 0.5 ? 0.9 : 0.05), // Short, single burst
      (t) => (t > 0.08 && t < 0.48 ? 0.85 : 0.05),
      (t) => (t > 0.15 && t < 0.55 ? 0.5 : 0.02),
      (t) => (t > 0.1 && t < 0.5 ? 0.2 : 0.02)
    ]
  },
  NO: {
    word: "No",
    durationMs: 500,
    envelopes: [
      (t) => (t > 0.05 && t < 0.4 ? 0.75 : 0.05),
      (t) => (t > 0.05 && t < 0.4 ? 0.75 : 0.05),
      (t) => (t > 0.05 && t < 0.35 ? 0.3 : 0.02),
      (t) => (t > 0.05 && t < 0.4 ? 0.4 : 0.02)
    ]
  },
  WATER: {
    word: "Water",
    durationMs: 1000,
    envelopes: [
      (t) => (t > 0.05 && t < 0.4 ? 0.7 : 0) + (t > 0.5 && t < 0.9 ? 0.8 : 0),
      (t) => (t > 0.05 && t < 0.4 ? 0.7 : 0) + (t > 0.5 && t < 0.9 ? 0.8 : 0),
      (t) => (t > 0.4 && t < 0.8 ? 0.9 : 0.05), // High thyrohyoid tongue movement for 't-er'
      (t) => (t > 0.1 && t < 0.9 ? 0.5 : 0.02)
    ]
  }
};

/**
 * Generates raw EMG samples for a specific timestamp (t in seconds).
 * If a word simulation is active, it modulates the noise with the word's envelopes.
 * 
 * @param {number} timestampSec - Current time in seconds.
 * @param {Object|null} activeWordState - State of the currently simulated word.
 * @param {boolean} inject50HzHum - Whether to add a 50Hz hum.
 * @param {number} noiseLevel - Multiplier for random muscle noise.
 * @returns {Array<number>} - 4 channels of raw sEMG values in microvolts (uV)
 */
export function generateRawSample(timestampSec, activeWordState, inject50HzHum, noiseLevel = 1.0) {
  const numChannels = 4;
  const sample = new Array(numChannels).fill(0);

  // 1. Generate base physiological muscle noise (simulates resting state firing of motor units)
  // Frequency of muscle firing is typically random between 20-200 Hz
  for (let ch = 0; ch < numChannels; ch++) {
    // Generate high-frequency pseudo-EMG signal
    const f1 = 65 + Math.sin(timestampSec * 10) * 15;
    const f2 = 145 + Math.cos(timestampSec * 15) * 35;
    const emgCarrier = Math.sin(2 * Math.PI * f1 * timestampSec) * 0.6 + 
                       Math.sin(2 * Math.PI * f2 * timestampSec) * 0.4;
    
    let envelope = 0.05; // Base resting tension (approx 5 uV)
    
    // 2. Modulate with active word envelope if speaking
    if (activeWordState && activeWordState.vocabKey) {
      const vocab = VOCABULARY[activeWordState.vocabKey];
      const elapsedMs = (timestampSec - activeWordState.startTimeSec) * 1000;
      
      if (elapsedMs >= 0 && elapsedMs <= vocab.durationMs) {
        const normTime = elapsedMs / vocab.durationMs; // 0.0 to 1.0
        const envelopeFn = vocab.envelopes[ch];
        envelope = envelopeFn(normTime);
      }
    }

    // Multiply carrier wave by envelope and scale to microvolts (e.g. peaks around 150uV)
    const emgSignal = emgCarrier * envelope * 120 * noiseLevel;
    
    // Add baseline random Gaussian-like noise
    const gaussianNoise = (Math.random() - 0.5) * 8 * noiseLevel;

    sample[ch] = emgSignal + gaussianNoise;
  }

  // 3. Inject 50Hz Powerline Interference (if enabled)
  if (inject50HzHum) {
    const humIntensity = 30; // 30uV amplitude
    const hum = Math.sin(2 * Math.PI * 50 * timestampSec) * humIntensity;
    for (let ch = 0; ch < numChannels; ch++) {
      sample[ch] += hum;
    }
  }

  return sample;
}

/**
 * Butterworth Bandpass Filter (2nd Order, 20Hz - 500Hz at Fs=1000Hz)
 * notch filter for 50Hz.
 * Since doing full IIR filter cascade in real-time is computationally sensitive,
 * we implement clean, optimized IIR filter coefficients for:
 * 1. Highpass at 20Hz
 * 2. Lowpass at 450Hz
 * 3. Notch at 50Hz
 */
export class RealTimeDSPFilter {
  constructor() {
    this.reset();
  }

  reset() {
    // History buffers for 4 channels
    // Highpass history (20Hz, Fs=1000Hz)
    this.hp_x = Array.from({ length: 4 }, () => [0, 0, 0]);
    this.hp_y = Array.from({ length: 4 }, () => [0, 0, 0]);
    
    // Lowpass history (450Hz, Fs=1000Hz)
    this.lp_x = Array.from({ length: 4 }, () => [0, 0, 0]);
    this.lp_y = Array.from({ length: 4 }, () => [0, 0, 0]);

    // Notch history (50Hz, Fs=1000Hz)
    this.notch_x = Array.from({ length: 4 }, () => [0, 0, 0]);
    this.notch_y = Array.from({ length: 4 }, () => [0, 0, 0]);
  }

  /**
   * Filter one 4-channel sample.
   */
  process(rawSample, options = { notch: true, bandpass: true }) {
    const output = [...rawSample];

    for (let ch = 0; ch < 4; ch++) {
      let val = rawSample[ch];

      // 1. Apply 50Hz Notch Filter
      if (options.notch) {
        val = this.applyNotch(ch, val);
      }

      // 2. Apply Bandpass (Highpass 20Hz + Lowpass 450Hz)
      if (options.bandpass) {
        val = this.applyHighPass20Hz(ch, val);
        val = this.applyLowPass450Hz(ch, val);
      }

      output[ch] = val;
    }

    return output;
  }

  // 2nd order IIR Notch filter (50Hz at Fs=1000Hz)
  // b = [0.965, -1.836, 0.965], a = [1.0, -1.836, 0.931]
  applyNotch(ch, x) {
    const x_hist = this.notch_x[ch];
    const y_hist = this.notch_y[ch];

    x_hist[2] = x_hist[1];
    x_hist[1] = x_hist[0];
    x_hist[0] = x;

    const y = 0.96508 * x_hist[0] - 1.8355 * x_hist[1] + 0.96508 * x_hist[2]
             + 1.8355 * y_hist[1] - 0.93017 * y_hist[2];

    y_hist[2] = y_hist[1];
    y_hist[1] = y_hist[0];
    y_hist[0] = y;

    return y;
  }

  // 2nd order Highpass filter (20Hz at Fs=1000Hz)
  // b = [0.915, -1.830, 0.915], a = [1.0, -1.823, 0.837]
  applyHighPass20Hz(ch, x) {
    const x_hist = this.hp_x[ch];
    const y_hist = this.hp_y[ch];

    x_hist[2] = x_hist[1];
    x_hist[1] = x_hist[0];
    x_hist[0] = x;

    const y = 0.91497 * x_hist[0] - 1.8299 * x_hist[1] + 0.91497 * x_hist[2]
             + 1.8227 * y_hist[1] - 0.83718 * y_hist[2];

    y_hist[2] = y_hist[1];
    y_hist[1] = y_hist[0];
    y_hist[0] = y;

    return y;
  }

  // 2nd order Lowpass filter (450Hz at Fs=1000Hz)
  applyLowPass450Hz(ch, x) {
    const x_hist = this.lp_x[ch];
    const y_hist = this.lp_y[ch];

    x_hist[2] = x_hist[1];
    x_hist[1] = x_hist[0];
    x_hist[0] = x;

    const y = 0.8929 * x_hist[0] + 1.7858 * x_hist[1] + 0.8929 * x_hist[2]
             - 1.7781 * y_hist[1] - 0.7935 * y_hist[2];

    y_hist[2] = y_hist[1];
    y_hist[1] = y_hist[0];
    y_hist[0] = y;

    return y;
  }
}

/**
 * Calculates Feature values for raw/filtered buffers.
 * Root Mean Square (RMS) is the standard metric for sEMG muscle activation.
 */
export function calculateRMS(buffer) {
  if (buffer.length === 0) return 0;
  let sum = 0;
  for (let i = 0; i < buffer.length; i++) {
    sum += buffer[i] * buffer[i];
  }
  return Math.sqrt(sum / buffer.length);
}
