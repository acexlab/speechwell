/*
File Logic Summary: Frontend route registry. It maps URLs to page components and wraps the app with shared navigation.
*/

import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import History from "./pages/History";
import TherapyHub from "./pages/TherapyHub";
import Results from "./pages/Results";
import Reports from "./pages/Reports";
import Profile from "./pages/Profile";
import Analytics from "./pages/Analytics";
import AIChat from "./pages/AIChat";
import Navbar from "./components/Navbar";
import IntroAnimation from "./components/IntroAnimation";
import LoadingAnimation from "./components/LoadingAnimation";
import "./App.css";

function AppShell() {
  const [showIntro, setShowIntro] = useState(() => !sessionStorage.getItem("speechwell_intro_seen"));
  const [showLoading, setShowLoading] = useState(() => !!sessionStorage.getItem("speechwell_intro_seen"));
  const timerRef = useRef<number | null>(null);

  const clearLoaderTimer = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  useEffect(() => {
    if (!showLoading) {
      return;
    }
    clearLoaderTimer();
    timerRef.current = window.setTimeout(() => {
      setShowLoading(false);
      timerRef.current = null;
    }, 1800);
  }, [showLoading]);

  useEffect(() => () => clearLoaderTimer(), []);

  const handleIntroDone = () => {
    sessionStorage.setItem("speechwell_intro_seen", "1");
    setShowIntro(false);
    setShowLoading(true);
  };

  return (
    <>
      <Navbar />
      {showIntro && <IntroAnimation duration={4000} onComplete={handleIntroDone} />}
      {!showIntro && showLoading && (
        <LoadingAnimation duration={2500} onComplete={() => setShowLoading(false)} />
      )}
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/history" element={<History />} />
        <Route path="/therapy-hub" element={<TherapyHub />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/ai-chat" element={<AIChat />} />
        <Route path="/results" element={<Results />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </>
  );
}

function App() {
  useEffect(() => {
    const theme = localStorage.getItem("speechwell-theme") || "lavender";
    document.documentElement.setAttribute("data-theme", theme);
  }, []);

  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}

export default App;

