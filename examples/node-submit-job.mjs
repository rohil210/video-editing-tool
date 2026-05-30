import { readFile } from "node:fs/promises";
import { basename } from "node:path";

const API_BASE_URL = process.env.VIDEO_API_URL ?? "http://127.0.0.1:8000";

async function appendFile(form, fieldName, filePath) {
  if (!filePath) return;
  const bytes = await readFile(filePath);
  form.append(fieldName, new Blob([bytes]), basename(filePath));
}

export async function createVideoJob({
  videoPath,
  videoUrl,
  logoPath,
  startTimestamp,
  endTimestamp,
  clipDuration,
  logoPosition = "bottom_right",
  logoOpacity = 0.85,
  logoScale = 0.18,
  logoPadding = 24,
  logoFadeInSeconds = 0,
  overflowPolicy = "trim",
}) {
  if (!videoPath && !videoUrl) {
    throw new Error("Provide videoPath or videoUrl.");
  }
  if (videoPath && videoUrl) {
    throw new Error("Provide only one of videoPath or videoUrl.");
  }

  const form = new FormData();
  await appendFile(form, "video_file", videoPath);
  await appendFile(form, "logo_file", logoPath);

  if (videoUrl) form.append("video_url", videoUrl);
  form.append("start_timestamp", startTimestamp);
  if (endTimestamp) form.append("end_timestamp", endTimestamp);
  if (clipDuration) form.append("clip_duration", clipDuration);
  form.append("logo_position", logoPosition);
  form.append("logo_opacity", String(logoOpacity));
  form.append("logo_scale", String(logoScale));
  form.append("logo_padding", String(logoPadding));
  form.append("logo_fade_in_seconds", String(logoFadeInSeconds));
  form.append("overflow_policy", overflowPolicy);

  const response = await fetch(`${API_BASE_URL}/jobs`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    throw new Error(`Video job failed to start: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const [, , videoPath, logoPath] = process.argv;
  const job = await createVideoJob({
    videoPath,
    logoPath,
    startTimestamp: "00:03:20",
    clipDuration: "30 seconds",
    logoPosition: "bottom_right",
  });
  console.log(job);
}
