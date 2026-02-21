/*
File Logic Summary: TypeScript module for frontend runtime logic, routing, API integration, or UI behavior.
*/

import { useNavigate } from "react-router-dom";
import "../styles/landing.css";

export default function Landing() {
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem("accessToken");

  const handleStartAnalysis = () => {
    if (isAuthenticated) {
      navigate("/upload");
    } else {
      navigate("/login");
    }
  };

  return (
    <div className="landing-container">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1>AI-Powered Clinical Speech Analysis</h1>
          <p>
            Detect dysarthria, stuttering, and speech fluency issues using
            advanced AI models.
          </p>
          <div className="hero-buttons">
            <button
              className="btn-primary"
              onClick={handleStartAnalysis}
            >
              Start Analysis
            </button>
            <button className="btn-secondary">View Sample Report</button>
          </div>
        </div>
        <div className="hero-illustration">
          <svg
            viewBox="0 0 300 300"
            xmlns="http://www.w3.org/2000/svg"
            className="brain-illustration"
          >
            {/* Head silhouette */}
            <path
              d="M 150 50 Q 190 80 200 130 Q 210 180 150 220 Q 90 180 80 130 Q 70 80 150 50"
              fill="url(#headGradient)"
              opacity="0.7"
            />

            {/* Neural network visualization */}
            <circle cx="120" cy="100" r="4" fill="#fff" opacity="0.8" />
            <circle cx="150" cy="80" r="4" fill="#fff" opacity="0.8" />
            <circle cx="180" cy="100" r="4" fill="#fff" opacity="0.8" />
            <circle cx="110" cy="140" r="4" fill="#fff" opacity="0.8" />
            <circle cx="150" cy="130" r="5" fill="#fff" opacity="0.9" />
            <circle cx="190" cy="140" r="4" fill="#fff" opacity="0.8" />
            <circle cx="130" cy="170" r="4" fill="#fff" opacity="0.8" />
            <circle cx="170" cy="170" r="4" fill="#fff" opacity="0.8" />

            {/* Connection lines */}
            <line
              x1="120"
              y1="100"
              x2="150"
              y2="130"
              stroke="#fff"
              strokeWidth="1"
              opacity="0.4"
            />
            <line
              x1="150"
              y1="80"
              x2="150"
              y2="130"
              stroke="#fff"
              strokeWidth="1"
              opacity="0.4"
            />
            <line
              x1="180"
              y1="100"
              x2="150"
              y2="130"
              stroke="#fff"
              strokeWidth="1"
              opacity="0.4"
            />
            <line
              x1="110"
              y1="140"
              x2="130"
              y2="170"
              stroke="#fff"
              strokeWidth="1"
              opacity="0.4"
            />
            <line
              x1="190"
              y1="140"
              x2="170"
              y2="170"
              stroke="#fff"
              strokeWidth="1"
              opacity="0.4"
            />

            {/* Audio waves */}
            <g opacity="0.5">
              <path
                d="M 60 180 Q 65 170 70 180"
                stroke="#fff"
                strokeWidth="2"
                fill="none"
              />
              <path
                d="M 70 180 Q 75 160 80 180"
                stroke="#fff"
                strokeWidth="2"
                fill="none"
              />
              <path
                d="M 80 180 Q 85 175 90 180"
                stroke="#fff"
                strokeWidth="2"
                fill="none"
              />
            </g>

            {/* Gradient definitions */}
            <defs>
              <linearGradient id="headGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style={{ stopColor: "#5b9ce1", stopOpacity: 1 }} />
                <stop offset="100%" style={{ stopColor: "#3b6ba3", stopOpacity: 1 }} />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <h2>Our Features</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon dysarthria">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
              </svg>
            </div>
            <h3>Dysarthria Detection</h3>
            <p>Identify speech motor disorders</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon stuttering">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
              </svg>
            </div>
            <h3>Stuttering Detection</h3>
            <p>Analyze speech disfluencies</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon grammar">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z" />
              </svg>
            </div>
            <h3>Grammar & Fluency</h3>
            <p>Evaluate language and coherence</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon reports">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z" />
              </svg>
            </div>
            <h3>Clinical Reports</h3>
            <p>Generate detailed PDF reports</p>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works">
        <h2>How It Works</h2>
        <div className="steps-container">
          <div className="step">
            <div className="step-number">1</div>
            <div className="step-icon upload">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4c-1.48 0-2.85.43-4.01 1.17l1.46 1.46C10.21 5.23 11.08 5 12 5c3.04 0 5.5 2.46 5.5 5.5v.5H19c1.66 0 3 1.34 3 3 0 1.13-.64 2.11-1.56 2.62l1.45 1.45C23.16 15.5 24 14.08 24 12.5c0-2.64-2.05-4.78-4.65-4.96zM16.5 16.5H13v3h-2v-3H8.5l4-4 4 4z" />
              </svg>
            </div>
            <h3>Upload Speech Audio</h3>
            <p>Upload your audio file.</p>
          </div>

          <div className="step-divider" />

          <div className="step">
            <div className="step-number">2</div>
            <div className="step-icon analyze">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z" />
              </svg>
            </div>
            <h3>AI Analyzes Speech</h3>
            <p>Our AI processes your speech.</p>
          </div>

          <div className="step-divider" />

          <div className="step">
            <div className="step-number">3</div>
            <div className="step-icon report">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zM16 18H8v-2h8v2zm0-4H8v-2h8v2zm0-4H8V8h8v2z" />
              </svg>
            </div>
            <h3>Get Clinical Report</h3>
            <p>Receive a comprehensive report.</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-links">
          <a href="#privacy">Privacy Policy</a>
          <a href="#about">About Us</a>
          <a href="#contact">Contact</a>
        </div>
        <p className="footer-text">
          © 2024 SpeechWell. For clinical support only. Not a diagnostic tool.
        </p>
      </footer>
    </div>
  );
}

