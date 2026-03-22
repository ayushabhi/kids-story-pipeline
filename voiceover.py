"""
Voiceover Generator — uses ElevenLabs API to produce warm, child-friendly narration.
"""

import os
import requests
from utils import logger

# ElevenLabs voice IDs — child-friendly warm voices
# "Lily" is soft and warm, great for kids stories
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "pFZP5JQG7iQjIQuC4Bku")  # Lily

ELEVENLABS_API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

VOICE_SETTINGS = {
    "stability": 0.75,          # Consistent, not too robotic
    "similarity_boost": 0.80,   # Stay true to voice character
    "style": 0.35,              # Slight expressiveness
    "use_speaker_boost": True
}


def generate_voiceover(script: str, output_dir: str) -> str:
    """
    Convert narration script to MP3 audio using ElevenLabs.
    Returns path to saved MP3 file.
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY environment variable not set")

    # ElevenLabs free tier: 10,000 chars/month
    # Typical 400-word story ≈ 2,500 chars — fits ~4 stories/month free
    char_count = len(script)
    logger.info(f"  Generating audio for {char_count} characters (~{char_count/1000:.1f}k of 10k free tier)")

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }

    payload = {
        "text": script,
        "model_id": "eleven_turbo_v2_5",   # Fast + high quality
        "voice_settings": VOICE_SETTINGS
    }

    response = requests.post(ELEVENLABS_API_URL, json=payload, headers=headers)
    response.raise_for_status()

    audio_path = os.path.join(output_dir, "narration.mp3")
    with open(audio_path, "wb") as f:
        f.write(response.content)

    logger.info(f"  Audio saved ({len(response.content) / 1024:.0f} KB)")
    return audio_path


def list_voices() -> list:
    """Helper to list available ElevenLabs voices and find good ones."""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    response = requests.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": api_key}
    )
    response.raise_for_status()
    voices = response.json()["voices"]
    return [{"id": v["voice_id"], "name": v["name"]} for v in voices]
