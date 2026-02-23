/*
File Logic Summary: Reports page. It lists completed analyses and triggers PDF downloads for each report entry.
*/

import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import { downloadReport, getAnalysisHistory, type HistoryItem } from "../api/api";
import LoadingState from "../components/LoadingState";
import RefreshButton from "../components/RefreshButton";
import "../styles/reports.css";

export default function Reports() {
  const [reports, setReports] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadReports = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const history = await getAnalysisHistory();
      setReports(history);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load reports");
    } finally {
      if (isRefresh) setRefreshing(false);
      else setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleDownload = async (item: HistoryItem) => {
    try {
      const blob = await downloadReport(item.audio_id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${item.filename.replace(/\.[^/.]+$/, "")}_report.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to download report");
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />
      <main className="dashboard-content">
        <div className="dashboard-header">
          <div className="header-top">
            <h1>Reports</h1>
            <RefreshButton refreshing={refreshing} onClick={() => loadReports(true)} />
          </div>
          <p className="header-subtitle">
            Generated PDF reports will appear here as you complete analyses.
          </p>
        </div>

        {loading ? (
          <LoadingState label="Loading reports..." />
        ) : error ? (
          <p style={{ color: "#c00" }}>Error: {error}</p>
        ) : reports.length === 0 ? (
          <p>No reports yet. Upload an audio file to generate your first report.</p>
        ) : (
          <div className="table-responsive">
            <table className="analyses-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Filename</th>
                  <th>Dysarthria</th>
                  <th>Stuttering</th>
                  <th>Grammar</th>
                  <th>Download</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((item) => (
                  <tr key={item.id}>
                    <td>{new Date(item.created_at).toLocaleString()}</td>
                    <td>{item.filename}</td>
                    <td>{Math.round(item.dysarthria_probability * 100)}%</td>
                    <td>{Math.round(item.stuttering_probability * 100)}%</td>
                    <td>{Math.round(item.grammar_score * 100)}%</td>
                    <td>
                      <button
                        className="view-report-btn"
                        onClick={() => handleDownload(item)}
                      >
                        Download PDF
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}

