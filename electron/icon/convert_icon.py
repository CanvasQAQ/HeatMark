from PIL import Image
import struct
import os
from io import BytesIO

SRC = os.path.join(os.path.dirname(__file__), "icon_original.png")
DST = os.path.join(os.path.dirname(__file__), "icon.ico")

img = Image.open(SRC).convert("RGBA")
pixels = img.load()
for y in range(img.height):
    for x in range(img.width):
        r, g, b, a = pixels[x, y]
        if r < 30 and g < 30 and b < 30:
            pixels[x, y] = (r, g, b, 0)

SIZES = [16, 24, 32, 48, 64, 128, 256, 512]
icons = [img.resize((s, s), Image.LANCZOS) for s in SIZES]

def write_ico(icons, sizes, path):
    """Write a multi-resolution ICO file with PNG-compressed entries.
    Handles sizes > 256 (stored as PNG, width/height = 0 in header)."""
    frames = []
    for icon, size in zip(icons, sizes):
        buf = BytesIO()
        icon.save(buf, "PNG")
        frames.append(buf.getvalue())
    frames_data = [BytesIO(data) for data in frames]

    with open(path, "wb") as f:
        f.write(b"\x00\x00\x01\x00")  # ICO magic
        f.write(struct.pack("<H", len(frames)))  # image count

        # Calc offset for image data (header + directory entries)
        offset = 6 + len(frames) * 16
        header_data = []

        for i, (icon, size) in enumerate(zip(icons, sizes)):
            w, h = size, size
            # ICO stores 0 for 256+, PNG handles the real size
            entry_w = w if w < 256 else 0
            entry_h = h if h < 256 else 0
            colors = 0
            reserved = 0
            planes = 1
            bpp = 32
            data_len = len(frames[i])
            header_data.append(
                struct.pack(
                    "<BBBBHHII",
                    entry_w, entry_h, colors, reserved,
                    planes, bpp,
                    data_len, offset,
                )
            )
            offset += data_len

        for hdr in header_data:
            f.write(hdr)
        for data in frames:
            f.write(data)

write_ico(icons, SIZES, DST)
print(f"Saved {DST} with sizes: {SIZES}")

# Also save processed 512x512 PNG
png_dst = os.path.join(os.path.dirname(__file__), "icon.png")
icons[-1].save(png_dst, "PNG")
print(f"Saved {png_dst} ({icons[-1].size[0]}x{icons[-1].size[1]})")

