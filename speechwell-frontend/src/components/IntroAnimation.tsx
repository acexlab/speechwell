/*
File Logic Summary: First-launch cinematic intro overlay with staged brand reveal and theme-adaptive particle/ring animation.
*/

import { useEffect, useMemo, useState } from "react";
import "../styles/intro-animation.css";

type IntroAnimationProps = {
  duration?: number;
  onComplete?: () => void;
};

type IntroStage = "logo" | "title" | "tagline";

const BRAND = "SpeechWell";

function getThemeName() {
  return document.documentElement.getAttribute("data-theme") || "lavender";
}

export default function IntroAnimation({
  duration = 4000,
  onComplete,
}: IntroAnimationProps) {
  const [stage, setStage] = useState<IntroStage>("logo");
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
    const t1 = window.setTimeout(() => setStage("title"), Math.round(duration * 0.25));
    const t2 = window.setTimeout(() => setStage("tagline"), Math.round(duration * 0.55));
    const t3 = window.setTimeout(() => setClosing(true), Math.round(duration * 0.86));
    const t4 = window.setTimeout(() => onComplete?.(), duration);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  }, [duration, onComplete]);

  const letters = useMemo(() => BRAND.split(""), []);

  return (
    <div
      className={`intro-overlay theme-${theme} ${closing ? "closing" : ""}`}
      aria-live="polite"
      role="status"
    >
      <div className={`intro-logo-wrap stage-${stage}`}>
        <div className="intro-ring outer" />
        <div className="intro-ring inner" />
        <div className="intro-mic">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z" />
          </svg>
        </div>
        {Array.from({ length: 8 }, (_, i) => (
          <span key={`particle-${i}`} className={`intro-orbit p-${i + 1}`} />
        ))}
      </div>

      <h1 className={`intro-title ${stage !== "logo" ? "visible" : ""}`}>
        {letters.map((ch, idx) => (
          <span key={`${ch}-${idx}`} style={{ animationDelay: `${idx * 0.1}s` }}>
            {ch}
          </span>
        ))}
      </h1>

      <div className={`intro-tagline ${stage === "tagline" ? "visible" : ""}`}>
        <div className="intro-tagline-icons">
          <span aria-hidden="true">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M9.5 2a4 4 0 0 0-4 4v1.4A4.5 4.5 0 0 0 2 11.8c0 2 1.3 3.8 3.2 4.4V18a4 4 0 0 0 4 4h5.3a4 4 0 0 0 4-4v-1.2a4.4 4.4 0 0 0 3.5-4.3c0-1.8-1.1-3.4-2.8-4.1V7a4 4 0 0 0-4-4H9.5zm.2 2h5.1a2 2 0 0 1 2 2v1.1c0 .9.6 1.7 1.5 1.9 1 .2 1.7 1 1.7 2 0 1.1-.8 2-1.9 2-.9 0-1.6.7-1.6 1.6V18a2 2 0 0 1-2 2H9.2a2 2 0 0 1-2-2v-2.3c0-.8-.5-1.5-1.3-1.8A2.6 2.6 0 0 1 4 11.8c0-1.2.9-2.2 2.1-2.4.8-.1 1.4-.8 1.4-1.6V6a2 2 0 0 1 2.2-2z" />
            </svg>
          </span>
          <span aria-hidden="true">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="m12 2 1.8 4.7L18.5 8l-4.7 1.3L12 14l-1.8-4.7L5.5 8l4.7-1.3L12 2zm6 10 1 2.5 2.5 1-2.5 1-1 2.5-1-2.5-2.5-1 2.5-1 1-2.5zm-12 1 1.2 3 3 1.2-3 1.2L6 21l-1.2-3L2 16.8l2.8-1.2L6 13z" />
            </svg>
          </span>
        </div>
        <p>Enhancing communication through AI</p>
        <div className="intro-progress">
          <span />
        </div>
      </div>

      <div className="intro-bg-particles" aria-hidden="true">
        {Array.from({ length: 15 }, (_, i) => (
          <i key={`bg-${i}`} style={{ animationDelay: `${(i % 7) * 0.2}s` }} />
        ))}
      </div>
    </div>
  );
}