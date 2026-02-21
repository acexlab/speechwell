/*
File Logic Summary: Upload/record page. It handles drag-drop, live recording, validation, and submission to backend analysis.
*/

import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { uploadAndAnalyzeAudio } from "../api/api";
import "../styles/upload.css";

export default function Upload() {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedSkill, setSelectedSkill] = useState("All Skills");
  const [selectedCondition, setSelectedCondition] = useState("Dysarthria");
  const [isRecording, setIsRecording] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<BlobPart[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      validateAndSetFile(files[0]);
    }
  };

  const validateAndSetFile = (file: File) => {
    const validTypes = [
      "audio/wav",
      "audio/x-wav",
      "audio/mp3",
      "audio/mpeg",
      "audio/webm",
      "audio/ogg",
      "audio/mp4",
      "application/octet-stream",
    ];
    const validExtensions = [".wav", ".mp3", ".webm", ".ogg", ".m4a"];
    const nameLower = file.name.toLowerCase();
    const hasValidExtension = validExtensions.some((ext) => nameLower.endsWith(ext));

    if ((validTypes.includes(file.type) || hasValidExtension) && file.size <= 50 * 1024 * 1024) {
      setSelectedFile(file);
      setError("");
      setUploadProgress(0);
    } else {
      setError("Invalid file. Please upload WAV, MP3, WEBM, OGG, or M4A up to 50MB.");
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files[0]) {
      validateAndSetFile(files[0]);
    }
  };

  const analyzeFile = async (file: File) => {
    setIsUploading(true);
    setError("");

    try {
      const result = await uploadAndAnalyzeAudio(file, (progress) => {
        setUploadProgress(progress);
      });

      navigate(`/results`, { state: { audioId: result.audio_id } });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
      setUploadProgress(0);
    } finally {
      setIsUploading(false);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    await analyzeFile(selectedFile);
  };

  const handleStartRecording = async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setError("This browser does not support live recording.");
      return;
    }

    try {
      setError("");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const preferredMimeTypes = ["audio/webm", "audio/ogg", "audio/mp4"];
      const mimeType = preferredMimeTypes.find((type) => MediaRecorder.isTypeSupported(type));

      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      recordedChunksRef.current = [];
      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const chunks = recordedChunksRef.current;
        if (!chunks.length) {
          setError("No audio was captured. Please try again.");
          return;
        }

        const recordedType = recorder.mimeType || "audio/webm";
        const extensionMap: Record<string, string> = {
          "audio/webm": "webm",
          "audio/ogg": "ogg",
          "audio/mp4": "m4a",
        };
        const extension = extensionMap[recordedType] || "webm";
        const recordedFile = new File(
          [new Blob(chunks, { type: recordedType })],
          `recording-${Date.now()}.${extension}`,
          { type: recordedType }
        );

        validateAndSetFile(recordedFile);
        await analyzeFile(recordedFile);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch {
      setError("Microphone access was denied or unavailable.");
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
        mediaStreamRef.current = null;
      }
      setIsRecording(false);
    }
  };

  const handleStopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    setIsRecording(false);
  };

  return (
    <div className="upload-layout">
      <Sidebar />
      <main className="upload-content">
        <div className="upload-header">
          <h1>Upload Speech Audio</h1>
          <p>
            Upload your speech audio for analysis. Our AI models will detect
            dysarthria, stuttering, grammar errors, and other speech patterns.
          </p>
        </div>

        <div className="upload-filters">
          <div className="filter-group">
            <label htmlFor="skill-select">Analysis Type</label>
            <select
              id="skill-select"
              value={selectedSkill}
              onChange={(e) => setSelectedSkill(e.target.value)}
              className="filter-select"
            >
              <option>All Skills</option>
              <option>Dysarthria</option>
              <option>Stuttering</option>
              <option>Fluency</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="condition-select">Primary Concern</label>
            <select
              id="condition-select"
              value={selectedCondition}
              onChange={(e) => setSelectedCondition(e.target.value)}
              className="filter-select"
            >
              <option>Dysarthria</option>
              <option>Stuttering</option>
              <option>Fluency</option>
            </select>
          </div>
        </div>

        <div className="upload-container">
          <div className="upload-box">
            <div
              className={`drag-drop ${dragActive ? "active" : ""}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <svg
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
                className="upload-icon"
              >
                <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4c-1.48 0-2.85.43-4.01 1.17l1.46 1.46C10.21 5.23 11.08 5 12 5c3.04 0 5.5 2.46 5.5 5.5v.5H19c1.66 0 3 1.34 3 3 0 1.13-.64 2.11-1.56 2.62l1.45 1.45C23.16 15.5 24 14.08 24 12.5c0-2.64-2.05-4.78-4.65-4.96zM16.5 16.5H13v3h-2v-3H8.5l4-4 4 4z" />
              </svg>
              <h2>Drag & Drop</h2>
              <p>an audio file here</p>

              <div className="file-input-wrapper">
                <input
                  type="file"
                  id="file-input"
                  accept=".wav,.mp3,.webm,.ogg,.m4a"
                  onChange={handleFileInput}
                  className="file-input"
                  disabled={isUploading}
                />
                <label htmlFor="file-input" className="browse-text">
                  or click to browse (.wav, .mp3, .webm, .ogg, .m4a)
                </label>
              </div>

              {selectedFile && (
                <div className="selected-file">
                  <p>&#10003; {selectedFile.name}</p>
                </div>
              )}

              <p className="file-size-info">Max file size: 50MB</p>
            </div>
          </div>

          <div className="recording-box">
            <h3>Or, Record Live Audio</h3>

            <div className="recording-area">
              <svg
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
                className="microphone-icon"
              >
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z" />
              </svg>

              {isRecording && <div className="recording-indicator"></div>}
            </div>

            {isRecording ? (
              <button
                className="btn-recording active"
                onClick={handleStopRecording}
                disabled={isUploading}
              >
                Stop Recording
              </button>
            ) : (
              <button
                className="btn-recording"
                onClick={handleStartRecording}
                disabled={isUploading}
              >
                Start Recording
              </button>
            )}

            <p className="recording-note">Please allow microphone access.</p>
          </div>
        </div>

        {error && (
          <div
            className="error-message"
            style={{
              margin: "20px 0",
              padding: "10px",
              borderRadius: "4px",
              backgroundColor: "#fee",
              color: "#c00",
              border: "1px solid #fcc",
            }}
          >
            {error}
          </div>
        )}

        {selectedFile && (
          <div className="upload-actions">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            {isUploading && uploadProgress > 0 && uploadProgress < 100 && (
              <p className="progress-text">Analyzing... {Math.round(uploadProgress)}%</p>
            )}
            {uploadProgress === 100 && isUploading && (
              <p className="progress-text">Processing your analysis...</p>
            )}
            {!isUploading && uploadProgress === 0 && (
              <button
                className="btn-upload"
                onClick={handleUpload}
                disabled={!selectedFile}
              >
                Analyze Audio
              </button>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

