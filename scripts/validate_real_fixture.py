from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

from tone_matcher.analysis import long_term_spectrum
from tone_matcher.audio import AudioBuffer, load_audio
from tone_matcher.dynamics import match_dynamics, robust_dynamic_range_db
from tone_matcher.eq_match import apply_match


def _spectral_error_db(reference: np.ndarray, candidate: np.ndarray, sample_rate: int) -> float:
    f_ref, p_ref = long_term_spectrum(reference, sample_rate)
    f_can, p_can = long_term_spectrum(candidate, sample_rate)
    if not np.array_equal(f_ref, f_can):
        raise RuntimeError("Spectrum grids differ")

    valid = (f_ref >= 80.0) & (f_ref <= 12000.0)
    ref_db = 10.0 * np.log10(np.maximum(p_ref[valid], 1e-12))
    can_db = 10.0 * np.log10(np.maximum(p_can[valid], 1e-12))
    delta = ref_db - can_db
    delta -= np.median(delta)
    return float(np.mean(np.abs(delta)))


def _apply_gain_envelope(data: np.ndarray, gain_db: np.ndarray) -> np.ndarray:
    gain = np.power(10.0, gain_db / 20.0)
    return data * gain[:, None]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the research matcher on one local real guitar fixture without committing audio."
    )
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()

    reference = load_audio(args.fixture)
    sr = reference.sample_rate
    x = np.asarray(reference.data, dtype=np.float64)

    # Spectral oracle: make the same performance deliberately brighter.
    sos = butter(2, 2500.0, btype="highpass", fs=sr, output="sos")
    bright = np.column_stack(
        [0.65 * x[:, ch] + 0.35 * sosfilt(sos, x[:, ch]) for ch in range(x.shape[1])]
    )

    spectral_before = _spectral_error_db(x, bright, sr)
    eq_result = apply_match(reference, AudioBuffer(bright, sr))
    spectral_after = _spectral_error_db(x, eq_result.audio.data, sr)

    # Dynamic oracle: deliberately expand the same performance.
    mono = np.mean(x, axis=1)
    window = max(1, round(sr * 0.040))
    kernel = np.ones(window, dtype=np.float64) / window
    envelope = np.sqrt(np.maximum(np.convolve(mono * mono, kernel, mode="same"), 1e-12))
    envelope_db = 20.0 * np.log10(np.maximum(envelope, 1e-12))
    center = float(np.median(envelope_db))
    gain_db = np.clip(0.45 * (envelope_db - center), -4.0, 4.0)
    expanded = _apply_gain_envelope(x, gain_db)

    dynamic_before = abs(
        robust_dynamic_range_db(x, sr) - robust_dynamic_range_db(expanded, sr)
    )
    dyn_result = match_dynamics(reference, AudioBuffer(expanded, sr))
    dynamic_after = abs(
        robust_dynamic_range_db(x, sr)
        - robust_dynamic_range_db(dyn_result.audio.data, sr)
    )

    result = {
        "sample_rate": sr,
        "frames": int(x.shape[0]),
        "channels": int(x.shape[1]),
        "spectral_error_db_before": spectral_before,
        "spectral_error_db_after": spectral_after,
        "spectral_improvement_db": spectral_before - spectral_after,
        "dynamic_range_error_db_before": dynamic_before,
        "dynamic_range_error_db_after": dynamic_after,
        "dynamic_improvement_db": dynamic_before - dynamic_after,
        "dynamic_scale": dyn_result.dynamic_scale,
        "pass": bool(
            spectral_after < spectral_before
            and dynamic_after < dynamic_before
        ),
    }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
