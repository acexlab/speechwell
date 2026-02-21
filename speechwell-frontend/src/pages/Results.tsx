/*
File Logic Summary: Results page. It fetches a single analysis, computes overall score, and renders transcript/metrics/report actions.
*/

import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { getAnalysisResult, downloadReport, type AnalysisResult } from "../api/api";
import "../styles/results.css";

type ResultsLocationState = {
  audioId?: string;
};

export default function Results() {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);

  useEffect(() => {
    const audioId = (location.state as ResultsLocationState | null)?.audioId;
    if (!audioId) {
      setError("No analysis ID provided");
      setLoading(false);
      return;
    }

    const fetchAnalysis = async () => {
      try {
        const result = await getAnalysisResult(audioId);
        setAnalysis(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analysis");
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [location, navigate]);

  const handleDownloadPDF = async () => {
    if (!analysis) return;
    try {
      const blob = await downloadReport(analysis.audio_id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `speech_analysis_${analysis.audio_id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to download PDF");
    }
  };

  const handleShare = () => {
    if (!analysis) return;
    const shareText = `Check out my speech analysis results from SpeechWell! Dysarthria: ${Math.round(analysis.dysarthria_probability * 100)}%, Stuttering: ${Math.round(analysis.stuttering_probability * 100)}%, Grammar: ${Math.round(analysis.grammar_score * 100)}%`;
    navigator.clipboard.writeText(shareText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleNewAnalysis = () => {
    navigate("/upload");
  };

  if (loading) {
    return (
      <div className="results-layout">
        <Sidebar />
        <main className="results-content">
          <div className="results-container">
            <p>Loading analysis results...</p>
          </div>
        </main>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="results-layout">
        <Sidebar />
        <main className="results-content">
          <div className="results-container">
            <p style={{ color: "#c00" }}>Error: {error}</p>
            <button onClick={() => navigate("/upload")}>Upload Another File</button>
          </div>
        </main>
      </div>
    );
  }

  // Calculate overall score based on probabilities
  const overallScore = Math.round(
    ((1 - analysis.dysarthria_probability) * 0.33 +
      (1 - analysis.stuttering_probability) * 0.33 +
      (analysis.grammar_score) * 0.34) *
      100
  );

  const scoreLevel =
    overallScore >= 80
      ? "Excellent"
      : overallScore >= 60
      ? "Good"
      : overallScore >= 40
      ? "Fair"
      : "Needs Improvement";

  const dysSeverity =
    analysis.dysarthria_probability < 0.3
      ? "Low"
      : analysis.dysarthria_probability < 0.6
      ? "Moderate"
      : "High";

  const stuttSeverity =
    analysis.stuttering_probability < 0.3
      ? "Mild"
      : analysis.stuttering_probability < 0.6
      ? "Moderate"
      : "Severe";

  return (
    <div className="results-layout">
      <Sidebar />
      <main className="results-content">
        <div className="results-header">
          <h1>Analysis Results</h1>
          <p className="analysis-info">
            File: {analysis.filename} | Date:{" "}
            {new Date(analysis.created_at).toLocaleDateString()}
          </p>
        </div>

        <div className="results-container">
          <div className="results-grid">
            {/* Overall Score Card */}
            <div className="overall-score-card">
              <h2>Overall Speech Health Score</h2>
              <div className="circular-progress">
                <svg viewBox="0 0 200 200" className="progress-circle">
                  <circle cx="100" cy="100" r="90" className="progress-circle-bg"></circle>
                  <circle
                    cx="100"
                    cy="100"
                    r="90"
                    className={`progress-circle-fill score-${Math.floor(overallScore / 25) + 1}`}
                    style={{
                      strokeDashoffset: 565 - (overallScore / 100) * 565,
                    }}
                  ></circle>
                </svg>
                <div className="score-text">
                  <span className="score-number">{overallScore}</span>
                  <span className="score-level">{scoreLevel}</span>
                </div>
              </div>
            </div>

            {/* Dysarthria Card */}
            <div className="analysis-card dysarthria-card">
              <h3>Dysarthria Analysis</h3>
              <div className="metric-row">
                <span className="metric-label">Probability</span>
                <span className="metric-value">
                  {Math.round(analysis.dysarthria_probability * 100)}%
                </span>
              </div>

              <div className="progress-bar">
                <div
                  className={`progress-fill dysarthria-fill`}
                  style={{
                    width: `${analysis.dysarthria_probability * 100}%`,
                  }}
                ></div>
              </div>

              <div className="severity-badges">
                {["Low", "Moderate", "High"].map((sev) => (
                  <span
                    key={sev}
                    className={`severity-dot ${sev === dysSeverity ? "active" : ""}`}
                  ></span>
                ))}
              </div>

              <p className="severity-text">
                <strong>Severity: {dysSeverity}</strong>
              </p>

              <p className="analysis-description">
                Motor speech coordination analysis shows{" "}
                {dysSeverity === "Low"
                  ? "normal patterns"
                  : dysSeverity === "Moderate"
                  ? "some atypical patterns"
                  : "significant atypical patterns"}{" "}
                in articulation and speech production.
              </p>
            </div>

            {/* Stuttering Card */}
            <div className="analysis-card stuttering-card">
              <h3>Stuttering Analysis</h3>
              <div className="metric-row">
                <span className="metric-label">Repetitions</span>
                <span className="metric-value">{analysis.stuttering_repetitions}</span>
              </div>

              <div className="metric-row">
                <span className="metric-label">Prolongations</span>
                <span className="metric-value">{analysis.stuttering_prolongations}</span>
              </div>

              <div className="metric-row">
                <span className="metric-label">Blocks</span>
                <span className="metric-value">{analysis.stuttering_blocks}</span>
              </div>

              <p className="severity-text">
                <strong>Severity: {stuttSeverity}</strong>
              </p>

              <p className="analysis-description">
                Fluency analysis detected{" "}
                {analysis.stuttering_repetitions +
                  analysis.stuttering_prolongations +
                  analysis.stuttering_blocks}{" "}
                disfluency events, indicating {stuttSeverity.toLowerCase()} stuttering patterns.
              </p>
            </div>

            {/* Grammar Card */}
            <div className="analysis-card grammar-card">
              <h3>Grammar Analysis</h3>
              <div className="metric-row">
                <span className="metric-label">Quality Score</span>
                <span className="metric-value">
                  {Math.round(analysis.grammar_score * 100)}%
                </span>
              </div>

              <div className="progress-bar">
                <div
                  className="progress-fill grammar-fill"
                  style={{ width: `${analysis.grammar_score * 100}%` }}
                ></div>
              </div>

              <div className="metric-row">
                <span className="metric-label">Estimated Errors</span>
                <span className="metric-value">{analysis.grammar_error_count}</span>
              </div>

              <p className="analysis-description">
                Language structure analysis identified{" "}
                {analysis.grammar_error_count > 0
                  ? `${analysis.grammar_error_count} grammatical patterns for review`
                  : "coherent language structure with minimal grammatical concerns"}{" "}
                in the speech sample.
              </p>
            </div>

            {/* Speech Metrics Card */}
            <div className="analysis-card metrics-card">
              <h3>Speech Metrics</h3>
              <div className="metric-row">
                <span className="metric-label">Speaking Rate (wps)</span>
                <span className="metric-value">
                  {analysis.speaking_rate_wps.toFixed(2)}
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Avg Pause (sec)</span>
                <span className="metric-value">
                  {analysis.average_pause_sec.toFixed(2)}
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Max Pause (sec)</span>
                <span className="metric-value">
                  {analysis.max_pause_sec.toFixed(2)}
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Duration (sec)</span>
                <span className="metric-value">
                  {analysis.total_duration_sec.toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          <div className="transcript-panels">
            <div className="analysis-card transcript-card">
              <h3>Original Transcript</h3>
              <p className="transcript-text">
                {analysis.transcript?.trim() || "No transcript available."}
              </p>
            </div>

            <div className="analysis-card transcript-card">
              <h3>AI-Corrected Transcript</h3>
              <p className="transcript-text">
                {analysis.corrected_text?.trim() || "No corrections were generated for this sample."}
              </p>
            </div>
          </div>

          <div className="analysis-card guide-card">
            <h3>How To Read These Results</h3>
            <p className="analysis-description">
              This is a support tool, not a diagnosis. Higher dysarthria and stuttering percentages
              mean the model detected more patterns commonly associated with those conditions.
            </p>
            <p className="analysis-description">
              Grammar score is a language quality estimate. A lower score usually means the system
              found more sentence-level issues in the transcript.
            </p>
            <p className="analysis-description">
              Use trends over multiple uploads rather than one recording. Consistent changes across
              time are more useful than a single result.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="results-actions">
            <button className="btn-pdf" onClick={handleDownloadPDF}>
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 12v7H5v-7H3v7c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-7h-2z" />
                <path d="M11 3L5.5 8.5l1.42 1.41L11 5.83V15h2V5.83l4.08 4.08L18.5 8.5 12 3z" />
              </svg>
              Download PDF
            </button>

            <button className="btn-share" onClick={handleShare}>
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.06c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.78 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.78 0 1.49-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z" />
              </svg>
              {copied ? "Copied!" : "Share"}
            </button>

            <button className="btn-new-analysis" onClick={handleNewAnalysis}>
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z" />
              </svg>
              New Analysis
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

