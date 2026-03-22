"""
Voiceover Generator — ElevenLabs with automatic fallback to gTTS (free).
Free ElevenLabs voices that work on the free tier:
  - Rachel  : 21m00Tcm4TlvDq8ikWAM  (warm, clear)
  - Bella   : EXAVITQu4vr4xnSDxMaL  (soft, friendly)
  - Elli    : MF3mGyEYCl7XYWbV9V6O  (young, bright)
  - Adam    : pNInz6obpgDQGcFmaJgB  (calm, neutral)
"""

import os
import requests
from utils import logger

# Free-tier safe voice: "Rachel" — warm and clear
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

VOICE_SETTINGS = {
    "stability": 0.75,
    "similarity_boost": 0.80,
    "style": 0.30,
    "use_speaker_boost": True,
}


def generate_voiceover(script: str, output_dir: str) -> str:
    """
    Try ElevenLabs first, fall back to gTTS if it fails.
    Returns path to the saved MP3 file.
    """
    try:
        return _elevenlabs_tts(script, output_dir)
    except Exception as e:
        logger.warning(f"  ElevenLabs failed ({e}). Falling back to gTTS...")
        return _gtts_fallback(script, output_dir)


def _elevenlabs_tts(script: str, output_dir: str) -> str:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not set")

    # Use env var voice ID if set, otherwise use free default
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "").strip() or DEFAULT_VOICE_ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    char_count = len(script)
    logger.info(f"  ElevenLabs: {char_count} chars, voice={voice_id}")

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": script,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": VOICE_SETTINGS,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=120)

    if response.status_code == 402:
        raise RuntimeError(
            "ElevenLabs 402: free tier exhausted or voice requires paid plan. "
            f"Try switching ELEVENLABS_VOICE_ID to: 21m00Tcm4TlvDq8ikWAM (Rachel)"
        )

    response.raise_for_status()

    audio_path = os.path.join(output_dir, "narration.mp3")
    with open(audio_path, "wb") as f:
        f.write(response.content)

    logger.info(f"  ElevenLabs audio saved ({len(response.content) / 1024:.0f} KB)")
    return audio_path


def _gtts_fallback(script: str, output_dir: str) -> str:
    """
    Google Text-to-Speech via gTTS — completely free, no API key needed.
    Quality is lower than ElevenLabs but perfectly usable.
    """
    try:
        from gtts import gTTS
    except ImportError:
        raise RuntimeError("gTTS not installed. Add 'gTTS' to requirements.txt")

    logger.info("  Using gTTS fallback (free, no API key needed)...")
    tts = gTTS(text=script, lang="en", slow=False)

    audio_path = os.path.join(output_dir, "narration.mp3")
    tts.save(audio_path)
    logger.info(f"  gTTS audio saved: {audio_path}")
    return audio_path


def list_free_voices() -> list:
    """Known free-tier ElevenLabs voice IDs (as of 2025)."""
    return [
        {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel  — warm, clear (recommended)"},
        {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella   — soft, friendly"},
        {"id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli    — young, bright"},
        {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam    — calm, neutral"},
    ]
