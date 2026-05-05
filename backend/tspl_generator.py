from PIL import Image


def image_to_bitmap_bytes(bw: Image.Image) -> tuple[bytes, bytes]:
    if bw.mode != "1":
        gray = bw.convert("L")
        bw = gray.point(lambda x: 0 if x < 128 else 255, "1")

    gray = bw.convert("L")
    width, height = gray.size
    bytes_per_row = (width + 7) // 8

    header = f"BITMAP 0,0,{bytes_per_row},{height},0,"
    header_bytes = header.encode("gbk")

    pixels = gray.load()
    bitmap_data = bytearray()

    for y in range(height):
        for byte_idx in range(bytes_per_row):
            byte_val = 0
            for bit in range(8):
                x = byte_idx * 8 + bit
                if x < width:
                    if pixels[x, y] >= 128:
                        byte_val |= (1 << (7 - bit))
            bitmap_data.append(byte_val)

    return header_bytes, bytes(bitmap_data)


def generate_tspl_bytes(
    bw: Image.Image,
    label_width_mm: int = 40,
    label_height_mm: int = 30,
    copies: int = 1,
) -> bytes:

    corrected = bw.rotate(180, expand=True)

    header_text = (
        f"SIZE {label_width_mm} mm,{label_height_mm} mm\r\n"
        "GAP 2 mm,0 mm\r\n"
        "DENSITY 8\r\n"
        "DIRECTION 1\r\n"
        "CLS\r\n"
    )

    footer_text = f"\r\nPRINT {copies}\r\n"

    header_bytes = header_text.encode("gbk")
    bitmap_header, bitmap_data = image_to_bitmap_bytes(corrected)
    footer_bytes = footer_text.encode("gbk")

    return header_bytes + bitmap_header + bitmap_data + footer_bytes
