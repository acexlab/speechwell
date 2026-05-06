/*
File Logic Summary: Guided training result page. It loads a saved training
session and renders the scores, transcript, and practical feedback.
*/

import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import LoadingState from "../components/LoadingState";
import ProgressBar from "../components/ProgressBar";
import {
  getTrainingSession,
  getTrainingModules,
  type TrainingModule,
  type TrainingSession,
} from "../api/api";
import "../styles/training.css";

export default function TrainingResult() {
  const { sessionId } = useParams();
  const [session, setSession] = useState<TrainingSession | null>(null);
  const [module, setModule] = useState<TrainingModule | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadResult = async () => {
      try {
        if (!sessionId) {
          setError("Missing training session ID.");
          setLoading(false);
          return;
        }
        const [sessionData, modules] = await Promise.all([
          getTrainingSession(Number(sessionId)),
          getTrainingModules(),
        ]);
        setSession(sessionData);
        setModule(modules.find((item) => item.key === sessionData.module_key) ?? null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load training result");
      } finally {
        setLoading(false);
      }
    };

    loadResult();
  }, [sessionId]);

  const feedbackItems = useMemo(() => {
    if (!session?.feedback_summary) return [];
    return session.feedback_summary
      .split(/\n+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }, [session]);

  return (
    <div className="training-layout">
      <Sidebar />
      <main className="training-content">
        {loading ? (
          <LoadingState label="Loading exercise result..." />
        ) : error || !session ? (
          <section className="training-panel">
            <p className="training-error">{error || "Training result not found."}</p>
            <Link className="training-link-button" to="/therapy-hub">
              Back To Training Home
            </Link>
          </section>
        ) : (
          <>
            <section className="training-breadcrumbs">
              <Link to="/therapy-hub">Training Home</Link>
              <span>/</span>
              {module ? <Link to={`/therapy-hub/${module.key}`}>{module.title}</Link> : <span>Module</span>}
              <span>/</span>
              <strong>Result</strong>
            </section>

            <section className="training-result-grid">
              <article className="training-panel training-panel--wide">
                <p className="training-kicker">Exercise Complete</p>
                <h1>Session #{session.id}</h1>
                <p className="training-copy">
                  Review your scores, transcript, and the next most useful adjustment.
                </p>

                <div className="training-score-grid">
                  <div className="training-score-card">
                    <small>Accuracy</small>
                    <strong>{Math.round(session.accuracy_score)}%</strong>
                  </div>
                  <div className="training-score-card">
                    <small>Fluency</small>
                    <strong>{Math.round(session.fluency_score)}%</strong>
                  </div>
                  <div className="training-score-card">
                    <small>Confidence</small>
                    <strong>{Math.round(session.confidence_score)}%</strong>
                  </div>
                </div>

                <div className="training-result-bars">
                  <ProgressBar label="Accuracy" value={Math.round(session.accuracy_score)} />
                  <ProgressBar label="Fluency" value={Math.round(session.fluency_score)} tone="success" />
                  <ProgressBar label="Confidence" value={Math.round(session.confidence_score)} tone="warning" />
                </div>

                <div className="training-transcript-grid">
                  <div className="training-prompt">
                    <small>Prompt</small>
                    <p>{session.prompt_text || "No prompt saved."}</p>
                  </div>
                  <div className="training-prompt">
                    <small>Your transcript</small>
                    <p>{session.transcript || "No transcript was captured."}</p>
                  </div>
                  <div className="training-prompt">
                    <small>Suggested cleaned sentence</small>
                    <p>{session.corrected_text || "No correction available."}</p>
                  </div>
                </div>

                <div className="training-actions">
                  <Link
                    className="training-link-button training-link-button--solid"
                    to={`/therapy-hub/${session.module_key}/${session.exercise_key}`}
                  >
                    Retry Exercise
                  </Link>
                  <Link className="training-link-button" to={`/therapy-hub/${session.module_key}`}>
                    Back To Module
                  </Link>
                </div>
              </article>

              <aside className="training-panel training-panel--side">
                <h2>Feedback</h2>
                <ul className="training-bullets">
                  {feedbackItems.length > 0 ? (
                    feedbackItems.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)
                  ) : (
                    <li>Your result was saved. Try another exercise to build a trend.</li>
                  )}
                </ul>

                <div className="training-mini-stats">
                  <div>
                    <small>Long Pauses</small>
                    <strong>{session.long_pause_count}</strong>
                  </div>
                  <div>
                    <small>Repeated Words</small>
                    <strong>{session.repeated_word_count}</strong>
                  </div>
                  <div>
                    <small>Duration</small>
                    <strong>{session.duration_sec.toFixed(1)}s</strong>
                  </div>
                </div>
              </aside>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
