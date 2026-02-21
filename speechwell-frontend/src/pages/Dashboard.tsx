/*
File Logic Summary: Dashboard page. It aggregates analysis history into averages and risk-level summaries for quick progress tracking.
*/

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { getAnalysisHistory, type HistoryItem } from "../api/api";
import "../styles/dashboard.css";

export default function Dashboard() {
  const [analyses, setAnalyses] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const navigate = useNavigate();
  const itemsPerPage = 5;

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await getAnalysisHistory();
        setAnalyses(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analyses");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const user = localStorage.getItem("user");
  const userObj = user ? JSON.parse(user) : null;
  const userName = userObj?.email?.split("@")[0] || "User";

  // Calculate statistics
  const avgDysarthria =
    analyses.length > 0
      ? Math.round(
          (analyses.reduce((sum, a) => sum + a.dysarthria_probability, 0) /
            analyses.length) *
            100
        )
      : 0;

  const avgStuttering =
    analyses.length > 0
      ? Math.round(
          (analyses.reduce((sum, a) => sum + a.stuttering_probability, 0) /
            analyses.length) *
            100
        )
      : 0;

  const avgGrammar =
    analyses.length > 0
      ? Math.round(
          (analyses.reduce((sum, a) => sum + a.grammar_score, 0) /
            analyses.length) *
            100
        )
      : 0;

  const totalPages = Math.ceil(analyses.length / itemsPerPage);
  const startIdx = (currentPage - 1) * itemsPerPage;
  const paginatedData = analyses.slice(startIdx, startIdx + itemsPerPage);

  const getRiskLevel = (value: number) => {
    if (value >= 0.4) return "High";
    if (value >= 0.25) return "Moderate";
    return "Low";
  };

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
      <main className="dashboard-content">
        <div className="dashboard-header">
          <div className="header-top">
            <h1>Welcome back, {userName}</h1>
            <div className="header-actions">
              <input type="text" placeholder="Search analyses..." className="search-bar" />
              <button className="notification-btn">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z" />
                </svg>
              </button>
              <div className="user-profile">
                <div className="avatar">{userName.substring(0, 2).toUpperCase()}</div>
                <span>{userName}</span>
              </div>
            </div>
          </div>
          <p className="header-subtitle">
            {analyses.length} analyses completed. Track your progress and insights.
          </p>
        </div>

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z" />
              </svg>
            </div>
            <h3>Total Analyses</h3>
            <p className="stat-value">{analyses.length}</p>
            <span className="stat-change">
              {analyses.length > 0 ? "+" + analyses.length + " total" : "Get started"}
            </span>
          </div>

          <div className="stat-card">
            <div className="stat-icon dysarthria">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z" />
              </svg>
            </div>
            <h3>Dysarthria Risk Avg</h3>
            <p className="stat-value">{avgDysarthria}%</p>
            <span className={`stat-badge ${getRiskColor(avgDysarthria / 100)}`}>
              {getRiskLevel(avgDysarthria / 100)}
            </span>
          </div>

          <div className="stat-card">
            <div className="stat-icon stuttering">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-13c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5z" />
              </svg>
            </div>
            <h3>Stuttering Risk Avg</h3>
            <p className="stat-value">{avgStuttering}%</p>
            <span className={`stat-badge ${getRiskColor(avgStuttering / 100)}`}>
              {getRiskLevel(avgStuttering / 100)}
            </span>
          </div>

          <div className="stat-card">
            <div className="stat-icon grammar">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zM16 18H8v-2h8v2zm0-4H8v-2h8v2zm0-4H8V8h8v2z" />
              </svg>
            </div>
            <h3>Grammar Score Avg</h3>
            <p className="stat-value">{avgGrammar}</p>
            <span className={`stat-badge ${getGrammarColor(avgGrammar / 100)}`}>
              {avgGrammar >= 80 ? "Good" : avgGrammar >= 60 ? "Moderate" : "Low"}
            </span>
          </div>
        </div>

        <section className="recent-analyses">
          <h2>Recent Analyses</h2>
          {loading ? (
            <p>Loading analyses...</p>
          ) : error ? (
            <p style={{ color: "#c00" }}>Error: {error}</p>
          ) : analyses.length === 0 ? (
            <p>No analyses yet. Start by uploading an audio file.</p>
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
                      <th>View Report</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedData.map((analysis) => (
                      <tr key={analysis.id}>
                        <td>{new Date(analysis.created_at).toLocaleDateString()}</td>
                        <td>{analysis.filename}</td>
                        <td>
                          <span
                            className={`badge badge-${
                              getRiskColor(analysis.dysarthria_probability)
                            }`}
                          >
                            {Math.round(analysis.dysarthria_probability * 100)}%
                          </span>
                        </td>
                        <td>
                          <span
                            className={`badge badge-${
                              getRiskColor(analysis.stuttering_probability)
                            }`}
                          >
                            {Math.round(analysis.stuttering_probability * 100)}%
                          </span>
                        </td>
                        <td>
                          <span
                            className={`badge badge-${getGrammarColor(
                              analysis.grammar_score
                            )}`}
                          >
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
                    Showing {startIdx + 1} to{" "}
                    {Math.min(startIdx + itemsPerPage, analyses.length)} of {analyses.length}
                  </span>
                  <div className="pagination-controls">
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                      (page) => (
                        <button
                          key={page}
                          className={`pagination-btn ${currentPage === page ? "active" : ""}`}
                          onClick={() => setCurrentPage(page)}
                        >
                          {page}
                        </button>
                      )
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  );
}

