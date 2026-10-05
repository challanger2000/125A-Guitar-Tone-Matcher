from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .analysis import long_term_spectrum
from .audio import AudioBuffer
from .dynamics import robust_dynamic_range_db, transient_index_db
from .texture import texture_features

_EPS = 1e-12


@dataclass(frozen=True)
class MatchDistance:
    spectral_error_db: float
    dynamic_error_db: float
    transient_error_db: float
    high_band_flatness_error_db: float

    def to_dict(self) -> dict:
        return asdict(self)


def spectral_error_db(reference: np.ndarray, candidate: np.ndarray, sample_rate: int) -> float:
    f_ref, p_ref = long_term_spectrum(reference, sample_rate)
    f_can, p_can = long_term_spectrum(candidate, sample_rate)

    valid = (f_ref >= 80.0) & (f_ref <= min(12000.0, sample_rate * 0.5))
    ref_db = 10.0 * np.log10(np.maximum(p_ref[valid], _EPS))
    can_db = 10.0 * np.log10(np.maximum(p_can[valid], _EPS))
    delta = ref_db - can_db
    delta -= np.median(delta)
    return float(np.mean(np.abs(delta)))


def match_distance(reference: AudioBuffer, candidate: AudioBuffer) -> MatchDistance:
    if reference.sample_rate != candidate.sample_rate:
        raise ValueError("Reference and candidate must have identical sample rates")

    sr = reference.sample_rate
    ref_tex = texture_features(reference.data, sr)
    can_tex = texture_features(candidate.data, sr)

    return MatchDistance(
        spectral_error_db=spectral_error_db(reference.data, candidate.data, sr),
        dynamic_error_db=abs(
            robust_dynamic_range_db(reference.data, sr)
            - robust_dynamic_range_db(candidate.data, sr)
        ),
        transient_error_db=abs(
            transient_index_db(reference.data, sr)
            - transient_index_db(candidate.data, sr)
        ),
        high_band_flatness_error_db=abs(
            ref_tex.high_band_flatness_db - can_tex.high_band_flatness_db
        ),
    )
