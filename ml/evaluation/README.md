# Evaluation

This folder contains validation scripts, comparison plots, learning-curve scripts, and saved evaluation reports.

## Current Default Validation

Run:

```powershell
.\venv\Scripts\python.exe ml/evaluation/validate_accuracy.py
```

Default outputs are driven by `ml/dysarthria_pipeline_config.py`.

Current default report:

- `validation_report_v2_rf_svc_ensemble.json`

## Current Key Artifacts

- `dysarthria_model_v2_rf_svc_ensemble_report.json`: group-aware holdout report
- `validation_report_v2_rf_svc_ensemble.json`: full-data validation report
- `learning_curves/final_latest_model_full_data_curve.csv`
- `learning_curves/final_latest_model_full_data_curve.png`
- `learning_curves/model_metric_comparison_holdout.png`

## Script Roles

- `validate_accuracy.py`: final artifact validation
- `plot_final_metrics.py`: final metric figure
- `plot_model_metric_comparison.py`: holdout comparison figure
- `full_dataset_latest_model_curve.py`: full-data fitted-model curve for the active model

## Legacy Evaluation Files

Older validation/report files remain for comparison and reproducibility.
