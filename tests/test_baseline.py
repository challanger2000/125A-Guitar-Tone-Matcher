from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfilt

from tone_matcher.analysis import long_term_spectrum
from tone_matcher.audio import AudioBuffer
from tone_matcher.eq_match import apply_match, derive_match_curve


def spectral_error_db(reference: np.ndarray, candidate: np.ndarray, sample_rate: int) -> float:
    f_ref, p_ref = long_term_spectrum(reference, sample_rate)
    f_can, p_can = long_term_spectrum(candidate, sample_rate)
    assert np.array_equal(f_ref, f_can)

    valid = (f_ref >= 80.0) & (f_ref <= 12000.0)
    ref_db = 10.0 * np.log10(np.maximum(p_ref[valid], 1e-12))
    can_db = 10.0 * np.log10(np.maximum(p_can[valid], 1e-12))

    # Remove global level offset; tone matching is judged independently of loudness.
    delta = ref_db - can_db
    delta -= np.median(delta)
    return float(np.mean(np.abs(delta)))


def test_identical_audio_produces_near_zero_curve() -> None:
    sr = 44100
    rng = np.random.default_rng(125)
    x = rng.standard_normal(sr * 2) * 0.05

    _, gain_db = derive_match_curve(x, x, sr)

    assert float(np.max(np.abs(gain_db))) < 1e-9


def test_eq_baseline_reduces_known_spectral_error() -> None:
    sr = 44100
    rng = np.random.default_rng(125)
    target = rng.standard_normal(sr * 4) * 0.05

    # Controlled oracle: same programme material through a known broad spectral tilt.
    sos = butter(2, 2200.0, btype="lowpass", fs=sr, output="sos")
    reference = sosfilt(sos, target)

    before = spectral_error_db(reference, target, sr)

    result = apply_match(
        AudioBuffer(reference[:, None], sr),
        AudioBuffer(target[:, None], sr),
        max_gain_db=12.0,
    )
    after = spectral_error_db(reference, result.audio.data[:, 0], sr)

    assert after < before
