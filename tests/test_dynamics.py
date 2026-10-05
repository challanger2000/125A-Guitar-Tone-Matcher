from __future__ import annotations

import numpy as np

from tone_matcher.audio import AudioBuffer
from tone_matcher.dynamics import match_dynamics, robust_dynamic_range_db, transient_index_db


def _make_bursty_signal(sr: int, seconds: float = 4.0) -> np.ndarray:
    n = int(sr * seconds)
    t = np.arange(n) / sr
    carrier = np.sin(2.0 * np.pi * 180.0 * t)
    envelope = np.full(n, 0.12)

    for start in np.arange(0.2, seconds, 0.4):
        i0 = int(start * sr)
        i1 = min(n, i0 + int(0.05 * sr))
        envelope[i0:i1] = 1.0

    return 0.2 * carrier * envelope


def test_dynamic_match_moves_range_toward_reference() -> None:
    sr = 44100
    target = _make_bursty_signal(sr)

    # Oracle reference with deliberately reduced macro-dynamics.
    reference = np.tanh(target * 8.0) * 0.08

    before = abs(
        robust_dynamic_range_db(reference, sr)
        - robust_dynamic_range_db(target, sr)
    )

    result = match_dynamics(
        AudioBuffer(reference[:, None], sr),
        AudioBuffer(target[:, None], sr),
    )

    after = abs(
        robust_dynamic_range_db(reference, sr)
        - robust_dynamic_range_db(result.audio.data[:, 0], sr)
    )

    assert after < before


def test_identical_signal_keeps_dynamic_parameters_near_neutral() -> None:
    sr = 44100
    x = _make_bursty_signal(sr)
    result = match_dynamics(
        AudioBuffer(x[:, None], sr),
        AudioBuffer(x[:, None], sr),
    )

    assert abs(result.dynamic_scale - 1.0) < 1e-9
    assert abs(result.transient_gain_db) < 1e-9


def test_transient_index_is_higher_for_impulsive_version() -> None:
    sr = 44100
    smooth = _make_bursty_signal(sr)

    impulsive = smooth.copy()
    for start in np.arange(0.2, 4.0, 0.4):
        idx = int(start * sr)
        impulsive[idx:idx + 12] += 0.5

    assert transient_index_db(impulsive, sr) > transient_index_db(smooth, sr)


def test_strong_reference_compression_reduces_dynamic_scale_below_unity() -> None:
    sr = 44100
    target = _make_bursty_signal(sr)
    reference = np.tanh(target * 10.0) * 0.07

    result = match_dynamics(
        AudioBuffer(reference[:, None], sr),
        AudioBuffer(target[:, None], sr),
    )

    assert result.dynamic_scale < 1.0
    assert abs(
        robust_dynamic_range_db(reference, sr)
        - robust_dynamic_range_db(result.audio.data[:, 0], sr)
    ) < abs(
        robust_dynamic_range_db(reference, sr)
        - robust_dynamic_range_db(target, sr)
    )
