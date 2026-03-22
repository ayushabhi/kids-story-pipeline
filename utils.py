import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("kids_story_pipeline")

def create_run_dir(run_id: str) -> str:
    """
    Creates a new directory for the current run under OUTPUT_DIR and returns its path.
    """
    base_output_dir = os.environ.get("OUTPUT_DIR", "output")
    run_dir = os.path.join(base_output_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)
    return run_dir
