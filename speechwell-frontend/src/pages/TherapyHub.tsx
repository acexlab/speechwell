/*
File Logic Summary: Therapy Hub page that filters exercises and offers direct YouTube speech-training resources by category.
*/

import { useMemo, useState } from "react";
import Sidebar from "../components/Sidebar";
import InteractiveButton from "../components/InteractiveButton";
import "../styles/therapy-hub.css";

interface Exercise {
  id: string;
  title: string;
  description: string;
  category: "Dysarthria" | "Stuttering";
  type?: string;
  youtubeUrl?: string;
}

interface ResourceLink {
  id: string;
  title: string;
  category: "Dysarthria" | "Stuttering" | "General";
  url: string;
}

const YOUTUBE_RESOURCES: ResourceLink[] = [
  {
    id: "r1",
    title: "Dysarthria speech therapy exercises (search)",
    category: "Dysarthria",
    url: "https://www.youtube.com/results?search_query=dysarthria+speech+therapy+exercises+for+adults",
  },
  {
    id: "r2",
    title: "Stuttering fluency shaping exercises (search)",
    category: "Stuttering",
    url: "https://www.youtube.com/results?search_query=stuttering+fluency+shaping+exercises",
  },
  {
    id: "r3",
    title: "Breathing exercises for speech clarity (search)",
    category: "General",
    url: "https://www.youtube.com/results?search_query=breathing+exercises+for+speech+therapy",
  },
  {
    id: "r4",
    title: "Articulation drills speech therapy (search)",
    category: "General",
    url: "https://www.youtube.com/results?search_query=articulation+drills+speech+therapy",
  },
  {
    id: "r5",
    title: "Smooth speech technique training (search)",
    category: "Stuttering",
    url: "https://www.youtube.com/results?search_query=smooth+speech+technique+stuttering+practice",
  },
];

export default function TherapyHub() {
  const [selectedCategory, setSelectedCategory] = useState("All Skills");
  const [isPracticePlaying, setIsPracticePlaying] = useState(false);
  const [exercises] = useState<Exercise[]>([
    {
      id: "1",
      title: "Vowel Prolongation",
      description: "Practice holding vowel sounds to improve breath control and speech clarity.",
      category: "Dysarthria",
      type: "WW41",
      youtubeUrl: "https://www.youtube.com/results?search_query=vowel+prolongation+speech+therapy",
    },
    {
      id: "2",
      title: "Breath Control Exercises",
      description: "Enhance breath support and control for clearer and more consistent speech.",
      category: "Dysarthria",
      youtubeUrl: "https://www.youtube.com/results?search_query=breath+control+speech+therapy+exercises",
    },
    {
      id: "3",
      title: "Articulation Drills",
      description: "Work on precise articulation of difficult sounds for better speech clarity.",
      category: "Dysarthria",
      type: "[11] 41",
      youtubeUrl: "https://www.youtube.com/results?search_query=articulation+drills+speech+therapy+adults",
    },
    {
      id: "4",
      title: "Rhythm & Rate Drills",
      description: "Practice pacing and rhythm to improve the fluency and naturalness of speech.",
      category: "Dysarthria",
      youtubeUrl: "https://www.youtube.com/results?search_query=speech+rate+control+exercises+therapy",
    },
    {
      id: "5",
      title: "Smooth Speech Exercises",
      description: "Develop techniques for smoother, more fluent speech with reduced stuttering.",
      category: "Stuttering",
      youtubeUrl: "https://www.youtube.com/results?search_query=smooth+speech+stuttering+exercises",
    },
    {
      id: "6",
      title: "Sentence Repetition",
      description: "Repeat sentences to improve clarity and speech muscle coordination.",
      category: "Dysarthria",
      youtubeUrl: "https://www.youtube.com/results?search_query=sentence+repetition+speech+therapy+practice",
    },
  ]);

  const filteredExercises =
    selectedCategory === "All Skills"
      ? exercises
      : exercises.filter((e) => e.category === selectedCategory);

  const filteredResources = useMemo(() => {
    if (selectedCategory === "All Skills") {
      return YOUTUBE_RESOURCES;
    }
    return YOUTUBE_RESOURCES.filter(
      (item) => item.category === selectedCategory || item.category === "General"
    );
  }, [selectedCategory]);

  return (
    <div className="therapy-layout">
      <Sidebar />
      <main className="therapy-content">
        <div className="therapy-header">
          <h1>Speech Therapy Hub</h1>
          <p>
            Targeted speech exercises for dysarthria, stuttering, and overall
            speech fluency improvement.
          </p>
        </div>

        <div className="therapy-filters">
          <InteractiveButton
            variant={selectedCategory === "All Skills" ? "primary" : "ghost"}
            onClick={() => setSelectedCategory("All Skills")}
          >
            All
          </InteractiveButton>
          <InteractiveButton
            variant={selectedCategory === "Dysarthria" ? "primary" : "ghost"}
            onClick={() => setSelectedCategory("Dysarthria")}
          >
            Dysarthria
          </InteractiveButton>
          <InteractiveButton
            variant={selectedCategory === "Stuttering" ? "primary" : "ghost"}
            onClick={() => setSelectedCategory("Stuttering")}
          >
            Stuttering
          </InteractiveButton>
          <InteractiveButton className="clear-filters" variant="ghost" onClick={() => setSelectedCategory("All Skills")}>
            Clear Filters
          </InteractiveButton>
        </div>

        <div className="filters-tags">
          <span className="tag">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
            </svg>
            {selectedCategory}
          </span>
        </div>

        <section className="video-resources">
          <h2>YouTube Practice Resources</h2>
          <p>Open any resource to practice with guided videos on YouTube.</p>
          <div className="resource-grid">
            {filteredResources.map((resource) => (
              <a key={resource.id} href={resource.url} target="_blank" rel="noreferrer" className="resource-link">
                <span>{resource.title}</span>
                <small>{resource.category}</small>
              </a>
            ))}
          </div>
        </section>

        <section className="practice-controls">
          <h2>Live Practice Session</h2>
          <p>Use this mini session control while following any drill.</p>
          <div className="practice-actions">
            <InteractiveButton
              variant={isPracticePlaying ? "danger" : "primary"}
              onClick={() => setIsPracticePlaying((v) => !v)}
            >
              {isPracticePlaying ? "Pause Session" : "Play Session"}
            </InteractiveButton>
            <InteractiveButton variant="ghost" onClick={() => setIsPracticePlaying(false)}>
              Reset
            </InteractiveButton>
          </div>
        </section>

        <div className="exercises-grid">
          {filteredExercises.map((exercise, index) => (
            <div key={exercise.id} className="exercise-card" style={{ animationDelay: `${index * 0.06}s` }}>
              <div className="card-header">
                <span
                  className={`category-badge ${
                    exercise.category === "Stuttering" ? "stuttering" : "dysarthria"
                  }`}
                >
                  {exercise.category}
                </span>
              </div>

              <h2 className="exercise-title">{exercise.title}</h2>
              <p className="exercise-description">{exercise.description}</p>

              <div className="exercise-meta">
                {exercise.type && (
                  <span className="exercise-type">
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path d="M11 17h2v-6h-2v6zm1-15C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-1.66 0-3 1.34-3 3h2c0-.55.45-1 1-1s1 .45 1 1c0 1-1.5 1.5-1.5 2.5h2c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5c0 1-1.5 1.5-1.5 2.5h2c0-1.33.67-2.5 1.5-2.5s1.5.67 1.5 1.5S13.5 11 12 11z" />
                    </svg>
                    {exercise.type}
                  </span>
                )}
              </div>

              <div className="exercise-actions">
                <InteractiveButton className="btn-start-exercise">
                  Start Exercise
                </InteractiveButton>
                {exercise.youtubeUrl && (
                  <a href={exercise.youtubeUrl} target="_blank" rel="noreferrer" className="btn-watch-video">
                    Watch Video
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
