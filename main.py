"""
Kids Story YouTube Pipeline - Main Orchestrator
Generates story → voiceover → images → video → uploads to YouTube
"""

import os
import json
import argparse
from datetime import datetime
from story_generator import generate_story
from voiceover import generate_voiceover
from image_generator import generate_images
from video_assembler import assemble_long_form, assemble_shorts
from youtube_uploader import upload_to_youtube
from utils import create_run_dir, logger


def run_pipeline(theme: str = None, dry_run: bool = False):
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = create_run_dir(run_id)
    logger.info(f"Starting pipeline run: {run_id}")

    # ── 1. Generate story ──────────────────────────────────────────────────
    logger.info("Step 1/5 → Generating story...")
    story = generate_story(theme=theme)
    story_path = os.path.join(run_dir, "story.json")
    with open(story_path, "w") as f:
        json.dump(story, f, indent=2)
    logger.info(f"  Story: '{story['title']}' | {len(story['scenes'])} scenes")

    # ── 2. Generate voiceover ──────────────────────────────────────────────
    logger.info("Step 2/5 → Generating voiceover with ElevenLabs...")
    audio_path = generate_voiceover(
        script=story["narration_script"],
        output_dir=run_dir
    )
    logger.info(f"  Audio saved: {audio_path}")

    # ── 3. Generate images ─────────────────────────────────────────────────
    logger.info("Step 3/5 → Generating scene images with FLUX...")
    image_paths = generate_images(
        scenes=story["scenes"],
        output_dir=run_dir,
        dry_run=dry_run
    )
    logger.info(f"  Generated {len(image_paths)} images")

    # ── 4. Assemble videos ─────────────────────────────────────────────────
    logger.info("Step 4/5 → Assembling videos...")
    long_form_path = assemble_long_form(
        image_paths=image_paths,
        audio_path=audio_path,
        story=story,
        output_dir=run_dir
    )

    shorts_paths = assemble_shorts(
        image_paths=image_paths,
        audio_path=audio_path,
        story=story,
        output_dir=run_dir
    )
    logger.info(f"  Long-form: {long_form_path}")
    logger.info(f"  Shorts: {len(shorts_paths)} clips")

    # ── 5. Upload to YouTube ───────────────────────────────────────────────
    if dry_run:
        logger.info("Step 5/5 → DRY RUN: Skipping YouTube upload")
    else:
        logger.info("Step 5/5 → Uploading to YouTube...")
        upload_to_youtube(
            long_form_path=long_form_path,
            shorts_paths=shorts_paths,
            story=story
        )

    logger.info(f"Pipeline complete! Run ID: {run_id}")
    return run_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kids Story YouTube Pipeline")
    parser.add_argument("--theme", type=str, default=None,
                        help="Story theme (e.g. 'courage', 'sharing', 'kindness')")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip image generation and YouTube upload")
    args = parser.parse_args()
    run_pipeline(theme=args.theme, dry_run=args.dry_run)
