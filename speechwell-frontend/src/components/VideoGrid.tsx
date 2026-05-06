/*
File Logic Summary: Responsive grid for grouped YouTube practice videos.
Supports optional category grouping and passes each item to VideoCard.
*/

import VideoCard, { type TrainingVideo } from "./VideoCard";

type VideoGridProps = {
  videos: TrainingVideo[];
  groupByCategory?: boolean;
  showWatchedToggle?: boolean;
  onSelectVideo?: (video: TrainingVideo) => void;
  selectedVideoUrl?: string | null;
};

function groupVideosByCategory(videos: TrainingVideo[]) {
  return videos.reduce<Record<string, TrainingVideo[]>>((acc, video) => {
    const category = video.category || "General";
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(video);
    return acc;
  }, {});
}

export default function VideoGrid({
  videos,
  groupByCategory = false,
  showWatchedToggle = false,
  onSelectVideo,
  selectedVideoUrl = null,
}: VideoGridProps) {
  if (!groupByCategory) {
    return (
      <div className="video-grid">
        {videos.map((video) => (
          <VideoCard
            key={`${video.title}-${video.url}`}
            video={video}
            showWatchedToggle={showWatchedToggle}
            onSelect={onSelectVideo}
            isActive={selectedVideoUrl === video.url}
          />
        ))}
      </div>
    );
  }

  const groupedVideos = groupVideosByCategory(videos);

  return (
    <div className="video-groups">
      {Object.entries(groupedVideos).map(([category, items]) => (
        <section key={category} className="video-group">
          <div className="video-group__header">
            <h3>{category}</h3>
            <span>{items.length} videos</span>
          </div>

          <div className="video-grid">
            {items.map((video) => (
              <VideoCard
                key={`${video.title}-${video.url}`}
                video={video}
                showWatchedToggle={showWatchedToggle}
                onSelect={onSelectVideo}
                isActive={selectedVideoUrl === video.url}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
