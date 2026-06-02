import os
from pathlib import Path

from django.utils.text import slugify
from PIL import Image as PILImage
from PIL import ImageOps, UnidentifiedImageError


def build_shelf_label_context(label_items, work_dir):
    return {
        "label_items": [
            _prepare_label_item(label_item=label_item, work_dir=work_dir)
            for label_item in label_items
        ]
    }


def _prepare_label_item(label_item, work_dir):
    item = label_item["item"] if isinstance(label_item, dict) else label_item.item
    render_image_path = get_printable_image_path(item=item, work_dir=work_dir)

    return {
        "item": item,
        "has_render_image": bool(render_image_path),
        "render_image_path": render_image_path,
    }


def get_printable_image_path(item, work_dir):
    if not item.image:
        return None

    try:
        source_path = Path(item.image.path)
    except (NotImplementedError, ValueError):
        return None

    output_dir = Path(work_dir) / "shelf_label_images"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / _build_image_name(item=item, source_path=source_path)

    try:
        with PILImage.open(source_path) as image:
            normalized_image = ImageOps.exif_transpose(image)
            normalized_image.load()

            if _has_transparency(normalized_image):
                rgba_image = normalized_image.convert("RGBA")
                flattened_image = PILImage.new("RGB", rgba_image.size, "white")
                flattened_image.paste(rgba_image, mask=rgba_image.getchannel("A"))
                normalized_image = flattened_image
            elif normalized_image.mode != "RGB":
                normalized_image = normalized_image.convert("RGB")

            normalized_image.save(output_path, format="PNG")
    except (FileNotFoundError, OSError, UnidentifiedImageError, ValueError):
        return None

    return os.fspath(output_path)


def _build_image_name(item, source_path):
    slug = slugify(source_path.stem) or "image"
    item_id = item.pk or "unknown"
    return f"item-{item_id}-{slug}.png"


def _has_transparency(image):
    if "A" in image.getbands():
        return True

    return image.mode == "P" and "transparency" in image.info
