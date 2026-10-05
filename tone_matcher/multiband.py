from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import butter, sosfiltfilt

from .audio import AudioBuffer, rms, to_mono
from .dynamics import robust_dynamic_range_db

_EPS = 1e-12


@dataclass(frozen=True)
class BandDynamics:
    low_hz: float
    high_hz: float
    reference_range_db: float
    target_range_db: float
    ratio: float


@dataclass(frozen=True)
class MultibandDynamicsResult:
    audio: AudioBuffer
    bands: tuple[BandDynamics, ...]


def _split_band(x: np.ndarray, sr: int, low: float, high: float) -> np.ndarray:
    nyq = 0.5 * sr
    if low <= 0.0:
        sos = butter(4, high, btype="lowpass", fs=sr, output="sos")
    elif high >= nyq * 0.999:
        sos = butter(4, low, btype="highpass", fs=sr, output="sos")
    else:
        sos = butter(4, [low, high], btype="bandpass", fs=sr, output="sos")
    return sosfiltfilt(sos, x, axis=0)


def _moving_rms(x: np.ndarray, window_samples: int) -> np.ndarray:
    window_samples = max(1, int(window_samples))
    power = np.asarray(x, dtype=np.float64) ** 2
    kernel = np.ones(window_samples, dtype=np.float64) / window_samples
    smoothed = np.convolve(power, kernel, mode="same")
    return np.sqrt(np.maximum(smoothed, _EPS))


def _band_gain_db(
    reference_band: np.ndarray,
    target_band: np.ndarray,
    sr: int,
    max_gain_db: float,
) -> tuple[np.ndarray, float, float, float]:
    ref_range = robust_dynamic_range_db(reference_band, sr, window_ms=20.0)
    tgt_range = robust_dynamic_range_db(target_band, sr, window_ms=20.0)
    ratio = 1.0 if tgt_range < 0.25 else float(np.clip(ref_range / tgt_range, 0.18, 1.80))

    mono = to_mono(target_band)
    env = _moving_rms(mono, round(sr * 0.020))
    env_db = 20.0 * np.log10(np.maximum(env, _EPS))
    finite = env_db[np.isfinite(env_db)]
    center = float(np.median(finite)) if finite.size else -120.0

    gain_db = (ratio - 1.0) * (env_db - center)
    gain_db = np.clip(gain_db, -abs(max_gain_db), abs(max_gain_db))
    gain_db = gaussian_filter1d(gain_db, sigma=max(1.0, sr * 0.004), mode="nearest")
    return gain_db, ref_range, tgt_range, ratio


def match_multiband_dynamics(
    reference: AudioBuffer,
    target: AudioBuffer,
    *,
    bands: tuple[tuple[float, float], ...] = (
        (60.0, 120.0),
        (120.0, 250.0),
        (250.0, 500.0),
        (500.0, 1000.0),
        (1000.0, 2500.0),
        (2500.0, 6000.0),
    ),
    max_gain_db: float = 10.0,
) -> MultibandDynamicsResult:
    if reference.sample_rate != target.sample_rate:
        raise ValueError("Reference and target must have identical sample rates")

    sr = target.sample_rate
    x = np.asarray(target.data, dtype=np.float64)
    r = np.asarray(reference.data, dtype=np.float64)

    wet = np.zeros_like(x)
    band_reports: list[BandDynamics] = []

    for low, high in bands:
        ref_band = _split_band(r, sr, low, high)
        tgt_band = _split_band(x, sr, low, high)
        gain_db, ref_range, tgt_range, ratio = _band_gain_db(
            ref_band,
            tgt_band,
            sr,
            max_gain_db,
        )
        gain = np.power(10.0, gain_db / 20.0)
        wet += tgt_band * gain[:, None]
        band_reports.append(
            BandDynamics(
                low_hz=low,
                high_hz=high,
                reference_range_db=ref_range,
                target_range_db=tgt_range,
                ratio=ratio,
            )
        )

    # Preserve frequency regions not covered by the analysis bands.
    covered = np.zeros_like(x)
    for low, high in bands:
        covered += _split_band(x, sr, low, high)
    wet += x - covered

    in_rms = rms(to_mono(x))
    out_rms = rms(to_mono(wet))
    if out_rms > _EPS:
        wet *= in_rms / out_rms

    peak = float(np.max(np.abs(wet)))
    if peak > 0.999:
        wet *= 0.999 / peak

    return MultibandDynamicsResult(
        audio=AudioBuffer(data=wet, sample_rate=sr),
        bands=tuple(band_reports),
    )
