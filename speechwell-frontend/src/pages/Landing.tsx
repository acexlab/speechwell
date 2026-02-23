/*
File Logic Summary: TypeScript module for frontend runtime logic, routing, API integration, or UI behavior.
*/

import type { CSSProperties } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/landing.css";

const FEATURE_ITEMS = [
  {
    title: "Dysarthria Detection",
    description: "Identify speech motor disorders",
    iconClass: "dysarthria",
    iconPath: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z",
  },
  {
    title: "Stuttering Detection",
    description: "Analyze speech disfluencies",
    iconClass: "stuttering",
    iconPath: "M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2",
  },
  {
    title: "Grammar & Fluency",
    description: "Evaluate language and coherence",
    iconClass: "grammar",
    iconPath: "M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z",
  },
  {
    title: "Clinical Reports",
    description: "Generate detailed PDF reports",
    iconClass: "reports",
    iconPath: "M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z",
  },
];

const STEP_ITEMS = [
  {
    number: "1",
    title: "Upload Speech Audio",
    description: "Upload your audio file.",
    iconClass: "upload",
    iconPath: "M19.35 10.04C18.67 6.59 15.64 4 12 4c-1.48 0-2.85.43-4.01 1.17l1.46 1.46C10.21 5.23 11.08 5 12 5c3.04 0 5.5 2.46 5.5 5.5v.5H19c1.66 0 3 1.34 3 3 0 1.13-.64 2.11-1.56 2.62l1.45 1.45C23.16 15.5 24 14.08 24 12.5c0-2.64-2.05-4.78-4.65-4.96zM16.5 16.5H13v3h-2v-3H8.5l4-4 4 4z",
  },
  {
    number: "2",
    title: "AI Analyzes Speech",
    description: "Our AI processes your speech.",
    iconClass: "analyze",
    iconPath: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z",
  },
  {
    number: "3",
    title: "Get Clinical Report",
    description: "Receive a comprehensive report.",
    iconClass: "report",
    iconPath: "M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zM16 18H8v-2h8v2zm0-4H8v-2h8v2zm0-4H8V8h8v2z",
  },
];

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

  const handleViewSampleReport = () => {
    if (isAuthenticated) {
      navigate("/reports");
    } else {
      navigate("/login");
    }
  };

  return (
    <div className="landing-container">
      <section className="hero">
        <div className="hero-ambient" aria-hidden="true">
          <span className="orb orb-1" />
          <span className="orb orb-2" />
          <span className="orb orb-3" />
        </div>

        <div className="hero-content">
          <h1 className="reveal-item reveal-1">AI-Powered Clinical Speech Analysis</h1>
          <p className="reveal-item reveal-2">
            Detect dysarthria, stuttering, and speech fluency issues using advanced AI models.
          </p>
          <div className="hero-buttons reveal-item reveal-3">
            <button className="btn-primary" onClick={handleStartAnalysis}>
              Start Analysis
            </button>
            <button className="btn-secondary" onClick={handleViewSampleReport}>
              View Sample Report
            </button>
          </div>
        </div>

        <div className="hero-illustration reveal-item reveal-4">
          <svg
            viewBox="0 0 300 300"
            xmlns="http://www.w3.org/2000/svg"
            className="brain-illustration"
          >
            <path
              d="M 150 50 Q 190 80 200 130 Q 210 180 150 220 Q 90 180 80 130 Q 70 80 150 50"
              fill="url(#headGradient)"
              opacity="0.7"
            />
            <circle cx="120" cy="100" r="4" fill="#fff" opacity="0.8" />
            <circle cx="150" cy="80" r="4" fill="#fff" opacity="0.8" />
            <circle cx="180" cy="100" r="4" fill="#fff" opacity="0.8" />
            <circle cx="110" cy="140" r="4" fill="#fff" opacity="0.8" />
            <circle cx="150" cy="130" r="5" fill="#fff" opacity="0.9" />
            <circle cx="190" cy="140" r="4" fill="#fff" opacity="0.8" />
            <circle cx="130" cy="170" r="4" fill="#fff" opacity="0.8" />
            <circle cx="170" cy="170" r="4" fill="#fff" opacity="0.8" />
            <line x1="120" y1="100" x2="150" y2="130" stroke="#fff" strokeWidth="1" opacity="0.4" />
            <line x1="150" y1="80" x2="150" y2="130" stroke="#fff" strokeWidth="1" opacity="0.4" />
            <line x1="180" y1="100" x2="150" y2="130" stroke="#fff" strokeWidth="1" opacity="0.4" />
            <line x1="110" y1="140" x2="130" y2="170" stroke="#fff" strokeWidth="1" opacity="0.4" />
            <line x1="190" y1="140" x2="170" y2="170" stroke="#fff" strokeWidth="1" opacity="0.4" />
            <g opacity="0.5">
              <path d="M 60 180 Q 65 170 70 180" stroke="#fff" strokeWidth="2" fill="none" />
              <path d="M 70 180 Q 75 160 80 180" stroke="#fff" strokeWidth="2" fill="none" />
              <path d="M 80 180 Q 85 175 90 180" stroke="#fff" strokeWidth="2" fill="none" />
            </g>
            <defs>
              <linearGradient id="headGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style={{ stopColor: "#5b9ce1", stopOpacity: 1 }} />
                <stop offset="100%" style={{ stopColor: "#3b6ba3", stopOpacity: 1 }} />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </section>

      <section className="features">
        <h2>Our Features</h2>
        <div className="features-grid">
          {FEATURE_ITEMS.map((feature, index) => (
            <div
              key={feature.title}
              className="feature-card"
              style={{ "--delay": `${0.08 * index}s` } as CSSProperties}
            >
              <div className={`feature-icon ${feature.iconClass}`}>
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d={feature.iconPath} />
                </svg>
              </div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="how-it-works">
        <h2>How It Works</h2>
        <div className="steps-container">
          {STEP_ITEMS.map((step, index) => (
            <div className="step-block" key={step.title}>
              <div className="step" style={{ "--delay": `${0.1 * index}s` } as CSSProperties}>
                <div className="step-number">{step.number}</div>
                <div className={`step-icon ${step.iconClass}`}>
                  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d={step.iconPath} />
                  </svg>
                </div>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </div>
              {index < STEP_ITEMS.length - 1 && <div className="step-divider" />}
            </div>
          ))}
        </div>
      </section>

      <footer className="footer">
        <div className="footer-links">
          <a href="#privacy">Privacy Policy</a>
          <a href="#about">About Us</a>
          <a href="#contact">Contact</a>
        </div>
        <p className="footer-text">© 2024 SpeechWell. For clinical support only. Not a diagnostic tool.</p>
      </footer>
    </div>
  );
}
