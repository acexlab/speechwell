"""
File Logic Summary: Training/data-prep script. It prepares datasets or trains evaluation models used to produce runtime artifacts.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler

# Load dataset
df = pd.read_pickle("ml/training/torgo_features_sample.pkl")

# Fluency features
X_fluency = df[
    ["speaking_rate_wps", "avg_pause_sec", "max_pause_sec"]
].values

# Acoustic embeddings
X_acoustic = np.vstack(df["embedding"].values)

# Scale acoustics
scaler = StandardScaler()
X_acoustic_scaled = scaler.fit_transform(X_acoustic)

# Reduce dimension
pca = PCA(n_components=30, random_state=42)
X_acoustic_pca = pca.fit_transform(X_acoustic_scaled)

# Combine features
X = np.hstack([X_fluency, X_acoustic_pca])
y = df["dysarthria"].values

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# Train model
model = LogisticRegression(
    max_iter=3000,
    class_weight="balanced"
)
model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred))

print("\n🧩 Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

