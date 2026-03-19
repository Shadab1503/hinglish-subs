import os
import tempfile
import shutil
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from transcribe import transcribe_hinglish, transcribe_urdu_english
from srt_builder import build_srt

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_MB = 500
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav", ".m4a", ".flac", ".ogg"}

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    os.getenv("FRONTEND_URL", "https://front-end-production-d335.up.railway.app"),
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan — warm up model on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Hinglish Subtitles API...")
    # Pre-load the Whisper model so the first request isn't slow
    from transcribe import get_model
    get_model()
    logger.info("✅ Whisper model loaded and ready")
    yield
    logger.info("👋 Shutting down...")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Hinglish Subtitles API",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def validate_file(filename: str, size: int) -> None:
    """Validate file extension and size before processing."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    if size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size / 1024 / 1024:.0f} MB). Max: {MAX_FILE_SIZE_MB} MB",
        )


def iter_file_then_cleanup(file_path: str, temp_dir: str):
    """Stream the file contents, then delete the temp directory."""
    try:
        with open(file_path, "rb") as f:
            yield from f
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info(f"🧹 Cleaned up temp dir: {temp_dir}")

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "version": "1.1.0"}


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form("hinglish"),
):
    # Read file into memory first to check size
    contents = await file.read()
    validate_file(file.filename or "unknown.mp4", len(contents))

    # Save to temp directory
    temp_dir = tempfile.mkdtemp(prefix="hinglish_")
    safe_name = file.filename.replace("/", "_").replace("\\", "_") if file.filename else "upload.mp4"
    file_path = os.path.join(temp_dir, safe_name)

    try:
        with open(file_path, "wb") as f:
            f.write(contents)

        logger.info(f"📝 Transcribing '{safe_name}' ({len(contents) / 1024 / 1024:.1f} MB) in '{language}' mode")

        # Transcribe
        if language == "hinglish":
            result = transcribe_hinglish(file_path)
        elif language in ("english", "urdu_english"):
            result = transcribe_urdu_english(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown language: {language}")

        if not result["segments"]:
            raise HTTPException(status_code=422, detail="No speech detected in the file")

        # Build SRT
        srt_content = build_srt(result["segments"])
        output_path = os.path.join(temp_dir, "subtitles.srt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        logger.info(f"✅ Generated {len(result['segments'])} subtitle segments")

        # Stream response — cleanup happens AFTER streaming finishes
        return StreamingResponse(
            iter_file_then_cleanup(output_path, temp_dir),
            media_type="application/x-subrip",
            headers={
                "Content-Disposition": 'attachment; filename="subtitles.srt"',
                "X-Segment-Count": str(len(result["segments"])),
            },
        )

    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error(f"❌ Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
