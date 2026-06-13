"""
media_processor.py — 
All image and video processing: resize, compress, format conversion.
Runs in a thread pool so it never blocks the async event loop.
"""

import os
import json
import logging
import subprocess
from typing import Optional

from PIL import Image, ImageOps

from config import CONFIG

logger = logging.getLogger(__name__)

# ── Supported output formats ───────────────────────────────────────────────────
IMAGE_FORMATS: dict[str, tuple[str, str]] = {
    # key : (PIL save format, file extension)
    "jpg":  ("JPEG", ".jpg"),
    "png":  ("PNG",  ".png"),
    "webp": ("WEBP", ".webp"),
}

VIDEO_FORMATS: dict[str, tuple[str, str, str]] = {
    # key : (video_codec, file extension, container label)
    "mp4": ("libx264", ".mp4", "MP4"),
    "avi": ("libxvid", ".avi", "AVI"),
    "mkv": ("libx264", ".mkv", "MKV"),
}

# ── Extension → format key mappings (for "Keep Original") ──────────────────────
EXT_TO_IMAGE_FORMAT: dict[str, str] = {
    ".jpg":  "jpg",
    ".jpeg": "jpg",
    ".png":  "png",
    ".webp": "webp",
}

EXT_TO_VIDEO_FORMAT: dict[str, str] = {
    ".mp4":  "mp4",
    ".mov":  "mp4",
    ".avi":  "avi",
    ".mkv":  "mkv",
    ".webm": "mp4",
}


# ── FFprobe helpers ────────────────────────────────────────────────────────────
def get_video_info(input_path: str) -> Optional[dict]:
    """Return ffprobe JSON dict or None on failure."""
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            input_path,
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, check=True
        )
        return json.loads(result.stdout)
    except Exception as exc:
        logger.error(f"ffprobe error: {exc}")
        return None


def has_audio_stream(info: dict) -> bool:
    if not info:
        return False
    return any(s.get("codec_type") == "audio" for s in info.get("streams", []))


# ── Image processor ────────────────────────────────────────────────────────────
def process_image_sync(
    input_path:    str,
    output_path:   str,
    width:         int,
    height:        int,
    mode:          str,   # "pad" | "stretch" | "compress"
    output_format: str = "jpg",
    compress:      bool = False,
    img_quality:   int = None,
) -> None:
    """
    Resize / compress / convert an image.
    Raises on failure so the caller can catch and report.
    """
    pil_fmt, _ = IMAGE_FORMATS.get(output_format, ("JPEG", ".jpg"))

    with Image.open(input_path) as img:
        # Fix EXIF orientation
        img = ImageOps.exif_transpose(img)

        # Flatten transparency onto white
        if img.mode in ("RGBA", "PA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img.convert("RGB"), mask=img.split()[-1])
            img = bg
        elif img.mode in ("LA",):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img.convert("RGB"), mask=img.split()[1])
            img = bg
        elif img.mode == "P":
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img.convert("RGB"), mask=img.split()[-1])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize
        if mode == "compress":
            result = img                                                # no resize
        elif mode == "pad":
            result = ImageOps.pad(
                img, (width, height), color=(0, 0, 0), centering=(0.5, 0.5)
            )
        else:  # stretch
            result = img.resize((width, height), Image.Resampling.LANCZOS)

        # Quality / compression settings
        use_compress = compress or (mode == "compress")
        if img_quality is None:
            img_quality = CONFIG["compress_image_quality"]
        quality = img_quality if use_compress else 92

        save_kwargs: dict = {"optimize": True}
        if pil_fmt == "JPEG":
            save_kwargs["quality"] = quality
            save_kwargs["subsampling"] = 0
        elif pil_fmt == "PNG":
            save_kwargs["compress_level"] = 9 if use_compress else 6
        elif pil_fmt == "WEBP":
            save_kwargs["quality"] = quality
            save_kwargs["method"] = 6

        result.save(output_path, format=pil_fmt, **save_kwargs)

    logger.info(
        f"Image saved → {output_path}  "
        f"({os.path.getsize(output_path) / 1024:.1f} KB)"
    )


# ── Video processor ────────────────────────────────────────────────────────────
def process_video_sync(
    input_path:    str,
    output_path:   str,
    width:         int,
    height:        int,
    mode:          str,   # "pad" | "stretch" | "compress"
    output_format: str = "mp4",
    compress:      bool = False,
    video_crf:     int = None,
    compress_crf:  int = None,
    video_preset:  str = None,
    max_bitrate:   str = None,
    timeout:       int = None,
) -> None:
    """
    Resize / compress / convert a video via FFmpeg.
    Raises on failure so the caller can catch and report.
    """
    info      = get_video_info(input_path)
    has_audio = has_audio_stream(info) if info else True

    codec, _, _ = VIDEO_FORMATS.get(output_format, ("libx264", ".mp4", "MP4"))
    use_compress = compress or (mode == "compress")
    if video_crf is None:
        video_crf = CONFIG["video_crf"]
    if compress_crf is None:
        compress_crf = CONFIG["compress_video_crf"]
    if video_preset is None:
        video_preset = CONFIG["video_preset"]
    if max_bitrate is None:
        max_bitrate = CONFIG["max_video_bitrate"]
    crf = compress_crf if use_compress else video_crf

    # Video filter
    if mode == "compress":
        vf = None
    elif mode == "pad":
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"setsar=1"
        )
    else:  # stretch
        vf = f"scale={width}:{height},setsar=1"

    # Build command
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", input_path]

    if vf:
        cmd += ["-vf", vf]

    if codec == "libxvid":
        q_val = max(1, int(crf * 31 / 51))  # map CRF range to XVid qscale
        cmd += ["-c:v", "libxvid", "-qscale:v", str(q_val)]
    else:
        cmd += [
            "-c:v", codec,
            "-preset", video_preset,
            "-crf", str(crf),
            "-maxrate", max_bitrate,
            "-bufsize", "10M",
            "-pix_fmt", "yuv420p",
        ]
        # faststart only for MP4
        if output_format == "mp4":
            cmd += ["-movflags", "+faststart"]

    if has_audio:
        cmd += ["-c:a", "aac", "-b:a", "128k", "-ac", "2"]
    else:
        cmd.append("-an")

    cmd.append(output_path)

    logger.info(f"FFmpeg: {' '.join(cmd)}")

    if timeout is None:
        timeout = CONFIG["process_timeout"]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )

    if result.returncode != 0:
        snippet = (result.stderr or "unknown FFmpeg error")[:400]
        raise RuntimeError(f"FFmpeg exited {result.returncode}: {snippet}")

    if not os.path.exists(output_path):
        raise RuntimeError("FFmpeg produced no output file")

    size_bytes = os.path.getsize(output_path)
    if size_bytes < 512:
        raise RuntimeError(f"Output file suspiciously small ({size_bytes} B)")

    logger.info(
        f"Video saved → {output_path}  "
        f"({size_bytes / 1024 / 1024:.2f} MB)"
    )
