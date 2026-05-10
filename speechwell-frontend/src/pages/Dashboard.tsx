/*
File Logic Summary: Dashboard page. It aggregates analysis history into progress insights and provides quick actions while preserving report navigation.
*/

import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import {
  getAnalysisHistory,
  type HistoryItem,
} from "../api/api";
import InteractiveButton from "../components/InteractiveButton";
import LoadingState from "../components/LoadingState";
import RefreshButton from "../components/RefreshButton";
import { PRACTICE_VIDEOS } from "../data/practiceVideos";
import { getVideoAccessStats } from "../utils/videoAnalytics";
import "../styles/dashboard.css";

const PERIOD_SESSION_LIMITS = {
  week: 7,
  month: 28,
  year: 84,
} as const;

const WEEK_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function calculateStreak(data: HistoryItem[]) {
  if (!data.length) return 0;

  const uniqueDays = new Set(
    data.map((item) => new Date(item.created_at).toISOString().slice(0, 10))
  );

  const sorted = Array.from(uniqueDays).sort((a, b) => b.localeCompare(a));
  let streak = 1;
  const cursor = new Date(sorted[0]);

  for (let i = 1; i < sorted.length; i += 1) {
    cursor.setDate(cursor.getDate() - 1);
    const expected = cursor.toISOString().slice(0, 10);
    if (sorted[i] === expected) {
      streak += 1;
    } else {
      break;
    }
  }

  return streak;
}

function clampPercent(value: number) {
  return Math.max(0, Math.min(100, value));
}

export default function Dashboard() {
  const [analyses, setAnalyses] = useState<HistoryItem[]>([]);
  const [period, setPeriod] = useState<keyof typeof PERIOD_SESSION_LIMITS>("week");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const navigate = useNavigate();
  const itemsPerPage = 5;

  const fetchHistory = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const data = await getAnalysisHistory();
      setAnalyses(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load analyses");
    } finally {
      if (isRefresh) setRefreshing(false);
      else setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const userRaw = localStorage.getItem("user");
  let userName = "Guest";
  if (userRaw) {
    try {
      userName = JSON.parse(userRaw)?.email?.split("@")[0] ?? "Guest";
    } catch {
      userName = "Guest";
    }
  }

  const avgDysarthria =
    analyses.length > 0
      ? Math.round(
          (analyses.reduce((sum, item) => sum + item.dysarthria_probability, 0) /
            analyses.length) *
            100
        )
      : 0;

  const avgStuttering =
    analyses.length > 0
      ? Math.round(
          (analyses.reduce((sum, item) => sum + item.stuttering_probability, 0) /
            analyses.length) *
            100
        )
      : 0;

  const avgGrammar =
    analyses.length > 0
      ? Math.round(
          (analyses.reduce((sum, item) => sum + item.grammar_score, 0) / analyses.length) *
            100
        )
      : 0;

  const scopedAnalyses = useMemo(() => {
    return [...analyses]
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
      .slice(0, PERIOD_SESSION_LIMITS[period]);
  }, [analyses, period]);

  const streakDays = useMemo(() => calculateStreak(analyses), [analyses]);
  const scopedAverageScore = useMemo(() => {
    if (!scopedAnalyses.length) return 0;
    const avgScopedGrammar =
      scopedAnalyses.reduce((sum, item) => sum + item.grammar_score, 0) /
      scopedAnalyses.length;
    const avgScopedRisk =
      scopedAnalyses.reduce(
        (sum, item) =>
          sum + Math.max(item.dysarthria_probability, item.stuttering_probability),
        0
      ) / scopedAnalyses.length;
    return Math.round((avgScopedGrammar * 0.7 + (1 - avgScopedRisk) * 0.3) * 100);
  }, [scopedAnalyses]);
  const videoAccessStats = getVideoAccessStats(PRACTICE_VIDEOS);
  const watchedVideos = videoAccessStats.filter((video) => video.accessCount > 0);
  const totalVideoAccesses = videoAccessStats.reduce(
    (sum, video) => sum + video.accessCount,
    0
  );
  const improvementScore = Math.max(0, Math.round(avgGrammar - (avgDysarthria + avgStuttering) / 4));
  const scopedPracticeHours = Number(((scopedAnalyses.length * 12) / 60).toFixed(1));
  const scopedPronunciation = useMemo(() => {
    if (!scopedAnalyses.length) return 0;
    const averageRisk =
      scopedAnalyses.reduce((sum, item) => sum + item.dysarthria_probability, 0) /
      scopedAnalyses.length;
    return clampPercent(Math.round((1 - averageRisk) * 100));
  }, [scopedAnalyses]);
  const scopedFluency = useMemo(() => {
    if (!scopedAnalyses.length) return 0;
    const averageRisk =
      scopedAnalyses.reduce((sum, item) => sum + item.stuttering_probability, 0) /
      scopedAnalyses.length;
    return clampPercent(Math.round((1 - averageRisk) * 100));
  }, [scopedAnalyses]);
  const scopedClarity = useMemo(() => {
    if (!scopedAnalyses.length) return 0;
    const averageScore =
      scopedAnalyses.reduce((sum, item) => sum + item.grammar_score, 0) /
      scopedAnalyses.length;
    return clampPercent(Math.round(averageScore * 100));
  }, [scopedAnalyses]);

  const totalPages = Math.ceil(analyses.length / itemsPerPage);
  const startIdx = (currentPage - 1) * itemsPerPage;
  const paginatedData = analyses.slice(startIdx, startIdx + itemsPerPage);
  const trendData = useMemo(() => {
    return [...analyses]
      .sort(
        (a, b) =>
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      )
      .slice(-8)
      .map((item) => ({
        label: new Date(item.created_at).toLocaleDateString(undefined, {
          month: "short",
          day: "numeric",
        }),
        grammar: Math.round(item.grammar_score * 100),
        fluency: Math.round((1 - item.stuttering_probability) * 100),
        risk: Math.round(
          Math.max(item.dysarthria_probability, item.stuttering_probability) * 100
        ),
      }));
  }, [analyses]);

  const riskBuckets = useMemo(() => {
    const bucket = { high: 0, moderate: 0, low: 0 };
    for (const item of analyses) {
      const maxRisk = Math.max(item.dysarthria_probability, item.stuttering_probability);
      if (maxRisk >= 0.4) bucket.high += 1;
      else if (maxRisk >= 0.25) bucket.moderate += 1;
      else bucket.low += 1;
    }
    return bucket;
  }, [analyses]);

  const totalBucketCount = Math.max(
    1,
    riskBuckets.high + riskBuckets.moderate + riskBuckets.low
  );

  const weeklyActivity = useMemo(() => {
    const counts = new Array(7).fill(0);
    for (const item of scopedAnalyses) {
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
  }, [scopedAnalyses]);

  const skillProgress = useMemo(() => {
    if (!scopedAnalyses.length) {
      return [
        { name: "Pronunciation", from: 0, to: 0 },
        { name: "Fluency", from: 0, to: 0 },
        { name: "Clarity", from: 0, to: 0 },
        { name: "Pace", from: 0, to: 0 },
      ];
    }
    const pronunciation = clampPercent(
      Math.round(
        (1 -
          scopedAnalyses.reduce((sum, item) => sum + item.dysarthria_probability, 0) /
            scopedAnalyses.length) *
          100
      )
    );
    const fluency = clampPercent(
      Math.round(
        (1 -
          scopedAnalyses.reduce((sum, item) => sum + item.stuttering_probability, 0) /
            scopedAnalyses.length) *
          100
      )
    );
    const clarity = clampPercent(
      Math.round(
        (scopedAnalyses.reduce((sum, item) => sum + item.grammar_score, 0) /
          scopedAnalyses.length) *
          100
      )
    );
    const pace = clampPercent(Math.round((pronunciation + fluency) / 2));
    return [
      { name: "Pronunciation", from: clampPercent(pronunciation - 6), to: pronunciation },
      { name: "Fluency", from: clampPercent(fluency - 4), to: fluency },
      { name: "Clarity", from: clampPercent(clarity - 5), to: clarity },
      { name: "Pace", from: clampPercent(pace - 3), to: pace },
    ];
  }, [scopedAnalyses]);

  const achievements = useMemo(
    () => [
      {
        title: "Consistency Streak",
        subtitle:
          streakDays >= 7
            ? `${streakDays} active days in a row`
            : "Practice 7 days in a row to unlock this badge",
        status: streakDays >= 7 ? "Earned" : "In Progress",
      },
      {
        title: "Clarity Builder",
        subtitle:
          scopedAverageScore >= 85
            ? "Recent sessions are showing strong improvement"
            : "Raise your recent average score to 85+",
        status: scopedAverageScore >= 85 ? "Earned" : "In Progress",
      },
      {
        title: "Video Momentum",
        subtitle:
          watchedVideos.length >= 3
            ? "Three practice videos have been opened"
            : "Open three practice videos to build momentum",
        status: watchedVideos.length >= 3 ? "Earned" : "In Progress",
      },
    ],
    [scopedAverageScore, streakDays, watchedVideos.length]
  );

  const chartWidth = 620;
  const chartHeight = 240;
  const yTicks = [0, 25, 50, 75, 100];

  const getChartPoints = (key: "grammar" | "fluency") => {
    if (!trendData.length) return [];
    if (trendData.length === 1) {
      return [{ x: chartWidth / 2, y: chartHeight - (clampPercent(trendData[0][key]) / 100) * chartHeight }];
    }
    const xStep = chartWidth / (trendData.length - 1);
    return trendData.map((point, idx) => ({
      x: idx * xStep,
      y: chartHeight - (clampPercent(point[key]) / 100) * chartHeight,
    }));
  };

  const toLinePath = (points: Array<{ x: number; y: number }>) =>
    points
      .map((point, idx) => `${idx === 0 ? "M" : "L"}${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
      .join(" ");

  const toAreaPath = (points: Array<{ x: number; y: number }>) => {
    if (!points.length) return "";
    const first = points[0];
    const last = points[points.length - 1];
    return `${toLinePath(points)} L${last.x.toFixed(2)} ${chartHeight} L${first.x.toFixed(2)} ${chartHeight} Z`;
  };

  const grammarPoints = getChartPoints("grammar");
  const fluencyPoints = getChartPoints("fluency");

  const getRiskColor = (value: number) => {
    if (value >= 0.4) return "high";
    if (value >= 0.25) return "moderate";
    return "low";
  };

  const getGrammarColor = (value: number) => {
    if (value >= 0.8) return "good";
    if (value >= 0.6) return "moderate";
    return "low";
  };

  const handleViewReport = (audioId: string) => {
    sessionStorage.setItem("speechwell_last_audio_id", audioId);
    navigate(`/results?audioId=${encodeURIComponent(audioId)}`, { state: { audioId } });
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-content page-enter">
        <section className="dashboard-hero">
          <div>
            <h1>Welcome back, {userName}!</h1>
            <p>One workspace for session progress, analytics, and training insights.</p>
          </div>
          <div className="hero-actions">
            <div className="period-buttons">
              <InteractiveButton
                type="button"
                variant={period === "week" ? "primary" : "ghost"}
                onClick={() => setPeriod("week")}
              >
                Week
              </InteractiveButton>
              <InteractiveButton
                type="button"
                variant={period === "month" ? "primary" : "ghost"}
                onClick={() => setPeriod("month")}
              >
                Month
              </InteractiveButton>
              <InteractiveButton
                type="button"
                variant={period === "year" ? "primary" : "ghost"}
                onClick={() => setPeriod("year")}
              >
                Year
              </InteractiveButton>
            </div>
            <RefreshButton refreshing={refreshing} onClick={() => fetchHistory(true)} label="Refresh Data" />
          </div>
          <div className="streak-card animated-streak" title="Consecutive active days">
            <span className="streak-number">{streakDays}</span>
            <span className="streak-label">Day Streak</span>
          </div>
        </section>

        {loading ? (
          <LoadingState label="Loading dashboard insights..." />
        ) : (
        <>
        <section className="dashboard-stats-grid">
          <article className="metric-card" style={{ animationDelay: "0.05s" }}>
            <h3>{scopedAnalyses.length}</h3>
            <p>{period[0].toUpperCase() + period.slice(1)} Sessions</p>
            <div className="metric-track">
              <span style={{ width: `${Math.min(100, scopedAnalyses.length * 12)}%` }} />
            </div>
          </article>

          <article className="metric-card" style={{ animationDelay: "0.1s" }}>
            <h3>{scopedAverageScore}</h3>
            <p>Recent Average Score</p>
            <div className="metric-track">
              <span style={{ width: `${scopedAverageScore}%` }} />
            </div>
          </article>

          <article className="metric-card" style={{ animationDelay: "0.15s" }}>
            <h3>{improvementScore}</h3>
            <p>Improvement Score</p>
            <div className="metric-track">
              <span style={{ width: `${Math.min(100, improvementScore)}%` }} />
            </div>
          </article>

          <article className="metric-card" style={{ animationDelay: "0.2s" }}>
            <h3>{scopedPracticeHours}h</h3>
            <p>{period[0].toUpperCase() + period.slice(1)} Practice Time</p>
            <div className="metric-track">
              <span style={{ width: `${Math.min(100, scopedPracticeHours * 16)}%` }} />
            </div>
          </article>
        </section>

        <section className="achievement-banner">
          <strong>New Achievement Unlocked!</strong>
          <span>
            {streakDays >= 7 ? "7-day consistency streak" : "Keep going to unlock your streak badge"}
          </span>
        </section>

        <section className="dashboard-grid-two">
          <article className="panel-card">
            <div className="panel-head">
              <h2>Quick Actions</h2>
            </div>
            <div className="quick-actions">
              <InteractiveButton type="button" variant="primary" onClick={() => navigate("/upload")}>Start Speech Analysis</InteractiveButton>
              <InteractiveButton type="button" variant="secondary" onClick={() => navigate("/history")}>Open History & Reports</InteractiveButton>
              <InteractiveButton type="button" variant="ghost" onClick={() => navigate("/therapy-hub")}>Open Video Sessions</InteractiveButton>
              <InteractiveButton type="button" variant="ghost" onClick={() => navigate("/ai-chat")}>Ask AI Coach</InteractiveButton>
            </div>
          </article>

          <article className="panel-card">
            <div className="panel-head">
              <h2>Video Activity</h2>
              <span className="panel-meta">{totalVideoAccesses} opens</span>
            </div>
            {watchedVideos.length === 0 ? (
              <p className="empty-state">No video activity yet. Open Therapy Hub and play a practice video.</p>
            ) : (
              <div className="recent-list">
                {watchedVideos.slice(0, 3).map((item) => (
                  <button
                    key={item.url}
                    className="recent-item"
                    type="button"
                    onClick={() => navigate("/therapy-hub")}
                  >
                    <div>
                      <h3>{item.title}</h3>
                      <p>{item.category ?? "Practice Video"}</p>
                    </div>
                    <strong>{item.accessCount}x</strong>
                  </button>
                ))}
              </div>
            )}
          </article>
        </section>

        <section className="progress-panel panel-card">
          <h2>Core Skill Metrics</h2>
          <div className="progress-grid">
            <div>
              <span>Pronunciation</span>
              <strong>{scopedPronunciation}%</strong>
              <div className="metric-track">
                <span style={{ width: `${scopedPronunciation}%` }} />
              </div>
            </div>
            <div>
              <span>Fluency</span>
              <strong>{scopedFluency}%</strong>
              <div className="metric-track">
                <span style={{ width: `${scopedFluency}%` }} />
              </div>
            </div>
            <div>
              <span>Clarity</span>
              <strong>{scopedClarity}%</strong>
              <div className="metric-track">
                <span style={{ width: `${scopedClarity}%` }} />
              </div>
            </div>
            <div>
              <span>Video Opens</span>
              <strong>{totalVideoAccesses}</strong>
              <div className="metric-track">
                <span style={{ width: `${Math.min(100, totalVideoAccesses * 12)}%` }} />
              </div>
            </div>
          </div>
        </section>

        <section className="dashboard-grid-two charts-row analytics-grid">
          <article className="panel-card">
            <div className="panel-head">
              <h2>Weekly Activity</h2>
              <span className="panel-meta">Session spread</span>
            </div>
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

          <article className="panel-card">
            <div className="panel-head">
              <h2>Skill Progress</h2>
              <span className="panel-meta">Recent change</span>
            </div>
            <div className="skill-list">
              {skillProgress.map((skill) => (
                <div key={skill.name} className="skill-row">
                  <div className="skill-head">
                    <span>{skill.name}</span>
                    <strong>
                      {skill.from}% -&gt; {skill.to}%
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

        <section className="panel-card">
          <div className="panel-head">
            <h2>Achievements</h2>
            <span className="panel-meta">Motivation without another page</span>
          </div>
          <div className="achievements-grid">
            {achievements.map((item) => (
              <article key={item.title} className="achievement-card">
                <h3>{item.title}</h3>
                <p>{item.subtitle}</p>
                <span className={`achievement-status ${item.status === "Earned" ? "earned" : "progress"}`}>
                  {item.status}
                </span>
              </article>
            ))}
          </div>
        </section>

        <section className="dashboard-grid-two charts-row">
          <article className="panel-card chart-card">
            <div className="panel-head">
              <h2>Performance Trend</h2>
            </div>
            {trendData.length < 2 ? (
              <p className="empty-state">Add more sessions to see trend charts.</p>
            ) : (
              <div className="trend-chart">
                <svg viewBox={`-44 -8 ${chartWidth + 52} ${chartHeight + 34}`} role="img" aria-label="Grammar and fluency trend chart">
                  {yTicks.map((tick) => {
                    const y = chartHeight - (tick / 100) * chartHeight;
                    return (
                      <g key={`tick-${tick}`}>
                        <line x1="0" y1={y} x2={chartWidth} y2={y} className="axis-line light" />
                        <text x="-10" y={y + 4} className="y-axis-label">{tick}%</text>
                      </g>
                    );
                  })}
                  <line x1="0" y1={chartHeight} x2={chartWidth} y2={chartHeight} className="axis-line" />
                  <path d={toAreaPath(grammarPoints)} className="trend-area grammar-area" />
                  <path d={toAreaPath(fluencyPoints)} className="trend-area fluency-area" />
                  <path d={toLinePath(grammarPoints)} className="trend-line grammar-line" />
                  <path d={toLinePath(fluencyPoints)} className="trend-line fluency-line" />
                  {trendData.map((point, index) => {
                    const x = trendData.length === 1 ? chartWidth / 2 : (chartWidth / (trendData.length - 1)) * index;
                    const grammarY = chartHeight - (clampPercent(point.grammar) / 100) * chartHeight;
                    const fluencyY = chartHeight - (clampPercent(point.fluency) / 100) * chartHeight;
                    return (
                      <g key={`${point.label}-${index}`}>
                        <circle cx={x} cy={grammarY} r="4" className="trend-dot grammar-dot" />
                        <circle cx={x} cy={fluencyY} r="4" className="trend-dot fluency-dot" />
                      </g>
                    );
                  })}
                </svg>
                <div className="chart-x-labels">
                  {trendData.map((point) => (
                    <span key={point.label}>{point.label}</span>
                  ))}
                </div>
                <div className="chart-legend">
                  <span><i className="legend-dot grammar-dot" />Grammar</span>
                  <span><i className="legend-dot fluency-dot" />Fluency</span>
                </div>
              </div>
            )}
          </article>

          <article className="panel-card chart-card">
            <div className="panel-head">
              <h2>Risk Distribution</h2>
            </div>
            <div className="risk-bars">
              <div className="risk-row">
                <span>High</span>
                <div className="risk-bar"><i className="risk-fill high" style={{ width: `${(riskBuckets.high / totalBucketCount) * 100}%` }} /></div>
                <strong>{riskBuckets.high}</strong>
              </div>
              <div className="risk-row">
                <span>Moderate</span>
                <div className="risk-bar"><i className="risk-fill moderate" style={{ width: `${(riskBuckets.moderate / totalBucketCount) * 100}%` }} /></div>
                <strong>{riskBuckets.moderate}</strong>
              </div>
              <div className="risk-row">
                <span>Low</span>
                <div className="risk-bar"><i className="risk-fill low" style={{ width: `${(riskBuckets.low / totalBucketCount) * 100}%` }} /></div>
                <strong>{riskBuckets.low}</strong>
              </div>
            </div>
            <div className="risk-summary">
              <div>
                <p>Avg Dysarthria</p>
                <h3>{avgDysarthria}%</h3>
              </div>
              <div>
                <p>Avg Stuttering</p>
                <h3>{avgStuttering}%</h3>
              </div>
              <div>
                <p>Avg Grammar</p>
                <h3>{avgGrammar}%</h3>
              </div>
            </div>
          </article>
        </section>

        <section className="panel-card">
          <div className="panel-head">
            <h2>Detailed Analyses</h2>
          </div>

          {error ? (
            <p className="error-state">Error: {error}</p>
          ) : analyses.length === 0 ? (
            <p className="empty-state">No analyses yet. Start by uploading an audio file.</p>
          ) : (
            <>
              <div className="table-responsive">
                <table className="analyses-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Filename</th>
                      <th>Dysarthria</th>
                      <th>Stuttering</th>
                      <th>Grammar</th>
                      <th>Report</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedData.map((analysis) => (
                      <tr key={analysis.id}>
                        <td>{new Date(analysis.created_at).toLocaleDateString()}</td>
                        <td>{analysis.filename}</td>
                        <td>
                          <span className={`badge badge-${getRiskColor(analysis.dysarthria_probability)}`}>
                            {Math.round(analysis.dysarthria_probability * 100)}%
                          </span>
                        </td>
                        <td>
                          <span className={`badge badge-${getRiskColor(analysis.stuttering_probability)}`}>
                            {Math.round(analysis.stuttering_probability * 100)}%
                          </span>
                        </td>
                        <td>
                          <span className={`badge badge-${getGrammarColor(analysis.grammar_score)}`}>
                            {Math.round(analysis.grammar_score * 100)}
                          </span>
                        </td>
                        <td>
                          <button
                            className="view-report-btn"
                            onClick={() => handleViewReport(analysis.audio_id)}
                          >
                            View Report
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="pagination">
                  <span className="pagination-info">
                    Showing {startIdx + 1} to {Math.min(startIdx + itemsPerPage, analyses.length)} of {analyses.length}
                  </span>
                  <div className="pagination-controls">
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                      <button
                        key={page}
                        className={`pagination-btn ${currentPage === page ? "active" : ""}`}
                        onClick={() => setCurrentPage(page)}
                      >
                        {page}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </section>
        </>
        )}
      </main>
    </div>
  );
}
