# Deploying FalconFX Booster to Render (Free Tier)

This avoids Replit's dev-time cap entirely. Render's free tier has no daily
minute limit — it just falls asleep after ~15 minutes of no traffic and
takes a few seconds to wake back up on the next request (the FalconFX app
already handles this with a 9-second fallback timeout on the map, and the
Booster client retries automatically).

## Step 1 — Create a GitHub repo (Render deploys from Git, not zip upload)

1. Go to github.com → New repository → name it `falconfx-booster` → Create
2. Upload every file in this folder to that repo:
   - `api.py`
   - `booster.py`
   - `places.json`
   - `requirements.txt`
   - `render.yaml`
   - `static/dashboard.html` (keep the `static` folder)
   - (`booster-client.js`, `seed_landmarks.py`, `test_intelligence.py` are
     optional — not required for the API to run, but fine to include)

   Easiest way on mobile: GitHub's web UI has an "Add file → Upload files"
   button — you can drag all these in directly, no git command line needed.

## Step 2 — Connect Render to that repo

1. Go to render.com → sign up (no credit card required for free tier)
2. Dashboard → "New +" → "Web Service"
3. Connect your GitHub account → select the `falconfx-booster` repo
4. Render will detect `render.yaml` automatically and pre-fill everything:
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - Plan: Free
5. Click "Create Web Service"

## Step 3 — Wait for the first build (~2-5 minutes)

Render will show live build logs. You're looking for:
`[FalconFX API v4.1] Ready. Predictive offset: +15min.`
(or similar — confirms the engine loaded `places.json` successfully)

## Step 4 — Get your permanent URL

Render gives you a URL like:
`https://falconfx-booster.onrender.com`

This does NOT rotate, NOT expire, NOT cap out on dev-minutes. It only
sleeps after idle time and wakes on the next request (few seconds delay).

## Step 5 — Update the frontend

Open `js/config.js` in the FalconFX frontend project, find:
```
BOOSTER_API : 'https://...replit.dev',
```
Replace with:
```
BOOSTER_API : 'https://falconfx-booster.onrender.com',
```
(no trailing slash, no port number)

## Verifying it worked

Visit `https://falconfx-booster.onrender.com/booster/health` directly in
any browser. You should see JSON like:
```json
{"status": "ok", "version": "4.1.0", "grid_cells": ..., "places_loaded": 27066, ...}
```
If you see that, the backend is live and the frontend will connect on the
next "Test Now" tap in the Booster Diagnostics screen.
