"""
Video Assembler — builds the long-form video and 3 Shorts from
scene images + narration audio. Adds burned-in captions via Whisper.
Output: 1920x1080 long-form MP4 + 1080x1920 Shorts MP4s
"""

import os
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
import json
import subprocess
import whisper
from moviepy.editor import (
    ImageClip, AudioFileClip, concatenate_videoclips,
    TextClip, CompositeVideoClip
)
from utils import logger

# Video specs
LONG_FORM_SIZE  = (1920, 1080)   # 16:9 horizontal
SHORTS_SIZE     = (1080, 1920)   # 9:16 vertical
FPS             = 24
FONT            = "DejaVu-Sans-Bold"
CAPTION_COLOR   = "white"
CAPTION_STROKE  = "black"
CAPTION_SIZE    = 52             # px — readable on mobile


def assemble_long_form(image_paths: list, audio_path: str,
                       story: dict, output_dir: str) -> str:
    """
    Build a 16:9 long-form video from all scenes + full audio.
    Captions are transcribed from audio and burned in.
    """
    logger.info("  Building long-form video...")
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration

    scenes = story["scenes"]
    clips = _build_scene_clips(image_paths, scenes, total_duration, LONG_FORM_SIZE)

    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(audio)

    # Add captions
    captions = _transcribe_audio(audio_path)
    if captions:
        video = _overlay_captions(video, captions, LONG_FORM_SIZE, position=("center", 0.82))

    output_path = os.path.join(output_dir, "long_form.mp4")
    video.write_videofile(
        output_path, fps=FPS, codec="libx264",
        audio_codec="aac", logger=None
    )
    logger.info(f"  Long-form saved: {output_path}")
    return output_path


def assemble_shorts(image_paths: list, audio_path: str,
                    story: dict, output_dir: str) -> list:
    """
    Build 3 Shorts (9:16) from scene groups defined in story['shorts'].
    Each Short has its own audio slice and captions.
    """
    logger.info("  Building Shorts...")
    audio = AudioFileClip(audio_path)
    scenes = story["scenes"]
    scene_map = {s["scene_number"]: s for s in scenes}
    image_map = {i + 1: p for i, p in enumerate(image_paths)}

    # Build cumulative scene start times from durations
    time_cursor = 0.0
    scene_times = {}
    for scene in scenes:
        scene_times[scene["scene_number"]] = time_cursor
        time_cursor += scene["duration_seconds"]

    shorts_paths = []
    for short in story["shorts"]:
        short_num = short["short_number"]
        scene_nums = short["scene_numbers"]

        start_time = scene_times[scene_nums[0]]
        end_scene = scene_map[scene_nums[-1]]
        end_time = scene_times[scene_nums[-1]] + end_scene["duration_seconds"]
        end_time = min(end_time, audio.duration)

        logger.info(f"    Short {short_num}: scenes {scene_nums} | {start_time:.1f}s–{end_time:.1f}s")

        # Slice audio
        audio_clip = audio.subclip(start_time, end_time)

        # Build clips for these scenes
        short_scenes = [scene_map[n] for n in scene_nums if n in scene_map]
        short_images = [image_map[n] for n in scene_nums if n in image_map]
        short_duration = end_time - start_time

        clips = _build_scene_clips(short_images, short_scenes, short_duration, SHORTS_SIZE)
        video = concatenate_videoclips(clips, method="compose").set_audio(audio_clip)

        # Add hook text overlay (first 2 seconds)
        hook_clip = _make_hook_overlay(short["hook_text"], SHORTS_SIZE, duration=2.5)
        video = CompositeVideoClip([video, hook_clip])

        # Transcribe and caption this slice
        slice_audio_path = os.path.join(output_dir, f"short_{short_num}_audio.mp3")
        audio_clip.write_audiofile(slice_audio_path, logger=None)
        captions = _transcribe_audio(slice_audio_path)
        if captions:
            video = _overlay_captions(video, captions, SHORTS_SIZE, position=("center", 0.78))

        output_path = os.path.join(output_dir, f"short_{short_num}.mp4")
        video.write_videofile(
            output_path, fps=FPS, codec="libx264",
            audio_codec="aac", logger=None
        )
        shorts_paths.append(output_path)
        logger.info(f"    Short {short_num} saved: {output_path}")

    return shorts_paths


# ── Helpers ────────────────────────────────────────────────────────────────

def _build_scene_clips(image_paths, scenes, total_duration, size):
    """Build ImageClips, distributing duration proportionally."""
    clips = []
    total_scene_secs = sum(s["duration_seconds"] for s in scenes)

    for i, (img_path, scene) in enumerate(zip(image_paths, scenes)):
        # Scale each scene's duration to fit total audio length
        duration = (scene["duration_seconds"] / total_scene_secs) * total_duration

        clip = (ImageClip(img_path)
                .set_duration(duration)
                .resize(size))
        clips.append(clip)
    return clips


def _transcribe_audio(audio_path: str) -> list:
    """
    Use Whisper (local, free) to transcribe audio into timed word segments.
    Returns list of {"start", "end", "text"} dicts.
    """
    try:
        logger.info("    Transcribing audio with Whisper...")
        model = whisper.load_model("base")  # ~140MB, fast enough for CI
        result = model.transcribe(audio_path, word_timestamps=True)

        segments = []
        for seg in result["segments"]:
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip()
            })
        return segments
    except Exception as e:
        logger.warning(f"    Whisper transcription failed: {e}. Skipping captions.")
        return []


def _overlay_captions(video, captions, size, position=("center", 0.80)):
    """Burn subtitle segments onto the video as styled TextClips."""
    caption_clips = [video]
    for seg in captions:
        try:
            txt = TextClip(
                seg["text"],
                fontsize=CAPTION_SIZE,
                font=FONT,
                color=CAPTION_COLOR,
                stroke_color=CAPTION_STROKE,
                stroke_width=2.5,
                method="caption",
                size=(int(size[0] * 0.85), None)  # 85% width, auto height
            )
            txt = (txt
                   .set_start(seg["start"])
                   .set_end(seg["end"])
                   .set_position(position, relative=True))
            caption_clips.append(txt)
        except Exception:
            pass  # Skip malformed segments
    return CompositeVideoClip(caption_clips, size=size)


def _make_hook_overlay(hook_text: str, size: tuple, duration: float = 2.5):
    """Big bold hook text for the first few seconds of a Short."""
    try:
        clip = TextClip(
            hook_text.upper(),
            fontsize=80,
            font=FONT,
            color="yellow",
            stroke_color="black",
            stroke_width=3,
            method="label"
        ).set_duration(duration).set_position(("center", 0.12), relative=True)
        return clip
    except Exception:
        return ImageClip(
            "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
            duration=duration
        )
