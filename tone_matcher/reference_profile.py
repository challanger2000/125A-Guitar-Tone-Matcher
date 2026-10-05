from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .analysis import long_term_spectrum
from .audio import AudioBuffer, to_mono
from .dynamics import robust_dynamic_range_db, transient_index_db
from .texture import texture_features

_EPS = 1e-12


@dataclass(frozen=True)
class ReferenceWindowScore:
    start_seconds: float
    end_seconds: float
    spectral_error_db: float
    dynamic_error_db: float
    transient_error_db: float
    texture_error: float
    total_score: float


@dataclass(frozen=True)
class ReferenceSelection:
    audio: AudioBuffer
    windows: tuple[ReferenceWindowScore, ...]


def _spectral_error_db(reference: np.ndarray, candidate: np.ndarray, sample_rate: int) -> float:
    f_ref, p_ref = long_term_spectrum(reference, sample_rate)
    f_can, p_can = long_term_spectrum(candidate, sample_rate)

    valid = (f_ref >= 80.0) & (f_ref <= min(12000.0, sample_rate * 0.5))
    ref_db = 10.0 * np.log10(np.maximum(p_ref[valid], _EPS))
    can_db = 10.0 * np.log10(np.maximum(p_can[valid], _EPS))
    delta = ref_db - can_db
    delta -= np.median(delta)
    return float(np.mean(np.abs(delta)))


def _window_activity_db(data: np.ndarray) -> float:
    mono = to_mono(data)
    peak = float(np.max(np.abs(mono)))
    if peak <= _EPS:
        return -240.0
    return float(20.0 * np.log10(peak))


def select_reference_windows(
    reference: AudioBuffer,
    target: AudioBuffer,
    *,
    window_seconds: float = 20.0,
    hop_seconds: float = 10.0,
    max_windows: int = 3,
    activity_threshold_dbfs: float = -45.0,
) -> ReferenceSelection:
    if reference.sample_rate != target.sample_rate:
        raise ValueError("Reference and target must have identical sample rates")
    if window_seconds <= 0.0 or hop_seconds <= 0.0:
        raise ValueError("window_seconds and hop_seconds must be positive")

    sr = reference.sample_rate
    ref = np.asarray(reference.data, dtype=np.float64)
    tgt = np.asarray(target.data, dtype=np.float64)

    window = max(1, int(round(window_seconds * sr)))
    hop = max(1, int(round(hop_seconds * sr)))

    target_dyn = robust_dynamic_range_db(tgt, sr)
    target_tr = transient_index_db(tgt, sr)
    target_tex = texture_features(tgt, sr)

    candidates: list[tuple[ReferenceWindowScore, np.ndarray]] = []

    if ref.shape[0] <= window:
        starts = [0]
        window = ref.shape[0]
    else:
        starts = list(range(0, ref.shape[0] - window + 1, hop))
        last = ref.shape[0] - window
        if starts[-1] != last:
            starts.append(last)

    for start in starts:
        chunk = ref[start : start + window]
        if _window_activity_db(chunk) < activity_threshold_dbfs:
            continue

        try:
            spec = _spectral_error_db(chunk, tgt, sr)
        except ValueError:
            continue

        dyn = abs(robust_dynamic_range_db(chunk, sr) - target_dyn)
        tr = abs(transient_index_db(chunk, sr) - target_tr)

        tex = texture_features(chunk, sr)
        tex_error = (
            0.65 * abs(tex.crest_db - target_tex.crest_db)
            + 0.35 * abs(tex.high_band_flatness_db - target_tex.high_band_flatness_db)
        )

        # Spectral shape is the primary selector; dynamics/transients/textural
        # descriptors break ties so we prefer reference passages with similar
        # articulation rather than only similar EQ.
        total = spec + 0.35 * dyn + 0.20 * tr + 0.15 * tex_error

        score = ReferenceWindowScore(
            start_seconds=start / sr,
            end_seconds=(start + len(chunk)) / sr,
            spectral_error_db=spec,
            dynamic_error_db=dyn,
            transient_error_db=tr,
            texture_error=tex_error,
            total_score=float(total),
        )
        candidates.append((score, chunk.copy()))

    if not candidates:
        return ReferenceSelection(audio=reference, windows=tuple())

    candidates.sort(key=lambda item: item[0].total_score)
    selected = candidates[: max(1, int(max_windows))]

    # Concatenate several best windows. Downstream analyzers then see a robust
    # profile instead of one potentially unrepresentative moment.
    selected_audio = np.concatenate([chunk for _, chunk in selected], axis=0)

    return ReferenceSelection(
        audio=AudioBuffer(selected_audio, sr),
        windows=tuple(score for score, _ in selected),
    )
