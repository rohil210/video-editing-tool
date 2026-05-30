from __future__ import annotations

import asyncio
import os
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from fastapi import HTTPException, UploadFile

from app.config import (
    ALLOWED_LOGO_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    INPUT_DIR,
    LOGO_DIR,
    MAX_DOWNLOAD_BYTES,
)
from app.video_processing import VideoProcessingError, resolve_media_tools


def _safe_extension(filename: str, allowed: set[str], label: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported {label} format: {suffix or 'missing extension'}.")
    return suffix


def _url_suffix(video_url: str) -> str:
    return Path(urlparse(video_url).path).suffix.lower()


def _is_direct_video_url(video_url: str) -> bool:
    return _url_suffix(video_url) in ALLOWED_VIDEO_EXTENSIONS


async def save_upload(upload: UploadFile, *, directory: Path, allowed: set[str], label: str) -> Path:
    suffix = _safe_extension(upload.filename or "", allowed, label)
    output = directory / f"{uuid4().hex}{suffix}"
    with output.open("wb") as file:
        while chunk := await upload.read(1024 * 1024):
            file.write(chunk)
    return output


async def save_video_upload(upload: UploadFile) -> Path:
    return await save_upload(upload, directory=INPUT_DIR, allowed=ALLOWED_VIDEO_EXTENSIONS, label="video")


async def save_logo_upload(upload: UploadFile | None) -> Path | None:
    if upload is None:
        return None
    return await save_upload(upload, directory=LOGO_DIR, allowed=ALLOWED_LOGO_EXTENSIONS, label="logo")


async def download_video(video_url: str) -> Path:
    parsed = urlparse(video_url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="video_url must be an http or https URL.")
    if not _is_direct_video_url(video_url):
        return await download_platform_video(video_url)

    suffix = _safe_extension(parsed.path, ALLOWED_VIDEO_EXTENSIONS, "video")
    output = INPUT_DIR / f"{uuid4().hex}{suffix}"

    total = 0
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
            async with client.stream("GET", video_url) as response:
                response.raise_for_status()
                with output.open("wb") as file:
                    async for chunk in response.aiter_bytes(1024 * 1024):
                        total += len(chunk)
                        if total > MAX_DOWNLOAD_BYTES:
                            output.unlink(missing_ok=True)
                            raise HTTPException(status_code=413, detail="Video download exceeds the configured size limit.")
                        file.write(chunk)
    except httpx.HTTPError as exc:
        output.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Unable to download video URL: {exc}") from exc

    return output


def _download_platform_video_sync(video_url: str) -> Path:
    try:
        from yt_dlp import YoutubeDL
        from yt_dlp.utils import DownloadError
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="YouTube/Instagram URL support requires yt-dlp. Run `pip install -r requirements.txt`.",
        ) from exc

    ffmpeg_path, _ = resolve_media_tools()
    output_id = uuid4().hex
    output_template = str(INPUT_DIR / f"{output_id}.%(ext)s")
    cookie_file = os.getenv("YTDLP_COOKIE_FILE")
    options = {
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/best",
        "merge_output_format": "mp4",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "ffmpeg_location": str(Path(ffmpeg_path).parent),
        "restrictfilenames": True,
    }
    if cookie_file:
        options["cookiefile"] = cookie_file

    try:
        with YoutubeDL(options) as ydl:
            ydl.download([video_url])
    except DownloadError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to extract this video URL. Public YouTube and Instagram links are supported; "
                "private, login-gated, age-restricted, or region-blocked videos may require cookies."
            ),
        ) from exc
    except VideoProcessingError:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to download video URL: {exc}") from exc

    candidates = sorted(
        path for path in INPUT_DIR.glob(f"{output_id}.*") if path.suffix.lower() in ALLOWED_VIDEO_EXTENSIONS
    )
    if not candidates:
        raise HTTPException(status_code=400, detail="The URL did not produce a supported video file.")

    output = next((path for path in candidates if path.suffix.lower() == ".mp4"), candidates[0])
    if output.stat().st_size > MAX_DOWNLOAD_BYTES:
        output.unlink(missing_ok=True)
        raise HTTPException(status_code=413, detail="Video download exceeds the configured size limit.")
    return output


async def download_platform_video(video_url: str) -> Path:
    return await asyncio.to_thread(_download_platform_video_sync, video_url)


async def resolve_video_input(video_file: UploadFile | None, video_url: str | None) -> Path:
    if video_file and video_url:
        raise HTTPException(status_code=400, detail="Provide either video_file or video_url, not both.")
    if video_file:
        return await save_video_upload(video_file)
    if video_url:
        return await download_video(video_url)
    raise HTTPException(status_code=400, detail="Provide a video_file upload or video_url.")
