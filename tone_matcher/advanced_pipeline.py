from __future__ import annotations

from dataclasses import dataclass

from .audio import AudioBuffer
from .dynamics import DynamicsMatchResult, match_dynamics
from .eq_match import EqMatchResult, apply_match
from .multiband import MultibandDynamicsResult, match_multiband_dynamics
from .texture import TextureMatchResult, match_texture


@dataclass(frozen=True)
class AdvancedMatchResult:
    audio: AudioBuffer
    initial_eq: EqMatchResult
    multiband: MultibandDynamicsResult
    final_dynamics: DynamicsMatchResult
    texture: TextureMatchResult


def apply_advanced_match(reference: AudioBuffer, target: AudioBuffer) -> AdvancedMatchResult:
    # 1) Large, level-independent spectral correction.
    initial_eq = apply_match(reference, target)

    # 2) Match frequency-dependent dynamics. This is the first stage that
    #    provides a clear measurable benefit beyond EQ-only on real fixtures.
    multiband = match_multiband_dynamics(reference, initial_eq.audio)

    # 3) Use the broadband dynamics block only as a bounded final
    #    distribution/transient correction, after the per-band behaviour is set.
    final_dynamics = match_dynamics(
        reference,
        multiband.audio,
        max_dynamic_gain_db=4.0,
        max_transient_gain_db=4.0,
    )

    # 4) Texture remains experimental and is allowed to select NONE.
    #    It is evaluated after dynamics so it cannot hide dynamic mismatch.
    texture = match_texture(reference, final_dynamics.audio)

    return AdvancedMatchResult(
        audio=texture.audio,
        initial_eq=initial_eq,
        multiband=multiband,
        final_dynamics=final_dynamics,
        texture=texture,
    )
