"""
Image Generator — uses Replicate's FLUX model to create
consistent Pixar-style 9:16 vertical scene illustrations.
"""

import os
import time
import requests
import replicate
from utils import logger

# FLUX model on Replicate — best quality
FLUX_MODEL = "black-forest-labs/flux-1.1-pro"

# Style prefix applied to every scene prompt for visual consistency
STYLE_PREFIX = (
    "Pixar 3D animation style, vibrant colors, soft warm lighting, "
    "child-friendly, expressive characters, storybook illustration, "
    "9:16 vertical aspect ratio, high quality render, "
    "no text, no watermarks, no logos, "
)


def generate_images(scenes: list, output_dir: str, dry_run: bool = False) -> list:
    """
    Generate one image per scene using FLUX on Replicate.
    Returns list of image file paths in scene order.
    """
    if dry_run:
        logger.info("  DRY RUN: Creating placeholder images")
        return _create_placeholder_images(scenes, output_dir)

    api_token = os.environ.get("REPLICATE_API_TOKEN")
    if not api_token:
        raise ValueError("REPLICATE_API_TOKEN environment variable not set")

    os.environ["REPLICATE_API_TOKEN"] = api_token
    image_paths = []

    for scene in scenes:
        scene_num = scene["scene_number"]
        prompt = STYLE_PREFIX + scene["image_prompt"]
        logger.info(f"  Generating image for scene {scene_num}/{len(scenes)}...")

        try:
            output = replicate.run(
                FLUX_MODEL,
                input={
                    "prompt": prompt,
                    "aspect_ratio": "9:16",
                    "output_format": "png",
                    "output_quality": 90,
                    "safety_tolerance": 2,   # strict — safe for kids
                }
            )

            # Output is a URL — download the image
            image_url = str(output) if not isinstance(output, list) else str(output[0])
            image_path = os.path.join(output_dir, f"scene_{scene_num:02d}.png")

            img_response = requests.get(image_url, timeout=60)
            img_response.raise_for_status()
            with open(image_path, "wb") as f:
                f.write(img_response.content)

            image_paths.append(image_path)
            logger.info(f"    Saved: scene_{scene_num:02d}.png")

            # Polite rate limiting
            time.sleep(1)

        except Exception as e:
            logger.error(f"  Failed to generate image for scene {scene_num}: {e}")
            # Use placeholder so pipeline doesn't crash
            placeholder = _create_single_placeholder(scene_num, output_dir)
            image_paths.append(placeholder)

    return image_paths


def _create_placeholder_images(scenes: list, output_dir: str) -> list:
    """Create colored placeholder PNGs for dry runs (no API calls)."""
    from PIL import Image, ImageDraw, ImageFont
    paths = []
    colors = ["#FF9AA2", "#FFB7B2", "#FFDAC1", "#E2F0CB", "#B5EAD7",
              "#C7CEEA", "#F8B4D9", "#A8E6CE"]
    for scene in scenes:
        n = scene["scene_number"]
        path = _create_single_placeholder(n, output_dir, colors[(n - 1) % len(colors)])
        paths.append(path)
    return paths


def _create_single_placeholder(scene_num: int, output_dir: str,
                                color: str = "#C7CEEA") -> str:
    """Create a single colored placeholder PNG (1080x1920 = 9:16)."""
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (1080, 1920), color)
        draw = ImageDraw.Draw(img)
        draw.text((540, 960), f"Scene {scene_num}", fill="#333333", anchor="mm")
        path = os.path.join(output_dir, f"scene_{scene_num:02d}.png")
        img.save(path)
        return path
    except ImportError:
        # Fallback: create empty file
        path = os.path.join(output_dir, f"scene_{scene_num:02d}.png")
        open(path, "w").close()
        return path
