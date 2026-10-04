from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import resample_poly

from .analysis import analyse, long_term_spectrum
from .audio import AudioBuffer, rms, to_mono

_EPS = 1e-12


@dataclass(frozen=True)
class TextureFeatures:
    crest_db: float
    high_band_flatness_db: float


@dataclass(frozen=True)
class TextureMatchResult:
    audio: AudioBuffer
    family: str
    drive: float
    mix: float
    score_before: float
    score_after: float


def _high_band_flatness_db(data: np.ndarray, sample_rate: int) -> float:
    freqs, power = long_term_spectrum(data, sample_rate, n_fft=8192, smoothing_sigma_bins=2.0)
    upper = min(12000.0, sample_rate * 0.5)
    mask = (freqs >= 3000.0) & (freqs <= upper)
    p = np.maximum(power[mask], _EPS)
    if p.size == 0:
        return 0.0
    geometric = float(np.exp(np.mean(np.log(p))))
    arithmetic = float(np.mean(p))
    return 10.0 * np.log10(max(geometric / max(arithmetic, _EPS), _EPS))


def texture_features(data: np.ndarray, sample_rate: int) -> TextureFeatures:
    metrics = analyse(data, sample_rate)
    return TextureFeatures(
        crest_db=metrics.crest_db,
        high_band_flatness_db=_high_band_flatness_db(data, sample_rate),
    )


def _feature_distance(a: TextureFeatures, b: TextureFeatures) -> float:
    crest = abs(a.crest_db - b.crest_db)
    flatness = abs(a.high_band_flatness_db - b.high_band_flatness_db)
    return float(0.65 * crest + 0.35 * flatness)


def _shape(x: np.ndarray, family: str, drive: float) -> np.ndarray:
    if family == "tanh":
        normalizer = np.tanh(drive)
        return np.tanh(drive * x) / max(abs(normalizer), _EPS)
    if family == "atan":
        normalizer = np.arctan(drive)
        return np.arctan(drive * x) / max(abs(normalizer), _EPS)
    if family == "softclip":
        z = drive * x
        return z / np.sqrt(1.0 + z * z)
    raise ValueError(f"Unknown saturation family: {family}")


def _saturate_oversampled(
    data: np.ndarray,
    family: str,
    drive: float,
    mix: float,
    oversample: int = 2,
) -> np.ndarray:
    x = np.asarray(data, dtype=np.float64)
    mono_input = x.ndim == 1
    if mono_input:
        x = x[:, None]

    up = resample_poly(x, oversample, 1, axis=0)
    wet = _shape(up, family, drive)
    wet = resample_poly(wet, 1, oversample, axis=0)
    wet = wet[: x.shape[0]]

    y = (1.0 - mix) * x + mix * wet

    in_rms = rms(to_mono(x))
    out_rms = rms(to_mono(y))
    if out_rms > _EPS:
        y *= in_rms / out_rms

    peak = float(np.max(np.abs(y)))
    if peak > 0.999:
        y *= 0.999 / peak

    return y[:, 0] if mono_input else y


def match_texture(
    reference: AudioBuffer,
    target: AudioBuffer,
    *,
    families: tuple[str, ...] = ("tanh", "atan", "softclip"),
    drives: tuple[float, ...] = (1.15, 1.35, 1.7, 2.2, 3.0),
    mixes: tuple[float, ...] = (0.20, 0.40, 0.65),
    oversample: int = 2,
) -> TextureMatchResult:
    if reference.sample_rate != target.sample_rate:
        raise ValueError("Reference and target must have identical sample rates")

    sr = target.sample_rate
    ref_features = texture_features(reference.data, sr)
    dry_features = texture_features(target.data, sr)
    best_score = _feature_distance(ref_features, dry_features)
    best_audio = np.asarray(target.data, dtype=np.float64).copy()
    best_family = "none"
    best_drive = 1.0
    best_mix = 0.0

    for family in families:
        for drive in drives:
            for mix in mixes:
                candidate = _saturate_oversampled(
                    target.data,
                    family=family,
                    drive=drive,
                    mix=mix,
                    oversample=oversample,
                )
                score = _feature_distance(ref_features, texture_features(candidate, sr))
                if score + 1e-9 < best_score:
                    best_score = score
                    best_audio = candidate
                    best_family = family
                    best_drive = float(drive)
                    best_mix = float(mix)

    return TextureMatchResult(
        audio=AudioBuffer(data=best_audio, sample_rate=sr),
        family=best_family,
        drive=best_drive,
        mix=best_mix,
        score_before=_feature_distance(ref_features, dry_features),
        score_after=best_score,
    )
