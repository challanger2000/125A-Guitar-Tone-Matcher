from __future__ import annotations

import numpy as np

from tone_matcher.audio import AudioBuffer
from tone_matcher.reference_profile import select_reference_windows


def _bursty(sr: int, seconds: float, density_hz: float) -> np.ndarray:
    n = int(sr * seconds)
    t = np.arange(n) / sr
    carrier = 0.08 * np.sin(2.0 * np.pi * 180.0 * t)
    env = np.full(n, 0.08, dtype=np.float64)

    spacing = max(1, int(sr / density_hz))
    width = max(1, int(0.035 * sr))
    for i in range(0, n, spacing):
        env[i : min(n, i + width)] = 1.0

    return carrier * env


def test_reference_selector_prefers_similar_articulation_not_similar_tone() -> None:
    sr = 44100
    seconds = 6.0

    target = _bursty(sr, seconds, density_hz=4.0)

    # Wrong articulation but intentionally same broad tone.
    sparse = _bursty(sr, seconds, density_hz=1.0)

    # Correct articulation but altered tone/amplitude to ensure the selector is
    # not simply choosing the closest timbre.
    close_articulation = 0.55 * _bursty(sr, seconds, density_hz=4.0)

    reference = np.concatenate([sparse, close_articulation, sparse])[:, None]

    selection = select_reference_windows(
        AudioBuffer(reference, sr),
        AudioBuffer(target[:, None], sr),
        window_seconds=seconds,
        hop_seconds=seconds,
        max_windows=1,
    )

    assert len(selection.windows) == 1
    assert abs(selection.windows[0].start_seconds - 6.0) < 0.1


def test_selector_returns_multiple_ranked_windows() -> None:
    sr = 44100
    seconds = 4.0
    target = _bursty(sr, seconds, density_hz=3.0)

    reference = np.concatenate(
        [
            _bursty(sr, seconds, density_hz=1.0),
            _bursty(sr, seconds, density_hz=3.0),
            _bursty(sr, seconds, density_hz=3.2),
        ]
    )[:, None]

    selection = select_reference_windows(
        AudioBuffer(reference, sr),
        AudioBuffer(target[:, None], sr),
        window_seconds=seconds,
        hop_seconds=seconds,
        max_windows=2,
    )

    assert len(selection.windows) == 2
    assert selection.windows[0].total_score <= selection.windows[1].total_score
