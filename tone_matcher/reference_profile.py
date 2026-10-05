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
    activity_error: float
    onset_density_error: float
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


def _moving_rms(x: np.ndarray, window_samples: int) -> np.ndarray:
    w = max(1, int(window_samples))
    kernel = np.ones(w, dtype=np.float64) / w
    return np.sqrt(np.maximum(np.convolve(x * x, kernel, mode="same"), _EPS))


def _articulation_features(data: np.ndarray, sample_rate: int) -> tuple[float, float]:
    mono = to_mono(data)
    env = _moving_rms(mono, round(sample_rate * 0.010))
    env_db = 20.0 * np.log10(np.maximum(env, _EPS))

    peak_db = float(np.max(env_db))
    active = env_db > (peak_db - 30.0)
    activity_ratio = float(np.mean(active))

    # Attack density from positive short-time envelope slopes. This intentionally
    # avoids spectral/timbral information so window selection follows performance
    # type rather than the tone that we are trying to transfer.
    step = max(1, round(sample_rate * 0.005))
    sampled = env_db[::step]
    if sampled.size < 3:
        return activity_ratio, 0.0

    slope = np.diff(sampled)
    active_slope = slope[np.isfinite(slope)]
    if active_slope.size == 0:
        return activity_ratio, 0.0

    threshold = max(0.75, float(np.percentile(active_slope, 85.0)))
    onsets = active_slope > threshold
    duration_seconds = max(len(mono) / sample_rate, 1e-6)
    onset_density_hz = float(np.count_nonzero(onsets) / duration_seconds)
    return activity_ratio, onset_density_hz


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
    target_activity, target_onset_density = _articulation_features(tgt, sr)
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

        # Spectral/texture distances are retained for diagnostics only.
        # They do NOT influence selection because tone is the thing we want to match.
        try:
            spec = _spectral_error_db(chunk, tgt, sr)
        except ValueError:
            continue

        dyn = abs(robust_dynamic_range_db(chunk, sr) - target_dyn)
        tr = abs(transient_index_db(chunk, sr) - target_tr)

        activity, onset_density = _articulation_features(chunk, sr)
        activity_error = abs(activity - target_activity)
        onset_density_error = abs(onset_density - target_onset_density)

        tex = texture_features(chunk, sr)
        tex_error = (
            0.65 * abs(tex.crest_db - target_tex.crest_db)
            + 0.35 * abs(tex.high_band_flatness_db - target_tex.high_band_flatness_db)
        )

        # Articulation-first score: dynamics, attack prominence, active-density
        # and onset density only. No spectral or texture term is allowed here.
        total = (
            0.45 * dyn
            + 0.25 * tr
            + 4.0 * activity_error
            + 0.08 * onset_density_error
        )

        score = ReferenceWindowScore(
            start_seconds=start / sr,
            end_seconds=(start + len(chunk)) / sr,
            spectral_error_db=spec,
            dynamic_error_db=dyn,
            transient_error_db=tr,
            texture_error=tex_error,
            activity_error=activity_error,
            onset_density_error=onset_density_error,
            total_score=float(total),
        )
        candidates.append((score, chunk.copy()))

    if not candidates:
        return ReferenceSelection(audio=reference, windows=tuple())

    candidates.sort(key=lambda item: item[0].total_score)
    selected = candidates[: max(1, int(max_windows))]
    selected_audio = np.concatenate([chunk for _, chunk in selected], axis=0)

    return ReferenceSelection(
        audio=AudioBuffer(selected_audio, sr),
        windows=tuple(score for score, _ in selected),
    )
