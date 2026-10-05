# Validation Log

This log records reproducible engineering checks. It is not a release PASS record.

## 2026-10-05 — real high-gain guitar fixture, local/private

Source:
- real processed high-gain rhythm-guitar recording;
- 44.1 kHz;
- stereo container carrying effectively mono programme material;
- approximately 24 seconds;
- fixture audio is intentionally not committed to the public repository.

Method:
1. use the real guitar recording as an oracle reference;
2. create a known spectral perturbation from the same programme material;
3. run the EQ-match baseline back toward the oracle;
4. create a known macro-dynamic expansion from the same programme material;
5. run the dynamics matcher back toward the oracle.

Observed research results:
- mean level-independent spectral-envelope error, 80 Hz–12 kHz:
  - before EQ match: approximately **1.12 dB**;
  - after EQ match: approximately **0.14 dB**;
- robust short-time dynamic-range error:
  - before dynamics match: approximately **1.58 dB**;
  - after dynamics match: approximately **0.10 dB**.

Interpretation:
- both baseline stages moved controlled perturbations substantially closer to the known source on real distorted-guitar programme material;
- these results validate direction, not generalisation;
- independent references and genuinely different performances are still required before any product-quality claim.

A local reproduction helper is provided in:
- `scripts/validate_real_fixture.py`


## 2026-10-05 — two different real guitar recordings

Purpose:
- test the actual product scenario rather than an oracle reconstruction;
- reference and target are different recordings / performances.

Local fixtures:
- reference: processed high-gain guitar recording;
- target: separate processed guitar recording;
- both 44.1 kHz;
- audio files remain local/private and are not committed.

Observed results:

### Spectral distance
Mean level-independent spectral-envelope error, 80 Hz–12 kHz:

- target before processing: approximately **4.21 dB**;
- after initial EQ match: approximately **1.27 dB**;
- after EQ + dynamics/transient stage: approximately **1.29 dB**;
- after final residual EQ: approximately **1.17 dB**.

This is about a **72% reduction** in the measured spectral-envelope error from the original target to the current final research chain.

### Macro dynamics
Robust short-time dynamic range:

- reference: approximately **3.58 dB**;
- target before processing: approximately **3.49 dB**;
- after initial EQ match: approximately **2.02 dB**;
- after dynamics/transient stage: approximately **3.18 dB**;
- after final residual EQ: approximately **3.22 dB**.

Interpretation:
- initial spectral correction materially altered short-time dynamics;
- the dynamics stage recovered most of that unintended change;
- processing stages therefore cannot be validated independently only; interaction matters.

### Transient index
Peak-to-body transient statistic:

- reference: approximately **10.79 dB**;
- target before processing: approximately **9.94 dB**;
- after initial EQ match: approximately **10.15 dB**;
- after dynamics/transient stage: approximately **10.16 dB**;
- after final residual EQ: approximately **10.03 dB**.

The reference/target difference is modest, so aggressive transient correction is not justified by this pair.

### Texture / saturation search
Current texture descriptor pair:
- crest factor;
- 3–12 kHz spectral flatness.

Observed:
- reference crest factor: approximately **14.61 dB**;
- post-dynamics target crest factor: approximately **14.31 dB**;
- reference high-band flatness: approximately **-21.69 dB**;
- post-dynamics target high-band flatness: approximately **-20.77 dB**.

The bounded saturation search selected **NONE**. No tested tanh / atan / soft-clip candidate improved the current texture score.

Interpretation:
- this is a positive guardrail result;
- the nonlinear stage is not allowed to process audio merely because nonlinear processing exists;
- for this pair the current measurable mismatch is dominated by spectral shape, not by a demonstrated need for added saturation.

### Current conclusion
The research chain clearly outperforms the unprocessed target on spectral similarity while recovering most dynamics disturbed by the EQ stage.

This is encouraging but not a product-quality proof. More independent guitar/reference pairs are required, and texture descriptors need broader validation before the nonlinear stage can be considered useful.


## 2026-10-05 — improved target performance (new FLAC)

Purpose:
- repeat the real two-performance comparison with a target riff whose register/articulation is closer to the reference;
- test whether the current chain remains useful on a musically better-matched target.

Local fixture:
- reference: previous processed high-gain guitar recording;
- target: new processed guitar FLAC;
- both 44.1 kHz and same duration;
- fixture audio remains local/private.

Observed results:

### Spectral distance
Mean level-independent spectral-envelope error, 80 Hz–12 kHz:

- target before processing: approximately **4.86 dB**;
- after initial EQ match: approximately **0.94 dB**;
- after EQ + dynamics/transient stage: approximately **0.94 dB**;
- after final residual EQ: approximately **0.66 dB**.

This is about an **86% reduction** in the measured spectral-envelope error relative to the unprocessed target.

### Macro dynamics
Robust short-time dynamic range:

- reference: approximately **3.58 dB**;
- target before processing: approximately **2.70 dB**;
- after initial EQ match: approximately **1.84 dB**;
- after dynamics/transient stage: approximately **2.79 dB**;
- after final residual EQ: approximately **2.63 dB**.

The controller reached the current maximum expansion ratio (**1.60x**), indicating the target remains dynamically flatter than the reference after spectral correction.

### Transient index
Peak-to-body transient statistic:

- reference: approximately **10.79 dB**;
- target before processing: approximately **8.76 dB**;
- after initial EQ match: approximately **9.81 dB**;
- after dynamics/transient stage: approximately **9.85 dB**;
- after final residual EQ: approximately **9.90 dB**.

The current transient stage improves the mismatch only modestly and remains an active research area.

### Texture / saturation search
- reference crest factor: approximately **14.61 dB**;
- target before: approximately **12.39 dB**;
- target after dynamics: approximately **13.41 dB**;
- reference 3–12 kHz flatness: approximately **-21.69 dB**;
- target before: approximately **-17.71 dB**;
- target after dynamics: approximately **-21.55 dB**.

The bounded saturation search again selected **NONE**.

Interpretation:
- the high-band texture mismatch was largely corrected by spectral/dynamic processing;
- adding the currently tested nonlinear families did not improve the defined texture score;
- nonlinear processing remains optional and must continue to justify itself per fixture.

Current conclusion:
- the improved target performance produces the strongest real two-performance result so far;
- spectral matching is already highly effective;
- the remaining measurable gap is dominated more by dynamics/attack than by the current texture descriptors.


## 2026-10-05 — paired DI / amp oracle

Purpose:
- evaluate the matcher against the same performance before and after a real amp/processing chain;
- separate source-performance behaviour from processing behaviour.

Local fixtures:
- DI and processed amp version of the same performance;
- 44.1 kHz;
- 192 seconds;
- files remain local/private.

Observed source relationship:
- DI crest factor: approximately **21.02 dB**;
- amp crest factor: approximately **18.91 dB**;
- active 40 ms short-time dynamic range:
  - DI: approximately **15.80 dB**;
  - amp: approximately **4.56 dB**;
- peak-to-body transient index:
  - DI: approximately **13.07 dB**;
  - amp: approximately **10.30 dB**;
- initial level-independent spectral-envelope error: approximately **8.63 dB**.

Current research chain:
- after initial EQ match:
  - spectral error: approximately **2.89 dB**;
  - active dynamic range: approximately **15.28 dB**;
  - transient index: approximately **13.05 dB**;
- after upgraded gated quantile dynamics/transient stage:
  - spectral error: approximately **2.85 dB**;
  - active dynamic range: approximately **5.49 dB**;
  - transient index: approximately **12.80 dB**;
  - inferred dynamic-range ratio: approximately **0.30**;
  - transient controller request: approximately **-2.76 dB**;
- after bounded residual EQ:
  - spectral error: approximately **1.78 dB**;
  - active dynamic range: approximately **6.83 dB**;
  - transient index: approximately **12.88 dB**.

Interpretation:
- the paired fixture proves that amp processing changes far more than long-term spectral shape;
- the former dynamics-controller floor of 0.60 was invalid for this material and has been removed;
- quantile-distribution matching substantially reproduces the reference macro-dynamic distribution without requiring aligned performance;
- transient reduction remains under-achieved and is the next clear subsystem to improve;
- residual EQ can perturb dynamics again, so the final stage ordering / iteration policy still needs optimisation.


## 2026-10-05 — stage-order comparison on separate target performance

Reference:
- real processed Amaranthe-style amp track.

Target:
- separate user guitar performance.

Compared:
1. unprocessed target;
2. EQ-only baseline;
3. current full chain;
4. alternative stage orders.

Best measured compromise:
- initial EQ;
- dynamics;
- optional texture search;
- residual EQ;
- bounded second dynamics/transient pass.

Measured distance to reference:

| Variant | Spectral error | Dynamic-range error | Transient error | High-band flatness error |
|---|---:|---:|---:|---:|
| Original | 4.524 dB | 1.870 dB | 1.548 dB | 3.408 dB |
| EQ only | 0.942 dB | 0.257 dB | 0.866 dB | 0.113 dB |
| Previous full chain | 0.750 dB | 1.145 dB | 0.504 dB | 0.038 dB |
| Iterated dynamics chain | **0.795 dB** | **0.281 dB** | **0.798 dB** | **0.037 dB** |

Interpretation:
- EQ-only is already a strong baseline;
- the previous full chain improved spectral/texture/transient metrics but damaged macro-dynamic matching too much;
- the iterated dynamics order retains almost all of EQ-only's dynamic accuracy while improving spectral and high-band texture similarity;
- this order is the current preferred research pipeline;
- additional complexity will be added only if it beats this baseline on multiple independent fixtures.


## 2026-10-05 — fine multiband refinement rejected

Experiment:
- replace the 6-band dynamics layout with a finer 9-band layout derived from paired DI/amp observations;
- reduce allowed gain motion below 250 Hz to preserve palm-mute fundamentals;
- compare against EQ-only and the existing 6-band matcher.

Robustness check:
- the finer layout improved high-band flatness and transient proximity slightly;
- however, macro-dynamic results changed substantially depending on which active section of the long reference recording was used;
- on a representative 35-second reference segment:
  - EQ-only dynamic-range error: approximately **0.16 dB**;
  - 6-band + transient error: approximately **1.74 dB**;
  - 9-band + transient error: approximately **1.38 dB**;
- therefore neither multiband result was robust enough on that segment to beat EQ-only overall.

Decision:
- the 9-band refinement is **rejected for current use** and has been reverted;
- the key unresolved issue is **reference-section sensitivity**, not simply band count;
- next research should estimate a stable reference profile from multiple active windows or automatically select comparable reference sections before deriving dynamics targets.

Engineering consequence:
- do not claim multiband dynamics as a general improvement until it wins across multiple reference windows and independent fixtures.


## 2026-10-05 — robust reference-window selection, first real test

Reference:
- 192-second processed Amaranthe-style amp track.

Target:
- separate user guitar performance.

Selector:
- 20-second windows;
- 10-second hop;
- top 3 active windows combined into one reference profile.

Selected windows in the first real test:
- approximately **40–60 s**;
- approximately **100–120 s**;
- approximately **170–190 s**.

The three selected windows had closely clustered short-time dynamics around **2.67–2.73 dB**, showing that the selector was internally consistent rather than choosing arbitrary sections.

Against the resulting combined reference profile:

- EQ-only dynamic-range error: approximately **1.23 dB**;
- EQ + multiband + transient error: approximately **0.69 dB**;
- spectral error remained essentially unchanged at approximately **0.94 dB**;
- transient error improved modestly from approximately **1.12 dB** to **1.03 dB**.

Interpretation:
- multi-window profiling reduces reference-section sensitivity compared with using one arbitrary segment;
- however, the current selector still includes spectral similarity in its score;
- this risks preferring reference windows that already resemble the target tone instead of selecting primarily by performance/articulation type.

Decision:
- keep the multi-window framework;
- revise the window score so articulation/density descriptors drive selection and tonal descriptors remain the target to be matched, not the criterion used to choose the reference passage.
