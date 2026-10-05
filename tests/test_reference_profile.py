from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfilt

from tone_matcher.audio import AudioBuffer
from tone_matcher.reference_profile import select_reference_windows


def test_reference_selector_prefers_spectrally_similar_active_window() -> None:
    sr = 44100
    rng = np.random.default_rng(125)
    seconds = 6
    n = sr * seconds

    target = 0.05 * rng.standard_normal(n)
    sos_dark = butter(2, 1000.0, btype="lowpass", fs=sr, output="sos")
    sos_close = butter(2, 5000.0, btype="lowpass", fs=sr, output="sos")

    wrong = sosfilt(sos_dark, target)
    close = sosfilt(sos_close, target)

    reference = np.concatenate([wrong, close, wrong])[:, None]
    target_audio = target[:, None]

    selection = select_reference_windows(
        AudioBuffer(reference, sr),
        AudioBuffer(target_audio, sr),
        window_seconds=seconds,
        hop_seconds=seconds,
        max_windows=1,
    )

    assert len(selection.windows) == 1
    # Middle window starts at 6 seconds.
    assert abs(selection.windows[0].start_seconds - 6.0) < 0.1
