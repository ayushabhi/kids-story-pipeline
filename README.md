# 🎬 Kids Story YouTube Pipeline

Fully automated pipeline that generates kids stories, creates voiceovers, generates AI illustrations, assembles videos, and uploads to YouTube — on a schedule.

**Output per run:** 1 long-form video (4–5 min) + 3 YouTube Shorts

---

## Architecture

```
Claude API          → Story script + scene prompts
ElevenLabs API      → MP3 narration voiceover
Replicate (FLUX)    → 8 scene illustrations (9:16)
MoviePy + Whisper   → Video assembly + auto captions
YouTube Data API    → Upload long-form + 3 Shorts
GitHub Actions      → Runs automatically twice a week
```

---

## Cost estimate (30 videos/month)

| Service | Usage | Cost |
|---|---|---|
| Anthropic (Claude Sonnet) | 30 stories | ~$1–2 |
| ElevenLabs | 10k chars free tier | Free |
| Replicate (FLUX 1.1 Pro) | 8 images × 30 = 240 | ~$7–10 |
| YouTube API | Free quota | Free |
| GitHub Actions | Free tier (2,000 min/mo) | Free |
| **Total** | | **~$8–12/mo** |

---

## Setup

### 1. Clone & prepare

```bash
git clone <your-repo>
cd kids-story-pipeline
pip install -r requirements.txt
```

### 2. Get API keys

| Key | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com |
| `ELEVENLABS_API_KEY` | https://elevenlabs.io → Profile → API Key |
| `ELEVENLABS_VOICE_ID` | ElevenLabs → Voices → choose one → copy ID |
| `REPLICATE_API_TOKEN` | https://replicate.com/account |
| `YOUTUBE_CREDENTIALS_JSON` | See step 3 below |

### 3. Set up YouTube OAuth2 (one time)

```bash
# 1. Go to https://console.cloud.google.com
# 2. Create a project → Enable YouTube Data API v3
# 3. Create OAuth2 credentials → Desktop App → Download client_secrets.json
# 4. Put client_secrets.json in the project root
# 5. Run:
python scripts/setup_youtube_auth.py
# 6. Copy the printed JSON into GitHub secret YOUTUBE_CREDENTIALS_JSON
```

### 4. Add GitHub Secrets

In your GitHub repo → Settings → Secrets and variables → Actions:

```
ANTHROPIC_API_KEY
ELEVENLABS_API_KEY
ELEVENLABS_VOICE_ID
REPLICATE_API_TOKEN
YOUTUBE_CREDENTIALS_JSON
```

### 5. Push to GitHub

```bash
git add .
git commit -m "Initial pipeline setup"
git push origin main
```

The pipeline will now run **every Tuesday and Friday at 8 AM UTC** automatically.

---

## Manual trigger

In GitHub → Actions → Kids Story Pipeline → Run workflow

You can optionally pass a theme like: `kindness`, `courage`, `sharing`

---

## Run locally

```bash
cd pipeline

# Normal run
python main.py

# With a specific theme
python main.py --theme "friendship"

# Dry run (no image generation, no YouTube upload — for testing)
python main.py --dry-run
```

Set your env vars first:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export ELEVENLABS_API_KEY=...
export REPLICATE_API_TOKEN=...
export YOUTUBE_CREDENTIALS_JSON='{"refresh_token": "...", ...}'
```

---

## Output structure

```
output/
  20241201_083012/
    story.json          # Full story data
    narration.mp3       # ElevenLabs voiceover
    scene_01.png        # FLUX illustrations
    scene_02.png
    ...
    scene_08.png
    long_form.mp4       # 16:9 full video
    short_1.mp4         # Opening hook Short
    short_2.mp4         # Climax Short
    short_3.mp4         # Ending/moral Short
    short_1_audio.mp3   # Temp audio slices
    short_2_audio.mp3
    short_3_audio.mp3
```

---

## Customization

### Change posting schedule
Edit `.github/workflows/pipeline.yml`:
```yaml
- cron: "0 8 * * 2,5"   # Tue + Fri 8am UTC
```

### Change story themes pool
Edit `pipeline/story_generator.py` → `THEMES` list

### Change voice
1. Go to ElevenLabs → Voices
2. Find a warm, friendly voice
3. Copy the voice ID
4. Set `ELEVENLABS_VOICE_ID` secret

### Change image style
Edit `pipeline/image_generator.py` → `STYLE_PREFIX`
Example: change "Pixar 3D animation style" to "watercolor illustration, storybook art"

---

## Important notes

- Videos are marked `madeForKids: True` (COPPA compliance) — ads may be limited
- ElevenLabs free tier = 10,000 chars/month ≈ 4 stories. Upgrade to Creator ($5/mo) for 30,000 chars
- YouTube has a daily upload quota — if uploading many videos, spread across days
- Never commit API keys or `youtube_credentials.json` to git
