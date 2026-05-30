from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
from functools import lru_cache
from fractions import Fraction
from pathlib import Path

from app.models import ClipRange, LogoPosition, OverflowPolicy, VideoMetadata


class VideoProcessingError(RuntimeError):
    """Raised when ffmpeg or validation cannot complete the requested job."""


@lru_cache(maxsize=1)
def resolve_media_tools() -> tuple[str, str]:
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    if ffmpeg_path and ffprobe_path:
        return ffmpeg_path, ffprobe_path

    try:
        from static_ffmpeg.run import get_or_fetch_platform_executables_else_raise

        return get_or_fetch_platform_executables_else_raise()
    except Exception as exc:
        raise VideoProcessingError(
            "FFmpeg and FFprobe are required for video processing. Install FFmpeg or run "
            "`pip install static-ffmpeg` and allow its binary download."
        ) from exc


def run_command(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "No stderr returned."
        raise VideoProcessingError(stderr)


def parse_timestamp(value: str | int | float, *, field_name: str = "timestamp") -> float:
    if isinstance(value, (int, float)):
        seconds = float(value)
        if seconds < 0:
            raise ValueError(f"{field_name} must be non-negative.")
        return seconds

    text = str(value).strip().lower()
    if not text:
        raise ValueError(f"{field_name} is required.")

    duration_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(s|sec|secs|second|seconds)?", text)
    if duration_match:
        return float(duration_match.group(1))

    parts = text.split(":")
    if len(parts) not in (2, 3):
        raise ValueError(f"{field_name} must be seconds, MM:SS, or HH:MM:SS.")

    try:
        numeric_parts = [float(part) for part in parts]
    except ValueError as exc:
        raise ValueError(f"{field_name} contains an invalid time component.") from exc

    if any(part < 0 for part in numeric_parts):
        raise ValueError(f"{field_name} must be non-negative.")

    if len(parts) == 2:
        minutes, seconds = numeric_parts
        hours = 0.0
    else:
        hours, minutes, seconds = numeric_parts

    if minutes >= 60 or seconds >= 60:
        raise ValueError(f"{field_name} minutes and seconds must be below 60.")

    return hours * 3600 + minutes * 60 + seconds


def format_seconds(seconds: float) -> str:
    return f"{seconds:.3f}".rstrip("0").rstrip(".")


def _parse_fps(raw: str | None) -> float | None:
    if not raw or raw == "0/0":
        return None
    try:
        value = float(Fraction(raw))
    except (ZeroDivisionError, ValueError):
        return None
    if math.isfinite(value) and value > 0:
        return round(value, 3)
    return None


def probe_video(path: Path) -> VideoMetadata:
    _, ffprobe_path = resolve_media_tools()
    command = [
        ffprobe_path,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise VideoProcessingError(result.stderr.strip() or "Unable to read video metadata.")

    payload = json.loads(result.stdout)
    video_stream = next(
        (stream for stream in payload.get("streams", []) if stream.get("codec_type") == "video"),
        None,
    )
    if not video_stream:
        raise VideoProcessingError("Input does not contain a video stream.")

    duration = (
        video_stream.get("duration")
        or payload.get("format", {}).get("duration")
        or 0
    )
    width = int(video_stream.get("width") or 0)
    height = int(video_stream.get("height") or 0)
    rotation = int(float(video_stream.get("tags", {}).get("rotate", 0) or 0))
    if abs(rotation) in (90, 270):
        width, height = height, width

    if width > height:
        orientation = "horizontal"
    elif height > width:
        orientation = "vertical"
    else:
        orientation = "square"

    has_audio = any(stream.get("codec_type") == "audio" for stream in payload.get("streams", []))

    return VideoMetadata(
        duration_seconds=round(float(duration), 3),
        width=width,
        height=height,
        fps=_parse_fps(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate")),
        has_audio=has_audio,
        orientation=orientation,
        format_name=payload.get("format", {}).get("format_name"),
    )


def validate_clip_range(
    *,
    total_duration: float,
    start_timestamp: str | int | float,
    end_timestamp: str | int | float | None = None,
    clip_duration: str | int | float | None = None,
    overflow_policy: OverflowPolicy = OverflowPolicy.trim,
) -> ClipRange:
    start = parse_timestamp(start_timestamp, field_name="start_timestamp")
    if start >= total_duration:
        raise ValueError("start_timestamp must be before the end of the video.")

    if end_timestamp is None and clip_duration is None:
        raise ValueError("Provide either end_timestamp or clip_duration.")
    if end_timestamp is not None and clip_duration is not None:
        raise ValueError("Provide only one of end_timestamp or clip_duration.")

    if clip_duration is not None:
        requested_duration = parse_timestamp(clip_duration, field_name="clip_duration")
        if requested_duration <= 0:
            raise ValueError("clip_duration must be greater than zero.")
        end = start + requested_duration
    else:
        end = parse_timestamp(end_timestamp, field_name="end_timestamp")
        if end <= start:
            raise ValueError("end_timestamp must be after start_timestamp.")

    if end > total_duration:
        if overflow_policy == OverflowPolicy.error:
            raise ValueError("Requested clip exceeds the source video duration.")
        end = total_duration

    duration = end - start
    if duration <= 0:
        raise ValueError("Validated clip duration must be greater than zero.")

    return ClipRange(
        start_seconds=round(start, 3),
        end_seconds=round(end, 3),
        duration_seconds=round(duration, 3),
    )


def extract_clip(source: Path, output: Path, clip: ClipRange) -> None:
    ffmpeg_path, _ = resolve_media_tools()
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg_path,
        "-y",
        "-ss",
        format_seconds(clip.start_seconds),
        "-i",
        str(source),
        "-t",
        format_seconds(clip.duration_seconds),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output),
    ]
    run_command(command)


def extract_thumbnail(clip_path: Path, output: Path) -> None:
    ffmpeg_path, _ = resolve_media_tools()
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(clip_path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(output),
    ]
    run_command(command)


def normalize_logo(logo_path: Path, work_dir: Path) -> Path:
    if logo_path.suffix.lower() != ".svg":
        return logo_path
    output = work_dir / "logo-normalized.png"
    try:
        import cairosvg

        cairosvg.svg2png(url=str(logo_path), write_to=str(output))
    except (ImportError, OSError) as exc:
        raise VideoProcessingError(
            "SVG logo conversion requires Cairo libraries. Install cairo or upload a PNG/JPG logo."
        ) from exc
    return output


def _overlay_position(position: LogoPosition, padding: int) -> tuple[str, str]:
    pad = str(max(0, padding))
    return {
        LogoPosition.top_left: (pad, pad),
        LogoPosition.top_right: (f"main_w-overlay_w-{pad}", pad),
        LogoPosition.bottom_left: (pad, f"main_h-overlay_h-{pad}"),
        LogoPosition.bottom_right: (f"main_w-overlay_w-{pad}", f"main_h-overlay_h-{pad}"),
        LogoPosition.center: ("(main_w-overlay_w)/2", "(main_h-overlay_h)/2"),
    }[position]


def apply_logo_overlay(
    *,
    clip_path: Path,
    logo_path: Path | None,
    output: Path,
    position: LogoPosition = LogoPosition.bottom_right,
    opacity: float = 0.85,
    logo_scale: float = 0.18,
    padding: int = 24,
    fade_in_seconds: float = 0.0,
) -> None:
    ffmpeg_path, _ = resolve_media_tools()
    output.parent.mkdir(parents=True, exist_ok=True)
    if logo_path is None:
        shutil.copyfile(clip_path, output)
        return

    opacity = min(max(opacity, 0.0), 1.0)
    logo_scale = min(max(logo_scale, 0.02), 1.0)
    fade_in_seconds = max(fade_in_seconds, 0.0)
    normalized_logo = normalize_logo(logo_path, output.parent)
    x_expr, y_expr = _overlay_position(position, padding)

    logo_filters = f"format=rgba,colorchannelmixer=aa={opacity}"
    if fade_in_seconds:
        logo_filters += f",fade=t=in:st=0:d={format_seconds(fade_in_seconds)}:alpha=1"

    filter_complex = (
        f"[1:v]{logo_filters}[logo0];"
        f"[logo0][0:v]scale2ref=w=main_w*{logo_scale}:h=-1[logo][base];"
        f"[base][logo]overlay=x={x_expr}:y={y_expr}:format=auto,format=yuv420p[vout]"
    )
    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(clip_path),
        "-loop",
        "1",
        "-i",
        str(normalized_logo),
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-c:a",
        "copy",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output),
    ]
    run_command(command)
