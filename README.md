# Dynamic Video Editing Tool

FastAPI + FFmpeg service for creating custom clips from uploaded videos or public video URLs. It detects video metadata, validates timestamp ranges, extracts a clip, captures the first frame as a thumbnail, and optionally overlays a persistent logo/watermark.

## Features

- Inputs: `mp4`, `mov`, `avi`, `webm`
- Input methods: multipart file upload, direct video URL, public YouTube URL, or public Instagram URL
- Metadata detection: duration, resolution, FPS, audio presence, orientation
- Dynamic clipping by `start_timestamp + clip_duration` or `start_timestamp + end_timestamp`
- First-frame thumbnail export from the clipped segment
- Logo overlay support for `png`, `jpg`, and `svg`
- Logo controls: position, opacity, scale, padding, optional fade-in
- Async-style background job API with downloadable output assets

## Requirements

Install FFmpeg first if you want to use system binaries. Cairo is also needed when uploading SVG logos:

```bash
brew install ffmpeg cairo
```

If system FFmpeg is unavailable, the app falls back to the `static-ffmpeg` Python package and uses its downloaded `ffmpeg` / `ffprobe` binaries.

Then install Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Open the API docs at:

```text
http://127.0.0.1:8000/docs
```

## API

### Health

```bash
curl http://127.0.0.1:8000/health
```

### Detect Metadata

Upload:

```bash
curl -X POST http://127.0.0.1:8000/metadata \
  -F "video_file=@input.mp4"
```

URL:

```bash
curl -X POST http://127.0.0.1:8000/metadata \
  -F "video_url=https://www.youtube.com/watch?v=VIDEO_ID"
```

### Create Clip + Thumbnail + Logo Overlay

```bash
curl -X POST http://127.0.0.1:8000/jobs \
  -F "video_file=@input.mp4" \
  -F "logo_file=@logo.png" \
  -F "start_timestamp=00:03:20" \
  -F "clip_duration=30 seconds" \
  -F "logo_position=bottom_right" \
  -F "logo_opacity=0.85" \
  -F "logo_scale=0.18" \
  -F "logo_padding=24"
```

Alternative clipping mode:

```bash
curl -X POST http://127.0.0.1:8000/jobs \
  -F "video_url=https://www.instagram.com/reel/REEL_ID/" \
  -F "start_timestamp=00:01:10" \
  -F "end_timestamp=00:01:40"
```

YouTube and Instagram downloads use `yt-dlp`. Public links usually work directly. Private, login-gated, age-restricted, or region-blocked links may require cookies; set `YTDLP_COOKIE_FILE=/path/to/cookies.txt` before starting the server.

Poll the job:

```bash
curl http://127.0.0.1:8000/jobs/{job_id}
```

Completed jobs return:

- `clipped_video`: `/assets/{job_id}/clipped_video.mp4`
- `thumbnail`: `/assets/{job_id}/thumbnail.png`
- `watermarked_video`: `/assets/{job_id}/final_video_with_logo.mp4`

## Node.js Client Example

The REST API can be called from any Node service. A dependency-free Node 18+ example is included at `examples/node-submit-job.mjs`:

```bash
VIDEO_API_URL=http://127.0.0.1:8000 node examples/node-submit-job.mjs input.mp4 logo.png
```

## Timestamp Rules

Accepted timestamp formats:

- seconds: `30`, `30.5`, `30 seconds`
- `MM:SS`: `01:10`
- `HH:MM:SS`: `00:03:20`

By default, overflow is trimmed to the available duration. Set `overflow_policy=error` to reject requests that exceed the source video duration.

## Logo Positions

- `top_left`
- `top_right`
- `bottom_left`
- `bottom_right`
- `center`

If no logo is uploaded, the service still generates `final_video_with_logo.mp4` as a copy of the trimmed clip so downstream systems can use a stable output name.

## Test

```bash
pytest
```
