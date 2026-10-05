from __future__ import annotations

from tone_matcher.advanced_pipeline import _distance_score
from tone_matcher.corpus import MatchDistance


def test_distance_score_prefers_better_non_eq_result_when_spectrum_is_preserved() -> None:
    eq = MatchDistance(
        spectral_error_db=0.90,
        dynamic_error_db=1.20,
        transient_error_db=1.00,
        high_band_flatness_error_db=0.10,
    )
    full = MatchDistance(
        spectral_error_db=0.92,
        dynamic_error_db=0.35,
        transient_error_db=0.85,
        high_band_flatness_error_db=0.12,
    )

    assert _distance_score(full) < _distance_score(eq)


def test_distance_score_rejects_large_overall_regression() -> None:
    eq = MatchDistance(
        spectral_error_db=1.00,
        dynamic_error_db=0.50,
        transient_error_db=0.50,
        high_band_flatness_error_db=0.10,
    )
    bad_full = MatchDistance(
        spectral_error_db=1.40,
        dynamic_error_db=0.40,
        transient_error_db=0.40,
        high_band_flatness_error_db=0.50,
    )

    assert _distance_score(bad_full) > _distance_score(eq)
