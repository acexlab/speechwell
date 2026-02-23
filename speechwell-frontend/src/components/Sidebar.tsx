/*
File Logic Summary: Shared UI component used across pages to provide consistent navigation and layout behavior.
*/

import { Link, useLocation, useNavigate } from "react-router-dom";
import "../styles/sidebar.css";

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const isActive = (path: string) => location.pathname === path;

  const userRaw = localStorage.getItem("user");
  let userName = "Guest User";

  if (userRaw) {
    try {
      const parsed = JSON.parse(userRaw);
      const emailName = parsed?.email?.split("@")[0];
      if (emailName) {
        userName = emailName;
      }
    } catch {
      userName = "Guest User";
    }
  }

  const userInitial = userName.slice(0, 1).toUpperCase();

  const handleLogout = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <div className="sidebar-brand">
          <div className="brand-icon">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z" />
            </svg>
          </div>
          <span>SpeechWell</span>
        </div>

        <div className="sidebar-search">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M15.5 14h-.79l-.28-.27a6.5 6.5 0 10-.71.71l.27.28v.79L20 21.49 21.49 20 15.5 14zM10 15a5 5 0 110-10 5 5 0 010 10z" />
          </svg>
          <input type="text" placeholder="Search..." aria-label="Search navigation" />
        </div>
      </div>

      <nav className="sidebar-nav">
        <Link to="/dashboard" className={`nav-item ${isActive("/dashboard") ? "active" : ""}`}>
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 13h2v8H3zm4-8h2v16H7zm4-2h2v18h-2zm4-2h2v20h-2zm4-2h2v22h-2z" />
          </svg>
          <span>Dashboard</span>
        </Link>

        <Link to="/upload" className={`nav-item ${isActive("/upload") ? "active" : ""}`}>
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2a3 3 0 00-3 3v6a3 3 0 006 0V5a3 3 0 00-3-3zm-7 9v1a7 7 0 006 6.93V21h2v-2.07A7 7 0 0019 12v-1h-2v1a5 5 0 01-10 0v-1H5z" />
          </svg>
          <span>Speech Analysis</span>
        </Link>

        <Link to="/therapy-hub" className={`nav-item ${isActive("/therapy-hub") ? "active" : ""}`}>
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zm-1 14H6v-2h12zm0-4H6V7h12z" />
          </svg>
          <span>Train Your Speech</span>
        </Link>

        <Link to="/analytics" className={`nav-item ${isActive("/analytics") ? "active" : ""}`}>
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 19h16v2H2V3h2v16zm3-3h2V9H7v7zm4 0h2V5h-2v11zm4 0h2v-4h-2v4z" />
          </svg>
          <span>Analytics</span>
        </Link>

        <Link to="/history" className={`nav-item ${isActive("/history") ? "active" : ""}`}>
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M13 3a9 9 0 100 18 9 9 0 000-18zm1 10h-4V7h2v4h2v2z" />
          </svg>
          <span>History</span>
        </Link>

        <Link to="/reports" className={`nav-item ${isActive("/reports") ? "active" : ""}`}>
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M7 3h10l4 4v14H3V3h4zm7 1.5V8h3.5L14 4.5zM6 12h12v2H6zm0 4h12v2H6z" />
          </svg>
          <span>Reports</span>
        </Link>

        <Link to="/profile" className={`nav-item ${isActive("/profile") ? "active" : ""}`}>
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 12c2.76 0 5-2.24 5-5S14.76 2 12 2 7 4.24 7 7s2.24 5 5 5zm0 2c-3.33 0-10 1.67-10 5v3h20v-3c0-3.33-6.67-5-10-5z" />
          </svg>
          <span>Settings</span>
        </Link>
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="user-initial">{userInitial}</div>
          <div>
            <p>{userName}</p>
            <small>SpeechWell User</small>
          </div>
        </div>
        <button type="button" className="sidebar-logout" onClick={handleLogout}>
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M10 17l1.41-1.41L8.83 13H21v-2H8.83l2.58-2.59L10 7l-5 5 5 5zM3 3h8v2H5v14h6v2H3z" />
          </svg>
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
