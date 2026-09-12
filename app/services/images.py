from pathlib import Path
from uuid import uuid4

from flask import current_app
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename


PRODUCT_THUMBNAIL_SIZE = 480
PRODUCT_THUMBNAIL_QUALITY = 82


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


def _images_dir():
    images_dir = (
        Path(current_app.static_folder)
        / "img"
    )

    images_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return images_dir


def _thumbnails_dir():
    thumbnails_dir = (
        _images_dir()
        / "thumbs"
    )

    thumbnails_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return thumbnails_dir


def product_thumbnail_name(filename):
    if not filename:
        return None

    return f"{Path(filename).stem}.webp"


def _save_product_thumbnail_from_image(
        image,
        filename,
):
    thumbnail_name = product_thumbnail_name(
        filename
    )

    if not thumbnail_name:
        return None

    destination = (
        _thumbnails_dir()
        / thumbnail_name
    )

    side = min(
        PRODUCT_THUMBNAIL_SIZE,
        image.width,
        image.height,
    )

    thumbnail = ImageOps.fit(
        image.convert("RGB"),
        (side, side),
        method=Image.Resampling.LANCZOS,
    )

    thumbnail.save(
        destination,
        format="WEBP",
        quality=PRODUCT_THUMBNAIL_QUALITY,
        method=4,
    )

    return thumbnail_name


def ensure_product_thumbnail(
        filename,
        *,
        overwrite=False,
):
    """
    Создаёт thumbnail для уже существующего изображения товара.

    Нужен для:
    - старых изображений;
    - картинок из Product Suggestions, которые могли быть сохранены
      с prefix="suggest", а затем стать main_image товара.
    """
    if not filename:
        return None

    safe_filename = Path(filename).name

    source = (
        _images_dir()
        / safe_filename
    )

    if not source.is_file():
        return None

    thumbnail_name = product_thumbnail_name(
        safe_filename
    )

    destination = (
        _thumbnails_dir()
        / thumbnail_name
    )

    if destination.exists() and not overwrite:
        return thumbnail_name

    with Image.open(source) as image:
        image = ImageOps.exif_transpose(
            image
        )

        return _save_product_thumbnail_from_image(
            image,
            safe_filename,
        )


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

    images_dir = _images_dir()

    filename = (
        f"{prefix}_{uuid4().hex}.{extension}"
    )

    destination = (
        images_dir
        / filename
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

        # Новые product-фото сразу получают WebP thumbnail.
        if prefix == "product":
            _save_product_thumbnail_from_image(
                image,
                filename,
            )

    return filename
