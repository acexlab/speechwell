/*
File Logic Summary: Premium route/loading overlay with staged animation (intro pulse, logo reveal, progress) and auto completion callback.
*/

import { useEffect, useMemo, useState } from "react";
import "../styles/loading-animation-premium.css";

type LoadingAnimationProps = {
  duration?: number;
  onComplete?: () => void;
};

type LoadingStage = "pulse" | "logo" | "progress";

function getThemeName() {
  return document.documentElement.getAttribute("data-theme") || "lavender";
}

export default function LoadingAnimation({
  duration = 2500,
  onComplete,
}: LoadingAnimationProps) {
  const [stage, setStage] = useState<LoadingStage>("pulse");
  const [closing, setClosing] = useState(false);
  const [theme, setTheme] = useState(getThemeName());

  useEffect(() => {
    const observer = new MutationObserver(() => setTheme(getThemeName()));
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const t1 = window.setTimeout(() => setStage("logo"), Math.round(duration * 0.32));
    const t2 = window.setTimeout(() => setStage("progress"), Math.round(duration * 0.64));
    const t3 = window.setTimeout(() => setClosing(true), Math.round(duration * 0.82));
    const t4 = window.setTimeout(() => onComplete?.(), duration);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  }, [duration, onComplete]);

  const letters = useMemo(() => "SpeechWell".split(""), []);

  return (
    <div
      className={`premium-loader theme-${theme} stage-${stage} ${closing ? "closing" : ""}`}
      aria-live="polite"
      role="status"
    >
      <div className="premium-loader-bg" />
      <div className="premium-loader-particles" aria-hidden="true">
        {Array.from({ length: 20 }, (_, i) => (
          <i key={`loader-p-${i}`} style={{ animationDelay: `${(i % 9) * 0.16}s` }} />
        ))}
      </div>

      <div className="pulse-layer">
        <span className="pulse-ring one" />
        <span className="pulse-ring two" />
        <span className="pulse-core" />
      </div>

      <div className="brand-layer">
        <div className="brand-logo">
          <span className="brand-pattern" />
          <div className="brand-center">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z" />
            </svg>
          </div>
          {Array.from({ length: 6 }, (_, i) => (
            <i className={`orbit-dot o-${i + 1}`} key={`orbit-${i}`} />
          ))}
        </div>

        <h2 className="brand-title">
          {letters.map((ch, idx) => (
            <span key={`${ch}-${idx}`} style={{ animationDelay: `${0.8 + idx * 0.05}s` }}>
              {ch}
            </span>
          ))}
        </h2>
        <p className="brand-subtitle">Initializing your experience...</p>
      </div>

      <div className="progress-layer">
        <div className="mini-spinner" />
        <div className="loader-progress">
          <span />
          <i />
        </div>
      </div>
    </div>
  );
}

