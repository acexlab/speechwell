/*
File Logic Summary: Shared UI component used across pages to provide consistent navigation and layout behavior.
*/

import { Link, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { checkHealth } from "../api/api";
import { THEME_OPTIONS, applyTheme, getStoredTheme } from "../utils/theme";
import "../styles/navbar.css";

export default function Navbar() {
  const location = useLocation();
  const isLandingPage = location.pathname === "/";
  const isAuthPage = location.pathname === "/login" || location.pathname === "/register";
  const isAuthenticated = !!localStorage.getItem("accessToken");
  const [theme, setTheme] = useState(getStoredTheme());
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    let active = true;

    const updateStatus = async () => {
      try {
        const ok = await checkHealth();
        if (active) {
          setApiStatus(ok ? "online" : "offline");
        }
      } catch {
        if (active) {
          setApiStatus("offline");
        }
      }
    };

    updateStatus();
    const intervalId = window.setInterval(updateStatus, 30000);
    return () => {
      active = false;
      clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    const syncTheme = () => setTheme(getStoredTheme());
    window.addEventListener("speechwell-theme-change", syncTheme);
    window.addEventListener("storage", syncTheme);
    return () => {
      window.removeEventListener("speechwell-theme-change", syncTheme);
      window.removeEventListener("storage", syncTheme);
    };
  }, []);

  const handleThemeChange = (value: string) => {
    setTheme(value);
    applyTheme(value);
  };

  return (
    <nav className={`navbar ${isLandingPage ? "landing" : "default"}`}>
      <div className="navbar-brand">
        <Link to="/" className="logo">
          SpeechWell
        </Link>
      </div>

      <div className="navbar-links" />

      <div className="navbar-auth">
        <div className={`connection-pill ${apiStatus}`}>
          <span className="connection-dot" />
          <span>
            {apiStatus === "online"
              ? "Backend online"
              : apiStatus === "offline"
              ? "Backend offline"
              : "Checking API"}
          </span>
        </div>
        <label className="theme-switch" aria-label="Theme switcher">
          <span>Theme</span>
          <select value={theme} onChange={(e) => handleThemeChange(e.target.value)}>
            {THEME_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        {!isAuthPage && !isAuthenticated ? (
          <>
            <Link to="/login" className="btn-login">
              Login
            </Link>
            <Link to="/register" className="btn-register">
              Register
            </Link>
          </>
        ) : null}
      </div>
    </nav>
  );
}

