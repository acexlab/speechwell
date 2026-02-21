"""
File Logic Summary: Training/data-prep script. It prepares datasets or trains evaluation models used to produce runtime artifacts.
"""

import os
import pandas as pd

TORGO_PATH = "ml/datasets/torgo/TORGO_RAW"

LABEL_MAP = {
    "F_Con": (1, 0),  # healthy, dysarthria
    "M_Con": (1, 0),
    "F_Dys": (0, 1),
    "M_Dys": (0, 1),
}

rows = []

for group_folder, (healthy, dysarthria) in LABEL_MAP.items():
    group_path = os.path.join(TORGO_PATH, group_folder)

    if not os.path.isdir(group_path):
        print(f"⚠️ Missing folder: {group_folder}")
        continue

    # 🔁 Walk recursively through all subfolders
    for root, _, files in os.walk(group_path):
        for file in files:
            if not file.lower().endswith(".wav"):
                continue

            audio_path = os.path.join(root, file)

            rows.append({
                "audio_path": audio_path,
                "group": group_folder,
                "healthy": healthy,
                "dysarthria": dysarthria
            })

df = pd.DataFrame(rows)

print("Columns:", df.columns.tolist())
print("Total rows:", len(df))

if len(df) == 0:
    raise RuntimeError("❌ No audio files found. Check folder paths.")

df.to_csv("ml/training/torgo_index.csv", index=False)

print("\nLabel distribution:")
print(df.groupby(["healthy", "dysarthria"]).size())

