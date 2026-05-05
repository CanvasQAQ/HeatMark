import io
import base64
from PIL import Image, ImageEnhance, ImageOps


def base64_to_image(b64: str) -> Image.Image:
    data = base64.b64decode(b64)
    return Image.open(io.BytesIO(data)).convert("RGBA")


def image_to_base64(img: Image.Image, fmt: str = "PNG") -> str:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def process_image(
    image: Image.Image,
    threshold: int = 128,
    contrast: float = 1.0,
    brightness: float = 1.0,
    rotation: int = 0,
    invert: bool = False,
    dither: bool = False,
    label_width_mm: int = 40,
    label_height_mm: int = 30,
    dpi: int = 203,
) -> Image.Image:

    img = image.copy()

    if rotation:
        img = img.rotate(rotation, expand=True, fillcolor=(255, 255, 255, 255))

    label_width_px = int(label_width_mm / 25.4 * dpi)
    label_height_px = int(label_height_mm / 25.4 * dpi)

    img = img.resize((label_width_px, label_height_px), Image.LANCZOS)
    gray = img.convert("L")

    if brightness != 1.0:
        gray = ImageEnhance.Brightness(gray).enhance(brightness)

    if contrast != 1.0:
        gray = ImageEnhance.Contrast(gray).enhance(contrast)

    if dither:
        bw = _floyd_steinberg_dither(gray, threshold)
    else:
        bw = gray.point(lambda x: 0 if x < threshold else 255, "1")

    if invert:
        bw = ImageOps.invert(bw.convert("L")).point(lambda x: 0 if x < 128 else 255, "1")

    return bw


def _floyd_steinberg_dither(gray: Image.Image, threshold: int) -> Image.Image:
    w, h = gray.size
    pixels = [float(p) for p in list(gray.getdata())]

    for y in range(h):
        for x in range(w):
            idx = y * w + x
            old_val = pixels[idx]
            new_val = 0.0 if old_val < threshold else 255.0
            pixels[idx] = new_val
            error = old_val - new_val
            if x + 1 < w:
                pixels[idx + 1] += error * 7 / 16
            if y + 1 < h:
                if x - 1 >= 0:
                    pixels[idx + w - 1] += error * 3 / 16
                pixels[idx + w] += error * 5 / 16
                if x + 1 < w:
                    pixels[idx + w + 1] += error * 1 / 16

    pixels = [max(0, min(255, int(p))) for p in pixels]
    bw = Image.new("L", (w, h))
    bw.putdata(pixels)
    return bw.point(lambda x: 0 if x < 128 else 255, "1")
