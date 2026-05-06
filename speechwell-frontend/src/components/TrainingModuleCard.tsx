/*
File Logic Summary: Guided training module summary card with progress snapshot
and entry action.
*/

import { Link } from "react-router-dom";
import type { TrainingModule, TrainingProgress } from "../api/api";
import ProgressBar from "./ProgressBar";

type TrainingModuleCardProps = {
  module: TrainingModule;
  progress?: TrainingProgress;
};

export default function TrainingModuleCard({
  module,
  progress,
}: TrainingModuleCardProps) {
  return (
    <article className="training-module-card">
      <div className="training-module-card__eyebrow">
        <span>{module.focus_area}</span>
        <span>{module.exercise_count} exercises</span>
      </div>

      <h2>{module.title}</h2>
      <p>{module.description}</p>

      <div className="training-module-card__stats">
        <div>
          <small>Sessions</small>
          <strong>{progress?.sessions_completed ?? 0}</strong>
        </div>
        <div>
          <small>Best Score</small>
          <strong>{progress?.best_score ?? 0}%</strong>
        </div>
      </div>

      <ProgressBar
        label="Average Accuracy"
        value={progress?.avg_accuracy ?? 0}
      />

      <Link className="training-link-button" to={`/therapy-hub/${module.key}`}>
        Open Module
      </Link>
    </article>
  );
}
