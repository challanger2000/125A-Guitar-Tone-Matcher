# 125A Guitar Tone Matcher

Reference-based guitar tone matching for processed electric-guitar tracks.

## Status

**Research / prototype phase — not a product release.**

Development branch: `v0.1.0-research`

This project follows the current rules in `challanger2000/125A-Engineering`, especially:

- `START-HERE.md`
- `STANDARDS/AI-ASSISTED-ENGINEERING.md`
- `STANDARDS/DSP-GUIDELINES.md`
- `STANDARDS/PROFESSIONAL-PLUGIN-BEHAVIOR.md`
- `STANDARDS/REPOSITORY-WORKFLOW.md`
- `QA/AUDIO-FIXTURES.md`
- `QA/REALTIME-QA.md`
- `QA/RELEASE-QA.md`

## Product hypothesis

Given:

1. a **reference guitar recording** whose tonal/dynamic character is desired; and
2. a **different processed guitar recording** to be transformed,

the matcher should move the target toward the reference while preserving the target performance.

The project is **not** an amp capture system and does not require the reference and target to contain the same performance.

## Initial quality claim to prove

The matcher must outperform a strong long-term spectral / EQ-matching baseline on multiple independent guitar sources.

A more complex DSP or ML-assisted method is accepted only if it produces a reproducible improvement over that baseline.

## Planned research stages

1. Build deterministic analysis and EQ-match baseline.
2. Add dynamic and transient matching.
3. Add nonlinear / distortion-texture matching.
4. Add residual, perceptual and programme-material evaluation.
5. Compare rule-based DSP against ML-assisted parameter estimation.
6. Only after the architecture earns its complexity: integrate into a realtime VST3.

See:

- [RESEARCH.md](RESEARCH.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/MEASUREMENT-PLAN.md](docs/MEASUREMENT-PLAN.md)
- [docs/EXTERNAL-RESEARCH.md](docs/EXTERNAL-RESEARCH.md)

## Core engineering rule

No component is included because it sounds plausible.

For every material stage:

**define -> measure baseline -> implement -> measure again -> challenge -> regress -> then judge quality**

## Licensing

External repositories and papers may be used as research references. Incompatible source code is not copied into 125A products. Exact dependency and license decisions will be documented before any external code is integrated.


## Offline baseline harness

Install the research dependencies:

```bash
python -m pip install -r requirements.txt
```

Analyse one file:

```bash
python scripts/analyze.py "reference.wav" --json results/reference.json
```

Create the deterministic EQ-match baseline:

```bash
python scripts/eq_match.py "reference.wav" "target.wav" "results/target_eqmatch.wav" \
  --report results/report.json \
  --curve-csv results/match_curve.csv
```

Run the synthetic regression tests:

```bash
pytest -q
```

Local WAV/FLAC/AIFF files and research outputs are ignored by default and should not be committed to the public repository.
