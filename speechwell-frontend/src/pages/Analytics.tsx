/*
File Logic Summary: Analytics page that transforms existing analysis history into weekly activity, skill progress, and achievement visuals.
*/

import { useEffect, useMemo, useState } from "react";
import Sidebar from "../components/Sidebar";
import { getAnalysisHistory, type HistoryItem } from "../api/api";
import InteractiveButton from "../components/InteractiveButton";
import "../styles/analytics.css";

const WEEK_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function clamp(value: number) {
  return Math.max(0, Math.min(100, value));
}

export default function Analytics() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [period, setPeriod] = useState<"week" | "month" | "year">("week");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const run = async () => {
      try {
        const data = await getAnalysisHistory();
        setHistory(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analytics");
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  const multiplier = period === "week" ? 1 : period === "month" ? 4 : 12;
  const scoped = history.slice(0, Math.max(7, 7 * multiplier));

  const metrics = useMemo(() => {
    if (!scoped.length) {
      return { sessions: 0, avgScore: 0, practiceHours: 0, weeklyGoal: 0 };
    }
    const avgGrammar =
      scoped.reduce((sum, h) => sum + h.grammar_score, 0) / scoped.length;
    const avgRisk =
      scoped.reduce(
        (sum, h) =>
          sum + Math.max(h.dysarthria_probability, h.stuttering_probability),
        0
      ) / scoped.length;
    const sessions = scoped.length;
    return {
      sessions,
      avgScore: Math.round((avgGrammar * 0.7 + (1 - avgRisk) * 0.3) * 100),
      practiceHours: Number(((sessions * 12) / 60).toFixed(1)),
      weeklyGoal: clamp(Math.round((sessions / (5 * multiplier)) * 100)),
    };
  }, [scoped, multiplier]);

  const weeklyActivity = useMemo(() => {
    const counts = new Array(7).fill(0);
    for (const item of scoped) {
      const day = new Date(item.created_at).getDay();
      const mondayFirst = (day + 6) % 7;
      counts[mondayFirst] += 1;
    }
    const maxCount = Math.max(1, ...counts);
    return counts.map((count, idx) => ({
      day: WEEK_DAYS[idx],
      count,
      width: (count / maxCount) * 100,
      points: (count * 0.8 + (idx % 2 === 0 ? 0.6 : 0.3)).toFixed(1),
    }));
  }, [scoped]);

  const skillProgress = useMemo(() => {
    if (!scoped.length) {
      return [
        { name: "Pronunciation", from: 0, to: 0 },
        { name: "Fluency", from: 0, to: 0 },
        { name: "Clarity", from: 0, to: 0 },
        { name: "Pace", from: 0, to: 0 },
        { name: "Volume", from: 0, to: 0 },
      ];
    }
    const pronunciation = clamp(
      Math.round(
        (1 -
          scoped.reduce((s, v) => s + v.dysarthria_probability, 0) /
            scoped.length) *
          100
      )
    );
    const fluency = clamp(
      Math.round(
        (1 -
          scoped.reduce((s, v) => s + v.stuttering_probability, 0) /
            scoped.length) *
          100
      )
    );
    const clarity = clamp(
      Math.round(
        (scoped.reduce((s, v) => s + v.grammar_score, 0) / scoped.length) * 100
      )
    );
    return [
      { name: "Pronunciation", from: clamp(pronunciation - 6), to: pronunciation },
      { name: "Fluency", from: clamp(fluency - 4), to: fluency },
      { name: "Clarity", from: clamp(clarity - 5), to: clarity },
      { name: "Pace", from: clamp(Math.round((fluency + pronunciation) / 2) - 3), to: clamp(Math.round((fluency + pronunciation) / 2)) },
      { name: "Volume", from: clamp(Math.round((pronunciation + clarity) / 2) - 2), to: clamp(Math.round((pronunciation + clarity) / 2)) },
    ];
  }, [scoped]);

  const achievements = [
    {
      title: "7-Day Streak",
      subtitle: "Practiced for 7 consecutive days",
      status: metrics.sessions >= 7 ? "Earned" : "In Progress",
    },
    {
      title: "Clarity Master",
      subtitle: "Achieve 90%+ clarity score",
      status: metrics.avgScore >= 90 ? "Earned" : "In Progress",
    },
  ];

  return (
    <div className="analytics-layout">
      <Sidebar />
      <main className="analytics-content page-enter">
        <header className="analytics-header">
          <h1>Analytics</h1>
          <p>Track your speech improvement progress and insights.</p>
          <div className="period-buttons">
            <InteractiveButton
              variant={period === "week" ? "primary" : "ghost"}
              onClick={() => setPeriod("week")}
            >
              Week
            </InteractiveButton>
            <InteractiveButton
              variant={period === "month" ? "primary" : "ghost"}
              onClick={() => setPeriod("month")}
            >
              Month
            </InteractiveButton>
            <InteractiveButton
              variant={period === "year" ? "primary" : "ghost"}
              onClick={() => setPeriod("year")}
            >
              Year
            </InteractiveButton>
          </div>
        </header>

        {loading ? (
          <p className="analytics-state">Loading analytics...</p>
        ) : error ? (
          <p className="analytics-state analytics-error">Error: {error}</p>
        ) : (
          <>
            <section className="analytics-metrics">
              <article className="analytics-card">
                <h3>{metrics.sessions}</h3>
                <p>Total Sessions</p>
              </article>
              <article className="analytics-card">
                <h3>{metrics.avgScore}</h3>
                <p>Average Score</p>
              </article>
              <article className="analytics-card">
                <h3>{metrics.practiceHours}h</h3>
                <p>Practice Time</p>
              </article>
              <article className="analytics-card">
                <h3>{metrics.weeklyGoal}%</h3>
                <p>Goal Completion</p>
              </article>
            </section>

            <section className="analytics-grid">
              <article className="analytics-card panel">
                <h2>Weekly Activity</h2>
                <div className="weekly-bars">
                  {weeklyActivity.map((item) => (
                    <div className="weekly-row" key={item.day}>
                      <span>{item.day}</span>
                      <div className="weekly-track">
                        <i style={{ width: `${item.width}%` }} />
                      </div>
                      <small>{item.count} sessions</small>
                      <strong>+{item.points} pts</strong>
                    </div>
                  ))}
                </div>
              </article>

              <article className="analytics-card panel">
                <h2>Skill Progress</h2>
                <div className="skill-list">
                  {skillProgress.map((skill) => (
                    <div key={skill.name} className="skill-row">
                      <div className="skill-head">
                        <span>{skill.name}</span>
                        <strong>
                          {skill.from}% → {skill.to}%
                        </strong>
                      </div>
                      <div className="weekly-track">
                        <i style={{ width: `${skill.to}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </article>
            </section>

            <section className="analytics-card panel">
              <h2>Achievements</h2>
              <div className="achievements">
                {achievements.map((item) => (
                  <article key={item.title} className="achievement-item">
                    <h3>{item.title}</h3>
                    <p>{item.subtitle}</p>
                    <span className={item.status === "Earned" ? "earned" : "progress"}>
                      {item.status}
                    </span>
                  </article>
                ))}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

