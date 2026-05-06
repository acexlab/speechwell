/*
File Logic Summary: Results page. It fetches a single analysis, computes overall score, and renders transcript/metrics/report actions.
*/

import { useState, useEffect } from "react";
import { useNavigate, useLocation, useSearchParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import InteractiveButton from "../components/InteractiveButton";
import LoadingState from "../components/LoadingState";
import { getAnalysisResult, downloadReport, type AnalysisResult } from "../api/api";
import "../styles/results.css";

type ResultsLocationState = {
  audioId?: string;
};

export default function Results() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);

  useEffect(() => {
    const stateAudioId = (location.state as ResultsLocationState | null)?.audioId;
    const queryAudioId = searchParams.get("audioId") || undefined;
    const storedAudioId = sessionStorage.getItem("speechwell_last_audio_id") || undefined;
    const audioId = stateAudioId || queryAudioId || storedAudioId;
    if (!audioId) {
      setError("No analysis ID provided");
      setLoading(false);
      return;
    }
    sessionStorage.setItem("speechwell_last_audio_id", audioId);

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
  }, [location, navigate, searchParams]);

  const handleDownloadPDF = async () => {
    if (!analysis) return;
    try {
      const { blob, filename } = await downloadReport(analysis.audio_id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename || analysis.report_filename || `speech_analysis_${analysis.audio_id}.pdf`;
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
    const shareText = `Check out my speech analysis results from SpeechWell! Pronunciation: ${Math.round((1 - analysis.dysarthria_probability) * 100)}%, Fluency: ${Math.round((1 - analysis.stuttering_probability) * 100)}%, Clarity: ${Math.round(analysis.grammar_score * 100)}%`;
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
            <LoadingState label="Loading analysis results..." />
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

  const overallScore = analysis.overall_score;

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

  const dysRiskPercent = Math.round(analysis.dysarthria_probability * 100);
  const dysRiskTone =
    analysis.dysarthria_label === "dysarthria"
      ? dysRiskPercent >= 90
        ? "high-likelihood"
        : "possible"
      : dysRiskPercent < 20
      ? "healthy"
      : dysRiskPercent < 45
      ? "reduced-risk"
      : "watch";

  const dysRiskTitle =
    dysRiskTone === "high-likelihood"
      ? "Higher likelihood of dysarthria"
      : dysRiskTone === "possible"
      ? "Possible dysarthria pattern"
      : dysRiskTone === "healthy"
      ? "Healthy speech pattern"
      : dysRiskTone === "reduced-risk"
      ? "Healthy with reduced risk"
      : "Mostly healthy, monitor over time";

  const dysRiskDescription =
    dysRiskTone === "high-likelihood"
      ? "The model found strong dysarthria-like patterns in the recording. Use repeated samples and clinical follow-up for confirmation."
      : dysRiskTone === "possible"
      ? "Some dysarthria-like features were detected. Try a few more recordings before treating this as a strong concern."
      : dysRiskTone === "healthy"
      ? "The recording looks consistent with healthy speech, with little evidence of dysarthria-like motor speech patterns."
      : dysRiskTone === "reduced-risk"
      ? "The recording is currently being treated as healthy. A few atypical features were present, but the risk was reduced by the guardrail."
      : "The result still lands on the healthy side, but it is worth watching trends across multiple recordings.";

  const stuttSeverity =
    analysis.stuttering_probability < 0.3
      ? "Mild"
      : analysis.stuttering_probability < 0.6
      ? "Moderate"
      : "Severe";

  const stuttRiskPercent = Math.round(analysis.stuttering_probability * 100);
  const fluencyScorePercent = Math.round((1 - analysis.stuttering_probability) * 100);
  const stuttRiskTone =
    stuttRiskPercent < 15
      ? "healthy"
      : stuttRiskPercent < 35
      ? "reduced-risk"
      : stuttRiskPercent < 60
      ? "watch"
      : stuttRiskPercent < 85
      ? "possible"
      : "high-likelihood";

  const stuttRiskTitle =
    stuttRiskTone === "healthy"
      ? "Fluent speech pattern"
      : stuttRiskTone === "reduced-risk"
      ? "Mostly fluent with minor disfluency"
      : stuttRiskTone === "watch"
      ? "Healthy, but monitor fluency"
      : stuttRiskTone === "possible"
      ? "Possible stuttering pattern"
      : "Higher likelihood of stuttering";

  const totalDisfluencyEvents =
    analysis.stuttering_repetitions +
    analysis.stuttering_prolongations +
    analysis.stuttering_blocks;

  const stuttRiskDescription =
    stuttRiskTone === "healthy"
      ? "The recording looks broadly fluent, with little evidence of clinically meaningful disfluency."
      : stuttRiskTone === "reduced-risk"
      ? "A small number of disfluency markers were detected, but the overall speech pattern still looks mostly fluent."
      : stuttRiskTone === "watch"
      ? "Some fluency interruptions were present. This still sits below a strong concern, but it is worth watching across repeated recordings."
      : stuttRiskTone === "possible"
      ? "The model detected a noticeable disfluency pattern. Compare a few more recordings before treating this as a stable issue."
      : "The recording shows a strong disfluency signal with repeated interruptions in flow.";

  const grammarErrorProbability =
    typeof analysis.grammar_error_probability === "number"
      ? analysis.grammar_error_probability
      : 1 - analysis.grammar_score;
  const grammarSignalPercent = Math.round(grammarErrorProbability * 100);
  const clarityScorePercent = Math.round(analysis.grammar_score * 100);
  const grammarRiskTone =
    grammarSignalPercent < 15
      ? "healthy"
      : grammarSignalPercent < 35
      ? "reduced-risk"
      : grammarSignalPercent < 60
      ? "watch"
      : grammarSignalPercent < 85
      ? "possible"
      : "high-likelihood";

  const grammarRiskTitle =
    grammarRiskTone === "healthy"
      ? "Clear language structure"
      : grammarRiskTone === "reduced-risk"
      ? "Mostly clear with minor issues"
      : grammarRiskTone === "watch"
      ? "Healthy, but review phrasing"
      : grammarRiskTone === "possible"
      ? "Noticeable grammar issues"
      : "High grammar correction need";

  const grammarRiskDescription =
    grammarRiskTone === "healthy"
      ? "The transcript looks linguistically clear, with little evidence of grammar-level disruption."
      : grammarRiskTone === "reduced-risk"
      ? "A few language-level corrections were needed, but the overall structure is still clear."
      : grammarRiskTone === "watch"
      ? "Some sentence-level issues were detected. This is still manageable, but worth reviewing over repeated samples."
      : grammarRiskTone === "possible"
      ? "The transcript required a meaningful level of grammar correction, which may affect overall clarity."
      : "The transcript shows a high concentration of grammar-level issues and likely needs guided review.";

  const dysImpactText =
    analysis.dysarthria_label === "dysarthria"
      ? "A higher signal here increases concern about motor-speech difficulty, especially when symptom evidence is also present."
      : "This score is being treated as low enough for a healthy result after the symptom guardrail reviewed the recording.";

  const stuttImpactText =
    totalDisfluencyEvents === 0
      ? "With no disfluency events detected, the fluency score stays high and the result remains on the fluent side."
      : "More repetitions, prolongations, and blocks increase the disfluency signal and reduce the fluency score.";

  const grammarImpactText =
    analysis.grammar_error_count <= 2
      ? "Only a small amount of correction was needed, so the transcript is still considered mostly clear."
      : "As correction needs and estimated errors rise, clarity drops and the result moves closer to a review-needed state.";

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
              <div className={`risk-banner ${dysRiskTone}`}>
                <span className="risk-banner-label">{dysRiskTitle}</span>
                <span className="risk-banner-value">{dysRiskPercent}% signal</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Model Signal</span>
                <span className="metric-value">
                  {dysRiskPercent}%
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

              <p className="severity-text">
                <strong>
                  {analysis.dysarthria_label === "dysarthria" ? "Current decision: Possible concern" : "Current decision: Healthy"}
                </strong>
              </p>

              <p className="analysis-description">
                {dysRiskDescription}
              </p>

              <p className="analysis-description secondary">
                Raw signal band: {dysSeverity}. The final decision also accounts for symptom evidence,
                not only the raw percentage.
              </p>

              <div className="analysis-insight-card">
                <p className="analysis-insight-title">How To Read This</p>
                <div className="analysis-insight-row">
                  <span className="analysis-insight-label">What the score means</span>
                  <span className="analysis-insight-copy">
                    Model Signal is the percentage of dysarthria-like motor speech patterns detected in this sample.
                  </span>
                </div>
                <div className="analysis-insight-row">
                  <span className="analysis-insight-label">How it affects the result</span>
                  <span className="analysis-insight-copy">{dysImpactText}</span>
                </div>
              </div>
            </div>

            {/* Stuttering Card */}
            <div className="analysis-card stuttering-card">
              <h3>Stuttering Analysis</h3>
              <div className={`risk-banner ${stuttRiskTone}`}>
                <span className="risk-banner-label">{stuttRiskTitle}</span>
                <span className="risk-banner-value">{stuttRiskPercent}% signal</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Disfluency Signal</span>
                <span className="metric-value">{stuttRiskPercent}%</span>
              </div>

              <div className="progress-bar">
                <div
                  className="progress-fill stuttering-fill"
                  style={{ width: `${stuttRiskPercent}%` }}
                ></div>
              </div>

              <div className="metric-row">
                <span className="metric-label">Fluency Score</span>
                <span className="metric-value">
                  {fluencyScorePercent}%
                </span>
              </div>

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
                <strong>{stuttRiskTone === "healthy" || stuttRiskTone === "reduced-risk" || stuttRiskTone === "watch" ? "Current decision: Mostly fluent" : "Current decision: Possible concern"}</strong>
              </p>

              <p className="analysis-description">
                {stuttRiskDescription}
              </p>

              <p className="analysis-description secondary">
                Raw signal band: {stuttSeverity}. Detected {totalDisfluencyEvents} disfluency event
                {totalDisfluencyEvents === 1 ? "" : "s"} across repetitions, prolongations, and blocks.
              </p>

              <div className="analysis-insight-card">
                <p className="analysis-insight-title">How To Read This</p>
                <div className="analysis-insight-row">
                  <span className="analysis-insight-label">What the score means</span>
                  <span className="analysis-insight-copy">
                    Disfluency Signal estimates how much the speech flow was interrupted. Fluency Score shows the smoother side of the same result.
                  </span>
                </div>
                <div className="analysis-insight-row">
                  <span className="analysis-insight-label">How it affects the result</span>
                  <span className="analysis-insight-copy">{stuttImpactText}</span>
                </div>
              </div>
            </div>

            {/* Grammar Card */}
            <div className="analysis-card grammar-card">
              <h3>Grammar Analysis</h3>
              <div className={`risk-banner ${grammarRiskTone}`}>
                <span className="risk-banner-label">{grammarRiskTitle}</span>
                <span className="risk-banner-value">{grammarSignalPercent}% signal</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Grammar Error Signal</span>
                <span className="metric-value">{grammarSignalPercent}%</span>
              </div>

              <div className="progress-bar">
                <div
                  className="progress-fill grammar-signal-fill"
                  style={{ width: `${grammarSignalPercent}%` }}
                ></div>
              </div>

              <div className="metric-row">
                <span className="metric-label">Clarity Score</span>
                <span className="metric-value">
                  {clarityScorePercent}%
                </span>
              </div>

              <div className="progress-bar">
                <div
                  className="progress-fill grammar-fill"
                  style={{ width: `${analysis.grammar_score * 100}%` }}
                ></div>
              </div>

              <p className="severity-text">
                <strong>{grammarRiskTone === "healthy" || grammarRiskTone === "reduced-risk" || grammarRiskTone === "watch" ? "Current decision: Mostly clear" : "Current decision: Needs review"}</strong>
              </p>

              <div className="metric-row">
                <span className="metric-label">Estimated Errors</span>
                <span className="metric-value">{analysis.grammar_error_count}</span>
              </div>

              <p className="analysis-description">
                {grammarRiskDescription}
              </p>

              {typeof analysis.grammar_error_probability === "number" && (
                <p className="analysis-description secondary">
                  Estimated grammar error probability: {Math.round(analysis.grammar_error_probability * 100)}%.
                </p>
              )}

              <div className="analysis-insight-card">
                <p className="analysis-insight-title">How To Read This</p>
                <div className="analysis-insight-row">
                  <span className="analysis-insight-label">What the score means</span>
                  <span className="analysis-insight-copy">
                    Grammar Error Signal estimates how much correction the transcript needed. Clarity Score reflects how readable and complete the language remained.
                  </span>
                </div>
                <div className="analysis-insight-row">
                  <span className="analysis-insight-label">How it affects the result</span>
                  <span className="analysis-insight-copy">{grammarImpactText}</span>
                </div>
              </div>
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
              Clarity score is calculated as `1 - grammar error probability`, so a higher score
              means the transcript needed fewer grammar-level corrections.
            </p>
            <p className="analysis-description">
              Use trends over multiple uploads rather than one recording. Consistent changes across
              time are more useful than a single result.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="results-actions">
            <InteractiveButton className="btn-pdf" onClick={handleNewAnalysis}>
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z" />
              </svg>
              Record Again
            </InteractiveButton>

            <InteractiveButton className="btn-pdf" onClick={handleDownloadPDF}>
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 12v7H5v-7H3v7c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-7h-2z" />
                <path d="M11 3L5.5 8.5l1.42 1.41L11 5.83V15h2V5.83l4.08 4.08L18.5 8.5 12 3z" />
              </svg>
              Save Results
            </InteractiveButton>

            <InteractiveButton className="btn-share" variant="secondary" onClick={handleShare}>
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.06c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.78 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.78 0 1.49-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z" />
              </svg>
              {copied ? "Copied!" : "Share Analysis"}
            </InteractiveButton>
          </div>
        </div>
      </main>
    </div>
  );
}

