"""
Story Generator — calls Claude API to produce a fully structured kids story
with narration script, scene breakdown, and Short clip markers.
"""

import os
import json
import random
import anthropic

THEMES = [
    "courage and facing fears",
    "kindness to strangers",
    "sharing with friends",
    "honesty and telling the truth",
    "perseverance and never giving up",
    "caring for animals",
    "helping family",
    "being patient",
    "celebrating differences",
    "protecting nature",
]

STORY_PROMPT = """You are a children's story writer creating content for YouTube.
Write a warm, engaging kids story (ages 3–7) with these requirements:

Theme: {theme}

Return ONLY valid JSON (no markdown, no preamble) with this exact structure:
{{
  "title": "Short catchy title (max 6 words)",
  "moral": "One sentence moral lesson",
  "target_age": "3-7",
  "narration_script": "Full narration text, ~400-500 words, warm friendly tone, simple vocabulary. No stage directions.",
  "youtube_description": "2-3 sentence YouTube description with emojis, kid-friendly",
  "youtube_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "scenes": [
    {{
      "scene_number": 1,
      "narration_excerpt": "Exact sentence(s) from narration_script that play during this scene",
      "image_prompt": "Detailed FLUX image prompt: bright, colorful, Pixar-style 3D illustration, child-friendly, 9:16 vertical format. Describe characters, setting, action, lighting. No text in image.",
      "duration_seconds": 25,
      "is_short_clip": false
    }}
  ],
  "shorts": [
    {{
      "short_number": 1,
      "title": "Catchy Short title with emoji",
      "scene_numbers": [1, 2],
      "hook_text": "First 3 words that appear as caption overlay"
    }}
  ]
}}

Rules:
- Create exactly 8 scenes, each 20-35 seconds (total ~4-5 minutes)
- Mark scenes 1-2 as "is_short_clip": true (opening hook Short)
- Mark scenes 4-5 as "is_short_clip": true (climax Short)  
- Mark scenes 7-8 as "is_short_clip": true (ending/moral Short)
- Create 3 shorts objects referencing those scene groups
- Image prompts must be vivid, consistent characters across all scenes
- Keep vocabulary simple (max grade 2 reading level)"""


def generate_story(theme: str = None) -> dict:
    """Generate a complete kids story using Claude API."""
    if not theme:
        theme = random.choice(THEMES)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": STORY_PROMPT.format(theme=theme)
            }
        ]
    )

    raw = response.content[0].text.strip()

    # Strip accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    story = json.loads(raw)
    story["theme"] = theme
    return story
