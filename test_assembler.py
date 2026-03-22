import os
import json
from video_assembler import assemble_long_form, assemble_shorts
from utils import logger

def test_local_assembly(run_dir: str):
    """
    Locally tests the MoviePy video assembly step using pre-generated assets.
    run_dir must contain story.json, narration.mp3, and scene_0X.png files.
    """
    logger.info(f"Starting Local Assembly Test on: {run_dir}")
    
    story_path = os.path.join(run_dir, "story.json")
    audio_path = os.path.join(run_dir, "narration.mp3")
    
    if not os.path.exists(story_path) or not os.path.exists(audio_path):
        logger.error(f"Missing required files in {run_dir}! Need story.json and narration.mp3")
        return

    with open(story_path, "r") as f:
        story = json.load(f)

    # Collect image paths based on scenes
    image_paths = []
    for idx in range(1, len(story["scenes"]) + 1):
        img_path = os.path.join(run_dir, f"scene_{idx:02d}.png")
        if not os.path.exists(img_path):
            logger.error(f"Missing image file: {img_path}")
            return
        image_paths.append(img_path)
        
    logger.info("All assets found. Assembling videos...")
    
    # 1. Assemble Long Form
    long_form_path = assemble_long_form(
        image_paths=image_paths,
        audio_path=audio_path,
        story=story,
        output_dir=run_dir
    )
    logger.info(f"Long form video constructed successfully at {long_form_path}!")

    # 2. Assemble Shorts
    shorts_paths = assemble_shorts(
        image_paths=image_paths,
        audio_path=audio_path,
        story=story,
        output_dir=run_dir
    )
    logger.info(f"Shorts constructed successfully: {shorts_paths}")
    
    logger.info("Local test complete! The MoviePy bug has been successfully resolved.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test video assembler locally")
    parser.add_argument("run_dir", type=str, help="Path to the directory containing narration.mp3 and scene images")
    args = parser.parse_args()
    
    test_local_assembly(args.run_dir)
