/*
File Logic Summary: Frontend API client layer. All auth, upload, history, results, and report requests go through this file.
*/

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Types
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    email: string;
    full_name?: string;
  };
}

export interface AnalysisResult {
  id: number;
  audio_id: string;
  filename: string;
  dysarthria_probability: number;
  dysarthria_label: string;
  stuttering_probability: number;
  stuttering_repetitions: number;
  stuttering_prolongations: number;
  stuttering_blocks: number;
  grammar_score: number;
  grammar_error_count: number;
  phonological_score: number;
  phonological_error_count: number;
  transcript?: string;
  corrected_text?: string;
  speaking_rate_wps: number;
  average_pause_sec: number;
  max_pause_sec: number;
  total_duration_sec: number;
  pdf_path?: string;
  status: string;
  created_at: string;
}

export interface HistoryItem {
  id: number;
  audio_id: string;
  filename: string;
  dysarthria_probability: number;
  stuttering_probability: number;
  grammar_score: number;
  created_at: string;
}

// Helper function to get authorization header
function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem("accessToken");
  if (token) {
    return {
      Authorization: `Bearer ${token}`,
    };
  }
  return {};
}

// ============ AUTHENTICATION ENDPOINTS ============

export async function registerUser(
  email: string,
  password: string,
  passwordConfirm: string,
  fullName?: string
): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email,
      password,
      password_confirm: passwordConfirm,
      full_name: fullName,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Registration failed");
  }

  return response.json();
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email,
      password,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Login failed");
  }

  return response.json();
}

// ============ ANALYSIS ENDPOINTS ============

export async function uploadAndAnalyzeAudio(
  file: File,
  onProgress?: (progress: number) => void
): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);

  const xhr = new XMLHttpRequest();

  return new Promise((resolve, reject) => {
    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener("progress", (event) => {
        if (event.lengthComputable) {
          const progress = (event.loaded / event.total) * 100;
          onProgress(progress);
        }
      });
    }

    xhr.addEventListener("load", () => {
      try {
        if (xhr.status === 200 || xhr.status === 201) {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } else {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || "Upload failed"));
        }
      } catch {
        reject(new Error("Failed to parse response"));
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Upload failed"));
    });

    xhr.open("POST", `${API_BASE_URL}/api/analyze`);

    // Add authorization header if available
    const token = localStorage.getItem("accessToken");
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    xhr.send(formData);
  });
}

export async function getAnalysisResult(audioId: string): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/api/analyze/${audioId}`, {
    method: "GET",
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch analysis");
  }

  return response.json();
}

// ============ HISTORY ENDPOINTS ============

export async function getAnalysisHistory(): Promise<HistoryItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/analyses`, {
    method: "GET",
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch history");
  }

  return response.json();
}

// ============ REPORT ENDPOINTS ============

export async function downloadReport(audioId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/reports/${audioId}`, {
    method: "GET",
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to download report");
  }

  return response.blob();
}

// ============ UTILITY ENDPOINTS ============

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}

