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
