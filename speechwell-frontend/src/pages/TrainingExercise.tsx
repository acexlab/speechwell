/*
File Logic Summary: Active guided exercise screen. It starts a backend training
session, captures microphone or text input, submits the attempt, and routes to
the result page.
*/

import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import LoadingState from "../components/LoadingState";
import InteractiveButton from "../components/InteractiveButton";
import {
  evaluateTrainingSession,
  getTrainingModules,
  startTrainingSession,
  type TrainingExercise,
  type TrainingModule,
} from "../api/api";
import "../styles/training.css";

export default function TrainingExercise() {
  const { moduleKey, exerciseKey } = useParams();
  const navigate = useNavigate();
  const [module, setModule] = useState<TrainingModule | null>(null);
  const [exercise, setExercise] = useState<TrainingExercise | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [textAnswer, setTextAnswer] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [recordedFile, setRecordedFile] = useState<File | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<BlobPart[]>([]);

  useEffect(() => {
    const loadExercise = async () => {
      try {
        const modules = await getTrainingModules();
        const selectedModule = modules.find((item) => item.key === moduleKey) ?? null;
        const selectedExercise =
          selectedModule?.exercises.find((item) => item.key === exerciseKey) ?? null;

        setModule(selectedModule);
        setExercise(selectedExercise);

        if (!selectedModule || !selectedExercise || !moduleKey || !exerciseKey) {
          setError("Training exercise not found.");
          setLoading(false);
          return;
        }

        const session = await startTrainingSession(moduleKey, exerciseKey);
        setSessionId(session.session_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load training exercise");
      } finally {
        setLoading(false);
      }
    };

    loadExercise();

    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, [exerciseKey, moduleKey]);

  useEffect(() => {
    if (!isRecording) return undefined;
    const timer = window.setInterval(() => {
      setRecordingTime((value) => value + 1);
    }, 1000);
    return () => window.clearInterval(timer);
  }, [isRecording]);

  const handleStartRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("This browser does not support audio recording.");
      return;
    }

    try {
      setError("");
      setRecordedFile(null);
      setRecordingTime(0);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const mimeType = MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "";
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      recordedChunksRef.current = [];
      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(recordedChunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });
        const file = new File([blob], `training-${Date.now()}.webm`, {
          type: blob.type || "audio/webm",
        });
        setRecordedFile(file);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch {
      setError("Microphone access was denied or unavailable.");
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    setIsRecording(false);
  };

  const handleSubmit = async () => {
    if (!sessionId || !exercise) return;
    if (exercise.input_mode === "text" && !textAnswer.trim()) {
      setError("Please enter your answer before submitting.");
      return;
    }
    if (exercise.input_mode === "mic" && !recordedFile) {
      setError("Please record your response before submitting.");
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      await evaluateTrainingSession({
        sessionId,
        textAnswer: exercise.input_mode === "text" ? textAnswer : undefined,
        audioFile: exercise.input_mode === "mic" ? recordedFile : undefined,
      });
      navigate(`/therapy-hub/session/${sessionId}/result`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit exercise");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="training-layout">
      <Sidebar />
      <main className="training-content">
        {loading ? (
          <LoadingState label="Preparing exercise..." />
        ) : error && !exercise ? (
          <section className="training-panel">
            <p className="training-error">{error}</p>
            <Link className="training-link-button" to="/therapy-hub">
              Back To Training Home
            </Link>
          </section>
        ) : exercise && module ? (
          <>
            <section className="training-breadcrumbs">
              <Link to="/therapy-hub">Training Home</Link>
              <span>/</span>
              <Link to={`/therapy-hub/${module.key}`}>{module.title}</Link>
              <span>/</span>
              <strong>{exercise.title}</strong>
            </section>

            <section className="training-exercise-screen">
              <div className="training-panel training-panel--wide">
                <p className="training-kicker">{module.title}</p>
                <h1>{exercise.title}</h1>
                <p className="training-copy">{exercise.description}</p>

                <div className="training-prompt">
                  <small>Prompt</small>
                  <p>{exercise.prompt_text}</p>
                </div>

                {exercise.input_mode === "text" ? (
                  <label className="training-text-input">
                    <span>Your answer</span>
                    <textarea
                      rows={6}
                      value={textAnswer}
                      onChange={(event) => setTextAnswer(event.target.value)}
                      placeholder="Type your response here..."
                    />
                  </label>
                ) : (
                  <div className="training-recorder">
                    <div className="training-recorder__status">
                      <div>
                        <small>Recorder</small>
                        <strong>
                          {isRecording
                            ? `Recording ${recordingTime}s`
                            : recordedFile
                            ? "Ready to submit"
                            : "Awaiting recording"}
                        </strong>
                      </div>
                      <span className={`training-dot ${isRecording ? "is-live" : ""}`} />
                    </div>

                    <div className="training-recorder__actions">
                      {isRecording ? (
                        <InteractiveButton
                          variant="danger"
                          onClick={handleStopRecording}
                        >
                          Stop Recording
                        </InteractiveButton>
                      ) : (
                        <InteractiveButton onClick={handleStartRecording}>
                          Start Recording
                        </InteractiveButton>
                      )}
                    </div>

                    {recordedFile && (
                      <p className="training-helper">
                        Recorded file ready: {recordedFile.name}
                      </p>
                    )}
                  </div>
                )}

                {error && <p className="training-error">{error}</p>}

                <div className="training-actions">
                  <InteractiveButton
                    onClick={handleSubmit}
                    disabled={submitting}
                  >
                    {submitting ? "Submitting..." : "Submit Exercise"}
                  </InteractiveButton>
                  <Link className="training-link-button" to={`/therapy-hub/${module.key}`}>
                    Back To Module
                  </Link>
                </div>
              </div>

              <aside className="training-panel training-panel--side">
                <h2>What you will get</h2>
                <ul className="training-bullets">
                  <li>Accuracy based on expected vs spoken words</li>
                  <li>Fluency based on pauses and repeated words</li>
                  <li>Short, actionable feedback after each attempt</li>
                </ul>
              </aside>
            </section>
          </>
        ) : null}
      </main>
    </div>
  );
}
