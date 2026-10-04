from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


@dataclass(frozen=True)
class AudioBuffer:
    data: np.ndarray
    sample_rate: int


def load_audio(path: str | Path) -> AudioBuffer:
    data, sample_rate = sf.read(path, always_2d=True, dtype="float64")
    if data.size == 0:
        raise ValueError(f"Empty audio file: {path}")
    if not np.isfinite(data).all():
        raise ValueError(f"Audio contains NaN/Inf: {path}")
    return AudioBuffer(data=data, sample_rate=int(sample_rate))


def save_audio(path: str | Path, audio: AudioBuffer) -> None:
    out = np.asarray(audio.data, dtype=np.float32)
    sf.write(path, out, audio.sample_rate, subtype="FLOAT")


def to_mono(data: np.ndarray) -> np.ndarray:
    x = np.asarray(data, dtype=np.float64)
    if x.ndim == 1:
        return x
    if x.ndim != 2:
        raise ValueError("Audio must be 1-D mono or 2-D frames x channels")
    return np.mean(x, axis=1)


def resample_audio(audio: AudioBuffer, target_rate: int) -> AudioBuffer:
    if target_rate <= 0:
        raise ValueError("target_rate must be positive")
    if audio.sample_rate == target_rate:
        return audio

    from math import gcd

    g = gcd(audio.sample_rate, target_rate)
    up = target_rate // g
    down = audio.sample_rate // g
    data = resample_poly(audio.data, up, down, axis=0)
    return AudioBuffer(data=data, sample_rate=target_rate)


def rms(data: np.ndarray, eps: float = 1e-15) -> float:
    x = np.asarray(data, dtype=np.float64)
    return float(np.sqrt(np.mean(x * x) + eps))


def peak(data: np.ndarray) -> float:
    x = np.asarray(data, dtype=np.float64)
    return float(np.max(np.abs(x)))
