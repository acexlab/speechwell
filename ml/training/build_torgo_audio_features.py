"""
Build a fast raw-audio feature table for the full TORGO index.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.feature_extraction.raw_audio_features import extract_raw_audio_features


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build raw-audio features for TORGO.")
    parser.add_argument(
        "--index",
        default="ml/training/torgo_index.csv",
        help="Path to TORGO index CSV.",
    )
    parser.add_argument(
        "--output",
        default="ml/training/torgo_audio_features.csv",
        help="Output CSV path for extracted features.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit for number of rows to process.",
    )
    parser.add_argument(
        "--save-every",
        type=int,
        default=500,
        help="Incremental save frequency.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    index_path = Path(args.index)
    output_path = Path(args.output)

    if not index_path.exists():
        raise FileNotFoundError(f"Index CSV not found: {index_path}")

    index_df = pd.read_csv(index_path)
    if args.limit > 0:
        index_df = index_df.head(args.limit)

    if output_path.exists():
        existing_df = pd.read_csv(output_path)
        processed_paths = set(existing_df["audio_path"].tolist())
        rows: list[dict[str, object]] = existing_df.to_dict(orient="records")
        print(f"Resuming from existing output with {len(existing_df)} rows.")
    else:
        processed_paths = set()
        rows = []
        print("Starting raw-audio feature extraction from scratch.")

    skipped = 0

    for idx, row in index_df.iterrows():
        audio_path = row["audio_path"]
        if audio_path in processed_paths:
            continue

        try:
            feature_row = extract_raw_audio_features(audio_path)
            source_speaker_id = str(row.get("speaker_id", "")).strip() if "speaker_id" in row else ""
            if source_speaker_id and feature_row.get("speaker_id") in {"", "unknown"}:
                feature_row["speaker_id"] = source_speaker_id
            if "dataset" in row:
                feature_row["dataset"] = row["dataset"]
            feature_row["group"] = row["group"]
            feature_row["healthy"] = int(row["healthy"])
            feature_row["dysarthria"] = int(row["dysarthria"])
            rows.append(feature_row)
        except Exception as exc:
            skipped += 1
            print(f"Skipping unreadable file: {audio_path} ({exc})")

        if len(rows) % args.save_every == 0:
            pd.DataFrame(rows).to_csv(output_path, index=False)
            print(f"Saved {len(rows)} extracted rows at source row {idx + 1}.")

    pd.DataFrame(rows).to_csv(output_path, index=False)
    print(f"Finished. Wrote {len(rows)} rows to {output_path}. Skipped {skipped} files.")


if __name__ == "__main__":
    main()
