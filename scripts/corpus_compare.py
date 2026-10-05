from __future__ import annotations

import argparse
import json
from pathlib import Path

from tone_matcher.advanced_pipeline import apply_advanced_match
from tone_matcher.audio import load_audio, resample_audio
from tone_matcher.corpus import match_distance
from tone_matcher.eq_match import apply_match


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare original, EQ-only and full matcher across multiple local guitar pairs."
    )
    parser.add_argument(
        "--pair",
        action="append",
        nargs=3,
        metavar=("NAME", "REFERENCE", "TARGET"),
        required=True,
        help="Repeat for each validation pair.",
    )
    parser.add_argument("--json", type=Path, dest="json_path")
    args = parser.parse_args()

    rows = []
    for name, reference_path, target_path in args.pair:
        reference = load_audio(reference_path)
        target = load_audio(target_path)
        if reference.sample_rate != target.sample_rate:
            reference = resample_audio(reference, target.sample_rate)

        eq = apply_match(reference, target)
        full = apply_advanced_match(reference, target)

        rows.append(
            {
                "name": name,
                "original": match_distance(full.reference_selection.audio, target).to_dict(),
                "eq_only": match_distance(full.reference_selection.audio, eq.audio).to_dict(),
                "full": match_distance(full.reference_selection.audio, full.audio).to_dict(),
                "selected_reference_windows": [
                    {
                        "start_seconds": w.start_seconds,
                        "end_seconds": w.end_seconds,
                        "score": w.total_score,
                    }
                    for w in full.reference_selection.windows
                ],
            }
        )

    payload = json.dumps({"pairs": rows}, indent=2, sort_keys=True)
    print(payload)

    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(payload + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
