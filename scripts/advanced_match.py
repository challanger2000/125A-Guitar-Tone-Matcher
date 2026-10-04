from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from tone_matcher.advanced_pipeline import apply_advanced_match
from tone_matcher.analysis import analyse
from tone_matcher.audio import load_audio, resample_audio, save_audio
from tone_matcher.dynamics import robust_dynamic_range_db, transient_index_db
from tone_matcher.texture import texture_features


def main() -> int:
    parser = argparse.ArgumentParser(
        description="125A advanced research matcher: EQ + dynamics + transients + texture + residual EQ."
    )
    parser.add_argument("reference", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--curve-csv", type=Path)
    args = parser.parse_args()

    reference = load_audio(args.reference)
    target = load_audio(args.target)

    if reference.sample_rate != target.sample_rate:
        reference = resample_audio(reference, target.sample_rate)

    result = apply_advanced_match(reference, target)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_audio(args.output, result.audio)

    ref_texture = texture_features(reference.data, reference.sample_rate)
    before_texture = texture_features(target.data, target.sample_rate)
    after_texture = texture_features(result.audio.data, result.audio.sample_rate)

    report = {
        "reference": analyse(reference.data, reference.sample_rate).to_dict(),
        "target_before": analyse(target.data, target.sample_rate).to_dict(),
        "target_after": analyse(result.audio.data, result.audio.sample_rate).to_dict(),
        "dynamic_features": {
            "reference_dynamic_range_db": robust_dynamic_range_db(reference.data, reference.sample_rate),
            "target_before_dynamic_range_db": robust_dynamic_range_db(target.data, target.sample_rate),
            "target_after_dynamic_range_db": robust_dynamic_range_db(result.audio.data, result.audio.sample_rate),
            "reference_transient_index_db": transient_index_db(reference.data, reference.sample_rate),
            "target_before_transient_index_db": transient_index_db(target.data, target.sample_rate),
            "target_after_transient_index_db": transient_index_db(result.audio.data, result.audio.sample_rate),
        },
        "texture_features": {
            "reference": ref_texture.__dict__,
            "target_before": before_texture.__dict__,
            "target_after": after_texture.__dict__,
        },
        "controller": {
            "dynamic_scale": result.dynamics.dynamic_scale,
            "transient_gain_db": result.dynamics.transient_gain_db,
            "texture_family": result.texture.family,
            "texture_drive": result.texture.drive,
            "texture_mix": result.texture.mix,
            "texture_score_before": result.texture.score_before,
            "texture_score_after": result.texture.score_after,
        },
    }

    payload = json.dumps(report, indent=2, sort_keys=True)
    print(payload)

    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8")

    if args.curve_csv is not None:
        args.curve_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.curve_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["frequency_hz", "initial_gain_db", "residual_gain_db"])
            writer.writerows(
                zip(
                    result.initial_eq.frequencies_hz,
                    result.initial_eq.gain_db,
                    result.residual_eq.gain_db,
                )
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
