"use client";
import { useState } from "react";

export default function Home() {
  const [file, setFile]         = useState<File | null>(null);
  const [language, setLanguage] = useState("hinglish");
  const [format, setFormat]     = useState("srt");
  const [style, setStyle]       = useState("classic");
  const [mode, setMode]         = useState<"subtitles" | "render">("render");
  const [loading, setLoading]   = useState(false);
  const [preview, setPreview]   = useState("");
  const [error, setError]       = useState("");

  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    setPreview("");

    const form = new FormData();
    form.append("file", file);
    form.append("language", language);
    form.append("style", style);

    try {
      if (mode === "render") {
        // Call /render → get back MP4 with burned captions
        const res = await fetch(`${API}/render`, { method: "POST", body: form });
        if (!res.ok) throw new Error(await res.text());

        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement("a");
        a.href = url;
        a.download = "hinglishsubs_output.mp4";
        a.click();
        URL.revokeObjectURL(url);
        setPreview("✅ Video rendered and downloaded!");

      } else {
        // Call /transcribe → get subtitle file
        form.append("format", format);
        const res = await fetch(`${API}/transcribe`, { method: "POST", body: form });
        if (!res.ok) throw new Error(await res.text());

        const text = await res.text();
        setPreview(text);

        const blob = new Blob([text], { type: "text/plain" });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement("a");
        a.href = url;
        a.download = `subtitles.${format}`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const styleLabels: Record<string, string> = {
    classic: "⚪ Classic — White + Black outline",
    yellow:  "🟡 Yellow — Viral / Reels style",
    netflix: "🔲 Netflix — White on dark box",
    neon:    "🟢 Neon — Green glow cinematic",
  };

  return (
    <main className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center p-8 gap-6">
      <div className="text-center">
        <h1 className="text-5xl font-bold mb-2">🎬 HinglishSubs</h1>
        <p className="text-gray-400 text-lg">Drop your video → Get Hinglish subtitles instantly</p>
      </div>

      {/* Mode Toggle */}
      <div className="flex bg-gray-800 rounded-xl p-1 gap-1">
        <button
          onClick={() => setMode("render")}
          className={`px-6 py-2 rounded-lg font-medium transition text-sm ${
            mode === "render"
              ? "bg-purple-600 text-white"
              : "text-gray-400 hover:text-white"
          }`}>
          🎥 Burn into Video
        </button>
        <button
          onClick={() => setMode("subtitles")}
          className={`px-6 py-2 rounded-lg font-medium transition text-sm ${
            mode === "subtitles"
              ? "bg-purple-600 text-white"
              : "text-gray-400 hover:text-white"
          }`}>
          📄 Download Subtitle File
        </button>
      </div>

      {/* Drop Zone */}
      <label
        className="border-2 border-dashed border-purple-500 rounded-2xl p-16 w-full max-w-xl
                   text-center cursor-pointer hover:bg-purple-950/30 transition"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <input type="file" accept="video/*,audio/*" className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] || null)} />
        {file
          ? <p className="text-green-400 text-lg font-medium">✅ {file.name}</p>
          : <div>
              <p className="text-2xl mb-2">📂</p>
              <p className="text-gray-300">Click or drag a video / audio file</p>
              <p className="text-gray-500 text-sm mt-1">MP4, MOV, MKV, MP3, WAV supported</p>
            </div>
        }
      </label>

      {/* Controls */}
      <div className="flex gap-4 flex-wrap justify-center">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-400 uppercase tracking-wider">Language</label>
          <select value={language} onChange={(e) => setLanguage(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white">
            <option value="hinglish">🇮🇳 Hinglish</option>
            <option value="urdu">🇵🇰 Urdu-English</option>
          </select>
        </div>

        {mode === "subtitles" && (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-400 uppercase tracking-wider">Format</label>
            <select value={format} onChange={(e) => setFormat(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white">
              <option value="srt">SRT — Premiere / DaVinci</option>
              <option value="vtt">VTT — Web / YouTube</option>
              <option value="ass">ASS — Styled Captions ✨</option>
            </select>
          </div>
        )}

        {(mode === "render" || format === "ass") && (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-400 uppercase tracking-wider">Caption Style</label>
            <select value={style} onChange={(e) => setStyle(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white">
              {Object.entries(styleLabels).map(([val, label]) => (
                <option key={val} value={val}>{label}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Generate Button */}
      <button onClick={handleUpload} disabled={!file || loading}
        className="bg-purple-600 hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed
                   px-10 py-3 rounded-xl font-semibold text-lg transition w-full max-w-xl">
        {loading
          ? (mode === "render" ? "⏳ Rendering video..." : "⏳ Transcribing...")
          : (mode === "render" ? "🎥 Generate & Download Video" : "✨ Generate Subtitles")}
      </button>

      {error && <p className="text-red-400 text-sm">❌ {error}</p>}

      {preview && mode === "subtitles" && (
        <div className="w-full max-w-xl">
          <p className="text-xs text-gray-400 mb-1 uppercase tracking-wider">Preview</p>
          <textarea readOnly value={preview}
            className="w-full bg-gray-900 border border-gray-700 rounded-xl p-4
                       text-sm text-green-300 h-52 font-mono resize-none" />
        </div>
      )}

      {preview && mode === "render" && (
        <p className="text-green-400 text-sm font-medium">{preview}</p>
      )}
    </main>
  );
}
