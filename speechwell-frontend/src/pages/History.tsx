/*
File Logic Summary: History page. It loads analysis records and applies date/severity filters before paginated display.
*/

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { getAnalysisHistory, type HistoryItem } from "../api/api";
import "../styles/history.css";

export default function History() {
  const [startDate, setStartDate] = useState("2024-01-01");
  const [endDate, setEndDate] = useState(new Date().toISOString().split("T")[0]);
  const [severity, setSeverity] = useState("All");
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [filteredData, setFilteredData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await getAnalysisHistory();
        setHistoryData(data);
        setFilteredData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load history");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const handleApplyFilters = () => {
    let filtered = historyData;

    // Filter by date range
    const start = new Date(startDate);
    const end = new Date(endDate);

    filtered = filtered.filter((item) => {
      const itemDate = new Date(item.created_at);
      return itemDate >= start && itemDate <= end;
    });

    // Filter by severity
    if (severity !== "All") {
      const severityThresholds = {
        High: 0.4,
        Moderate: 0.25,
        Low: 0,
      };

      const threshold =
        severityThresholds[severity as keyof typeof severityThresholds] || 0;

      filtered = filtered.filter((item) => {
        const maxRisk = Math.max(
          item.dysarthria_probability,
          item.stuttering_probability
        );
        if (severity === "High") return maxRisk >= threshold;
        if (severity === "Moderate")
          return maxRisk >= threshold && maxRisk < 0.4;
        if (severity === "Low") return maxRisk < 0.25;
        return true;
      });
    }

    setFilteredData(filtered);
    setCurrentPage(1);
  };

  const totalPages = Math.ceil(filteredData.length / rowsPerPage);
  const startIdx = (currentPage - 1) * rowsPerPage;
  const paginatedData = filteredData.slice(startIdx, startIdx + rowsPerPage);

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
    <div className="history-layout">
      <Sidebar />
      <main className="history-content">
        <div className="history-header">
          <h1>Analysis History</h1>
          <p>Review and filter all your speech analyses</p>
        </div>

        <div className="history-filters">
          <div className="date-filter">
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="date-input"
            />
            <span className="date-separator">to</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="date-input"
            />
          </div>

          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="severity-select"
          >
            <option value="All">Severity: All</option>
            <option value="High">Severity: High</option>
            <option value="Moderate">Severity: Moderate</option>
            <option value="Low">Severity: Low</option>
          </select>

          <button className="apply-btn" onClick={handleApplyFilters}>
            Apply Filters
          </button>
        </div>

        {loading ? (
          <p>Loading history...</p>
        ) : error ? (
          <p style={{ color: "#c00" }}>Error: {error}</p>
        ) : filteredData.length === 0 ? (
          <p>No analyses found for the selected filters.</p>
        ) : (
          <>
            <div className="table-responsive">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Filename</th>
                    <th>Dysarthria</th>
                    <th>Stuttering</th>
                    <th>Grammar</th>
                    <th>View</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedData.map((item) => (
                    <tr key={item.id}>
                      <td>{new Date(item.created_at).toLocaleDateString()}</td>
                      <td>{item.filename}</td>
                      <td>
                        <span
                          className={`badge badge-${getRiskColor(
                            item.dysarthria_probability
                          )}`}
                        >
                          {Math.round(item.dysarthria_probability * 100)}%
                        </span>
                      </td>
                      <td>
                        <span
                          className={`badge badge-${getRiskColor(
                            item.stuttering_probability
                          )}`}
                        >
                          {Math.round(item.stuttering_probability * 100)}%
                        </span>
                      </td>
                      <td>
                        <span
                          className={`badge badge-${getGrammarColor(
                            item.grammar_score
                          )}`}
                        >
                          {Math.round(item.grammar_score * 100)}
                        </span>
                      </td>
                      <td>
                        <button
                          className="view-btn"
                          onClick={() => handleViewReport(item.audio_id)}
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
              <div className="history-pagination">
                <select
                  value={rowsPerPage}
                  onChange={(e) => {
                    setRowsPerPage(parseInt(e.target.value));
                    setCurrentPage(1);
                  }}
                  className="rows-select"
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>

                <span className="pagination-info">
                  Showing {startIdx + 1} to{" "}
                  {Math.min(startIdx + rowsPerPage, filteredData.length)} of{" "}
                  {filteredData.length}
                </span>

                <div className="pagination-buttons">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                    (page) => (
                      <button
                        key={page}
                        className={`pagination-btn ${
                          currentPage === page ? "active" : ""
                        }`}
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
      </main>
    </div>
  );
}

