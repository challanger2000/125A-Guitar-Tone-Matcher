# Research Definition

## 1. Problem

The intended task is **reference-based guitar tone transfer**, not amp profiling.

Input A: a reference recording with a desired processed guitar tone.

Input B: a different processed guitar recording whose performance must be preserved.

Output: a transformed version of Input B whose relevant tonal and dynamic attributes are closer to Input A.

The reference and target do **not** need to contain the same notes, timing or performance.

## 2. What can be inferred from an unpaired reference

Candidate observable features include:

- long-term spectral envelope;
- low-frequency rolloff and low-mid body;
- presence and upper-mid structure;
- high-frequency / fizz distribution;
- spectral centroid, slope and flatness;
- band-wise RMS and crest factor;
- short-time dynamic range;
- transient density and attack statistics;
- envelope attack / decay distributions;
- sustain behaviour;
- spectral flux;
- MFCC-like timbral descriptors;
- selected noise-like vs tonal measures;
- stereo width/correlation when relevant.

These are **descriptors**, not proof of the physical amp/cab/microphone that created them.

## 3. What cannot be uniquely inferred

From one arbitrary processed recording alone we cannot uniquely recover:

- exact amplifier circuit;
- exact cabinet or microphone;
- exact nonlinear transfer function;
- exact gain staging;
- exact compressor settings;
- player/pickup/string contribution separated from the processing chain.

The product must therefore avoid claims of exact physical reconstruction.

## 4. Baseline

The mandatory first baseline is a robust, smoothed long-term spectral match with controlled gain limits and level matching.

Every later system is evaluated against:

- unprocessed target;
- level-matched EQ-match baseline;
- candidate advanced matcher.

## 5. Candidate advanced stages

Only stages that prove useful by measurement and listening survive.

Candidate stages:

- dynamic EQ / per-band dynamics;
- low-end transient control;
- attack/sustain shaping;
- broadband or multiband compression/expansion;
- nonlinear saturation / clipping families;
- high-frequency fizz shaping;
- resonance / cab-like spectral correction;
- adaptive stage ordering if justified;
- ML-assisted parameter estimation.

## 6. ML policy

ML is not a product requirement.

It is introduced only if it measurably improves generalisation or matching quality beyond a deterministic DSP controller.

Preferred first ML role:

**reference + target descriptors -> DSP parameter estimates**

rather than unconstrained waveform generation.

A waveform-to-waveform neural transform may be researched later only if it clearly outperforms the structured approach without unacceptable artifacts, latency, CPU or maintainability cost.

## 7. Success criterion

The concept advances toward product development only if, across a fixed multi-source guitar corpus:

1. the advanced matcher consistently moves objective descriptors closer to the reference than EQ-match alone;
2. improvements remain after loudness matching;
3. gains generalise to unseen riffs / guitars / source tones;
4. audible artifacts do not offset the improvement;
5. the method remains compatible with a practical realtime implementation.

No single scalar metric is sufficient for acceptance.
