"""
Build a combined training index from TORGO plus optional dysarthria-only UASpeech
audio downloaded via kagglehub.

Why this exists:
- TORGO provides both healthy and dysarthric speech.
- The Kaggle UASpeech package requested by the user contains only dysarthric audio.
- Positive-only datasets can strengthen the dysarthria class, but they cannot replace
  healthy/control data for binary classification.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

TORGO_PATH = ROOT_DIR / "ml" / "datasets" / "torgo" / "TORGO_RAW"
DEFAULT_OUTPUT = ROOT_DIR / "ml" / "training" / "combined_dysarthria_index.csv"
UASPEECH_DATASET_NAME = "aryashah2k/noise-reduced-uaspeech-dysarthria-dataset"

TORGO_LABEL_MAP = {
    "F_Con": (1, 0),
    "M_Con": (1, 0),
    "F_Dys": (0, 1),
    "M_Dys": (0, 1),
}

SPEAKER_TOKEN_PATTERN = re.compile(r"\b([FMU]?[A-Z]?\d{2,3}[A-Z]?)\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build combined TORGO + optional UASpeech dysarthria index."
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output CSV path.",
    )
    parser.add_argument(
        "--include-uaspeech",
        action="store_true",
        help="Download/index the Kaggle UASpeech dysarthria-only dataset too.",
    )
    parser.add_argument(
        "--uaspeech-path",
        default="",
        help="Existing local path to the UASpeech dataset. If omitted with --include-uaspeech, kagglehub is used.",
    )
    return parser.parse_args()


def _iter_wavs(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.wav") if path.is_file())


def _infer_speaker_id(audio_path: Path, dataset_name: str) -> str:
    parts = [audio_path.stem] + [parent.name for parent in audio_path.parents[:4]]
    for token_source in parts:
        match = SPEAKER_TOKEN_PATTERN.search(token_source.replace("-", "_"))
        if match:
            return f"{dataset_name}_{match.group(1).upper()}"
    return f"{dataset_name}_unknown"


def build_torgo_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for group_folder, (healthy, dysarthria) in TORGO_LABEL_MAP.items():
        group_path = TORGO_PATH / group_folder
        if not group_path.is_dir():
            print(f"Warning: missing TORGO folder: {group_folder}")
            continue

        for audio_path in _iter_wavs(group_path):
            rows.append(
                {
                    "audio_path": str(audio_path),
                    "dataset": "TORGO",
                    "group": group_folder,
                    "speaker_id": _infer_speaker_id(audio_path, "TORGO"),
                    "healthy": healthy,
                    "dysarthria": dysarthria,
                }
            )
    return rows


def resolve_uaspeech_root(explicit_path: str) -> Path:
    if explicit_path:
        root = Path(explicit_path).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"UASpeech path does not exist: {root}")
        return root

    try:
        import kagglehub  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "kagglehub is required for --include-uaspeech when --uaspeech-path is not provided."
        ) from exc

    download_path = Path(kagglehub.dataset_download(UASPEECH_DATASET_NAME)).resolve()
    print(f"Downloaded UASpeech dataset to: {download_path}")
    return download_path


def build_uaspeech_rows(root: Path) -> list[dict[str, object]]:
    wavs = _iter_wavs(root)
    rows: list[dict[str, object]] = []
    for audio_path in wavs:
        rows.append(
            {
                "audio_path": str(audio_path),
                "dataset": "UASPEECH",
                "group": "UASpeech_Dys",
                "speaker_id": _infer_speaker_id(audio_path, "UASPEECH"),
                "healthy": 0,
                "dysarthria": 1,
            }
        )
    return rows


def main() -> None:
    args = parse_args()

    rows = build_torgo_rows()

    if args.include_uaspeech or args.uaspeech_path:
        uaspeech_root = resolve_uaspeech_root(args.uaspeech_path)
        rows.extend(build_uaspeech_rows(uaspeech_root))

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No audio files found for the combined index.")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"Wrote {len(df)} rows to {output_path}")
    print("\nLabel distribution:")
    print(df.groupby(["dataset", "healthy", "dysarthria"]).size())


if __name__ == "__main__":
    main()
