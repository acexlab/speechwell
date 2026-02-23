/*
File Logic Summary: Dashboard page. It aggregates analysis history into progress insights and provides quick actions while preserving report navigation.
*/

import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { getAnalysisHistory, type HistoryItem } from "../api/api";
import InteractiveButton from "../components/InteractiveButton";
import LoadingState from "../components/LoadingState";
import RefreshButton from "../components/RefreshButton";
import "../styles/dashboard.css";

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

  const streakDays = useMemo(() => calculateStreak(analyses), [analyses]);
  const totalMinutes = analyses.length * 12;
  const practiceHours = (totalMinutes / 60).toFixed(1);
  const improvementScore = Math.max(0, Math.round(avgGrammar - (avgDysarthria + avgStuttering) / 4));
  const weeklyGoal = Math.min(100, Math.round((analyses.length / 5) * 100));

  const totalPages = Math.ceil(analyses.length / itemsPerPage);
  const startIdx = (currentPage - 1) * itemsPerPage;
  const paginatedData = analyses.slice(startIdx, startIdx + itemsPerPage);
  const recentSessions = analyses.slice(0, 3);
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
    navigate("/results", { state: { audioId } });
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-content page-enter">
        <section className="dashboard-hero">
          <div>
            <h1>Welcome back, {userName}!</h1>
            <p>Ready to continue your speech improvement journey?</p>
          </div>
          <RefreshButton refreshing={refreshing} onClick={() => fetchHistory(true)} label="Refresh Data" />
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
            <h3>{analyses.length}</h3>
            <p>Total Sessions</p>
            <div className="metric-track">
              <span style={{ width: `${Math.min(100, analyses.length * 8)}%` }} />
            </div>
          </article>

          <article className="metric-card" style={{ animationDelay: "0.1s" }}>
            <h3>{weeklyGoal}%</h3>
            <p>Weekly Goal</p>
            <div className="metric-track">
              <span style={{ width: `${weeklyGoal}%` }} />
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
            <h3>{practiceHours}h</h3>
            <p>Estimated Practice Time</p>
            <div className="metric-track">
              <span style={{ width: `${Math.min(100, totalMinutes / 3)}%` }} />
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
              <InteractiveButton type="button" variant="secondary" onClick={() => navigate("/history")}>Review History</InteractiveButton>
              <InteractiveButton type="button" variant="ghost" onClick={() => navigate("/therapy-hub")}>Open Therapy Hub</InteractiveButton>
              <InteractiveButton type="button" variant="ghost" onClick={() => navigate("/reports")}>Browse Reports</InteractiveButton>
            </div>
          </article>

          <article className="panel-card">
            <div className="panel-head">
              <h2>Recent Sessions</h2>
            </div>
            {recentSessions.length === 0 ? (
              <p className="empty-state">No sessions yet. Start by uploading audio.</p>
            ) : (
              <div className="recent-list">
                {recentSessions.map((item) => (
                  <button
                    key={item.id}
                    className="recent-item"
                    type="button"
                    onClick={() => handleViewReport(item.audio_id)}
                  >
                    <div>
                      <h3>{item.filename}</h3>
                      <p>{new Date(item.created_at).toLocaleString()}</p>
                    </div>
                    <strong>{Math.round(item.grammar_score * 100)}%</strong>
                  </button>
                ))}
              </div>
            )}
          </article>
        </section>

        <section className="progress-panel panel-card">
          <h2>This Week's Progress</h2>
          <div className="progress-grid">
            <div>
              <span>Pronunciation</span>
              <strong>{Math.max(0, 100 - avgDysarthria)}%</strong>
              <div className="metric-track">
                <span style={{ width: `${Math.max(0, 100 - avgDysarthria)}%` }} />
              </div>
            </div>
            <div>
              <span>Fluency</span>
              <strong>{Math.max(0, 100 - avgStuttering)}%</strong>
              <div className="metric-track">
                <span style={{ width: `${Math.max(0, 100 - avgStuttering)}%` }} />
              </div>
            </div>
            <div>
              <span>Clarity</span>
              <strong>{avgGrammar}%</strong>
              <div className="metric-track">
                <span style={{ width: `${avgGrammar}%` }} />
              </div>
            </div>
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

          {loading ? (
            <p className="empty-state">Loading analyses...</p>
          ) : error ? (
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
