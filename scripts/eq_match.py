from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from tone_matcher.analysis import analyse
from tone_matcher.audio import load_audio, resample_audio, save_audio
from tone_matcher.eq_match import apply_match


def main() -> int:
    parser = argparse.ArgumentParser(description="125A deterministic EQ-match research baseline.")
    parser.add_argument("reference", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--curve-csv", type=Path)
    parser.add_argument("--max-gain-db", type=float, default=12.0)
    args = parser.parse_args()

    reference = load_audio(args.reference)
    target = load_audio(args.target)

    if reference.sample_rate != target.sample_rate:
        reference = resample_audio(reference, target.sample_rate)

    result = apply_match(reference, target, max_gain_db=args.max_gain_db)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_audio(args.output, result.audio)

    before = analyse(target.data, target.sample_rate).to_dict()
    after = analyse(result.audio.data, result.audio.sample_rate).to_dict()
    ref = analyse(reference.data, reference.sample_rate).to_dict()

    report = {
        "reference": ref,
        "target_before": before,
        "target_after": after,
        "settings": {
            "max_gain_db": args.max_gain_db,
            "sample_rate": target.sample_rate,
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
            writer.writerow(["frequency_hz", "gain_db"])
            writer.writerows(zip(result.frequencies_hz, result.gain_db))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
