import io
import base64
import math
import os
from PIL import Image, ImageDraw, ImageFont

FONT_MAP = {
    "microsoft yahei": ("C:\\Windows\\Fonts\\msyh.ttc", 0),
    "simsun": ("C:\\Windows\\Fonts\\simsun.ttc", 0),
    "simhei": ("C:\\Windows\\Fonts\\simhei.ttf", 0),
    "kaiti": ("C:\\Windows\\Fonts\\simkai.ttf", 0),
    "fangsong": ("C:\\Windows\\Fonts\\simfang.ttf", 0),
    "arial": ("C:\\Windows\\Fonts\\arial.ttf", 0),
    "times new roman": ("C:\\Windows\\Fonts\\times.ttf", 0),
    "courier new": ("C:\\Windows\\Fonts\\cour.ttf", 0),
    "verdana": ("C:\\Windows\\Fonts\\verdana.ttf", 0),
}

_FONT_CACHE = {}


def _find_font(family_str, size, text_hint=""):
    if not family_str:
        return ImageFont.load_default()
    families = [f.strip().lower() for f in family_str.split(",")]
    has_cjk = any('\u4e00' <= c <= '\u9fff' or '\u3000' <= c <= '\u303f' for c in text_hint) if text_hint else False
    if has_cjk:
        cjk_fonts = ["microsoft yahei", "simsun", "simhei", "kaiti", "fangsong"]
        families = [f for f in cjk_fonts if f in families] + [f for f in families if f not in cjk_fonts]
    for fam in families:
        if fam in _FONT_CACHE:
            font_path, font_index = _FONT_CACHE[fam]
        elif fam in FONT_MAP:
            font_path, font_index = FONT_MAP[fam]
            _FONT_CACHE[fam] = (font_path, font_index)
        else:
            continue
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size=size, index=font_index)
            except Exception:
                pass
    return ImageFont.load_default()


def _hex_to_rgb(hex_str):
    if not hex_str or hex_str == "transparent":
        return None
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    if len(hex_str) == 6:
        return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
    return None


def _wrap_text(text, font, max_width):
    if not text:
        return [""]
    paragraphs = text.split("\n")
    lines = []
    for para in paragraphs:
        if not para:
            lines.append("")
            continue
        current_line = ""
        for ch in para:
            test_line = current_line + ch
            try:
                bbox = font.getbbox(test_line)
                w = bbox[2] - bbox[0]
            except Exception:
                w = len(test_line) * 8
            if w <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = ch
        if current_line:
            lines.append(current_line)
    return lines


def render_canvas(canvas_json, label_width_px, label_height_px, slot_values=None):
    if slot_values is None:
        slot_values = {}

    img = Image.new("RGBA", (label_width_px, label_height_px), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    objects = canvas_json.get("objects", []) if isinstance(canvas_json, dict) else []

    for obj in objects:
        obj_type = obj.get("type", "").lower()
        left = obj.get("left", 0)
        top = obj.get("top", 0)
        angle = obj.get("angle", 0) or 0
        scale_x = obj.get("scaleX", 1) or 1
        scale_y = obj.get("scaleY", 1) or 1
        opacity = obj.get("opacity", 1) or 1
        visible = obj.get("visible", True)
        if visible is False:
            continue

        if obj_type in ("textbox", "itext", "text"):
            _draw_textbox(draw, obj, slot_values, label_width_px, label_height_px,
                          angle, scale_x, scale_y, opacity)
        elif obj_type == "rect":
            _draw_rect(draw, obj, label_width_px, label_height_px,
                       angle, scale_x, scale_y, opacity)
        elif obj_type == "line":
            _draw_line(draw, obj, label_width_px, label_height_px,
                       angle, scale_x, scale_y, opacity)
        elif obj_type == "image":
            _draw_image(img, draw, obj, label_width_px, label_height_px,
                        angle, scale_x, scale_y, opacity)

    if img.mode == "RGBA":
        background = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(background, img)
    return img


def _draw_textbox(draw, obj, slot_values, canvas_w, canvas_h, angle, scale_x, scale_y, opacity):
    text = obj.get("text", "")
    slot_id = obj.get("slotId")
    if slot_id and slot_id in slot_values:
        text = slot_values[slot_id]

    font_family = obj.get("fontFamily", "")
    font_size = int((obj.get("fontSize") or 24) * scale_y)
    font = _find_font(font_family, font_size, text_hint=text)

    fill_color = _hex_to_rgb(obj.get("fill", "#000000"))
    text_align = obj.get("textAlign", "left")
    width = (obj.get("width") or 300) * scale_x
    left = obj.get("left", 0)
    top = obj.get("top", 0)
    font_style = obj.get("fontStyle", "normal")
    font_weight = obj.get("fontWeight", "normal")
    underline = obj.get("underline", False)

    if font_style == "italic" or font_weight == "bold":
        try:
            font_path = font.path if hasattr(font, "path") else None
            if font_path:
                from PIL import ImageFont as _IF
                variant = _IF.truetype(font_path, size=font_size)
                setattr(variant, "_style_override", (font_style, font_weight))
                font = variant
        except Exception:
            pass

    lines = _wrap_text(text, font, int(width))

    if not lines:
        return

    line_height = font_size + 4
    total_height = len(lines) * line_height

    if angle != 0:
        _draw_rotated_text(draw, lines, font, font_size, left, top, width, total_height,
                           fill_color, text_align, angle, opacity, canvas_w, canvas_h)
        return

    for i, line in enumerate(lines):
        y = top + i * line_height
        if text_align == "center":
            bbox = font.getbbox(line)
            tw = bbox[2] - bbox[0]
            x = left + (width - tw) / 2
        elif text_align == "right":
            bbox = font.getbbox(line)
            tw = bbox[2] - bbox[0]
            x = left + width - tw
        else:
            x = left
        _draw_text_opacity(draw, (x, y), line, font, fill_color, opacity)
        if underline:
            bbox = font.getbbox(line)
            uw = bbox[2] - bbox[0]
            draw.line([(x, y + font_size + 2), (x + uw, y + font_size + 2)],
                      fill=fill_color, width=1)


def _draw_rotated_text(draw, lines, font, font_size, left, top, width, total_height,
                       fill_color, text_align, angle, opacity, canvas_w, canvas_h):
    txt_img = Image.new("RGBA", (int(width) + 4, int(total_height) + 4), (0, 0, 0, 0))
    txt_draw = ImageDraw.Draw(txt_img)
    line_height = font_size + 4
    for i, line in enumerate(lines):
        y = i * line_height
        if text_align == "center":
            bbox = font.getbbox(line)
            tw = bbox[2] - bbox[0]
            x = (width - tw) / 2
        elif text_align == "right":
            bbox = font.getbbox(line)
            tw = bbox[2] - bbox[0]
            x = width - tw
        else:
            x = 0
        txt_draw.text((x, y), line, fill=fill_color, font=font)

    rotated = txt_img.rotate(-angle, expand=True, resample=Image.BICUBIC)
    if opacity < 1:
        rotated = _apply_opacity(rotated, opacity)
    draw._image.paste(rotated, (int(left), int(top)), rotated)


def _draw_rect(draw, obj, canvas_w, canvas_h, angle, scale_x, scale_y, opacity):
    left = obj.get("left", 0)
    top = obj.get("top", 0)
    width = obj.get("width", 0) * scale_x
    height = obj.get("height", 0) * scale_y
    fill_color = _hex_to_rgb(obj.get("fill", ""))
    stroke_color = _hex_to_rgb(obj.get("stroke", "#000000"))
    stroke_width = obj.get("strokeWidth", 0) or 0

    if angle != 0:
        rect_img = Image.new("RGBA", (int(width) + stroke_width * 2 + 4,
                                       int(height) + stroke_width * 2 + 4), (0, 0, 0, 0))
        rect_draw = ImageDraw.Draw(rect_img)
        ox, oy = stroke_width + 2, stroke_width + 2
        if fill_color:
            rect_draw.rectangle([ox, oy, ox + width, oy + height], fill=fill_color)
        if stroke_width > 0 and stroke_color:
            rect_draw.rectangle([ox, oy, ox + width, oy + height],
                                outline=stroke_color, width=int(stroke_width))
        rotated = rect_img.rotate(-angle, expand=True, resample=Image.BICUBIC)
        if opacity < 1:
            rotated = _apply_opacity(rotated, opacity)
        paste_x = int(left - stroke_width - 2)
        paste_y = int(top - stroke_width - 2)
        draw._image.paste(rotated, (paste_x, paste_y), rotated)
    else:
        if fill_color:
            draw.rectangle([left, top, left + width, top + height], fill=fill_color)
        if stroke_width > 0 and stroke_color:
            draw.rectangle([left, top, left + width, top + height],
                           outline=stroke_color, width=int(stroke_width))
        if opacity < 1:
            _apply_opacity_region(draw._image, int(left), int(top),
                                  int(left + width), int(top + height), opacity)


def _draw_line(draw, obj, canvas_w, canvas_h, angle, scale_x, scale_y, opacity):
    x1 = obj.get("x1", 0)
    y1 = obj.get("y1", 0)
    x2 = obj.get("x2", 0)
    y2 = obj.get("y2", 0)
    stroke_color = _hex_to_rgb(obj.get("stroke", "#000000"))
    stroke_width = obj.get("strokeWidth", 1) or 1

    if angle != 0:
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        bw = max(abs(x2 - x1) + 20, 40)
        bh = max(abs(y2 - y1) + 20, 40)
        line_img = Image.new("RGBA", (int(bw), int(bh)), (0, 0, 0, 0))
        line_draw = ImageDraw.Draw(line_img)
        ox, oy = bw / 2, bh / 2
        lx1, ly1 = ox + (x1 - cx), oy + (y1 - cy)
        lx2, ly2 = ox + (x2 - cx), oy + (y2 - cy)
        line_draw.line([(lx1, ly1), (lx2, ly2)], fill=stroke_color, width=int(stroke_width))
        rotated = line_img.rotate(-angle, expand=True, resample=Image.BICUBIC)
        if opacity < 1:
            rotated = _apply_opacity(rotated, opacity)
        draw._image.paste(rotated, (int(cx - bw / 2), int(cy - bh / 2)), rotated)
    else:
        draw.line([(x1, y1), (x2, y2)], fill=stroke_color, width=int(stroke_width))


def _draw_image(canvas_img, draw, obj, canvas_w, canvas_h, angle, scale_x, scale_y, opacity):
    src = obj.get("src", "")
    if not src:
        return
    left = obj.get("left", 0)
    top = obj.get("top", 0)
    width = obj.get("width", 100) * scale_x
    height = obj.get("height", 100) * scale_y

    try:
        if src.startswith("data:"):
            header, b64_data = src.split(",", 1)
            data = base64.b64decode(b64_data)
            obj_img = Image.open(io.BytesIO(data)).convert("RGBA")
        else:
            return
    except Exception:
        return

    obj_img = obj_img.resize((int(width), int(height)), Image.LANCZOS)

    if angle != 0:
        obj_img = obj_img.rotate(-angle, expand=True, resample=Image.BICUBIC)

    if opacity < 1:
        obj_img = _apply_opacity(obj_img, opacity)

    canvas_img.paste(obj_img, (int(left), int(top)), obj_img)


def _draw_text_opacity(draw, pos, text, font, fill, opacity):
    if opacity >= 1:
        draw.text(pos, text, fill=fill, font=font)
    else:
        x, y = pos
        bbox = font.getbbox(text)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if tw <= 0 or th <= 0:
            return
        tmp = Image.new("RGBA", (tw + 4, th + 4), (0, 0, 0, 0))
        tmp_draw = ImageDraw.Draw(tmp)
        tmp_draw.text((0, 0), text, fill=fill, font=font)
        tmp = _apply_opacity(tmp, opacity)
        draw._image.paste(tmp, (int(x), int(y)), tmp)


def _apply_opacity(img, opacity):
    if opacity >= 1:
        return img
    alpha = img.split()[-1].point(lambda x: int(x * opacity))
    r, g, b, _ = img.split()
    result = Image.merge("RGBA", (r, g, b, alpha))
    return result


def _apply_opacity_region(img, x1, y1, x2, y2, opacity):
    if opacity >= 1:
        return
    crop = img.crop((x1, y1, x2, y2))
    if crop.mode != "RGBA":
        crop = crop.convert("RGBA")
    blended = _apply_opacity(crop, opacity)
    img.paste(blended, (x1, y1), blended)
