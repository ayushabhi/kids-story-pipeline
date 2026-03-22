"""
YouTube Uploader — uploads long-form video and Shorts to YouTube
using the YouTube Data API v3 with OAuth2 service account credentials.
"""

import os
import json
import time
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from utils import logger

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE   = "youtube"
YOUTUBE_API_VERSION   = "v3"
MAX_RETRIES = 3


def upload_to_youtube(long_form_path: str, shorts_paths: list, story: dict):
    """Upload long-form video then each Short to YouTube."""
    youtube = _get_youtube_client()

    # ── Long-form upload ──────────────────────────────────────────────────
    logger.info("  Uploading long-form video...")
    long_form_meta = {
        "title": story["title"] + " | Kids Story",
        "description": _build_description(story, is_short=False),
        "tags": story["youtube_tags"] + ["kids story", "bedtime story", "children"],
        "categoryId": "27",          # Education
        "privacyStatus": "public",
        "defaultLanguage": "en",
        "madeForKids": True,         # IMPORTANT: comply with COPPA
    }
    long_form_id = _upload_video(youtube, long_form_path, long_form_meta)
    logger.info(f"  Long-form uploaded: https://youtube.com/watch?v={long_form_id}")

    # ── Shorts upload ─────────────────────────────────────────────────────
    for i, (short_path, short_meta_src) in enumerate(zip(shorts_paths, story["shorts"])):
        logger.info(f"  Uploading Short {i + 1}/{len(shorts_paths)}...")
        shorts_meta = {
            "title": short_meta_src["title"] + " #Shorts",
            "description": _build_description(story, is_short=True,
                                               long_form_id=long_form_id),
            "tags": story["youtube_tags"] + ["shorts", "kidsstory", "storytime"],
            "categoryId": "27",
            "privacyStatus": "public",
            "defaultLanguage": "en",
            "madeForKids": True,
        }
        short_id = _upload_video(youtube, short_path, shorts_meta)
        logger.info(f"  Short {i + 1} uploaded: https://youtube.com/shorts/{short_id}")
        time.sleep(2)   # Polite gap between uploads

    logger.info("  All uploads complete!")


def _build_description(story: dict, is_short: bool = False,
                        long_form_id: str = None) -> str:
    desc = story["youtube_description"] + "\n\n"
    desc += f"✨ Moral: {story['moral']}\n\n"
    if is_short and long_form_id:
        desc += f"▶️ Watch the full story: https://youtube.com/watch?v={long_form_id}\n\n"
    desc += "#KidsStory #BedtimeStory #StorytimeForKids #ChildrensStories #Shorts"
    return desc


def _upload_video(youtube, file_path: str, metadata: dict) -> str:
    """Upload a single video and return its YouTube video ID."""
    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": metadata["categoryId"],
            "defaultLanguage": metadata.get("defaultLanguage", "en"),
        },
        "status": {
            "privacyStatus": metadata["privacyStatus"],
            "madeForKids": metadata.get("madeForKids", True),
            "selfDeclaredMadeForKids": metadata.get("madeForKids", True),
        }
    }

    media = MediaFileUpload(
        file_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=8 * 1024 * 1024   # 8MB chunks
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    pct = int(status.progress() * 100)
                    logger.info(f"    Upload progress: {pct}%")
            return response["id"]
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504] and attempt < MAX_RETRIES:
                wait = 2 ** attempt
                logger.warning(f"    HTTP {e.resp.status} — retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def _get_youtube_client():
    """
    Build YouTube API client from OAuth2 credentials stored in env var.
    YOUTUBE_CREDENTIALS_JSON should contain the full credentials JSON string.
    """
    creds_json = os.environ.get("YOUTUBE_CREDENTIALS_JSON")
    if not creds_json:
        raise ValueError("YOUTUBE_CREDENTIALS_JSON environment variable not set")

    creds_data = json.loads(creds_json)
    creds = google.oauth2.credentials.Credentials(
        token=creds_data.get("token"),
        refresh_token=creds_data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=[YOUTUBE_UPLOAD_SCOPE]
    )
    return build(YOUTUBE_API_SERVICE, YOUTUBE_API_VERSION, credentials=creds)
