from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import fftconvolve

from .analysis import long_term_spectrum
from .audio import AudioBuffer, rms, to_mono

_EPS = 1e-12


@dataclass(frozen=True)
class EqMatchResult:
    audio: AudioBuffer
    frequencies_hz: np.ndarray
    gain_db: np.ndarray


def derive_match_curve(
    reference: np.ndarray,
    target: np.ndarray,
    sample_rate: int,
    n_fft: int = 8192,
    max_gain_db: float = 12.0,
    smoothing_sigma_bins: float = 18.0,
    min_frequency_hz: float = 40.0,
    max_frequency_hz: float = 16000.0,
) -> tuple[np.ndarray, np.ndarray]:
    ref_f, ref_p = long_term_spectrum(reference, sample_rate, n_fft=n_fft, smoothing_sigma_bins=6.0)
    tgt_f, tgt_p = long_term_spectrum(target, sample_rate, n_fft=n_fft, smoothing_sigma_bins=6.0)

    if not np.array_equal(ref_f, tgt_f):
        raise RuntimeError("Reference/target frequency grids differ")

    delta_db = 10.0 * np.log10(np.maximum(ref_p, _EPS) / np.maximum(tgt_p, _EPS))
    delta_db = gaussian_filter1d(delta_db, smoothing_sigma_bins, mode="nearest")

    valid = (ref_f >= min_frequency_hz) & (ref_f <= min(max_frequency_hz, sample_rate * 0.5))

    # Tone matching must be independent of overall loudness. Remove the robust
    # broadband offset before limiting the shape correction.
    if np.any(valid):
        delta_db = delta_db - float(np.median(delta_db[valid]))

    delta_db = np.where(valid, delta_db, 0.0)
    delta_db = np.clip(delta_db, -abs(max_gain_db), abs(max_gain_db))

    return ref_f, delta_db


def _linear_phase_fir_from_curve(gain_db: np.ndarray, n_fft: int, fir_length: int) -> np.ndarray:
    if fir_length < 3:
        raise ValueError("fir_length must be >= 3")
    linear = np.power(10.0, gain_db / 20.0)
    full = np.concatenate([linear, linear[-2:0:-1]])
    impulse = np.fft.ifft(full).real

    impulse = np.roll(impulse, n_fft // 2)
    center = len(impulse) // 2
    half = fir_length // 2
    start = center - half
    stop = start + fir_length
    fir = impulse[start:stop].copy()

    window = np.hanning(fir_length)
    fir *= window

    dc = np.sum(fir)
    if abs(dc) > _EPS:
        fir /= dc
    return fir


def apply_match(
    reference: AudioBuffer,
    target: AudioBuffer,
    n_fft: int = 8192,
    fir_length: int = 2049,
    max_gain_db: float = 12.0,
) -> EqMatchResult:
    if reference.sample_rate != target.sample_rate:
        raise ValueError("Reference and target must have identical sample rates")

    freqs, gain_db = derive_match_curve(
        reference.data,
        target.data,
        reference.sample_rate,
        n_fft=n_fft,
        max_gain_db=max_gain_db,
    )

    fir = _linear_phase_fir_from_curve(gain_db, n_fft=n_fft, fir_length=fir_length)

    x = np.asarray(target.data, dtype=np.float64)
    if x.ndim == 1:
        y = fftconvolve(x, fir, mode="same")
    else:
        y = np.column_stack([fftconvolve(x[:, ch], fir, mode="same") for ch in range(x.shape[1])])

    target_rms = rms(to_mono(x))
    output_rms = rms(to_mono(y))
    if output_rms > _EPS:
        y *= target_rms / output_rms

    peak = np.max(np.abs(y))
    if peak > 0.999:
        y *= 0.999 / peak

    return EqMatchResult(
        audio=AudioBuffer(data=y, sample_rate=target.sample_rate),
        frequencies_hz=freqs,
        gain_db=gain_db,
    )
