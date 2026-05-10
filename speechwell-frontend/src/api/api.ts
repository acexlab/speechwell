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

export interface UserProfile {
  id: number;
  email: string;
  full_name?: string | null;
  age?: number | null;
  gender?: string | null;
  location?: string | null;
  occupation?: string | null;
  primary_goal?: string | null;
  bio?: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserProfileUpdatePayload {
  full_name?: string | null;
  age?: number | null;
  gender?: string | null;
  location?: string | null;
  occupation?: string | null;
  primary_goal?: string | null;
  bio?: string | null;
}

export interface AnalysisResult {
  id: number;
  audio_id: string;
  filename: string;
  overall_score: number;
  dysarthria_probability: number;
  dysarthria_label: string;
  stuttering_probability: number;
  stuttering_repetitions: number;
  stuttering_prolongations: number;
  stuttering_blocks: number;
  grammar_score: number;
  grammar_error_probability?: number;
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
  report_filename?: string;
  status: string;
  created_at: string;
}

export interface HistoryItem {
  id: number;
  audio_id: string;
  filename: string;
  report_filename?: string;
  dysarthria_probability: number;
  stuttering_probability: number;
  grammar_score: number;
  created_at: string;
}

export interface ChatMessagePayload {
  role: "user" | "assistant";
  text: string;
}

export interface TrainingExercise {
  key: string;
  title: string;
  description: string;
  input_mode: "mic" | "text" | "click";
  prompt_text?: string;
  expected_text?: string;
  difficulty?: string;
}

export interface TrainingModule {
  key: string;
  title: string;
  description: string;
  focus_area: string;
  exercise_count: number;
  exercises: TrainingExercise[];
}

export interface TrainingSessionStartResponse {
  session_id: number;
  module_key: string;
  exercise_key: string;
  prompt_text?: string;
  expected_text?: string;
  input_mode: "mic" | "text" | "click";
  status: string;
}

export interface TrainingSession {
  id: number;
  user_id: number;
  module_key: string;
  exercise_key: string;
  prompt_text?: string;
  expected_text?: string;
  transcript?: string;
  input_mode: "mic" | "text" | "click";
  accuracy_score: number;
  fluency_score: number;
  confidence_score: number;
  long_pause_count: number;
  repeated_word_count: number;
  duration_sec: number;
  feedback_summary?: string;
  corrected_text?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TrainingEvaluationResult {
  session_id: number;
  transcript: string;
  accuracy_score: number;
  fluency_score: number;
  confidence_score: number;
  long_pause_count: number;
  repeated_word_count: number;
  duration_sec: number;
  corrected_text?: string;
  feedback: string[];
}

export interface TrainingProgress {
  module_key: string;
  sessions_completed: number;
  avg_accuracy: number;
  avg_fluency: number;
  best_score: number;
  last_practiced_at?: string | null;
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

function hasAuthToken(): boolean {
  return Boolean(localStorage.getItem("accessToken"));
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

export async function getUserProfile(): Promise<UserProfile> {
  const response = await fetch(`${API_BASE_URL}/api/profile`, {
    method: "GET",
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch profile");
  }

  return response.json();
}

export async function updateUserProfile(
  payload: UserProfileUpdatePayload
): Promise<UserProfile> {
  const response = await fetch(`${API_BASE_URL}/api/profile`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update profile");
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

export async function downloadReport(audioId: string): Promise<{ blob: Blob; filename?: string }> {
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

  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const filenameMatch =
    disposition.match(/filename\*=UTF-8''([^;]+)/i) ||
    disposition.match(/filename="?([^";]+)"?/i);
  const filename = filenameMatch?.[1] ? decodeURIComponent(filenameMatch[1]) : undefined;
  return { blob, filename };
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

// ============ CHAT ENDPOINTS ============

export async function sendChatMessage(
  message: string,
  history: ChatMessagePayload[],
  audioId?: string
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify({ message, history, audio_id: audioId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to get AI response");
  }

  const data = await response.json();
  return data.reply as string;
}

// ============ TRAINING ENDPOINTS ============

export async function getTrainingModules(): Promise<TrainingModule[]> {
  const response = await fetch(`${API_BASE_URL}/api/training/modules`, {
    method: "GET",
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch training modules");
  }

  return response.json();
}

export async function startTrainingSession(
  moduleKey: string,
  exerciseKey: string
): Promise<TrainingSessionStartResponse> {
  const response = await fetch(`${API_BASE_URL}/api/training/session/start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify({
      module_key: moduleKey,
      exercise_key: exerciseKey,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to start training session");
  }

  return response.json();
}

export async function evaluateTrainingSession(input: {
  sessionId: number;
  textAnswer?: string;
  audioFile?: File | null;
}): Promise<TrainingEvaluationResult> {
  const formData = new FormData();
  formData.append("session_id", String(input.sessionId));
  if (input.textAnswer) {
    formData.append("transcript_text", input.textAnswer);
  }
  if (input.audioFile) {
    formData.append("file", input.audioFile);
  }

  const response = await fetch(`${API_BASE_URL}/api/training/session/evaluate`, {
    method: "POST",
    headers: {
      ...getAuthHeader(),
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to evaluate training session");
  }

  return response.json();
}

export async function getTrainingSession(sessionId: number): Promise<TrainingSession> {
  const response = await fetch(`${API_BASE_URL}/api/training/session/${sessionId}`, {
    method: "GET",
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch training session");
  }

  return response.json();
}

export async function getTrainingSessions(): Promise<TrainingSession[]> {
  const response = await fetch(`${API_BASE_URL}/api/training/sessions`, {
    method: "GET",
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch training sessions");
  }

  return response.json();
}

export async function getTrainingProgress(): Promise<TrainingProgress[]> {
  if (!hasAuthToken()) {
    return [];
  }

  const response = await fetch(`${API_BASE_URL}/api/training/progress`, {
    method: "GET",
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch training progress");
  }

  return response.json();
}

