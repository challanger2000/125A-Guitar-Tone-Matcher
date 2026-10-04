# Measurement Plan

## 1. Experimental corpus

Use fixed real-audio fixtures containing multiple categories:

- tight palm-muted high-gain rhythm;
- sustained distorted chords;
- single-note riffs;
- lower-gain crunch;
- bright / fizzy source;
- dark / muffled source;
- different guitars/pickups where available.

Reference and target performances should deliberately differ.

Synthetic signals are added for subsystem validation but do not replace real guitar material.

## 2. Level discipline

All comparison renders must be level-matched where appropriate.

Record both:

- raw output level change;
- level-matched comparison.

A louder result is not accepted as a better match.

## 3. Baseline spectral metrics

Candidate metrics:

- log-frequency spectral-envelope error;
- per-band RMS delta;
- spectral centroid delta;
- spectral slope delta;
- spectral rolloff delta;
- spectral flatness delta.

Windowing, smoothing bandwidth, FFT size and aggregation method must be fixed and recorded.

## 4. Dynamic metrics

- full-file and short-window crest factor;
- short-time RMS distribution;
- envelope percentile distribution;
- attack-time distribution;
- decay/sustain statistics;
- transient peak-to-body ratio.

## 5. Texture / distortion descriptors

Research candidates:

- spectral flux;
- high-band flatness / noise-likeness;
- MFCC distance;
- harmonic/noise proxies appropriate to polyphonic distorted guitar;
- band-limited modulation statistics.

Any descriptor that is unstable across different notes or riffs is rejected or down-weighted.

## 6. Residual and alignment

For paired synthetic tests or deliberately generated oracle data:

- time-aligned residual;
- null / residual RMS;
- band-wise residual energy.

For arbitrary unpaired musical performances, waveform nulling is not a valid primary metric.

## 7. Acceptance ladder

Each stage must beat the previous stage on held-out fixtures:

A. Target unchanged  
B. EQ-match baseline  
C. EQ + dynamics  
D. + transient stage  
E. + nonlinear/texture stage  
F. optional ML controller

A stage is retained only if it improves a defined subset of metrics without causing unacceptable regressions elsewhere.

## 8. Realtime gate

Before VST3 release work:

- measure CPU p95 / p99 / max;
- test 44.1 / 48 / 88.2 / 96 kHz where supported;
- test small and variable block sizes;
- verify mono/stereo behaviour;
- test silence, impulses, extremes, NaN/Inf containment and denormal stress;
- verify offline/realtime parity;
- verify state and automation;
- run Steinberg Validator and 125A lifecycle/I/O QA.

## 9. Listening

Objective metrics guide the engineering but do not replace listening.

Listening protocol should include:

- level-matched A/B;
- EQ baseline vs advanced matcher;
- several unseen target performances;
- checks for pumping, smeared attacks, fizz artifacts, phase problems and over-processing.
