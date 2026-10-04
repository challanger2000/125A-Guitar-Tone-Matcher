from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import gaussian_filter1d

from .audio import AudioBuffer, rms, to_mono

_EPS = 1e-12


@dataclass(frozen=True)
class DynamicsMatchResult:
    audio: AudioBuffer
    dynamic_scale: float
    transient_gain_db: float


def _moving_rms(x: np.ndarray, window_samples: int) -> np.ndarray:
    window_samples = max(1, int(window_samples))
    power = np.asarray(x, dtype=np.float64) ** 2
    kernel = np.ones(window_samples, dtype=np.float64) / window_samples
    smoothed = np.convolve(power, kernel, mode="same")
    return np.sqrt(np.maximum(smoothed, _EPS))


def _envelope_db(x: np.ndarray, sample_rate: int, window_ms: float) -> np.ndarray:
    env = _moving_rms(x, round(sample_rate * window_ms * 0.001))
    return 20.0 * np.log10(np.maximum(env, _EPS))


def robust_dynamic_range_db(data: np.ndarray, sample_rate: int, window_ms: float = 40.0) -> float:
    x = to_mono(data)
    env_db = _envelope_db(x, sample_rate, window_ms)
    finite = env_db[np.isfinite(env_db)]
    if finite.size == 0:
        return 0.0
    p10, p90 = np.percentile(finite, [10.0, 90.0])
    return float(max(0.0, p90 - p10))


def transient_index_db(data: np.ndarray, sample_rate: int) -> float:
    x = to_mono(data)
    fast = _envelope_db(x, sample_rate, 2.0)
    slow = _envelope_db(x, sample_rate, 30.0)
    delta = fast - slow
    finite = delta[np.isfinite(delta)]
    if finite.size == 0:
        return 0.0
    return float(np.percentile(finite, 90.0))


def _apply_gain_envelope(data: np.ndarray, gain_db: np.ndarray) -> np.ndarray:
    gain = np.power(10.0, gain_db / 20.0)
    x = np.asarray(data, dtype=np.float64)
    if x.ndim == 1:
        return x * gain
    return x * gain[:, None]


def match_dynamics(
    reference: AudioBuffer,
    target: AudioBuffer,
    *,
    max_dynamic_gain_db: float = 5.0,
    max_transient_gain_db: float = 3.0,
) -> DynamicsMatchResult:
    if reference.sample_rate != target.sample_rate:
        raise ValueError("Reference and target must have identical sample rates")

    sr = target.sample_rate
    ref_mono = to_mono(reference.data)
    tgt_mono = to_mono(target.data)

    ref_range = robust_dynamic_range_db(ref_mono, sr)
    tgt_range = robust_dynamic_range_db(tgt_mono, sr)

    if tgt_range < 0.25:
        dynamic_scale = 1.0
    else:
        dynamic_scale = float(np.clip(ref_range / tgt_range, 0.60, 1.60))

    env_db = _envelope_db(tgt_mono, sr, 40.0)
    center = float(np.median(env_db[np.isfinite(env_db)]))
    dynamic_gain_db = (dynamic_scale - 1.0) * (env_db - center)
    dynamic_gain_db = np.clip(dynamic_gain_db, -abs(max_dynamic_gain_db), abs(max_dynamic_gain_db))
    dynamic_gain_db = gaussian_filter1d(dynamic_gain_db, sigma=max(1.0, sr * 0.010), mode="nearest")

    y = _apply_gain_envelope(target.data, dynamic_gain_db)

    ref_transient = transient_index_db(reference.data, sr)
    tgt_transient = transient_index_db(y, sr)
    transient_gain_db = float(np.clip(ref_transient - tgt_transient, -abs(max_transient_gain_db), abs(max_transient_gain_db)))

    if abs(transient_gain_db) > 1e-6:
        fast = _envelope_db(to_mono(y), sr, 2.0)
        slow = _envelope_db(to_mono(y), sr, 30.0)
        transient_shape = np.maximum(0.0, fast - slow)
        norm = float(np.percentile(transient_shape, 95.0))
        if norm > 1e-6:
            weight = np.clip(transient_shape / norm, 0.0, 1.0)
            weight = gaussian_filter1d(weight, sigma=max(1.0, sr * 0.0015), mode="nearest")
            y = _apply_gain_envelope(y, transient_gain_db * weight)

    input_rms = rms(to_mono(target.data))
    output_rms = rms(to_mono(y))
    if output_rms > _EPS:
        y *= input_rms / output_rms

    peak = float(np.max(np.abs(y)))
    if peak > 0.999:
        y *= 0.999 / peak

    return DynamicsMatchResult(
        audio=AudioBuffer(data=y, sample_rate=sr),
        dynamic_scale=dynamic_scale,
        transient_gain_db=transient_gain_db,
    )
