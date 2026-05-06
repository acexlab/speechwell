/*
File Logic Summary: Shared theme definitions and helpers used by Navbar,
Profile, and app bootstrapping so theme behavior stays consistent.
*/

export const DEFAULT_THEME = "lavender";

export const THEME_OPTIONS = [
  { value: "lavender", label: "Lavender", colors: ["#2d0c7a", "#f4c7b5", "#ece9f8"] },
  { value: "ocean", label: "Ocean", colors: ["#0e4f90", "#138d9f", "#d9e9fb"] },
  { value: "forest", label: "Forest", colors: ["#1e6a45", "#2a9d66", "#d7ebe0"] },
  { value: "dark", label: "Dark", colors: ["#7c5cff", "#1a2440", "#0d1321"] },
] as const;

export type ThemeValue = (typeof THEME_OPTIONS)[number]["value"];

export function applyTheme(theme: string) {
  const nextTheme = theme || DEFAULT_THEME;
  document.documentElement.setAttribute("data-theme", nextTheme);
  localStorage.setItem("speechwell-theme", nextTheme);
  window.dispatchEvent(new CustomEvent("speechwell-theme-change", { detail: nextTheme }));
}

export function getStoredTheme() {
  return localStorage.getItem("speechwell-theme") || DEFAULT_THEME;
}
