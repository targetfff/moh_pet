from pathlib import Path
from uuid import uuid4

from flask import current_app
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename


IMAGE_PROFILES = {
    "vendor": {
        "size": 512,
        "format": "PNG",
        "extension": "png",
    },

    "request": {
        "size": 1200,
        "format": "JPEG",
        "extension": "jpg",
        "quality": 88,
    },

    "suggest": {
        "size": 1200,
        "format": "JPEG",
        "extension": "jpg",
        "quality": 88,
    },

    "product": {
        "size": 1600,
        "format": "JPEG",
        "extension": "jpg",
        "quality": 90,
    },
}


def save_square_image(file, prefix):
    if not file or not file.filename:
        return None

    safe_name = secure_filename(
        file.filename
    )

    if not safe_name:
        return None

    profile = IMAGE_PROFILES.get(
        prefix,
        IMAGE_PROFILES["request"],
    )

    size = profile["size"]
    image_format = profile["format"]
    extension = profile["extension"]

    images_dir = (
            Path(current_app.static_folder)
            / "img"
    )

    images_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = (
        f"{prefix}_{uuid4().hex}.{extension}"
    )

    destination = (
            images_dir / filename
    )

    with Image.open(file.stream) as image:
        image = ImageOps.exif_transpose(
            image
        )

        image = image.convert("RGB")

        side = min(image.size)

        target_size = min(
            size,
            side,
        )

        image = ImageOps.fit(
            image,
            (
                target_size,
                target_size,
            ),
            method=Image.Resampling.LANCZOS,
        )

        if image_format == "JPEG":
            image.save(
                destination,
                format="JPEG",
                quality=profile["quality"],
                subsampling=0,
            )

        else:
            image.save(
                destination,
                format="PNG",
            )

    return filename