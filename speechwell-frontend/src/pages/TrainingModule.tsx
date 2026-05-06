/*
File Logic Summary: Module detail page. It shows one guided training module and
its exercises before the user starts a session.
*/

import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import LoadingState from "../components/LoadingState";
import InteractiveButton from "../components/InteractiveButton";
import {
  getTrainingModules,
  getTrainingProgress,
  type TrainingModule,
  type TrainingProgress,
} from "../api/api";
import ProgressBar from "../components/ProgressBar";
import "../styles/training.css";

export default function TrainingModule() {
  const { moduleKey } = useParams();
  const navigate = useNavigate();
  const [module, setModule] = useState<TrainingModule | null>(null);
  const [progress, setProgress] = useState<TrainingProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadModule = async () => {
      try {
        const [moduleData, progressData] = await Promise.all([
          getTrainingModules(),
          getTrainingProgress().catch(() => []),
        ]);
        const selectedModule = moduleData.find((item) => item.key === moduleKey) ?? null;
        setModule(selectedModule);
        setProgress(progressData.find((item) => item.module_key === moduleKey) ?? null);
        if (!selectedModule) {
          setError("Training module not found.");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load module");
      } finally {
        setLoading(false);
      }
    };

    loadModule();
  }, [moduleKey]);

  const averageScore = useMemo(() => {
    if (!progress) return 0;
    return Math.round((progress.avg_accuracy + progress.avg_fluency) / 2);
  }, [progress]);

  return (
    <div className="training-layout">
      <Sidebar />
      <main className="training-content">
        {loading ? (
          <LoadingState label="Loading module..." />
        ) : error || !module ? (
          <section className="training-panel">
            <p className="training-error">{error || "Module not found."}</p>
            <Link className="training-link-button" to="/therapy-hub">
              Back To Training Home
            </Link>
          </section>
        ) : (
          <>
            <section className="training-breadcrumbs">
              <Link to="/therapy-hub">Training Home</Link>
              <span>/</span>
              <strong>{module.title}</strong>
            </section>

            <section className="training-module-hero">
              <div>
                <p className="training-kicker">{module.focus_area}</p>
                <h1>{module.title}</h1>
                <p className="training-copy">{module.description}</p>
              </div>

              <div className="training-panel training-panel--compact">
                <ProgressBar
                  label="Average Accuracy"
                  value={progress?.avg_accuracy ?? 0}
                />
                <ProgressBar
                  label="Average Fluency"
                  value={progress?.avg_fluency ?? 0}
                  tone="success"
                />
                <div className="training-mini-stats">
                  <div>
                    <small>Sessions Completed</small>
                    <strong>{progress?.sessions_completed ?? 0}</strong>
                  </div>
                  <div>
                    <small>Average Score</small>
                    <strong>{averageScore}%</strong>
                  </div>
                </div>
              </div>
            </section>

            <section className="training-exercise-list">
              {module.exercises.map((exercise, index) => (
                <article key={exercise.key} className="training-exercise-card">
                  <div className="training-exercise-card__head">
                    <span>Exercise {index + 1}</span>
                    <span>{exercise.input_mode === "mic" ? "Microphone" : "Text Entry"}</span>
                  </div>
                  <h2>{exercise.title}</h2>
                  <p>{exercise.description}</p>
                  <div className="training-exercise-card__meta">
                    <span>{exercise.difficulty ?? "Practice"}</span>
                    <span>{exercise.input_mode}</span>
                  </div>
                  <InteractiveButton
                    onClick={() =>
                      navigate(`/therapy-hub/${module.key}/${exercise.key}`)
                    }
                  >
                    Start Exercise
                  </InteractiveButton>
                </article>
              ))}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
