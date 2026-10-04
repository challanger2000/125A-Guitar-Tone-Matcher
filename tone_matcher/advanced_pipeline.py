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


def apply_advanced_match(reference: AudioBuffer, target: AudioBuffer) -> AdvancedMatchResult:
    initial_eq = apply_match(reference, target)
    dynamics = match_dynamics(reference, initial_eq.audio)
    texture = match_texture(reference, dynamics.audio)
    residual_eq = apply_match(reference, texture.audio, max_gain_db=4.0)

    return AdvancedMatchResult(
        audio=residual_eq.audio,
        initial_eq=initial_eq,
        dynamics=dynamics,
        texture=texture,
        residual_eq=residual_eq,
    )
