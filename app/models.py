from __future__ import annotations

from enum import Enum
from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field


class LogoPosition(str, Enum):
    top_left = "top_left"
    top_right = "top_right"
    bottom_left = "bottom_left"
    bottom_right = "bottom_right"
    center = "center"


class OverflowPolicy(str, Enum):
    trim = "trim"
    error = "error"


class VideoMetadata(BaseModel):
    duration_seconds: float
    width: int
    height: int
    fps: Optional[float]
    has_audio: bool
    orientation: Literal["horizontal", "vertical", "square"]
    format_name: Optional[str] = None


class ClipRange(BaseModel):
    start_seconds: float
    end_seconds: float
    duration_seconds: float


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    message: Optional[str] = None
    metadata: Optional[VideoMetadata] = None
    clip: Optional[ClipRange] = None
    outputs: Dict[str, str] = Field(default_factory=dict)
