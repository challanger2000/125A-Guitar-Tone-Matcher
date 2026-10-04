from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import get_window, stft

from .audio import rms, to_mono

_EPS = 1e-12


@dataclass(frozen=True)
class ToneMetrics:
    sample_rate: int
    duration_seconds: float
    channels: int
    peak_dbfs: float
    rms_dbfs: float
    crest_db: float
    spectral_centroid_hz: float
    spectral_rolloff_95_hz: float
    spectral_flatness_db: float
    low_80_ratio_db: float
    high_6000_ratio_db: float

    def to_dict(self) -> dict:
        return asdict(self)


def amp_to_db(value: float, floor_db: float = -240.0) -> float:
    if value <= 0.0:
        return floor_db
    return max(floor_db, 20.0 * np.log10(value))


def long_term_spectrum(
    data: np.ndarray,
    sample_rate: int,
    n_fft: int = 8192,
    hop: int | None = None,
    smoothing_sigma_bins: float = 6.0,
) -> tuple[np.ndarray, np.ndarray]:
    mono = to_mono(data)
    if hop is None:
        hop = n_fft // 4
    noverlap = max(0, n_fft - hop)
    _, _, z = stft(
        mono,
        fs=sample_rate,
        window=get_window("hann", n_fft, fftbins=True),
        nperseg=n_fft,
        noverlap=noverlap,
        nfft=n_fft,
        boundary=None,
        padded=False,
    )
    magnitude = np.abs(z)
    if magnitude.size == 0:
        raise ValueError("Audio is too short for requested FFT size")
    power = np.median(magnitude * magnitude, axis=1)
    power = np.maximum(power, _EPS)
    if smoothing_sigma_bins > 0:
        power_db = 10.0 * np.log10(power)
        power_db = gaussian_filter1d(power_db, smoothing_sigma_bins, mode="nearest")
        power = np.power(10.0, power_db / 10.0)
    freqs = np.fft.rfftfreq(n_fft, 1.0 / sample_rate)
    return freqs, power


def _weighted_centroid(freqs: np.ndarray, power: np.ndarray) -> float:
    total = float(np.sum(power))
    if total <= _EPS:
        return 0.0
    return float(np.sum(freqs * power) / total)


def _rolloff(freqs: np.ndarray, power: np.ndarray, fraction: float = 0.95) -> float:
    cumulative = np.cumsum(power)
    total = float(cumulative[-1])
    if total <= _EPS:
        return 0.0
    idx = int(np.searchsorted(cumulative, fraction * total, side="left"))
    idx = min(idx, len(freqs) - 1)
    return float(freqs[idx])


def _flatness_db(power: np.ndarray) -> float:
    p = np.maximum(power, _EPS)
    geo = float(np.exp(np.mean(np.log(p))))
    arith = float(np.mean(p))
    return 10.0 * np.log10(max(geo / max(arith, _EPS), _EPS))


def _band_ratio_db(freqs: np.ndarray, power: np.ndarray, mask: np.ndarray) -> float:
    total = float(np.sum(power))
    band = float(np.sum(power[mask]))
    return 10.0 * np.log10(max(band, _EPS) / max(total, _EPS))


def analyse(data: np.ndarray, sample_rate: int) -> ToneMetrics:
    x = np.asarray(data, dtype=np.float64)
    channels = 1 if x.ndim == 1 else int(x.shape[1])
    mono = to_mono(x)

    p = float(np.max(np.abs(mono)))
    r = rms(mono)
    crest = amp_to_db(p / max(r, _EPS))

    freqs, power = long_term_spectrum(x, sample_rate)
    nyquist = sample_rate * 0.5
    valid = (freqs >= 20.0) & (freqs <= min(20000.0, nyquist))
    vf = freqs[valid]
    vp = power[valid]

    return ToneMetrics(
        sample_rate=int(sample_rate),
        duration_seconds=float(len(mono) / sample_rate),
        channels=channels,
        peak_dbfs=amp_to_db(p),
        rms_dbfs=amp_to_db(r),
        crest_db=crest,
        spectral_centroid_hz=_weighted_centroid(vf, vp),
        spectral_rolloff_95_hz=_rolloff(vf, vp, 0.95),
        spectral_flatness_db=_flatness_db(vp),
        low_80_ratio_db=_band_ratio_db(vf, vp, vf < 80.0),
        high_6000_ratio_db=_band_ratio_db(vf, vp, vf > 6000.0),
    )
