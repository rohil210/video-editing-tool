from __future__ import annotations

from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from app.config import OUTPUT_DIR, ensure_storage
from app.models import JobStatus, LogoPosition, OverflowPolicy
from app.storage import resolve_video_input, save_logo_upload
from app.ui import INDEX_HTML
from app.video_processing import (
    VideoProcessingError,
    apply_logo_overlay,
    extract_clip,
    extract_thumbnail,
    probe_video,
    validate_clip_range,
)

app = FastAPI(
    title="Dynamic Video Editing Tool",
    description="Extract custom video clips, thumbnails, and branded logo overlays.",
    version="1.0.0",
)

jobs: dict[str, JobStatus] = {}


@app.on_event("startup")
def startup() -> None:
    ensure_storage()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return INDEX_HTML


@app.post("/metadata", response_model=dict)
async def metadata(
    video_file: Optional[UploadFile] = File(default=None),
    video_url: Optional[str] = Form(default=None),
) -> dict:
    ensure_storage()
    source = await resolve_video_input(video_file, video_url)
    try:
        return {"metadata": probe_video(source).model_dump()}
    except VideoProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _asset_url(job_id: str, filename: str) -> str:
    return f"/assets/{job_id}/{filename}"


def process_job(
    *,
    job_id: str,
    source_path: Path,
    logo_path: Optional[Path],
    start_timestamp: str,
    end_timestamp: Optional[str],
    clip_duration: Optional[str],
    overflow_policy: OverflowPolicy,
    logo_position: LogoPosition,
    logo_opacity: float,
    logo_scale: float,
    logo_padding: int,
    logo_fade_in_seconds: float,
) -> None:
    job = jobs[job_id]
    job.status = "processing"
    job.message = "Processing video."

    try:
        metadata = probe_video(source_path)
        clip = validate_clip_range(
            total_duration=metadata.duration_seconds,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            clip_duration=clip_duration,
            overflow_policy=overflow_policy,
        )
        job.metadata = metadata
        job.clip = clip

        job_dir = OUTPUT_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        clipped_path = job_dir / "clipped_video.mp4"
        thumbnail_path = job_dir / "thumbnail.png"
        final_path = job_dir / "final_video_with_logo.mp4"

        extract_clip(source_path, clipped_path, clip)
        extract_thumbnail(clipped_path, thumbnail_path)
        apply_logo_overlay(
            clip_path=clipped_path,
            logo_path=logo_path,
            output=final_path,
            position=logo_position,
            opacity=logo_opacity,
            logo_scale=logo_scale,
            padding=logo_padding,
            fade_in_seconds=logo_fade_in_seconds,
        )

        job.status = "completed"
        job.message = "Processing completed."
        job.outputs = {
            "clipped_video": _asset_url(job_id, clipped_path.name),
            "thumbnail": _asset_url(job_id, thumbnail_path.name),
            "watermarked_video": _asset_url(job_id, final_path.name),
        }
    except (ValueError, VideoProcessingError) as exc:
        job.status = "failed"
        job.message = str(exc)
    except Exception as exc:  # pragma: no cover - defensive boundary for background tasks
        job.status = "failed"
        job.message = f"Unexpected processing error: {exc}"


@app.post("/jobs", response_model=JobStatus)
async def create_job(
    background_tasks: BackgroundTasks,
    video_file: Optional[UploadFile] = File(default=None),
    logo_file: Optional[UploadFile] = File(default=None),
    video_url: Optional[str] = Form(default=None),
    start_timestamp: str = Form(...),
    end_timestamp: Optional[str] = Form(default=None),
    clip_duration: Optional[str] = Form(default=None),
    overflow_policy: OverflowPolicy = Form(default=OverflowPolicy.trim),
    logo_position: LogoPosition = Form(default=LogoPosition.bottom_right),
    logo_opacity: float = Form(default=0.85, ge=0.0, le=1.0),
    logo_scale: float = Form(default=0.18, ge=0.02, le=1.0),
    logo_padding: int = Form(default=24, ge=0),
    logo_fade_in_seconds: float = Form(default=0.0, ge=0.0),
) -> JobStatus:
    ensure_storage()
    source_path = await resolve_video_input(video_file, video_url)
    logo_path = await save_logo_upload(logo_file)

    job_id = uuid4().hex
    jobs[job_id] = JobStatus(job_id=job_id, status="queued", message="Job queued.")
    background_tasks.add_task(
        process_job,
        job_id=job_id,
        source_path=source_path,
        logo_path=logo_path,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        clip_duration=clip_duration,
        overflow_policy=overflow_policy,
        logo_position=logo_position,
        logo_opacity=logo_opacity,
        logo_scale=logo_scale,
        logo_padding=logo_padding,
        logo_fade_in_seconds=logo_fade_in_seconds,
    )
    return jobs[job_id]


@app.get("/jobs/{job_id}", response_model=JobStatus)
def get_job(job_id: str) -> JobStatus:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@app.get("/assets/{job_id}/{filename}")
def get_asset(job_id: str, filename: str) -> FileResponse:
    if filename not in {"clipped_video.mp4", "thumbnail.png", "final_video_with_logo.mp4"}:
        raise HTTPException(status_code=404, detail="Asset not found.")
    path = OUTPUT_DIR / job_id / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Asset not found.")
    return FileResponse(path)
