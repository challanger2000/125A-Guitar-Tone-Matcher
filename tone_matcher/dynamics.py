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


def _active_envelope(env_db: np.ndarray, gate_below_peak_db: float = 50.0) -> np.ndarray:
    finite = env_db[np.isfinite(env_db)]
    if finite.size == 0:
        return finite
    gate = float(np.max(finite) - abs(gate_below_peak_db))
    active = finite[finite > gate]
    return active if active.size else finite


def robust_dynamic_range_db(
    data: np.ndarray,
    sample_rate: int,
    window_ms: float = 40.0,
    gate_below_peak_db: float = 50.0,
) -> float:
    x = to_mono(data)
    env_db = _envelope_db(x, sample_rate, window_ms)
    active = _active_envelope(env_db, gate_below_peak_db)
    if active.size == 0:
        return 0.0
    p10, p90 = np.percentile(active, [10.0, 90.0])
    return float(max(0.0, p90 - p10))


def transient_index_db(data: np.ndarray, sample_rate: int) -> float:
    x = to_mono(data)
    slow = _moving_rms(x, round(sample_rate * 0.030))
    peak_to_body_db = 20.0 * np.log10(
        np.maximum(np.abs(x), _EPS) / np.maximum(slow, _EPS)
    )
    finite = peak_to_body_db[np.isfinite(peak_to_body_db)]
    if finite.size == 0:
        return 0.0
    return float(np.percentile(finite, 99.95))


def _apply_gain_envelope(data: np.ndarray, gain_db: np.ndarray) -> np.ndarray:
    gain = np.power(10.0, gain_db / 20.0)
    x = np.asarray(data, dtype=np.float64)
    if x.ndim == 1:
        return x * gain
    return x * gain[:, None]


def _quantile_dynamic_gain_db(
    reference: np.ndarray,
    target: np.ndarray,
    sample_rate: int,
    *,
    max_dynamic_gain_db: float,
    gate_below_peak_db: float = 50.0,
) -> tuple[np.ndarray, float]:
    ref_env = _envelope_db(to_mono(reference), sample_rate, 40.0)
    tgt_env = _envelope_db(to_mono(target), sample_rate, 40.0)

    ref_active = _active_envelope(ref_env, gate_below_peak_db)
    tgt_active = _active_envelope(tgt_env, gate_below_peak_db)

    if ref_active.size < 16 or tgt_active.size < 16:
        return np.zeros_like(tgt_env), 1.0

    ref_range = float(np.percentile(ref_active, 90.0) - np.percentile(ref_active, 10.0))
    tgt_range = float(np.percentile(tgt_active, 90.0) - np.percentile(tgt_active, 10.0))
    dynamic_scale = 1.0 if tgt_range < 0.25 else float(ref_range / tgt_range)

    # Distribution matching: map target envelope quantiles to the reference
    # envelope shape. This does not require the same performance or timing.
    q = np.linspace(0.02, 0.98, 65)
    ref_q = np.quantile(ref_active, q)
    tgt_q = np.quantile(tgt_active, q)

    ref_median = float(np.median(ref_active))
    tgt_median = float(np.median(tgt_active))
    ref_rel = ref_q - ref_median
    tgt_rel = tgt_q - tgt_median

    # Guard against duplicate quantile positions in extremely static material.
    tgt_rel = np.maximum.accumulate(tgt_rel + np.arange(tgt_rel.size) * 1e-9)

    tgt_env_rel = tgt_env - tgt_median
    desired_rel = np.interp(
        tgt_env_rel,
        tgt_rel,
        ref_rel,
        left=ref_rel[0],
        right=ref_rel[-1],
    )

    gain_db = desired_rel - tgt_env_rel

    # Fade the controller out into deep silence so pauses/noise floors are not
    # lifted merely to imitate the reference distribution.
    tgt_peak = float(np.max(tgt_env))
    gate_start = tgt_peak - (gate_below_peak_db + 10.0)
    gate_end = tgt_peak - gate_below_peak_db
    activity = np.clip((tgt_env - gate_start) / max(gate_end - gate_start, 1e-6), 0.0, 1.0)
    gain_db *= activity

    gain_db = np.clip(gain_db, -abs(max_dynamic_gain_db), abs(max_dynamic_gain_db))
    gain_db = gaussian_filter1d(
        gain_db,
        sigma=max(1.0, sample_rate * 0.008),
        mode="nearest",
    )
    return gain_db, dynamic_scale


def match_dynamics(
    reference: AudioBuffer,
    target: AudioBuffer,
    *,
    max_dynamic_gain_db: float = 18.0,
    max_transient_gain_db: float = 4.0,
) -> DynamicsMatchResult:
    if reference.sample_rate != target.sample_rate:
        raise ValueError("Reference and target must have identical sample rates")

    sr = target.sample_rate

    # Exact identity is a hard neutral case. Avoid numerical envelope/smoothing
    # differences causing a meaningless sub-hundredth-dB transient correction.
    if reference.data.shape == target.data.shape and np.array_equal(reference.data, target.data):
        return DynamicsMatchResult(
            audio=AudioBuffer(data=np.asarray(target.data, dtype=np.float64).copy(), sample_rate=sr),
            dynamic_scale=1.0,
            transient_gain_db=0.0,
        )

    dynamic_gain_db, dynamic_scale = _quantile_dynamic_gain_db(
        reference.data,
        target.data,
        sr,
        max_dynamic_gain_db=max_dynamic_gain_db,
    )
    y = _apply_gain_envelope(target.data, dynamic_gain_db)

    ref_transient = transient_index_db(reference.data, sr)
    tgt_transient = transient_index_db(y, sr)
    transient_gain_db = float(
        np.clip(
            ref_transient - tgt_transient,
            -abs(max_transient_gain_db),
            abs(max_transient_gain_db),
        )
    )

    if abs(transient_gain_db) > 1e-6:
        mono_y = to_mono(y)
        slow = _moving_rms(mono_y, round(sr * 0.030))
        transient_shape = np.maximum(
            0.0,
            20.0 * np.log10(
                np.maximum(np.abs(mono_y), _EPS) / np.maximum(slow, _EPS)
            ),
        )
        norm = float(np.percentile(transient_shape, 95.0))
        if norm > 1e-6:
            weight = np.clip(transient_shape / norm, 0.0, 1.0)
            weight = gaussian_filter1d(
                weight,
                sigma=max(1.0, sr * 0.0015),
                mode="nearest",
            )
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
