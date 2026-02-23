/*
File Logic Summary: Shared UI component used across pages to provide consistent navigation and layout behavior.
*/

import { Link, useLocation } from "react-router-dom";
import "../styles/navbar.css";

export default function Navbar() {
  const location = useLocation();
  const isLandingPage = location.pathname === "/";
  const isAuthPage = location.pathname === "/login" || location.pathname === "/register";
  const isAuthenticated = !!localStorage.getItem("accessToken");

  return (
    <nav className={`navbar ${isLandingPage ? "landing" : "default"}`}>
      <div className="navbar-brand">
        <Link to="/" className="logo">
          SpeechWell
        </Link>
      </div>

      <div className="navbar-links" />

      <div className="navbar-auth">
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

