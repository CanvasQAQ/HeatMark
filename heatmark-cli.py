#!/usr/bin/env python
"""
HeatMark CLI — 热敏标签模板命令行打印工具

用法:
    python heatmark-cli.py -t 模板名 --slots key=value ... [--print] [--output file.png]
    python heatmark-cli.py -t 模板名 --csv data.csv --print [--copies 1] [--printer NAME]

示例:
    python heatmark-cli.py -t product_label --slots name="苹果" price="¥5" --print
    python heatmark-cli.py -t product_label --csv batch.csv --print --copies 2
    python heatmark-cli.py -t product_label --csv batch.csv --output result.png
"""

import os
import sys
import json
import base64
import argparse
import csv
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(SCRIPT_DIR, "backend")
TEMPLATES_DIR = os.environ.get(
    "HEATMARK_TEMPLATES_DIR",
    os.path.join(SCRIPT_DIR, "templates"),
)

sys.path.insert(0, BACKEND_DIR)

from canvas_renderer import render_canvas
from image_processor import process_image, image_to_base64
from tspl_generator import generate_tspl_bytes


def find_template(template_ref):
    """Find a template by ID or file path."""
    if template_ref.endswith(".json") and os.path.isfile(template_ref):
        with open(template_ref, "r", encoding="utf-8") as f:
            return template_ref, json.load(f)

    index_path = os.path.join(TEMPLATES_DIR, "index.json")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        for entry in index:
            if entry.get("id") == template_ref or entry.get("name") == template_ref:
                tpl_path = os.path.join(TEMPLATES_DIR, entry["id"], "template.json")
                if os.path.exists(tpl_path):
                    with open(tpl_path, "r", encoding="utf-8") as f:
                        return entry["id"], json.load(f)

    candidate = os.path.join(TEMPLATES_DIR, template_ref, "template.json")
    if os.path.exists(candidate):
        with open(candidate, "r", encoding="utf-8") as f:
            return template_ref, json.load(f)

    return None, None


def render_and_process(template_data, slot_values, printer_name, copies):
    label_opts = template_data.get("labelOptions", {})
    label_w = label_opts.get("labelWidthMm", label_opts.get("label_width_mm", 40))
    label_h = label_opts.get("labelHeightMm", label_opts.get("label_height_mm", 30))
    dpi = label_opts.get("dpi", 203)
    threshold = label_opts.get("threshold", 128)
    contrast = label_opts.get("contrast", 1.0)
    brightness = label_opts.get("brightness", 1.0)
    rotation = label_opts.get("rotation", 0)
    invert = label_opts.get("invert", False)
    dither = label_opts.get("dither", True)

    canvas = template_data.get("canvasJson", template_data.get("canvas_json", {}))
    label_w_px = round(label_w / 25.4 * dpi)
    label_h_px = round(label_h / 25.4 * dpi)

    rendered = render_canvas(canvas, label_w_px, label_h_px, slot_values=slot_values)
    rendered = rendered.convert("RGBA")

    bw = process_image(
        rendered,
        threshold=threshold,
        contrast=contrast,
        brightness=brightness,
        rotation=rotation,
        invert=invert,
        dither=dither,
        label_width_mm=label_w,
        label_height_mm=label_h,
        dpi=dpi,
    )

    data = generate_tspl_bytes(bw, label_width_mm=label_w, label_height_mm=label_h,
                               copies=copies)

    if printer_name:
        try:
            from printer_driver import send_to_printer
            send_to_printer(printer_name, data)
            return True, f"已发送 {copies} 份到 {printer_name}"
        except Exception as e:
            return False, f"打印失败: {e}"
    return True, data


def save_png(template_data, slot_values, output_path):
    label_opts = template_data.get("labelOptions", {})
    label_w = label_opts.get("labelWidthMm", label_opts.get("label_width_mm", 40))
    label_h = label_opts.get("labelHeightMm", label_opts.get("label_height_mm", 30))
    dpi = label_opts.get("dpi", 203)
    threshold = label_opts.get("threshold", 128)
    contrast = label_opts.get("contrast", 1.0)
    brightness = label_opts.get("brightness", 1.0)
    dither = label_opts.get("dither", True)

    canvas = template_data.get("canvasJson", template_data.get("canvas_json", {}))
    label_w_px = round(label_w / 25.4 * dpi)
    label_h_px = round(label_h / 25.4 * dpi)

    rendered = render_canvas(canvas, label_w_px, label_h_px, slot_values=slot_values)
    rendered = rendered.convert("RGBA")

    bw = process_image(
        rendered,
        threshold=threshold,
        contrast=contrast,
        brightness=brightness,
        rotation=0,
        invert=False,
        dither=dither,
        label_width_mm=label_w,
        label_height_mm=label_h,
        dpi=dpi,
    )
    bw = bw.convert("L").point(lambda x: 255 - x, "1").convert("RGB")
    bw.save(output_path, "PNG")
    print(f"预览图已保存: {output_path}")


def read_csv(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return []
        return [row for row in reader]


def parse_slots(slot_args):
    result = {}
    for arg in slot_args:
        if "=" in arg:
            key, val = arg.split("=", 1)
            result[key.strip()] = val.strip().strip('"').strip("'")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="HeatMark CLI - 热敏标签模板打印工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python heatmark-cli.py -t product_label --slots name="苹果" price="¥5" --print
  python heatmark-cli.py -t product_label --csv data.csv --print --copies 2
  python heatmark-cli.py -t product_label --csv data.csv --output preview.png
  python heatmark-cli.py -t templates/product_label/template.json --slots name="测试" --print
        """,
    )

    parser.add_argument("-t", "--template", required=True,
                        help="模板ID、名称或 template.json 路径")
    parser.add_argument("--slots", nargs="*", default=[],
                        help="槽位值，格式: key=value (例如: name=\"苹果\" price=\"¥5\")")
    parser.add_argument("--csv", default=None,
                        help="CSV 批量数据文件路径")
    parser.add_argument("--print", action="store_true",
                        help="发送到打印机")
    parser.add_argument("--printer", default=None,
                        help="打印机名称 (默认: CHITENG-CT221D)")
    parser.add_argument("--copies", type=int, default=1,
                        help="每份打印份数 (默认: 1)")
    parser.add_argument("--output", default=None,
                        help="输出渲染后的 PNG 文件路径 (不打印)")

    args = parser.parse_args()

    tpl_id, tpl_data = find_template(args.template)
    if not tpl_data:
        print(f"错误: 找不到模板 '{args.template}'")
        sys.exit(1)

    print(f"模板: {tpl_data.get('name', tpl_id)}")

    slots_info = tpl_data.get("slots", [])
    if slots_info:
        print(f"槽位: {', '.join(s['id'] for s in slots_info)}")

    if args.csv:
        rows = read_csv(args.csv)
        if not rows:
            print(f"错误: CSV 文件为空或无有效数据")
            sys.exit(1)
        print(f"读取 {len(rows)} 行数据")

        for i, row in enumerate(rows, 1):
            slot_values = {k: v for k, v in row.items() if k and v}
            print(f"  [{i}/{len(rows)}] {slot_values}")

            if args.output:
                out_path = f"{os.path.splitext(args.output)[0]}_{i:03d}.png"
                save_png(tpl_data, slot_values, out_path)
            elif args.print:
                printer = args.printer or "CHITENG-CT221D"
                ok, msg = render_and_process(tpl_data, slot_values, printer, args.copies)
                print(f"    {msg}")
                if not ok:
                    sys.exit(1)
            else:
                printer = args.printer or "CHITENG-CT221D"
                ok, msg = render_and_process(tpl_data, slot_values, printer, args.copies)
                if ok:
                    if isinstance(msg, bytes):
                        output_file = args.output or f"{tpl_id}_output.bin"
                        with open(output_file, "wb") as f:
                            f.write(msg)
                        print(f"    TSPL 数据已保存: {output_file}")
                else:
                    print(f"    错误: {msg}")
    else:
        slot_values = parse_slots(args.slots)

        for s in slots_info:
            sid = s["id"]
            if sid not in slot_values:
                if args.print:
                    print(f"警告: 槽位 '{sid}' 未赋值，使用默认值 '{s.get('defaultText', '')}'")
                slot_values[sid] = s.get("defaultText", "")

        if args.output:
            save_png(tpl_data, slot_values, args.output)
        elif args.print:
            printer = args.printer or "CHITENG-CT221D"
            ok, msg = render_and_process(tpl_data, slot_values, printer, args.copies)
            print(msg)
            if not ok:
                sys.exit(1)
        else:
            printer = args.printer or "CHITENG-CT221D"
            ok, msg = render_and_process(tpl_data, slot_values, printer, args.copies)
            if ok:
                if isinstance(msg, bytes):
                    output_file = args.output or f"{tpl_id}_output.bin"
                    with open(output_file, "wb") as f:
                        f.write(msg)
                    print(f"TSPL 数据已保存: {output_file}")
            else:
                print(f"错误: {msg}")


if __name__ == "__main__":
    main()
