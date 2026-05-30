from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
INPUT_DIR = STORAGE_DIR / "inputs"
OUTPUT_DIR = STORAGE_DIR / "outputs"
LOGO_DIR = STORAGE_DIR / "logos"

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm"}
ALLOWED_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg"}
MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024 * 1024


def ensure_storage() -> None:
    for directory in (INPUT_DIR, OUTPUT_DIR, LOGO_DIR):
        directory.mkdir(parents=True, exist_ok=True)

