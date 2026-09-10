from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.utils import secure_filename


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".webm",
    ".mov",
}


def get_ads_directory():
    ads_dir = Path(current_app.static_folder) / "ads"
    ads_dir.mkdir(parents=True, exist_ok=True)
    return ads_dir


def save_ad_media(file):
    safe_name = secure_filename(file.filename or "")
    suffix = Path(safe_name).suffix.lower()
    mimetype = (file.mimetype or "").lower()

    if (
            suffix in IMAGE_EXTENSIONS
            and mimetype.startswith("image/")
    ):
        media_type = "image"

    elif (
            suffix in VIDEO_EXTENSIONS
            and mimetype.startswith("video/")
    ):
        media_type = "video"

    else:
        raise ValueError(
            "Поддерживаются изображения "
            "PNG/JPG/WEBP и видео MP4/WEBM/MOV."
        )

    ads_dir = get_ads_directory()

    filename = f"ad_{uuid4().hex}{suffix}"
    destination = ads_dir / filename

    file.save(destination)

    if media_type == "image":
        frame = filename
    else:
        # В новом интерфейсе видео показывается напрямую через <video>,
        # поэтому отдельный кадр-превью больше не нужен.
        frame = None

    return filename, media_type, frame


def delete_ad_files(filename, frame):
    ads_dir = get_ads_directory()

    names = {
        name
        for name in (filename, frame)
        if name
    }

    for name in names:
        path = ads_dir / Path(name).name
        path.unlink(missing_ok=True)
