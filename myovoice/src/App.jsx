import React, { useState, useEffect, useRef } from "react";
import {
  VOCABULARY,
  generateRawSample,
  RealTimeDSPFilter,
  calculateRMS
} from "./emgSimulator";

// In-app styles for premium aesthetics (Dark Glassmorphism)
import "./App.css";

function App() {
  // App states
  const [isPlaying, setIsPlaying] = useState(true);
  const [notchFilter, setNotchFilter] = useState(true);
  const [bandpassFilter, setBandpassFilter] = useState(true);
  const [noiseLevel, setNoiseLevel] = useState(1.0);
  const [injectHum, setInjectHum] = useState(true);
  const [activeWordState, setActiveWordState] = useState(null);
  const [translationLog, setTranslationLog] = useState([
    { time: "00:00:00", text: "System Initialized. Ready for neuromuscular input.", type: "system" }
  ]);
  const [latency, setLatency] = useState(0);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState("");
  const [availableVoices, setAvailableVoices] = useState([]);
  const [activeTab, setActiveTab] = useState("monitor"); // monitor, clinical, setup

  // Muscle energy levels for clinical diagnostic view
  const [muscleRMS, setMuscleRMS] = useState([0, 0, 0, 0]);

  // Refs for animation loop and DSP
  const dspFilterRef = useRef(new RealTimeDSPFilter());
  const canvasRawRef = useRef(null);
  const canvasFilteredRef = useRef(null);
  const rawHistoryRef = useRef(Array.from({ length: 4 }, () => new Array(300).fill(0)));
  const filteredHistoryRef = useRef(Array.from({ length: 4 }, () => new Array(300).fill(0)));
  const lastTimeRef = useRef(performance.now());
  const requestRef = useRef(null);
  const sampleTimeRef = useRef(0);

  // Initialize Speech Synthesis Voices
  useEffect(() => {
    const loadVoices = () => {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        const voices = window.speechSynthesis.getVoices();
        setAvailableVoices(voices.filter(v => v.lang.startsWith("en") || v.lang.startsWith("th")));
        if (voices.length > 0 && !selectedVoice) {
          setSelectedVoice(voices[0].name);
        }
      }
    };
    loadVoices();
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  // Continuous Simulation & Animation Loop (1000Hz sampling rate, rendered at ~60fps)
  useEffect(() => {
    const loop = (time) => {
      const deltaMs = time - lastTimeRef.current;
      lastTimeRef.current = time;

      // Number of samples to generate since last frame at Fs = 1000Hz (1 sample/ms)
      const samplesToGenerate = Math.min(Math.floor(deltaMs), 50); // limit spikes

      if (isPlaying) {
        for (let i = 0; i < samplesToGenerate; i++) {
          sampleTimeRef.current += 0.001; // 1 ms steps

          // 1. Generate Raw Sample (Microvolts)
          const rawSample = generateRawSample(
            sampleTimeRef.current,
            activeWordState,
            injectHum,
            noiseLevel
          );

          // 2. Run real-time DSP filters
          const filteredSample = dspFilterRef.current.process(rawSample, {
            notch: notchFilter,
            bandpass: bandpassFilter
          });

          // 3. Update histories for visualization (circular buffer style)
          for (let ch = 0; ch < 4; ch++) {
            rawHistoryRef.current[ch].shift();
            rawHistoryRef.current[ch].push(rawSample[ch]);

            filteredHistoryRef.current[ch].shift();
            filteredHistoryRef.current[ch].push(filteredSample[ch]);
          }
        }

        // Calculate live RMS values for UI gauges
        const newRMS = [0, 1, 2, 3].map((ch) =>
          calculateRMS(filteredHistoryRef.current[ch].slice(-50))
        );
        setMuscleRMS(newRMS);
      }

      // Render plots on Canvas
      drawPlot(canvasRawRef.current, rawHistoryRef.current, "raw");
      drawPlot(canvasFilteredRef.current, filteredHistoryRef.current, "filtered");

      requestRef.current = requestAnimationFrame(loop);
    };

    if (isPlaying) {
      requestRef.current = requestAnimationFrame(loop);
    }
    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [isPlaying, activeWordState, injectHum, noiseLevel, notchFilter, bandpassFilter]);

  // Track simulated speech timeouts
  useEffect(() => {
    if (activeWordState) {
      const vocab = VOCABULARY[activeWordState.vocabKey];
      const elapsed = (performance.now() - activeWordState.triggerTimeMs);
      
      const timer = setTimeout(() => {
        // Speech trigger
        triggerTextToSpeech(vocab.word);
        setActiveWordState(null);
      }, Math.max(vocab.durationMs - elapsed, 0));

      return () => clearTimeout(timer);
    }
  }, [activeWordState]);

  // Color palette for the 4 sEMG channels
  const channelColors = [
    "#ff4a7d", // Laryngeal Left (Pink-Red)
    "#3bf7be", // Laryngeal Right (Aqua-Green)
    "#3b82f6", // Thyrohyoid (Blue)
    "#a855f7"  // Sternohyoid (Purple)
  ];

  // Plot renderer
  const drawPlot = (canvas, history, type) => {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;

    // Clear with dark blue-gray backing
    ctx.fillStyle = "#0c1424";
    ctx.fillRect(0, 0, width, height);

    // Draw grid lines
    ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
    ctx.lineWidth = 1;
    const gridRows = 8;
    for (let i = 1; i < gridRows; i++) {
      const y = (height / gridRows) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    const channelHeight = height / 4;

    // Plot each of the 4 channels in its own lane
    for (let ch = 0; ch < 4; ch++) {
      const data = history[ch];
      const len = data.length;
      const centerY = channelHeight * ch + channelHeight / 2;

      // Draw baseline axis
      ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
      ctx.beginPath();
      ctx.moveTo(0, centerY);
      ctx.lineTo(width, centerY);
      ctx.stroke();

      // Plot signal wave
      ctx.strokeStyle = channelColors[ch];
      ctx.lineWidth = type === "filtered" ? 2 : 1;
      ctx.beginPath();

      for (let i = 0; i < len; i++) {
        const x = (width / len) * i;
        // Scale factor: assume amplitude range +-150 uV fits in channelHeight
        const scale = channelHeight / (type === "filtered" ? 180 : 300);
        const y = centerY - data[i] * scale;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      // Show channel labels
      ctx.fillStyle = "rgba(255, 255, 255, 0.7)";
      ctx.font = "10px sans-serif";
      const channelNames = ["L1 (Laryngeal L)", "L2 (Laryngeal R)", "T1 (Thyrohyoid)", "S1 (Sternohyoid)"];
      ctx.fillText(channelNames[ch], 10, channelHeight * ch + 15);
    }
  };

  // Silently "speak" a word (generates muscle potentials)
  const triggerSilentSpeech = (vocabKey) => {
    if (activeWordState) return; // Wait for active word to finish

    const t0 = performance.now();
    setActiveWordState({
      vocabKey,
      startTimeSec: sampleTimeRef.current,
      triggerTimeMs: t0
    });

    // Simulate AI classification latency (typically 45-80ms for neural neck collars)
    const simulatedLatency = Math.floor(45 + Math.random() * 35);
    setLatency(simulatedLatency);
  };

  // Convert translated text to audible speech using Web Speech API
  const triggerTextToSpeech = (text) => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel(); // kill active speech

      const utterance = new SpeechSynthesisUtterance(text);
      if (selectedVoice) {
        const voiceObj = availableVoices.find(v => v.name === selectedVoice);
        if (voiceObj) utterance.voice = voiceObj;
      }
      utterance.rate = 1.0;
      
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);

      // Append to local log
      const now = new Date();
      const timeStr = now.toTimeString().split(" ")[0];
      setTranslationLog(prev => [
        { time: timeStr, text: `[Neuromuscular Decoded] "${text}"`, type: "user" },
        ...prev
      ]);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-brand">
          <div className="pulse-dot"></div>
          <h1>MyoVoice</h1>
          <span className="badge">v1.0 - Silent Speech Interface</span>
        </div>
        <div className="header-status">
          <span className="status-label">Device Status:</span>
          <span className="status-value connected">Online (sEMG Connected)</span>
        </div>
      </header>

      {/* Navigation tabs */}
      <div className="tab-navigation">
        <button 
          className={activeTab === "monitor" ? "active" : ""} 
          onClick={() => setActiveTab("monitor")}
        >
          Signal Monitor
        </button>
        <button 
          className={activeTab === "clinical" ? "active" : ""} 
          onClick={() => setActiveTab("clinical")}
        >
          Diagnostic Panel
        </button>
        <button 
          className={activeTab === "setup" ? "active" : ""} 
          onClick={() => setActiveTab("setup")}
        >
          System Settings
        </button>
      </div>

      <main className="app-main">
        {/* Left Side: Waveform Visualizers */}
        <section className="visualization-section">
          {activeTab === "monitor" && (
            <>
              <div className="panel card">
                <div className="panel-header">
                  <h3>Raw sEMG Signals (Microvolts)</h3>
                  <span className="help-text">Contains 50Hz hum and noise before processing</span>
                </div>
                <div className="canvas-wrapper">
                  <canvas ref={canvasRawRef} width={650} height={280} />
                </div>
              </div>

              <div className="panel card">
                <div className="panel-header">
                  <h3>Filtered & Conditioned sEMG Signals</h3>
                  <span className="help-text">Processed via 50Hz Notch + 20-450Hz Bandpass filters</span>
                </div>
                <div className="canvas-wrapper">
                  <canvas ref={canvasFilteredRef} width={650} height={280} />
                </div>
              </div>
            </>
          )}

          {activeTab === "clinical" && (
            <div className="panel card full-height">
              <div className="panel-header">
                <h3>Neuromuscular Diagnostic & Energy Output</h3>
                <p>Objective measurement of continuous muscle motor unit recruitment.</p>
              </div>

              <div className="grid-2">
                <div className="rms-meters-container">
                  <h4>Live Muscle Tension (RMS uV)</h4>
                  {muscleRMS.map((rms, idx) => {
                    const channelNames = ["Laryngeal Left", "Laryngeal Right", "Thyrohyoid", "Sternohyoid"];
                    const percent = Math.min((rms / 80) * 100, 100);
                    return (
                      <div key={idx} className="rms-meter-row">
                        <div className="rms-label">
                          <span>{channelNames[idx]}</span>
                          <span style={{ color: channelColors[idx] }}>{rms.toFixed(2)} uV</span>
                        </div>
                        <div className="rms-bar-bg">
                          <div 
                            className="rms-bar-fill" 
                            style={{ 
                              width: `${percent}%`, 
                              backgroundColor: channelColors[idx] 
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="clinical-analytics">
                  <h4>Clinical Metrics Summary</h4>
                  <div className="metric-box">
                    <span className="metric-title">Fatigue Index</span>
                    <span className="metric-val">Normal (94%)</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-title">Swallow Co-activation</span>
                    <span className="metric-val">12 ms delay</span>
                  </div>
                  <div className="metric-box">
                    <span className="metric-title">Motor Unit Recruitment Rate</span>
                    <span className="metric-val">180 Hz avg</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "setup" && (
            <div className="panel card full-height">
              <div className="panel-header">
                <h3>Neuromuscular Hardware Configuration</h3>
              </div>
              <div className="settings-form">
                <div className="form-group">
                  <label>Selected Voice Synthesizer Profile</label>
                  <select 
                    value={selectedVoice} 
                    onChange={(e) => setSelectedVoice(e.target.value)}
                    className="custom-select"
                  >
                    {availableVoices.map((voice) => (
                      <option key={voice.name} value={voice.name}>
                        {voice.name} ({voice.lang})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>sEMG Electrode Input Gain (dB)</label>
                  <input type="range" min="12" max="48" defaultValue="24" className="custom-range" />
                </div>
                <div className="form-group">
                  <label>Powerline Hum Frequency</label>
                  <div className="radio-group">
                    <label><input type="radio" name="hum-freq" defaultChecked /> 50 Hz (Asia/Europe)</label>
                    <label><input type="radio" name="hum-freq" /> 60 Hz (Americas)</label>
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Right Side: Interactive Console and Controllers */}
        <section className="controls-section">
          {/* Translation Logs Console */}
          <div className="panel card console-card">
            <div className="panel-header">
              <h3>Neuromuscular Decode Output</h3>
            </div>
            <div className="console-log">
              {translationLog.map((log, index) => (
                <div key={index} className={`console-line ${log.type}`}>
                  <span className="console-time">[{log.time}]</span>
                  <span className="console-text">{log.text}</span>
                </div>
              ))}
            </div>
            <div className="latency-bar">
              <span>Decode Latency: <strong>{latency} ms</strong></span>
              <span className="latency-bar-indicator">
                <span className="latency-progress" style={{ width: `${Math.min(latency * 2, 100)}%` }} />
              </span>
            </div>
          </div>

          {/* Silent Speaking Trigger Panel */}
          <div className="panel card">
            <div className="panel-header">
              <h3>Silent Speech Vocabulary Simulator</h3>
              <p className="subtitle">Click a word to simulate the throat muscle signals of that word:</p>
            </div>
            <div className="vocab-grid">
              {Object.keys(VOCABULARY).map((key) => (
                <button
                  key={key}
                  disabled={activeWordState !== null}
                  onClick={() => triggerSilentSpeech(key)}
                  className={`vocab-btn ${activeWordState?.vocabKey === key ? "active" : ""}`}
                >
                  <span className="vocab-word">{VOCABULARY[key].word}</span>
                  <span className="vocab-desc">({VOCABULARY[key].durationMs}ms activation)</span>
                </button>
              ))}
            </div>
          </div>

          {/* Filter Configuration */}
          <div className="panel card">
            <div className="panel-header">
              <h3>Real-Time DSP Signal Filtering</h3>
            </div>
            <div className="toggle-grid">
              <div className="toggle-row">
                <div className="toggle-label">
                  <span>50Hz Notch Filter</span>
                  <span className="desc">Eliminates powerline hum</span>
                </div>
                <button
                  onClick={() => setNotchFilter(!notchFilter)}
                  className={`toggle-btn ${notchFilter ? "on" : "off"}`}
                >
                  {notchFilter ? "Active" : "Bypassed"}
                </button>
              </div>

              <div className="toggle-row">
                <div className="toggle-label">
                  <span>Bandpass (20-450Hz)</span>
                  <span className="desc">Removes noise outside EMG range</span>
                </div>
                <button
                  onClick={() => setBandpassFilter(!bandpassFilter)}
                  className={`toggle-btn ${bandpassFilter ? "on" : "off"}`}
                >
                  {bandpassFilter ? "Active" : "Bypassed"}
                </button>
              </div>

              <div className="toggle-row">
                <div className="toggle-label">
                  <span>Inject Powerline Hum</span>
                  <span className="desc">Adds artificial 50Hz hum into sensor input</span>
                </div>
                <button
                  onClick={() => setInjectHum(!injectHum)}
                  className={`toggle-btn ${injectHum ? "on" : "off"}`}
                >
                  {injectHum ? "ON" : "OFF"}
                </button>
              </div>

              <div className="slider-row">
                <div className="slider-header">
                  <span>Noise Amplitude</span>
                  <span>{(noiseLevel * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="2.5"
                  step="0.1"
                  value={noiseLevel}
                  onChange={(e) => setNoiseLevel(parseFloat(e.target.value))}
                  className="custom-range"
                />
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
