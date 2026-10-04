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
