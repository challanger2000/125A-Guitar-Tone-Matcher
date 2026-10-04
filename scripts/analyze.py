from __future__ import annotations

import argparse
import json
from pathlib import Path

from tone_matcher.analysis import analyse
from tone_matcher.audio import load_audio


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyse a guitar WAV and print deterministic tone metrics.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--json", type=Path, dest="json_path")
    args = parser.parse_args()

    audio = load_audio(args.input)
    metrics = analyse(audio.data, audio.sample_rate).to_dict()
    payload = json.dumps(metrics, indent=2, sort_keys=True)
    print(payload)

    if args.json_path is not None:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(payload + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
