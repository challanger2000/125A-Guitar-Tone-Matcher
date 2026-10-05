from __future__ import annotations

from dataclasses import dataclass

from .audio import AudioBuffer
from .corpus import MatchDistance, match_distance
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
    eq_distance: MatchDistance
    full_distance: MatchDistance
    selected_variant: str


def _distance_score(distance: MatchDistance) -> float:
    # Spectral similarity remains the anchor. Dynamics and transients add value
    # beyond match-EQ, while high-band flatness protects against fizz damage.
    return (
        1.00 * distance.spectral_error_db
        + 0.50 * distance.dynamic_error_db
        + 0.30 * distance.transient_error_db
        + 0.20 * distance.high_band_flatness_error_db
    )


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

    eq_distance = match_distance(profiled_reference, initial_eq.audio)
    full_distance = match_distance(profiled_reference, texture.audio)

    eq_score = _distance_score(eq_distance)
    full_score = _distance_score(full_distance)

    # Never accept a "smarter" chain that materially damages the strong EQ
    # baseline. Full must win overall and must not worsen spectral similarity
    # by more than 0.10 dB or high-band flatness by more than 0.25 dB.
    full_is_safe = (
        full_distance.spectral_error_db
        <= eq_distance.spectral_error_db + 0.10
        and full_distance.high_band_flatness_error_db
        <= eq_distance.high_band_flatness_error_db + 0.25
    )
    use_full = full_is_safe and (full_score + 1e-9 < eq_score)

    if use_full:
        selected_audio = texture.audio
        selected_variant = "full"
    else:
        selected_audio = initial_eq.audio
        selected_variant = "eq_only"

    return AdvancedMatchResult(
        audio=selected_audio,
        reference_selection=reference_selection,
        initial_eq=initial_eq,
        multiband=multiband,
        final_dynamics=final_dynamics,
        texture=texture,
        eq_distance=eq_distance,
        full_distance=full_distance,
        selected_variant=selected_variant,
    )
