/*
File Logic Summary: Frontend route registry. It maps URLs to page components and wraps the app with shared navigation.
*/

import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect, useState } from "react";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import History from "./pages/History";
import TherapyHub from "./pages/TherapyHub";
import Results from "./pages/Results";
import Profile from "./pages/Profile";
import AIChat from "./pages/AIChat";
import Navbar from "./components/Navbar";
import IntroAnimation from "./components/IntroAnimation";
import { applyTheme, getStoredTheme } from "./utils/theme";
import "./App.css";

function AppShell() {
  const [showIntro, setShowIntro] = useState(() => !sessionStorage.getItem("speechwell_intro_seen"));

  const handleIntroDone = () => {
    sessionStorage.setItem("speechwell_intro_seen", "1");
    setShowIntro(false);
  };

  return (
    <>
      <Navbar />
      {showIntro && <IntroAnimation duration={4000} onComplete={handleIntroDone} />}
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/history" element={<History />} />
        <Route path="/therapy-hub" element={<TherapyHub />} />
        <Route path="/analytics" element={<Dashboard />} />
        <Route path="/ai-chat" element={<AIChat />} />
        <Route path="/results" element={<Results />} />
        <Route path="/reports" element={<History />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </>
  );
}

function App() {
  useEffect(() => {
    applyTheme(getStoredTheme());
  }, []);

  return (
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <AppShell />
    </BrowserRouter>
  );
}

export default App;

