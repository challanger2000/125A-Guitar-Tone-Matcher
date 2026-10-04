from __future__ import annotations

import numpy as np

from tone_matcher.audio import AudioBuffer
from tone_matcher.texture import match_texture, texture_features


def _distance(a, b) -> float:
    return 0.65 * abs(a.crest_db - b.crest_db) + 0.35 * abs(
        a.high_band_flatness_db - b.high_band_flatness_db
    )


def test_texture_search_improves_known_nonlinear_oracle() -> None:
    sr = 44100
    rng = np.random.default_rng(125)
    n = sr * 3
    t = np.arange(n) / sr

    target = (
        0.12 * np.sin(2.0 * np.pi * 110.0 * t)
        + 0.08 * np.sin(2.0 * np.pi * 220.0 * t)
        + 0.04 * rng.standard_normal(n)
    )

    reference = np.tanh(2.0 * target) / np.tanh(2.0)

    ref_f = texture_features(reference, sr)
    before_f = texture_features(target, sr)
    before = _distance(ref_f, before_f)

    result = match_texture(
        AudioBuffer(reference[:, None], sr),
        AudioBuffer(target[:, None], sr),
    )

    after_f = texture_features(result.audio.data, sr)
    after = _distance(ref_f, after_f)

    assert after < before
    assert result.family != "none"


def test_texture_search_can_choose_dry() -> None:
    sr = 44100
    rng = np.random.default_rng(125)
    x = 0.05 * rng.standard_normal(sr * 2)

    result = match_texture(
        AudioBuffer(x[:, None], sr),
        AudioBuffer(x[:, None], sr),
    )

    assert result.family == "none"
    assert result.mix == 0.0
    assert abs(result.score_after) < 1e-9
