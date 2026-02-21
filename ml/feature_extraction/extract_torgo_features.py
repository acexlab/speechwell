"""
File Logic Summary: Python module for backend/ML logic that contributes to request handling, analysis, or model workflow.
"""

import pandas as pd
import os
from backend.app.services.whisper_service import analyze_audio
from backend.app.services.acoustic_service import extract_acoustic_embedding

INDEX_PATH = "ml/training/torgo_index.csv"
OUTPUT_PATH = "ml/training/torgo_features_full.pkl"

# Load index
df = pd.read_csv(INDEX_PATH)

# Load existing progress if any
if os.path.exists(OUTPUT_PATH):
    out_df = pd.read_pickle(OUTPUT_PATH)
    processed = set(out_df["audio_path"])
    print(f"🔁 Resuming from {len(out_df)} processed files")
else:
    out_df = pd.DataFrame()
    processed = set()
    print("🆕 Starting fresh extraction")

rows = []
save_every = 50  # autosave frequency

for i, row in df.iterrows():
    audio_path = row["audio_path"]

    if audio_path in processed:
        continue

    try:
        whisper_feat = analyze_audio(audio_path)
        acoustic_embed = extract_acoustic_embedding(audio_path)

        rows.append({
            "audio_path": audio_path,
            "speaking_rate_wps": whisper_feat["speaking_rate_wps"],
            "avg_pause_sec": whisper_feat["average_pause_sec"],
            "max_pause_sec": whisper_feat["max_pause_sec"],
            "embedding": acoustic_embed,
            "healthy": row["healthy"],
            "dysarthria": row["dysarthria"]
        })

        print(f"✅ Processed {len(processed) + len(rows)}")

        # Incremental save
        if len(rows) >= save_every:
            out_df = pd.concat([out_df, pd.DataFrame(rows)], ignore_index=True)
            out_df.to_pickle(OUTPUT_PATH)
            rows = []

    except Exception as e:
        print(f"❌ Error on {audio_path}: {e}")

# Final save
if rows:
    out_df = pd.concat([out_df, pd.DataFrame(rows)], ignore_index=True)
    out_df.to_pickle(OUTPUT_PATH)

print("🎉 Full feature extraction complete:", len(out_df))

