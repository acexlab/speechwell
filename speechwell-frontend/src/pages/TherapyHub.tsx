/*
File Logic Summary: Guided training home page. It loads the module catalog and
saved progress so the existing Therapy Hub route becomes a real training entry.
*/

import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import LoadingState from "../components/LoadingState";
import TrainingModuleCard from "../components/TrainingModuleCard";
import VideoGrid from "../components/VideoGrid";
import {
  getTrainingModules,
  getTrainingProgress,
  type TrainingModule,
  type TrainingProgress,
} from "../api/api";
import "../styles/training.css";
import { PRACTICE_VIDEOS } from "../data/practiceVideos";
import { getYouTubeEmbedUrl } from "../utils/youtube";
import type { TrainingVideo } from "../components/VideoCard";

type ProgressMap = Record<string, TrainingProgress>;

export default function TherapyHub() {
  const [modules, setModules] = useState<TrainingModule[]>([]);
  const [progress, setProgress] = useState<ProgressMap>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedVideo, setSelectedVideo] = useState<TrainingVideo | null>(
    PRACTICE_VIDEOS[0] ?? null
  );
  const playerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const loadTrainingHome = async () => {
      try {
        const [moduleData, progressData] = await Promise.all([
          getTrainingModules(),
          getTrainingProgress().catch(() => []),
        ]);

        setModules(moduleData);
        setProgress(
          progressData.reduce<ProgressMap>((acc, item) => {
            acc[item.module_key] = item;
            return acc;
          }, {})
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load training modules");
      } finally {
        setLoading(false);
      }
    };

    loadTrainingHome();
  }, []);

  const totalSessions = useMemo(
    () =>
      Object.values(progress).reduce(
        (sum, item) => sum + item.sessions_completed,
        0
      ),
    [progress]
  );

  const bestModule = useMemo(() => {
    const progressValues = Object.values(progress);
    if (!progressValues.length) return null;
    const best = [...progressValues].sort((a, b) => b.best_score - a.best_score)[0];
    return modules.find((module) => module.key === best.module_key) ?? null;
  }, [modules, progress]);

  const selectedVideoEmbedUrl = useMemo(
    () => (selectedVideo ? getYouTubeEmbedUrl(selectedVideo.url) : null),
    [selectedVideo]
  );

  const handleSelectVideo = (video: TrainingVideo) => {
    setSelectedVideo(video);
    window.requestAnimationFrame(() => {
      playerRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  };

  return (
    <div className="training-layout">
      <Sidebar />
      <main className="training-content">
        <section className="training-hero">
          <div>
            <p className="training-kicker">Guided Speech Training</p>
            <h1>Practice speech skills in short, structured sessions.</h1>
            <p className="training-copy">
              Choose a module, complete one exercise at a time, and save your
              results directly into SpeechWell.
            </p>
          </div>
          <div className="training-hero__panel">
            <div>
              <small>Total Practice Sessions</small>
              <strong>{totalSessions}</strong>
            </div>
            <div>
              <small>Best Module</small>
              <strong>{bestModule?.title ?? "Start your first module"}</strong>
            </div>
            <Link className="training-link-button training-link-button--solid" to="/therapy-hub/fluency">
              Start With Fluency
            </Link>
          </div>
        </section>

        {loading ? (
          <LoadingState label="Loading training modules..." />
        ) : error ? (
          <section className="training-panel">
            <p className="training-error">{error}</p>
          </section>
        ) : (
          <>
            <section className="training-summary-grid">
              <article className="training-summary-card">
                <small>Modules Ready</small>
                <strong>{modules.length}</strong>
                <p>Breath, articulation, fluency, and grammar practice.</p>
              </article>
              <article className="training-summary-card">
                <small>Reusable Scoring</small>
                <strong>Accuracy + Fluency</strong>
                <p>Simple transcript and timing feedback, no extra complexity.</p>
              </article>
              <article className="training-summary-card">
                <small>Progress Sync</small>
                <strong>Saved To Your Account</strong>
                <p>Practice history and module scores connect to the current user.</p>
              </article>
            </section>

            <section className="training-module-grid">
              {modules.map((module) => (
                <TrainingModuleCard
                  key={module.key}
                  module={module}
                  progress={progress[module.key]}
                />
              ))}
            </section>

            <section className="training-video-section training-panel">
              <div className="training-video-section__header">
                <div>
                  <p className="training-kicker">Practice Videos</p>
                  <h2>Practice videos inside SpeechWell.</h2>
                  <p className="training-copy">
                    The selected YouTube video loads here in an embedded player.
                    Some full youtube.com features stay on YouTube, so the original link is still available below.
                  </p>
                </div>
              </div>

              {selectedVideo && (
                <section className="training-video-player" ref={playerRef}>
                  <div className="training-video-player__frame">
                    {selectedVideoEmbedUrl ? (
                      <iframe
                        src={selectedVideoEmbedUrl}
                        title={selectedVideo.title}
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                        allowFullScreen
                      />
                    ) : (
                      <div className="training-video-player__fallback">
                        This video could not be embedded here. Use the original YouTube link instead.
                      </div>
                    )}
                  </div>
                  <div className="training-video-player__meta">
                    <div>
                      {selectedVideo.category && (
                        <span className="video-card__category">{selectedVideo.category}</span>
                      )}
                      <h3>{selectedVideo.title}</h3>
                    </div>
                    <a
                      className="training-link-button"
                      href={selectedVideo.url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open on YouTube
                    </a>
                  </div>
                </section>
              )}

              <VideoGrid
                videos={PRACTICE_VIDEOS}
                groupByCategory
                onSelectVideo={handleSelectVideo}
                selectedVideoUrl={selectedVideo?.url ?? null}
              />
            </section>
          </>
        )}
      </main>
    </div>
  );
}
