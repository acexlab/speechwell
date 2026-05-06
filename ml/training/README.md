# Training

This folder contains offline data preparation and model training scripts.

## Current Main Training Script

- `train_dysarthria_rf_svc_ensemble.py`
- `train_dysarthria_model_comparison.py` for side-by-side model selection on combined data

This trains the latest RF + SVC ensemble and saves:

- model: `ml/models/dysarthria_model_v2_rf_svc_ensemble.pkl`
- report: `ml/evaluation/dysarthria_model_v2_rf_svc_ensemble_report.json`

The comparison script saves:

- best model: `ml/models/dysarthria_best_comparison_model.pkl`
- report: `ml/evaluation/dysarthria_model_comparison_report.json`

## Supporting Files

- `build_torgo_audio_features.py`: builds raw-audio feature tables
- `build_combined_dysarthria_index.py`: builds a combined index from TORGO plus optional Kaggle UASpeech dysarthria-only audio
- `torgo_audio_features_v4.csv`: current active feature dataset
- `torgo_index.csv`: corpus index used for dataset generation

## Legacy Scripts

These remain for comparison or historical reproducibility:

- `train_dysarthria_model.py`
- `train_dysarthria_full.py`
- `train_dysarthria_with_acoustics.py`

## Optional Positive-Class Augmentation

If you want to add the Kaggle UASpeech dysarthria-only dataset alongside TORGO:

```powershell
python ml/training/build_combined_dysarthria_index.py --include-uaspeech
python ml/training/build_torgo_audio_features.py --index ml/training/combined_dysarthria_index.csv --output ml/training/combined_audio_features.csv
```

Important:

- UASpeech in this workflow is treated as `dysarthria=1` only
- it improves positive-class diversity
- it does **not** replace healthy/control samples from TORGO

## Retrain The Existing Ensemble On Combined Data

```powershell
python ml/training/train_dysarthria_rf_svc_ensemble.py ^
  --data ml/training/combined_audio_features.csv ^
  --group-aware ^
  --group-by-dataset ^
  --positive-weight 1.15 ^
  --max-positive-ratio 0.55 ^
  --report-out ml/evaluation/dysarthria_model_v2_rf_svc_combined_report.json ^
  --model-out ml/models/dysarthria_model_v2_rf_svc_combined.pkl
```

What this adds over the older trainer:

- speaker-aware / dataset-aware split support
- positive-class balancing for dysarthria-only augmentation sets
- threshold tuning on a validation split before test evaluation
- removal of `sample_rate` and `channels` from model inputs

## Compare Several Model Families On Combined Data

```powershell
python ml/training/train_dysarthria_model_comparison.py ^
  --data ml/training/combined_audio_features.csv ^
  --group-aware ^
  --group-by-dataset ^
  --positive-weight 1.15 ^
  --max-positive-ratio 0.55 ^
  --report-out ml/evaluation/dysarthria_model_comparison_report.json ^
  --best-model-out ml/models/dysarthria_best_comparison_model.pkl
```

Compared models:

- calibrated logistic regression
- RBF SVM
- Random Forest
- RF + SVM ensemble
- HistGradientBoostingClassifier
- `train_dysarthria_optimized.py`
