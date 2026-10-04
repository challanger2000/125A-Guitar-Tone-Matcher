from __future__ import annotations

from dataclasses import dataclass

from .audio import AudioBuffer
from .dynamics import DynamicsMatchResult, match_dynamics
from .eq_match import EqMatchResult, apply_match


@dataclass(frozen=True)
class MatchPipelineResult:
    audio: AudioBuffer
    eq: EqMatchResult
    dynamics: DynamicsMatchResult


def apply_reference_match(reference: AudioBuffer, target: AudioBuffer) -> MatchPipelineResult:
    eq = apply_match(reference, target)
    dynamics = match_dynamics(reference, eq.audio)
    return MatchPipelineResult(audio=dynamics.audio, eq=eq, dynamics=dynamics)
