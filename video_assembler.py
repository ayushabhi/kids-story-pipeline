"""
Video Assembler — builds long-form video and 3 Shorts from
scene images + narration audio. Burns in captions via Whisper.
Output: 1920x1080 long-form MP4 + 1080x1920 Shorts MP4s
"""

import os
import numpy as np
from PIL import Image as PILImage
import whisper
from moviepy.editor import (
    ImageClip, AudioFileClip, concatenate_videoclips,
    TextClip, CompositeVideoClip
)
from utils import logger

# Patch PIL.ANTIALIAS before MoviePy uses it internally anywhere else
import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

LONG_FORM_SIZE = (1920, 1080)
SHORTS_SIZE    = (1080, 1920)
FPS            = 24
FONT           = "DejaVu-Sans-Bold"
CAPTION_COLOR  = "white"
CAPTION_STROKE = "black"
CAPTION_SIZE   = 52


def assemble_long_form(image_paths, audio_path, story, output_dir):
    logger.info("  Building long-form video...")
    audio = AudioFileClip(audio_path)
    clips = _build_scene_clips(image_paths, story["scenes"], audio.duration, LONG_FORM_SIZE)
    video = concatenate_videoclips(clips, method="compose").set_audio(audio)

    captions = _transcribe_audio(audio_path)
    if captions:
        video = _overlay_captions(video, captions, LONG_FORM_SIZE, ("center", 0.82))

    output_path = os.path.join(output_dir, "long_form.mp4")
    video.write_videofile(output_path, fps=FPS, codec="libx264", audio_codec="aac", logger=None)
    logger.info(f"  Long-form saved: {output_path}")
    return output_path


def assemble_shorts(image_paths, audio_path, story, output_dir):
    logger.info("  Building Shorts...")
    audio      = AudioFileClip(audio_path)
    scenes     = story["scenes"]
    scene_map  = {s["scene_number"]: s for s in scenes}
    image_map  = {i + 1: p for i, p in enumerate(image_paths)}

    time_cursor = 0.0
    scene_times = {}
    for scene in scenes:
        scene_times[scene["scene_number"]] = time_cursor
        time_cursor += scene["duration_seconds"]

    shorts_paths = []
    for short in story["shorts"]:
        short_num  = short["short_number"]
        scene_nums = short["scene_numbers"]

        start_time = scene_times[scene_nums[0]]
        end_time   = min(scene_times[scene_nums[-1]] + scene_map[scene_nums[-1]]["duration_seconds"],
                         audio.duration)

        logger.info(f"    Short {short_num}: scenes {scene_nums} | {start_time:.1f}s–{end_time:.1f}s")

        audio_clip    = audio.subclip(start_time, end_time)
        short_scenes  = [scene_map[n] for n in scene_nums if n in scene_map]
        short_images  = [image_map[n] for n in scene_nums if n in image_map]
        short_duration = end_time - start_time

        clips = _build_scene_clips(short_images, short_scenes, short_duration, SHORTS_SIZE)
        video = concatenate_videoclips(clips, method="compose").set_audio(audio_clip)
        video = CompositeVideoClip([video, _make_hook_overlay(short["hook_text"], SHORTS_SIZE)])

        slice_audio_path = os.path.join(output_dir, f"short_{short_num}_audio.mp3")
        audio_clip.write_audiofile(slice_audio_path, logger=None)
        captions = _transcribe_audio(slice_audio_path)
        if captions:
            video = _overlay_captions(video, captions, SHORTS_SIZE, ("center", 0.78))

        output_path = os.path.join(output_dir, f"short_{short_num}.mp4")
        video.write_videofile(output_path, fps=FPS, codec="libx264", audio_codec="aac", logger=None)
        shorts_paths.append(output_path)
        logger.info(f"    Short {short_num} saved: {output_path}")

    return shorts_paths


# ── Helpers ────────────────────────────────────────────────────────────────

def _build_scene_clips(image_paths, scenes, total_duration, size):
    """
    Load each image with Pillow, resize to target dimensions using LANCZOS,
    convert to numpy array, then wrap in ImageClip.
    This completely bypasses MoviePy's broken .resize() which calls PIL.ANTIALIAS.
    """
    clips = []
    total_scene_secs = sum(s["duration_seconds"] for s in scenes)

    for img_path, scene in zip(image_paths, scenes):
        duration = (scene["duration_seconds"] / total_scene_secs) * total_duration

        # Open → resize → numpy array → ImageClip (no MoviePy resize involved)
        img  = PILImage.open(img_path).convert("RGB")
        img  = img.resize((size[0], size[1]), PILImage.LANCZOS)
        frame = np.array(img)

        clips.append(ImageClip(frame).set_duration(duration))

    return clips


def _transcribe_audio(audio_path):
    try:
        logger.info("    Transcribing with Whisper...")
        model  = whisper.load_model("base")
        result = model.transcribe(audio_path, word_timestamps=True)
        return [{"start": s["start"], "end": s["end"], "text": s["text"].strip()}
                for s in result["segments"]]
    except Exception as e:
        logger.warning(f"    Whisper failed: {e}. Skipping captions.")
        return []


def _overlay_captions(video, captions, size, position=("center", 0.80)):
    clips = [video]
    for seg in captions:
        try:
            txt = (TextClip(seg["text"], fontsize=CAPTION_SIZE, font=FONT,
                            color=CAPTION_COLOR, stroke_color=CAPTION_STROKE,
                            stroke_width=2.5, method="caption",
                            size=(int(size[0] * 0.85), None))
                   .set_start(seg["start"]).set_end(seg["end"])
                   .set_position(position, relative=True))
            clips.append(txt)
        except Exception:
            pass
    return CompositeVideoClip(clips, size=size)


def _make_hook_overlay(hook_text, size, duration=2.5):
    try:
        return (TextClip(hook_text.upper(), fontsize=80, font=FONT,
                         color="yellow", stroke_color="black", stroke_width=3,
                         method="label")
                .set_duration(duration)
                .set_position(("center", 0.12), relative=True))
    except Exception:
        from moviepy.editor import ColorClip
        return ColorClip(size=(1, 1), color=[0, 0, 0], ismask=True).set_duration(duration)
