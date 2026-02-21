"""
File Logic Summary: Training/data-prep script. It prepares datasets or trains evaluation models used to produce runtime artifacts.
"""

import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix

# Load full dataset
df = pd.read_pickle("ml/training/torgo_features_full.pkl")

# Fluency features
X_fluency = df[
    ["speaking_rate_wps", "avg_pause_sec", "max_pause_sec"]
].values

# Acoustic embeddings
X_acoustic = np.vstack(df["embedding"].values)

# Scale acoustics
scaler = StandardScaler()
X_acoustic_scaled = scaler.fit_transform(X_acoustic)

# Dimensionality reduction
pca = PCA(n_components=40, random_state=42)
X_acoustic_pca = pca.fit_transform(X_acoustic_scaled)

# Combine features
X = np.hstack([X_fluency, X_acoustic_pca])
y = df["dysarthria"].values

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# Train classifier
model = LogisticRegression(
    max_iter=5000,
    class_weight="balanced",
    n_jobs=-1
)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)

print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred))

print("\n🧩 Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Save artifacts
os.makedirs("ml/models", exist_ok=True)

joblib.dump(model, "ml/models/dysarthria_model_v1.pkl")
joblib.dump(pca, "ml/models/dysarthria_pca_v1.pkl")
joblib.dump(scaler, "ml/models/dysarthria_scaler_v1.pkl")

print("\n✅ Production model saved (v1)")

