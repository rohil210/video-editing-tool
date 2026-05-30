INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dynamic Video Editing Tool</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --panel-soft: #eef2f6;
      --text: #17202a;
      --muted: #647181;
      --line: #d8dee6;
      --accent: #167a72;
      --accent-strong: #0f5f59;
      --danger: #b42318;
      --shadow: 0 16px 38px rgba(30, 42, 54, 0.12);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }

    header {
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.92);
      backdrop-filter: blur(10px);
      position: sticky;
      top: 0;
      z-index: 5;
    }

    .topbar,
    main {
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
    }

    .topbar {
      min-height: 64px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
    }

    h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 760;
    }

    .docs-link {
      color: var(--accent-strong);
      font-size: 14px;
      font-weight: 650;
      text-decoration: none;
    }

    main {
      display: grid;
      grid-template-columns: minmax(0, 1.08fr) minmax(340px, 0.72fr);
      gap: 22px;
      padding: 28px 0 44px;
    }

    section {
      min-width: 0;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }

    .form-panel {
      padding: 22px;
    }

    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }

    h2 {
      margin: 0;
      font-size: 16px;
      font-weight: 760;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }

    .field,
    .wide {
      display: flex;
      flex-direction: column;
      gap: 7px;
    }

    .wide {
      grid-column: 1 / -1;
    }

    label {
      font-size: 13px;
      font-weight: 680;
      color: #28323f;
    }

    input,
    select {
      width: 100%;
      height: 42px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      color: var(--text);
      padding: 0 12px;
      font: inherit;
      font-size: 14px;
      outline: none;
    }

    input[type="file"] {
      padding: 8px 10px;
    }

    input:focus,
    select:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(22, 122, 114, 0.16);
    }

    .toggle {
      display: inline-grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 4px;
      background: var(--panel-soft);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 4px;
    }

    .toggle button {
      border: 0;
      border-radius: 6px;
      background: transparent;
      color: var(--muted);
      padding: 8px 12px;
      font: inherit;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
    }

    .toggle button.active {
      background: #fff;
      color: var(--text);
      box-shadow: 0 1px 4px rgba(23, 32, 42, 0.12);
    }

    .actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 12px;
      margin-top: 20px;
    }

    .button {
      border: 0;
      border-radius: 7px;
      height: 42px;
      padding: 0 16px;
      background: var(--accent);
      color: #fff;
      font: inherit;
      font-size: 14px;
      font-weight: 760;
      cursor: pointer;
    }

    .button:hover {
      background: var(--accent-strong);
    }

    .button.secondary {
      background: #e7ecef;
      color: #1d2732;
    }

    .button:disabled {
      cursor: not-allowed;
      opacity: 0.58;
    }

    .status-panel {
      padding: 18px;
      position: sticky;
      top: 88px;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      padding: 0 10px;
      border-radius: 999px;
      background: #e8f4f2;
      color: var(--accent-strong);
      font-size: 13px;
      font-weight: 780;
      text-transform: capitalize;
    }

    .status-pill.failed {
      background: #fdecec;
      color: var(--danger);
    }

    .status-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      margin-top: 14px;
      background: #fbfcfd;
    }

    .status-card p,
    .meta-list p {
      margin: 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }

    .meta-list {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 14px;
    }

    .meta-item {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 10px;
      min-height: 64px;
    }

    .meta-item b {
      display: block;
      margin-bottom: 3px;
      font-size: 12px;
      color: var(--muted);
    }

    .meta-item span {
      font-size: 15px;
      font-weight: 740;
    }

    .outputs {
      display: grid;
      gap: 10px;
      margin-top: 14px;
    }

    .asset-link {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      min-height: 42px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--text);
      padding: 0 12px;
      text-decoration: none;
      font-size: 14px;
      font-weight: 700;
    }

    .thumb {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      margin-top: 14px;
      display: none;
      background: #eef2f6;
    }

    .error {
      color: var(--danger);
      font-weight: 680;
    }

    .hidden {
      display: none;
    }

    @media (max-width: 860px) {
      main {
        grid-template-columns: 1fr;
      }

      .status-panel {
        position: static;
      }

      .grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <h1>Dynamic Video Editing Tool</h1>
      <a class="docs-link" href="/docs">API Docs</a>
    </div>
  </header>

  <main>
    <section class="panel form-panel">
      <div class="panel-header">
        <h2>Clip Builder</h2>
        <div class="toggle" aria-label="Input source">
          <button type="button" id="fileMode" class="active">Upload</button>
          <button type="button" id="urlMode">URL</button>
        </div>
      </div>

      <form id="jobForm">
        <div class="grid">
          <div class="field wide" id="fileField">
            <label for="videoFile">Video File</label>
            <input id="videoFile" name="video_file" type="file" accept=".mp4,.mov,.avi,.webm,video/mp4,video/quicktime,video/x-msvideo,video/webm">
          </div>

          <div class="field wide hidden" id="urlField">
            <label for="videoUrl">Video URL</label>
            <input id="videoUrl" name="video_url" type="url" placeholder="YouTube, Instagram, or direct video URL">
          </div>

          <div class="field">
            <label for="startTimestamp">Start Timestamp</label>
            <input id="startTimestamp" name="start_timestamp" required placeholder="00:03:20">
          </div>

          <div class="field">
            <label for="rangeMode">Clip Mode</label>
            <select id="rangeMode">
              <option value="duration">Duration</option>
              <option value="end">End timestamp</option>
            </select>
          </div>

          <div class="field" id="durationField">
            <label for="clipDuration">Clip Duration</label>
            <input id="clipDuration" name="clip_duration" placeholder="30 seconds">
          </div>

          <div class="field hidden" id="endField">
            <label for="endTimestamp">End Timestamp</label>
            <input id="endTimestamp" name="end_timestamp" placeholder="00:03:50">
          </div>

          <div class="field">
            <label for="overflowPolicy">Overflow</label>
            <select id="overflowPolicy" name="overflow_policy">
              <option value="trim">Trim to available video</option>
              <option value="error">Return validation error</option>
            </select>
          </div>

          <div class="field">
            <label for="logoFile">Logo</label>
            <input id="logoFile" name="logo_file" type="file" accept=".png,.jpg,.jpeg,.svg,image/png,image/jpeg,image/svg+xml">
          </div>

          <div class="field">
            <label for="logoPosition">Logo Position</label>
            <select id="logoPosition" name="logo_position">
              <option value="bottom_right">Bottom Right</option>
              <option value="bottom_left">Bottom Left</option>
              <option value="top_right">Top Right</option>
              <option value="top_left">Top Left</option>
              <option value="center">Center</option>
            </select>
          </div>

          <div class="field">
            <label for="logoOpacity">Logo Opacity</label>
            <input id="logoOpacity" name="logo_opacity" type="number" min="0" max="1" step="0.05" value="0.85">
          </div>

          <div class="field">
            <label for="logoScale">Logo Scale</label>
            <input id="logoScale" name="logo_scale" type="number" min="0.02" max="1" step="0.01" value="0.18">
          </div>

          <div class="field">
            <label for="logoPadding">Logo Padding</label>
            <input id="logoPadding" name="logo_padding" type="number" min="0" step="1" value="24">
          </div>

          <div class="field">
            <label for="logoFade">Logo Fade In</label>
            <input id="logoFade" name="logo_fade_in_seconds" type="number" min="0" step="0.1" value="0">
          </div>
        </div>

        <div class="actions">
          <button type="button" class="button secondary" id="metadataButton">Detect Metadata</button>
          <button type="submit" class="button" id="submitButton">Create Clip</button>
        </div>
      </form>
    </section>

    <aside class="panel status-panel">
      <div class="panel-header">
        <h2>Job Status</h2>
        <span class="status-pill" id="statusPill">Ready</span>
      </div>
      <div class="status-card">
        <p id="message">Select a video and create a clip.</p>
      </div>
      <div class="meta-list" id="metadata"></div>
      <img id="thumbnail" class="thumb" alt="Clip thumbnail">
      <div class="outputs" id="outputs"></div>
    </aside>
  </main>

  <script>
    const fileMode = document.getElementById("fileMode");
    const urlMode = document.getElementById("urlMode");
    const fileField = document.getElementById("fileField");
    const urlField = document.getElementById("urlField");
    const videoFile = document.getElementById("videoFile");
    const videoUrl = document.getElementById("videoUrl");
    const rangeMode = document.getElementById("rangeMode");
    const durationField = document.getElementById("durationField");
    const endField = document.getElementById("endField");
    const clipDuration = document.getElementById("clipDuration");
    const endTimestamp = document.getElementById("endTimestamp");
    const form = document.getElementById("jobForm");
    const statusPill = document.getElementById("statusPill");
    const message = document.getElementById("message");
    const metadataPanel = document.getElementById("metadata");
    const outputs = document.getElementById("outputs");
    const thumbnail = document.getElementById("thumbnail");
    const submitButton = document.getElementById("submitButton");
    const metadataButton = document.getElementById("metadataButton");
    let activeInput = "file";
    let pollTimer = null;

    function setInputMode(mode) {
      activeInput = mode;
      const isFile = mode === "file";
      fileMode.classList.toggle("active", isFile);
      urlMode.classList.toggle("active", !isFile);
      fileField.classList.toggle("hidden", !isFile);
      urlField.classList.toggle("hidden", isFile);
      if (isFile) {
        videoUrl.value = "";
      } else {
        videoFile.value = "";
      }
    }

    function setRangeMode(mode) {
      const useDuration = mode === "duration";
      durationField.classList.toggle("hidden", !useDuration);
      endField.classList.toggle("hidden", useDuration);
      if (useDuration) {
        endTimestamp.value = "";
      } else {
        clipDuration.value = "";
      }
    }

    function setStatus(status, text) {
      statusPill.textContent = status;
      statusPill.classList.toggle("failed", status === "failed");
      message.textContent = text || "";
      message.classList.toggle("error", status === "failed");
    }

    function clearResults() {
      metadataPanel.innerHTML = "";
      outputs.innerHTML = "";
      thumbnail.removeAttribute("src");
      thumbnail.style.display = "none";
    }

    function renderMetadata(metadata, clip) {
      if (!metadata && !clip) {
        metadataPanel.innerHTML = "";
        return;
      }
      const rows = [];
      if (metadata) {
        rows.push(["Duration", `${metadata.duration_seconds}s`]);
        rows.push(["Resolution", `${metadata.width} x ${metadata.height}`]);
        rows.push(["FPS", metadata.fps ?? "Unknown"]);
        rows.push(["Audio", metadata.has_audio ? "Present" : "None"]);
        rows.push(["Orientation", metadata.orientation]);
      }
      if (clip) {
        rows.push(["Clip", `${clip.start_seconds}s to ${clip.end_seconds}s`]);
      }
      metadataPanel.innerHTML = rows.map(([label, value]) => (
        `<div class="meta-item"><b>${label}</b><span>${value}</span></div>`
      )).join("");
    }

    function appendCommonFields(data) {
      if (activeInput === "file") {
        if (!videoFile.files[0]) throw new Error("Select a video file.");
        data.append("video_file", videoFile.files[0]);
      } else {
        if (!videoUrl.value.trim()) throw new Error("Enter a video URL.");
        data.append("video_url", videoUrl.value.trim());
      }
    }

    function buildJobData() {
      const data = new FormData();
      appendCommonFields(data);
      data.append("start_timestamp", document.getElementById("startTimestamp").value.trim());

      if (rangeMode.value === "duration") {
        data.append("clip_duration", clipDuration.value.trim());
      } else {
        data.append("end_timestamp", endTimestamp.value.trim());
      }

      for (const id of ["overflowPolicy", "logoPosition", "logoOpacity", "logoScale", "logoPadding", "logoFade"]) {
        const input = document.getElementById(id);
        data.append(input.name, input.value);
      }

      const logo = document.getElementById("logoFile").files[0];
      if (logo) data.append("logo_file", logo);
      return data;
    }

    function buildMetadataData() {
      const data = new FormData();
      appendCommonFields(data);
      return data;
    }

    async function requestJson(path, options) {
      const response = await fetch(path, options);
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Request failed.");
      }
      return payload;
    }

    async function pollJob(jobId) {
      const job = await requestJson(`/jobs/${jobId}`);
      setStatus(job.status, job.message);
      renderMetadata(job.metadata, job.clip);
      if (job.status === "completed") {
        clearInterval(pollTimer);
        submitButton.disabled = false;
        renderOutputs(job.outputs);
      }
      if (job.status === "failed") {
        clearInterval(pollTimer);
        submitButton.disabled = false;
      }
    }

    function renderOutputs(jobOutputs) {
      const entries = [
        ["Trimmed Clip", jobOutputs.clipped_video],
        ["Thumbnail", jobOutputs.thumbnail],
        ["Watermarked Clip", jobOutputs.watermarked_video],
      ].filter(([, url]) => Boolean(url));

      outputs.innerHTML = entries.map(([label, url]) => (
        `<a class="asset-link" href="${url}" target="_blank" rel="noreferrer">${label}<span>Open</span></a>`
      )).join("");

      if (jobOutputs.thumbnail) {
        thumbnail.src = `${jobOutputs.thumbnail}?t=${Date.now()}`;
        thumbnail.style.display = "block";
      }
    }

    fileMode.addEventListener("click", () => setInputMode("file"));
    urlMode.addEventListener("click", () => setInputMode("url"));
    rangeMode.addEventListener("change", () => setRangeMode(rangeMode.value));

    metadataButton.addEventListener("click", async () => {
      try {
        clearResults();
        metadataButton.disabled = true;
        setStatus("processing", "Reading metadata...");
        const result = await requestJson("/metadata", {
          method: "POST",
          body: buildMetadataData(),
        });
        setStatus("ready", "Metadata loaded.");
        renderMetadata(result.metadata, null);
      } catch (error) {
        setStatus("failed", error.message);
      } finally {
        metadataButton.disabled = false;
      }
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        clearResults();
        submitButton.disabled = true;
        setStatus("queued", "Creating job...");
        const job = await requestJson("/jobs", {
          method: "POST",
          body: buildJobData(),
        });
        setStatus(job.status, job.message);
        clearInterval(pollTimer);
        pollTimer = setInterval(() => pollJob(job.job_id).catch((error) => {
          clearInterval(pollTimer);
          submitButton.disabled = false;
          setStatus("failed", error.message);
        }), 1200);
        await pollJob(job.job_id);
      } catch (error) {
        submitButton.disabled = false;
        setStatus("failed", error.message);
      }
    });
  </script>
</body>
</html>
"""
