/*
File Logic Summary: Local video access tracking helpers used by the training
hub and dashboard. Counts are stored per browser profile in localStorage.
*/

import type { TrainingVideo } from "../components/VideoCard";

const STORAGE_KEY = "speechwell-video-access-counts";

type VideoAccessCounts = Record<string, number>;

function readCounts(): VideoAccessCounts {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function writeCounts(counts: VideoAccessCounts) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(counts));
}

export function recordVideoAccess(video: TrainingVideo) {
  const counts = readCounts();
  counts[video.url] = (counts[video.url] ?? 0) + 1;
  writeCounts(counts);
}

export function getVideoAccessStats(videos: TrainingVideo[]) {
  const counts = readCounts();
  return videos
    .map((video) => ({
      ...video,
      accessCount: counts[video.url] ?? 0,
    }))
    .sort((a, b) => b.accessCount - a.accessCount || a.title.localeCompare(b.title));
}
