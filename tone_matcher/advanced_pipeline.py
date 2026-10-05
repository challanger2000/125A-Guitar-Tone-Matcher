from __future__ import annotations

from dataclasses import dataclass

from .audio import AudioBuffer
from .dynamics import DynamicsMatchResult, match_dynamics
from .eq_match import EqMatchResult, apply_match
from .multiband import MultibandDynamicsResult, match_multiband_dynamics
from .reference_profile import ReferenceSelection, select_reference_windows
from .texture import TextureMatchResult, match_texture


@dataclass(frozen=True)
class AdvancedMatchResult:
    audio: AudioBuffer
    reference_selection: ReferenceSelection
    initial_eq: EqMatchResult
    multiband: MultibandDynamicsResult
    final_dynamics: DynamicsMatchResult
    texture: TextureMatchResult


def apply_advanced_match(reference: AudioBuffer, target: AudioBuffer) -> AdvancedMatchResult:
    # Long reference files may contain different riffs, articulations and density.
    # Build a robust profile from the best-matching active windows first.
    reference_selection = select_reference_windows(
        reference,
        target,
        window_seconds=20.0,
        hop_seconds=10.0,
        max_windows=3,
    )
    profiled_reference = reference_selection.audio

    # 1) Large, level-independent spectral correction.
    initial_eq = apply_match(profiled_reference, target)

    # 2) Match frequency-dependent dynamics against comparable reference passages.
    multiband = match_multiband_dynamics(profiled_reference, initial_eq.audio)

    # 3) Bounded final distribution/transient correction.
    final_dynamics = match_dynamics(
        profiled_reference,
        multiband.audio,
        max_dynamic_gain_db=4.0,
        max_transient_gain_db=4.0,
    )

    # 4) Texture remains experimental and is allowed to select NONE.
    texture = match_texture(profiled_reference, final_dynamics.audio)

    return AdvancedMatchResult(
        audio=texture.audio,
        reference_selection=reference_selection,
        initial_eq=initial_eq,
        multiband=multiband,
        final_dynamics=final_dynamics,
        texture=texture,
    )
