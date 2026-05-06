# ML Package

This folder contains the SpeechWell machine-learning pipeline and its supporting artifacts.

## Active Production Path

The current active dysarthria model is:

- `ml/models/dysarthria_model_v2_rf_svc_ensemble.pkl`

Shared defaults are defined in:

- `ml/dysarthria_pipeline_config.py`

Current default dataset:

- `ml/training/torgo_audio_features_v4.csv`

Current default validation report:

- `ml/evaluation/validation_report_v2_rf_svc_ensemble.json`

## Folder Layout

- `datasets/`: raw or source corpora
- `feature_extraction/`: reusable feature extractors
- `training/`: dataset builders and model training scripts
- `models/`: serialized trained model artifacts
- `services/`: runtime orchestration code used by the backend
- `evaluation/`: validation, curves, comparison plots, and reports

## Important Distinction

This package still contains legacy `v1` and older `v2_group` artifacts for reproducibility and fallback compatibility.

They are not the primary default path anymore.

The active default path is the RF + SVC ensemble configured through `ml/dysarthria_pipeline_config.py`.
