/*
File Logic Summary: TypeScript module for frontend runtime logic, routing, API integration, or UI behavior.
*/

import { useState } from "react";
import Sidebar from "../components/Sidebar";
import "../styles/therapy-hub.css";

interface Exercise {
  id: string;
  title: string;
  description: string;
  category: string;
  type?: string;
}

export default function TherapyHub() {
  const [selectedCategory, setSelectedCategory] = useState("All Skills");
  const [exercises] = useState<Exercise[]>([
    {
      id: "1",
      title: "Vowel Prolongation",
      description: "Practice holding vowel sounds to improve breath control and speech clarity.",
      category: "Dysarthria",
      type: "WW41",
    },
    {
      id: "2",
      title: "Breath Control Exercises",
      description: "Enhance breath support and control for clearer and more consistent speech.",
      category: "Dysarthria",
    },
    {
      id: "3",
      title: "Articulation Drills",
      description: "Work on precise articulation of difficult sounds for better speech clarity.",
      category: "Dysarthria",
      type: "[11] 41",
    },
    {
      id: "4",
      title: "Rhythm & Rate Drills",
      description: "Practice pacing and rhythm to improve the fluency and naturalness of speech.",
      category: "Dysarthria",
    },
    {
      id: "5",
      title: "Smooth Speech Exercises",
      description: "Develop techniques for smoother, more fluent speech with reduced stuttering.",
      category: "Stuttering",
    },
    {
      id: "6",
      title: "Sentence Repetition",
      description: "Repeat sentences to improve clarity and speech muscle coordination.",
      category: "Dysarthria",
    },
  ]);

  const filteredExercises =
    selectedCategory === "All Skills"
      ? exercises
      : exercises.filter((e) => e.category === selectedCategory);

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
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="filter-dropdown"
          >
            <option>All Skills</option>
            <option>Dysarthria</option>
            <option>Stuttering</option>
          </select>

          <button className="clear-filters">Clear Filters</button>
        </div>

        <div className="filters-tags">
          <span className="tag">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
            </svg>
            All Skills
          </span>
          {selectedCategory !== "All Skills" && (
            <span className="tag">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
              </svg>
              {selectedCategory}
            </span>
          )}
        </div>

        <div className="exercises-grid">
          {filteredExercises.map((exercise) => (
            <div key={exercise.id} className="exercise-card">
              <div className="card-header">
                <span className={`category-badge dysarthria`}>
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

              <button className="btn-start-exercise">Start Exercise</button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

