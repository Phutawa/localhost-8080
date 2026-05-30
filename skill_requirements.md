# Skill Requirements: DSP Filter Expert

We need a skill that guides Claude to write highly optimized, noise-robust, and edge-case-safe Digital Signal Processing (DSP) filter logic in JavaScript/TypeScript (especially for real-time biological signal filtering like EMG or ECG).

## Key Requirements
1. Prevent NaN or Infinity values from ever propagating (e.g., guard against division-by-zero, negative square roots, or log of non-positive numbers).
2. Clamping: If the computed frequency or coefficient is outside Nyquist limits or is invalid, clamp to a safe fallback.
3. Fast execution: The algorithm runs inside a real-time audio/data stream, so it must avoid expensive object allocations in the critical loop.
4. Support standard filters: High-pass, Low-pass, Band-pass, and Notch.

## Triggers
- When requested to write or review real-time DSP filter classes/functions.
- When fixing issues related to NaN/Infinity output in filter algorithms.
