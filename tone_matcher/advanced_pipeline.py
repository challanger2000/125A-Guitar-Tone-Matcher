from __future__ import annotations

from dataclasses import dataclass

from .audio import AudioBuffer
from .dynamics import DynamicsMatchResult, match_dynamics
from .eq_match import EqMatchResult, apply_match
from .texture import TextureMatchResult, match_texture


@dataclass(frozen=True)
class AdvancedMatchResult:
    audio: AudioBuffer
    initial_eq: EqMatchResult
    dynamics: DynamicsMatchResult
    texture: TextureMatchResult
    residual_eq: EqMatchResult
    final_dynamics: DynamicsMatchResult


def apply_advanced_match(reference: AudioBuffer, target: AudioBuffer) -> AdvancedMatchResult:
    # 1) Large spectral correction.
    initial_eq = apply_match(reference, target)

    # 2) Restore/match macro dynamics disturbed by the spectral correction.
    dynamics = match_dynamics(reference, initial_eq.audio)

    # 3) Optional nonlinear texture search. "none" remains a valid result.
    texture = match_texture(reference, dynamics.audio)

    # 4) Small bounded residual spectral correction after nonlinear/dynamic stages.
    residual_eq = apply_match(reference, texture.audio, max_gain_db=4.0)

    # 5) Residual EQ can perturb the level distribution again. Run a bounded
    #    second dynamics pass and transient correction at the very end.
    final_dynamics = match_dynamics(
        reference,
        residual_eq.audio,
        max_dynamic_gain_db=8.0,
        max_transient_gain_db=4.0,
    )

    return AdvancedMatchResult(
        audio=final_dynamics.audio,
        initial_eq=initial_eq,
        dynamics=dynamics,
        texture=texture,
        residual_eq=residual_eq,
        final_dynamics=final_dynamics,
    )
