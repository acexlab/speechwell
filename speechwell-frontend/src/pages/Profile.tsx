/*
File Logic Summary: Profile settings page. It lets users manage personal details and theme preferences, then persists profile fields to backend DB.
*/

import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import InteractiveButton from "../components/InteractiveButton";
import { getUserProfile, updateUserProfile, type UserProfile } from "../api/api";
import "../styles/profile.css";

interface ProfileForm {
  full_name: string;
  age: string;
  gender: string;
  location: string;
  occupation: string;
  primary_goal: string;
  bio: string;
}

const THEME_OPTIONS = [
  { value: "lavender", label: "Lavender (Default)", colors: ["#2d0c7a", "#f4c7b5", "#ece9f8"] },
  { value: "ocean", label: "Ocean Blue", colors: ["#0e4f90", "#138d9f", "#d9e9fb"] },
  { value: "sunset", label: "Sunset Warm", colors: ["#b4451d", "#8a2be2", "#fde6dc"] },
  { value: "forest", label: "Forest Calm", colors: ["#1e6a45", "#2a9d66", "#d7ebe0"] },
];

function sanitizeNullable(value: string): string | null {
  return value.trim() ? value.trim() : null;
}

export default function Profile() {
  const [form, setForm] = useState<ProfileForm>({
    full_name: "",
    age: "",
    gender: "",
    location: "",
    occupation: "",
    primary_goal: "",
    bio: "",
  });
  const [theme, setTheme] = useState(localStorage.getItem("speechwell-theme") || "lavender");
  const [previewTheme, setPreviewTheme] = useState(localStorage.getItem("speechwell-theme") || "lavender");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const profile: UserProfile = await getUserProfile();
        setForm({
          full_name: profile.full_name || "",
          age: profile.age != null ? String(profile.age) : "",
          gender: profile.gender || "",
          location: profile.location || "",
          occupation: profile.occupation || "",
          primary_goal: profile.primary_goal || "",
          bio: profile.bio || "",
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load profile");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", previewTheme);
  }, [previewTheme]);

  const updateField = (key: keyof ProfileForm, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");

    try {
      const ageNumber = form.age.trim() ? Number(form.age) : null;
      if (ageNumber !== null && (Number.isNaN(ageNumber) || ageNumber < 1 || ageNumber > 120)) {
        throw new Error("Age must be a valid number between 1 and 120");
      }

      const updated = await updateUserProfile({
        full_name: sanitizeNullable(form.full_name),
        age: ageNumber,
        gender: sanitizeNullable(form.gender),
        location: sanitizeNullable(form.location),
        occupation: sanitizeNullable(form.occupation),
        primary_goal: sanitizeNullable(form.primary_goal),
        bio: sanitizeNullable(form.bio),
      });

      const existingUser = localStorage.getItem("user");
      if (existingUser) {
        try {
          const parsed = JSON.parse(existingUser);
          parsed.full_name = updated.full_name;
          localStorage.setItem("user", JSON.stringify(parsed));
        } catch {
          // Ignore localStorage parse errors.
        }
      }

      setMessage("Settings saved successfully.");
      localStorage.setItem("speechwell-theme", previewTheme);
      setTheme(previewTheme);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="profile-layout">
      <Sidebar />
      <main className="profile-content page-enter">
        <div className="profile-header">
          <h1>Settings</h1>
          <p>Update your personal details and choose your preferred app theme.</p>
        </div>

        <form className="profile-form" onSubmit={handleSave}>
          <section className="profile-card">
            <h2>Theme</h2>
            <div className="theme-grid">
              {THEME_OPTIONS.map((option, index) => (
                <button
                  type="button"
                  key={option.value}
                  className={`theme-card ${previewTheme === option.value ? "active" : ""}`}
                  style={{ animationDelay: `${index * 0.1}s` }}
                  onClick={() => setPreviewTheme(option.value)}
                >
                  <div className="theme-card-head">
                    <strong>{option.label}</strong>
                    {previewTheme === option.value && <span className="theme-check">✓</span>}
                  </div>
                  <div className="theme-palette">
                    {option.colors.map((color) => (
                      <i key={color} style={{ background: color }} />
                    ))}
                  </div>
                </button>
              ))}
            </div>
            {previewTheme !== theme && (
              <div className="theme-preview-banner">
                <p>Theme preview active. Apply to keep this style.</p>
                <div>
                  <InteractiveButton type="button" variant="ghost" onClick={() => setPreviewTheme(theme)}>
                    Cancel
                  </InteractiveButton>
                  <InteractiveButton type="button" onClick={() => { localStorage.setItem("speechwell-theme", previewTheme); setTheme(previewTheme); setMessage("Theme applied."); }}>
                    Apply Theme
                  </InteractiveButton>
                </div>
              </div>
            )}
          </section>

          <section className="profile-card profile-grid">
            <h2>Personal Details</h2>

            <label>
              Full name
              <input
                type="text"
                value={form.full_name}
                onChange={(e) => updateField("full_name", e.target.value)}
                placeholder="Your full name"
                disabled={saving || loading}
              />
            </label>

            <label>
              Age
              <input
                type="number"
                min="1"
                max="120"
                value={form.age}
                onChange={(e) => updateField("age", e.target.value)}
                placeholder="Your age"
                disabled={saving || loading}
              />
            </label>

            <label>
              Gender
              <input
                type="text"
                value={form.gender}
                onChange={(e) => updateField("gender", e.target.value)}
                placeholder="Gender"
                disabled={saving || loading}
              />
            </label>

            <label>
              Location
              <input
                type="text"
                value={form.location}
                onChange={(e) => updateField("location", e.target.value)}
                placeholder="City, Country"
                disabled={saving || loading}
              />
            </label>

            <label>
              Occupation
              <input
                type="text"
                value={form.occupation}
                onChange={(e) => updateField("occupation", e.target.value)}
                placeholder="Occupation"
                disabled={saving || loading}
              />
            </label>

            <label>
              Primary speech goal
              <input
                type="text"
                value={form.primary_goal}
                onChange={(e) => updateField("primary_goal", e.target.value)}
                placeholder="Example: Improve fluency"
                disabled={saving || loading}
              />
            </label>

            <label className="full-width">
              Bio / notes
              <textarea
                rows={4}
                value={form.bio}
                onChange={(e) => updateField("bio", e.target.value)}
                placeholder="Add any background details helpful for your sessions"
                disabled={saving || loading}
              />
            </label>
          </section>

          {error && <p className="profile-error">{error}</p>}
          {message && <p className="profile-success">{message}</p>}

          <InteractiveButton type="submit" className="profile-save" disabled={saving || loading}>
            {saving ? "Saving..." : "Save Settings"}
          </InteractiveButton>
        </form>
      </main>
    </div>
  );
}
