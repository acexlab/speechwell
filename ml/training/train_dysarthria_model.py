"""
File Logic Summary: Training/data-prep script. It prepares datasets or trains evaluation models used to produce runtime artifacts.
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

# Load dataset
df = pd.read_csv("ml/training/torgo_features_sample.csv")

# Features (fluency-based baseline)
X = df[[
    "speaking_rate_wps",
    "avg_pause_sec",
    "max_pause_sec"
]]

# Target
y = df["dysarthria"]

# Train-test split (stratified)
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# Train model
model = LogisticRegression(
    max_iter=1000,
    class_weight="balanced"
)
model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

# Evaluation
print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred))

print("\n🧩 Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

