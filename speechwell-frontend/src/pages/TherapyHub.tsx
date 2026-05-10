/*
File Logic Summary: Video sessions page. It hides guided exercise modules for
now and focuses only on embedded practice video sessions.
*/

import { useMemo, useRef, useState } from "react";
import Sidebar from "../components/Sidebar";
import VideoGrid from "../components/VideoGrid";
import "../styles/training.css";
import { PRACTICE_VIDEOS } from "../data/practiceVideos";
import { getYouTubeEmbedUrl } from "../utils/youtube";
import { getVideoAccessStats, recordVideoAccess } from "../utils/videoAnalytics";
import type { TrainingVideo } from "../components/VideoCard";

export default function TherapyHub() {
  const [selectedVideo, setSelectedVideo] = useState<TrainingVideo | null>(
    PRACTICE_VIDEOS[0] ?? null
  );
  const playerRef = useRef<HTMLElement | null>(null);

  const selectedVideoEmbedUrl = useMemo(
    () => (selectedVideo ? getYouTubeEmbedUrl(selectedVideo.url) : null),
    [selectedVideo]
  );

  const videoStats = getVideoAccessStats(PRACTICE_VIDEOS);
  const totalOpens = videoStats.reduce((sum, video) => sum + video.accessCount, 0);
  const watchedCount = videoStats.filter((video) => video.accessCount > 0).length;
  const topVideo = videoStats.find((video) => video.accessCount > 0);

  const handleSelectVideo = (video: TrainingVideo) => {
    recordVideoAccess(video);
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
        <section className="training-hero video-session-hero">
          <div>
            <p className="training-kicker">Video Sessions</p>
            <h1>Practice speech skills with guided video sessions.</h1>
            <p className="training-copy">
              Watch curated videos for clarity, fluency, articulation, breath support, and spoken grammar.
            </p>
          </div>
          <div className="training-hero__panel">
            <div>
              <small>Videos Opened</small>
              <strong>{totalOpens}</strong>
            </div>
            <div>
              <small>Unique Videos Tried</small>
              <strong>{watchedCount}</strong>
            </div>
            <div>
              <small>Most Opened</small>
              <strong>{topVideo?.title ?? "Start a video session"}</strong>
            </div>
          </div>
        </section>

        <section className="training-video-section training-panel video-only-panel">
          <div className="training-video-section__header">
            <div>
              <p className="training-kicker">Now Playing</p>
              <h2>{selectedVideo?.title ?? "Choose a practice video"}</h2>
              <p className="training-copy">
                Video opens are counted locally and reflected in your dashboard activity.
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
                  onClick={() => recordVideoAccess(selectedVideo)}
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
      </main>
    </div>
  );
}
