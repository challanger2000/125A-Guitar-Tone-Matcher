from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfilt

from tone_matcher.audio import AudioBuffer
from tone_matcher.dynamics import robust_dynamic_range_db
from tone_matcher.multiband import match_multiband_dynamics


def test_multiband_match_can_reduce_midband_dynamic_error() -> None:
    sr = 44100
    rng = np.random.default_rng(125)
    n = sr * 4
    x = rng.standard_normal(n) * 0.02

    sos = butter(4, [250.0, 1000.0], btype="bandpass", fs=sr, output="sos")
    mid = sosfilt(sos, x)

    target = x + 2.5 * mid
    reference = x + 0.55 * np.tanh(4.0 * mid)

    reference_mid = sosfilt(sos, reference)
    target_mid = sosfilt(sos, target)

    before = abs(
        robust_dynamic_range_db(reference_mid, sr, window_ms=20.0)
        - robust_dynamic_range_db(target_mid, sr, window_ms=20.0)
    )

    result = match_multiband_dynamics(
        AudioBuffer(reference[:, None], sr),
        AudioBuffer(target[:, None], sr),
    )

    result_mid = sosfilt(sos, result.audio.data[:, 0])

    after = abs(
        robust_dynamic_range_db(reference_mid, sr, window_ms=20.0)
        - robust_dynamic_range_db(result_mid, sr, window_ms=20.0)
    )

    assert after < before


def test_multiband_stays_neutral_when_band_dynamics_already_match() -> None:
    sr = 44100
    rng = np.random.default_rng(125)
    x = 0.03 * rng.standard_normal(sr * 3)

    result = match_multiband_dynamics(
        AudioBuffer(x[:, None], sr),
        AudioBuffer(x[:, None], sr),
    )

    assert all(abs(b.ratio - 1.0) < 1e-12 for b in result.bands)
    assert all(abs(b.applied_strength) < 1e-12 for b in result.bands)
    assert np.max(np.abs(result.audio.data[:, 0] - x)) < 1e-6
