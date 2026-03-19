"use client";

import { useState, useRef, useCallback } from "react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MAX_FILE_MB = 500;
const MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024;
const ALLOWED_TYPES = [
  "video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska",
  "video/webm", "audio/mpeg", "audio/wav", "audio/x-m4a", "audio/flac",
  "audio/ogg",
];

type AppState = "idle" | "ready" | "uploading" | "transcribing" | "done" | "error";
type Language = "hinglish" | "english";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase() || "";
  if (["mp4", "mov", "avi", "mkv", "webm"].includes(ext)) return "🎬";
  if (["mp3", "wav", "m4a", "flac", "ogg"].includes(ext)) return "🎵";
  return "📄";
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState<Language>("hinglish");
  const [state, setState] = useState<AppState>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [segmentCount, setSegmentCount] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- File validation ---
  const handleFile = useCallback((f: File | null) => {
    setErrorMsg("");
    setDownloadUrl(null);
    setSegmentCount(0);

    if (!f) { setFile(null); setState("idle"); return; }

    if (!ALLOWED_TYPES.includes(f.type) && !f.name.match(/\.(mp4|mov|avi|mkv|webm|mp3|wav|m4a|flac|ogg)$/i)) {
      setErrorMsg("Unsupported file type. Use video or audio files.");
      return;
    }
    if (f.size > MAX_FILE_BYTES) {
      setErrorMsg(`File too large (${formatBytes(f.size)}). Maximum is ${MAX_FILE_MB} MB.`);
      return;
    }

    setFile(f);
    setState("ready");
  }, []);

  // --- Drag & drop ---
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files?.[0] || null);
  }, [handleFile]);

  // --- Submit ---
  const handleSubmit = async () => {
    if (!file || state === "uploading" || state === "transcribing") return;

    setState("uploading");
    setErrorMsg("");
    setDownloadUrl(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", language);

    try {
      setState("transcribing");

      const response = await fetch(`${API_URL}/transcribe`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: "Transcription failed" }));
        throw new Error(err.detail || `Server error: ${response.status}`);
      }

      const segCount = parseInt(response.headers.get("X-Segment-Count") || "0", 10);
      setSegmentCount(segCount);

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      setDownloadUrl(url);
      setState("done");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      setErrorMsg(message);
      setState("error");
    }
  };

  const handleDownload = () => {
    if (!downloadUrl) return;
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = `${file?.name.replace(/\.[^.]+$/, "")}_subtitles.srt`;
    a.click();
  };

  const handleReset = () => {
    setFile(null);
    setState("idle");
    setErrorMsg("");
    setDownloadUrl(null);
    setSegmentCount(0);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const isProcessing = state === "uploading" || state === "transcribing";

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* ---- NAV ---- */}
      <nav style={{
        padding: "16px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "1px solid var(--border-default)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: "linear-gradient(135deg, var(--accent), #a78bfa)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 16,
          }}>
            字
          </div>
          <span style={{ fontWeight: 600, fontSize: 18, letterSpacing: "-0.02em" }}>
            Hinglish Subs
          </span>
        </div>
        <span style={{
          fontSize: 12, color: "var(--text-muted)",
          fontFamily: "var(--font-mono)", letterSpacing: "0.05em",
        }}>
          v1.1
        </span>
      </nav>

      {/* ---- MAIN ---- */}
      <main style={{
        flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
        padding: "40px 20px",
      }}>
        <div style={{ width: "100%", maxWidth: 520 }}>

          {/* Header */}
          <div style={{ textAlign: "center", marginBottom: 40 }}>
            <h1 style={{
              fontSize: 36, fontWeight: 700, letterSpacing: "-0.03em",
              lineHeight: 1.1, marginBottom: 12,
            }}>
              Video → Subtitles
              <br />
              <span style={{ color: "var(--accent-light)" }}>in seconds</span>
            </h1>
            <p style={{ color: "var(--text-secondary)", fontSize: 15, lineHeight: 1.5 }}>
              Upload a video. Get Hinglish (Roman) or English subtitles.
              <br />
              Optimized 3-word chunks for easy reading.
            </p>
          </div>

          {/* Upload zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => !isProcessing && fileInputRef.current?.click()}
            style={{
              border: `2px dashed ${dragOver ? "var(--accent)" : file ? "var(--border-hover)" : "var(--border-default)"}`,
              borderRadius: 16,
              padding: file ? "20px 24px" : "48px 24px",
              textAlign: "center",
              cursor: isProcessing ? "default" : "pointer",
              background: dragOver ? "var(--accent-glow)" : file ? "var(--bg-card)" : "transparent",
              transition: "all 0.2s ease",
              marginBottom: 20,
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*,audio/*"
              onChange={(e) => handleFile(e.target.files?.[0] || null)}
              style={{ display: "none" }}
            />

            {file ? (
              <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <span style={{ fontSize: 28 }}>{getFileIcon(file.name)}</span>
                <div style={{ flex: 1, textAlign: "left" }}>
                  <div style={{
                    fontWeight: 500, fontSize: 14,
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                  }}>
                    {file.name}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                    {formatBytes(file.size)}
                  </div>
                </div>
                {!isProcessing && (
                  <button
                    onClick={(e) => { e.stopPropagation(); handleReset(); }}
                    style={{
                      background: "var(--bg-accent)", border: "1px solid var(--border-default)",
                      color: "var(--text-secondary)", borderRadius: 8, padding: "6px 12px",
                      fontSize: 12, cursor: "pointer",
                    }}
                  >
                    Change
                  </button>
                )}
              </div>
            ) : (
              <>
                <div style={{ fontSize: 40, marginBottom: 12, opacity: 0.6 }}>↑</div>
                <div style={{ fontWeight: 500, fontSize: 15, marginBottom: 6 }}>
                  Drop your video or audio here
                </div>
                <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                  or click to browse · MP4, MOV, MKV, MP3, WAV · up to {MAX_FILE_MB} MB
                </div>
              </>
            )}
          </div>

          {/* Language selector */}
          <div style={{
            display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10,
            marginBottom: 20,
          }}>
            {(["hinglish", "english"] as Language[]).map((lang) => (
              <button
                key={lang}
                onClick={() => setLanguage(lang)}
                disabled={isProcessing}
                style={{
                  padding: "14px 16px",
                  borderRadius: 12,
                  border: `1.5px solid ${language === lang ? "var(--accent)" : "var(--border-default)"}`,
                  background: language === lang ? "var(--accent-glow)" : "var(--bg-card)",
                  cursor: isProcessing ? "default" : "pointer",
                  transition: "all 0.15s ease",
                  textAlign: "left",
                }}
              >
                <div style={{
                  fontWeight: 600, fontSize: 14,
                  color: language === lang ? "var(--accent-light)" : "var(--text-primary)",
                }}>
                  {lang === "hinglish" ? "Hinglish" : "English"}
                </div>
                <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                  {lang === "hinglish" ? "Roman script · Hindi phonetic" : "Translated · English output"}
                </div>
              </button>
            ))}
          </div>

          {/* Error message */}
          {errorMsg && (
            <div style={{
              padding: "12px 16px", borderRadius: 10, marginBottom: 16,
              background: "rgba(255, 107, 107, 0.08)",
              border: "1px solid rgba(255, 107, 107, 0.2)",
              fontSize: 13, color: "var(--error)", lineHeight: 1.5,
            }}>
              {errorMsg}
            </div>
          )}

          {/* Action button */}
          {state !== "done" ? (
            <button
              onClick={handleSubmit}
              disabled={!file || isProcessing}
              style={{
                width: "100%", padding: "16px",
                borderRadius: 12, border: "none",
                background: !file
                  ? "var(--bg-card)"
                  : isProcessing
                  ? "var(--bg-accent)"
                  : "linear-gradient(135deg, var(--accent), #a78bfa)",
                color: !file ? "var(--text-muted)" : "white",
                fontWeight: 600, fontSize: 15,
                cursor: !file || isProcessing ? "default" : "pointer",
                fontFamily: "var(--font-body)",
                transition: "all 0.2s ease",
                position: "relative",
                overflow: "hidden",
              }}
            >
              {isProcessing ? (
                <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10 }}>
                  <Spinner />
                  {state === "uploading" ? "Uploading..." : "Transcribing — this may take a minute..."}
                </span>
              ) : (
                "Generate Subtitles"
              )}
            </button>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {/* Success card */}
              <div style={{
                padding: "16px 20px", borderRadius: 12,
                background: "rgba(0, 201, 167, 0.06)",
                border: "1px solid rgba(0, 201, 167, 0.2)",
                display: "flex", alignItems: "center", gap: 12,
              }}>
                <span style={{ fontSize: 22 }}>✅</span>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: "var(--success)" }}>
                    Subtitles ready!
                  </div>
                  {segmentCount > 0 && (
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                      {segmentCount} subtitle segments generated
                    </div>
                  )}
                </div>
              </div>

              {/* Download button */}
              <button
                onClick={handleDownload}
                style={{
                  width: "100%", padding: "16px",
                  borderRadius: 12, border: "none",
                  background: "linear-gradient(135deg, #00c9a7, #00b894)",
                  color: "white", fontWeight: 600, fontSize: 15,
                  cursor: "pointer", fontFamily: "var(--font-body)",
                }}
              >
                ↓ Download .srt File
              </button>

              {/* Start over */}
              <button
                onClick={handleReset}
                style={{
                  width: "100%", padding: "12px",
                  borderRadius: 12,
                  border: "1px solid var(--border-default)",
                  background: "transparent",
                  color: "var(--text-secondary)", fontWeight: 500, fontSize: 13,
                  cursor: "pointer", fontFamily: "var(--font-body)",
                }}
              >
                Transcribe another file
              </button>
            </div>
          )}

          {/* Footer note */}
          <p style={{
            textAlign: "center", fontSize: 12, color: "var(--text-muted)",
            marginTop: 32, lineHeight: 1.6,
          }}>
            Processing happens server-side. Large files may take 1–3 minutes.
            <br />
            Powered by Faster-Whisper AI.
          </p>
        </div>
      </main>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Spinner component
// ---------------------------------------------------------------------------
function Spinner() {
  return (
    <svg
      width="18" height="18" viewBox="0 0 18 18"
      style={{ animation: "spin 0.8s linear infinite" }}
    >
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <circle cx="9" cy="9" r="7" fill="none" stroke="currentColor" strokeWidth="2.5"
        strokeDasharray="32" strokeDashoffset="10" strokeLinecap="round"
      />
    </svg>
  );
}
