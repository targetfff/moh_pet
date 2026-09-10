from pathlib import Path
from uuid import uuid4

from flask import current_app
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename


def save_square_image(file, prefix):
    if not file or not file.filename:
        return None

    safe_name = secure_filename(file.filename)

    if not safe_name:
        return None

    images_dir = Path(current_app.static_folder) / "img"
    images_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{prefix}_{uuid4().hex}.png"
    destination = images_dir / filename

    with Image.open(file.stream) as image:
        image = image.convert("RGB")

        side = min(image.size)

        image = ImageOps.fit(
            image,
            (side, side),
            method=Image.Resampling.LANCZOS,
        )

        image.save(
            destination,
            format="PNG",
        )

    return filename