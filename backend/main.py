from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, uuid, subprocess

from audio_extractor import extract_audio
from transcribe import transcribe_hinglish, transcribe_urdu_english
from srt_builder import build_srt, build_vtt, build_ass

app = FastAPI(title="HinglishSubs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "C:/tmp/hinglish_subs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/transcribe")
async def transcribe(
    file:     UploadFile = File(...),
    language: str        = Form("hinglish"),
    format:   str        = Form("srt"),
    style:    str        = Form("yellow_impact")
):
    ext      = file.filename.rsplit(".", 1)[-1]
    job_id   = str(uuid.uuid4())
    vid_path = f"{UPLOAD_DIR}/{job_id}.{ext}"

    with open(vid_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        audio_path = extract_audio(vid_path)
        result     = transcribe_urdu_english(audio_path) if language == "urdu" \
                     else transcribe_hinglish(audio_path)
        segments   = result.get("segments") or \
                     [{"start": 0, "end": result.get("total_time", 10),
                       "text": result.get("text", "")}]

        if format == "vtt":
            content, mime, fname = build_vtt(segments), "text/vtt", f"subtitles_{language}.vtt"
        elif format == "ass":
            content, mime, fname = build_ass(segments, style=style), "text/plain", f"subtitles_{language}.ass"
        else:
            content, mime, fname = build_srt(segments), "text/plain", f"subtitles_{language}.srt"

        return Response(
            content=content, media_type=mime,
            headers={"Content-Disposition": f"attachment; filename={fname}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for p in [vid_path, vid_path.rsplit(".", 1)[0] + "_audio.wav"]:
            if os.path.exists(p): os.remove(p)


@app.post("/render")
async def render(
    file:     UploadFile = File(...),
    language: str        = Form("hinglish"),
    style:    str        = Form("yellow_impact")
):
    ext      = file.filename.rsplit(".", 1)[-1]
    job_id   = str(uuid.uuid4())
    vid_path = f"{UPLOAD_DIR}/{job_id}.{ext}"
    ass_path = f"{UPLOAD_DIR}/{job_id}.ass"

    with open(vid_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        audio_path = extract_audio(vid_path)
        result     = transcribe_urdu_english(audio_path) if language == "urdu" \
                     else transcribe_hinglish(audio_path)
        segments   = result.get("segments") or []

        ass_content = build_ass(segments, style=style)
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        force_styles = {
            "yellow_impact": "FontName=Impact,FontSize=90,PrimaryColour=&H0000EEFF,OutlineColour=&H00000000,Bold=1,Outline=4,Shadow=2,Alignment=2,MarginV=350",
            "green_outline": "FontName=Impact,FontSize=90,PrimaryColour=&H0000DD00,OutlineColour=&H00000000,Bold=1,Outline=4,Shadow=0,Alignment=2,MarginV=350",
            "blue_box":      "FontName=Arial,FontSize=85,PrimaryColour=&H00FFFFFF,OutlineColour=&H00E85C1A,Bold=1,BorderStyle=3,Outline=0,Alignment=2,MarginV=350",
            "classic":       "FontName=Arial,FontSize=80,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Bold=1,Outline=4,Shadow=2,Alignment=2,MarginV=350",
        }
        fs = force_styles.get(style, force_styles["yellow_impact"])

        simple_ass = f"{job_id}.ass"
        simple_out = f"{job_id}_output.mp4"

        subprocess.run([
            "ffmpeg", "-y",
            "-i", vid_path,
            "-vf", f"subtitles={simple_ass}:force_style='{fs}'",
            "-c:a", "copy",
            simple_out
        ], check=True, cwd=UPLOAD_DIR)

        out_path = f"{UPLOAD_DIR}/{simple_out}"

        return FileResponse(
            out_path,
            media_type="video/mp4",
            filename="hinglishsubs_output.mp4"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for p in [vid_path, ass_path,
                  vid_path.rsplit(".", 1)[0] + "_audio.wav"]:
            if os.path.exists(p): os.remove(p)


@app.get("/health")
def health():
    return {"status": "ok"}
