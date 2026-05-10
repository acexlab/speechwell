/*
File Logic Summary: Reusable YouTube video card. It renders a thumbnail,
title, optional category, and opens the original URL in a new tab.
*/

import { useMemo, useState } from "react";
import type { MouseEvent } from "react";
import { getYouTubeThumbnailUrl } from "../utils/youtube";
import { recordVideoAccess } from "../utils/videoAnalytics";

export type TrainingVideo = {
  title: string;
  url: string;
  category?: string;
};

type VideoCardProps = {
  video: TrainingVideo;
  showWatchedToggle?: boolean;
  onSelect?: (video: TrainingVideo) => void;
  isActive?: boolean;
};

export default function VideoCard({
  video,
  showWatchedToggle = false,
  onSelect,
  isActive = false,
}: VideoCardProps) {
  const [watched, setWatched] = useState(false);
  const thumbnailUrl = useMemo(() => getYouTubeThumbnailUrl(video.url), [video.url]);
  const handleSelect = (event: MouseEvent<HTMLAnchorElement>) => {
    if (!onSelect) {
      recordVideoAccess(video);
      return;
    }
    event.preventDefault();
    onSelect(video);
  };

  return (
    <article className="video-card">
      <a
        className={`video-card__link ${isActive ? "video-card__link--active" : ""}`}
        href={video.url}
        target="_blank"
        rel="noreferrer"
        aria-label={`Watch ${video.title} on YouTube`}
        onClick={handleSelect}
      >
        <div className="video-card__thumbnail-wrap">
          {thumbnailUrl ? (
            <img
              className="video-card__thumbnail"
              src={thumbnailUrl}
              alt={video.title}
              loading="lazy"
            />
          ) : (
            <div className="video-card__thumbnail video-card__thumbnail--fallback">
              Thumbnail unavailable
            </div>
          )}
          <div className="video-card__play">
            <span className="video-card__play-triangle" />
          </div>
        </div>
      </a>

      <div className="video-card__body">
        {video.category && <span className="video-card__category">{video.category}</span>}
        <a
          className="video-card__title-link"
          href={video.url}
          target="_blank"
          rel="noreferrer"
          aria-label={`Open ${video.title} on YouTube`}
          onClick={handleSelect}
        >
          <h3 className="video-card__title">{video.title}</h3>
        </a>
      </div>

      {showWatchedToggle && (
        <button
          type="button"
          className={`video-card__watched ${watched ? "is-watched" : ""}`}
          onClick={() => setWatched((value) => !value)}
        >
          {watched ? "Watched" : "Mark as Watched"}
        </button>
      )}
    </article>
  );
}
