# Architecture — Research Target

## Phase A: offline research harness

### Reference analyser

Extracts deterministic descriptors from the reference:

- smoothed spectral envelope;
- octave / fractional-octave or perceptually spaced band energies;
- crest-factor distribution;
- envelope statistics;
- transient statistics;
- spectral centroid / rolloff / slope / flatness;
- spectral flux;
- MFCC-like timbral descriptors;
- optional stereo descriptors.

### Target analyser

Runs the same feature extraction on the target under identical conditions.

### Match controller

Produces bounded transformation parameters.

Research order:

1. analytic / rule-based controller;
2. optimisation-based controller;
3. ML-assisted controller only if justified.

### DSP engine

Candidate processing graph:

`Input trim -> spectral correction -> dynamic correction -> transient correction -> nonlinear texture correction -> final residual EQ -> output trim`

The exact ordering is experimental and must be tested rather than assumed.

### Evaluator

Produces:

- before/after descriptor deltas;
- level-matched residual measurements;
- per-band errors;
- transient/dynamic errors;
- perceptually weighted supplementary metrics;
- deterministic renders for listening comparison.

## Phase B: realtime VST3

Only after Phase A demonstrates a repeatable advantage.

Realtime design constraints:

- no file analysis on the audio thread;
- no allocation / blocking locks / file I/O in processing;
- reference analysis performed outside realtime processing;
- precomputed coefficients / target descriptors transferred safely to DSP;
- bounded computation;
- correct state recall of analysed reference state or derived matching state;
- explicit latency reporting if lookahead / FFT processing is used.

## User-facing concept — provisional

The final interface should remain simpler than the internal engine.

Potential top-level controls:

- REFERENCE / ANALYZE
- MATCH 0–100%
- TIGHT
- ATTACK
- BODY
- FIZZ
- OUTPUT

This is provisional. GUI work begins only after the DSP architecture is validated.
