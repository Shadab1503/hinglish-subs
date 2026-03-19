# Hinglish Subs v1.1 — Deployment Guide

## What Changed (v1.0 → v1.1)

### 🐛 Backend Bug Fixes
1. **FileResponse race condition FIXED** — Old code used `FileResponse` + `shutil.rmtree` in `finally`, which deleted the file before it finished streaming. Now uses `StreamingResponse` with a generator that cleans up AFTER streaming completes.
2. **`romanize=True` doesn't exist in faster-whisper** — This parameter was silently ignored, meaning you were getting Devanagari output, not Roman script. Now uses `indic-transliteration` library for proper Hindi → Roman conversion.
3. **No file validation** — Now validates file type and size (500 MB limit) before processing.
4. **No error messages** — Backend now returns proper HTTP error codes and messages for all failure cases.
5. **Model loaded on every import** — Now lazy-loads the model as a singleton, and pre-warms it on startup via FastAPI lifespan.

### 🎨 Frontend Redesign
- Dark theme with polished SaaS aesthetics
- Drag-and-drop file upload
- File type and size validation on client side
- Real loading states (uploading → transcribing)
- Success card with segment count
- Named download files (video_name_subtitles.srt)
- Mobile responsive

### 🚀 Deployment Improvements
- Backend Dockerfile with FFmpeg and pre-downloaded Whisper model
- Railway configs for both services
- Health check endpoints
- `output: "standalone"` for optimized Next.js builds

---

## Deployment Steps (Railway)

### Prerequisites
- GitHub account with your repo pushed
- Railway account (https://railway.app)

### Step 1 — Push Code to GitHub

Replace your existing files with the new ones from the zip:

```powershell
cd "F:\Hinglish Transribe SAAS\hinglish-subs"

# Backend files — replace these:
#   backend/main.py
#   backend/transcribe.py
#   backend/srt_builder.py
#   backend/requirements.txt
#   backend/Dockerfile          (NEW)
#   backend/railway.toml        (NEW)
#   backend/.dockerignore       (UPDATE)

# Frontend files — replace these:
#   frontend/app/layout.tsx
#   frontend/app/page.tsx
#   frontend/app/globals.css    (NEW)
#   frontend/app/api/health/route.ts  (NEW - replaces api/transcribe/route.ts)
#   frontend/package.json
#   frontend/tsconfig.json
#   frontend/postcss.config.mjs (NEW)
#   frontend/next.config.ts     (NEW or UPDATE)
#   frontend/railway.toml
#   frontend/.env.local

# Delete old files:
#   frontend/app/api/transcribe/route.ts  (no longer needed)

# Commit and push
git add .
git commit -m "v1.1: bug fixes, new UI, deployment configs"
git push
```

### Step 2 — Deploy Backend on Railway

1. Go to **Railway Dashboard** → your project
2. If you already have a backend service, it will auto-deploy from the push
3. If creating new:
   - **New Service** → **GitHub Repo** → select your repo
   - **Root Directory**: `backend`
   - Railway will detect the Dockerfile automatically

4. **Set environment variables:**
   ```
   PORT=8000
   FRONTEND_URL=https://your-frontend-url.up.railway.app
   ```

5. Wait for build (first build takes ~5-8 min because it downloads the Whisper model)

6. **Verify**: Visit `https://your-backend-url.up.railway.app/health`
   - Should return: `{"status": "ok", "version": "1.1.0"}`

### Step 3 — Deploy Frontend on Railway

1. **New Service** → **GitHub Repo** → select your repo
   - **Root Directory**: `frontend`

2. **Set environment variables:**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.up.railway.app
   PORT=3000
   NODE_VERSION=20
   ```

3. Wait for build (~2-3 min)

4. **Verify**: Visit your frontend URL and test with a short video

### Step 4 — Update CORS

After both services are deployed, update the backend `FRONTEND_URL` env var with the actual frontend Railway URL. This is used in CORS configuration.

The backend `main.py` reads `FRONTEND_URL` from env, so just set it in Railway dashboard:
```
FRONTEND_URL=https://front-end-production-d335.up.railway.app
```

Redeploy the backend after changing this.

---

## Testing Checklist

- [ ] Backend health check returns OK
- [ ] Upload a short MP4 (under 30 seconds)
- [ ] Hinglish mode produces Roman script output (not Devanagari)
- [ ] English mode produces translated English subtitles
- [ ] SRT file downloads with correct timestamps
- [ ] 3-word chunking is applied
- [ ] Large file (>500 MB) shows error message
- [ ] Unsupported file type shows error message
- [ ] Drag and drop works
- [ ] Mobile layout looks correct

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Backend build fails on Railway | Check Dockerfile — ensure Railway has enough memory (recommend 2 GB+) |
| First request is slow | Normal — model loads on startup. Check logs for "Whisper model loaded" |
| CORS errors in browser console | Update `FRONTEND_URL` env var on backend to match your frontend URL |
| "No speech detected" error | File might be silent or too short. Try a different video |
| Devanagari output instead of Roman | Make sure `indic-transliteration` is installed (it's in requirements.txt) |
| Frontend shows "backend_unreachable" | Check that `NEXT_PUBLIC_API_URL` is set correctly on frontend |

---

## Railway Resource Recommendations

| Service | RAM | CPU | Disk |
|---------|-----|-----|------|
| Backend | 2 GB+ | 2 vCPU | 4 GB (for model) |
| Frontend | 512 MB | 1 vCPU | 1 GB |

The Whisper model needs ~1.5 GB RAM. Railway's Hobby plan ($5/mo) should work for light usage.
