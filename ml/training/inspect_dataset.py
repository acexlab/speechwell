"""
File Logic Summary: Training/data-prep script. It prepares datasets or trains evaluation models used to produce runtime artifacts.
"""

import pandas as pd

df = pd.read_csv("ml/training/torgo_features_sample.csv")

print("\n🔹 Head:")
print(df.head())

print("\n🔹 Describe:")
print(df.describe())

print("\n🔹 Label distribution:")
print(df[["healthy", "dysarthria"]].value_counts())
