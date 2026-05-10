import os
import json
import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import (
    ImageOptions,
    PrintRequest, ProcessRequest, ProcessResponse, PrintResponse, PrinterListResponse,
    SlotDef, TemplateDef, TemplateListItem, TemplateListResponse,
    TemplateSaveRequest, TemplateSaveResponse, TemplateRenderRequest,
)
from image_processor import base64_to_image, image_to_base64, process_image
from tspl_generator import generate_tspl_bytes
from printer_driver import list_printers, send_to_printer
from canvas_renderer import render_canvas

app = FastAPI(title="HeatMark - Thermal Label Printer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_TEMPLATES_DIR = os.environ.get(
    "HEATMARK_TEMPLATES_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates"),
)
_INDEX_PATH = os.path.join(_TEMPLATES_DIR, "index.json")


def _read_index():
    if os.path.exists(_INDEX_PATH):
        with open(_INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _write_index(data):
    os.makedirs(_TEMPLATES_DIR, exist_ok=True)
    with open(_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _read_template(tpl_id):
    tpl_dir = os.path.join(_TEMPLATES_DIR, tpl_id)
    tpl_path = os.path.join(tpl_dir, "template.json")
    if os.path.exists(tpl_path):
        with open(tpl_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _write_template(tpl_id, data):
    tpl_dir = os.path.join(_TEMPLATES_DIR, tpl_id)
    os.makedirs(tpl_dir, exist_ok=True)
    tpl_path = os.path.join(tpl_dir, "template.json")
    with open(tpl_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _safe_id(name):
    import re
    safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", name.lower())
    return safe.strip("_") or "template"


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/printers", response_model=PrinterListResponse)
def get_printers():
    try:
        printers = list_printers()
        return PrinterListResponse(success=True, printers=printers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process", response_model=ProcessResponse)
def process(req: ProcessRequest):
    try:
        img = base64_to_image(req.image_base64)
        opts = req.options
        bw = process_image(
            img,
            threshold=opts.threshold,
            contrast=opts.contrast,
            brightness=opts.brightness,
            rotation=opts.rotation,
            invert=opts.invert,
            dither=opts.dither,
            label_width_mm=opts.label_width_mm,
            label_height_mm=opts.label_height_mm,
            dpi=opts.dpi,
        )
        display = bw.convert("RGB")
        w, h = display.size
        bytes_per_row = (w + 7) // 8
        return ProcessResponse(
            success=True,
            image_base64=image_to_base64(display),
            width=w,
            height=h,
            bytes_per_row=bytes_per_row,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/print", response_model=PrintResponse)
def print_label(req: PrintRequest):
    try:
        img = base64_to_image(req.image_base64)
        opts = req.options
        bw = process_image(
            img,
            threshold=opts.threshold,
            contrast=opts.contrast,
            brightness=opts.brightness,
            rotation=opts.rotation,
            invert=opts.invert,
            dither=opts.dither,
            label_width_mm=opts.label_width_mm,
            label_height_mm=opts.label_height_mm,
            dpi=opts.dpi,
        )
        data = generate_tspl_bytes(
            bw,
            label_width_mm=opts.label_width_mm,
            label_height_mm=opts.label_height_mm,
            copies=req.copies,
        )
        # DEBUG: save GUI's input PNG and TSPL for comparison
        _debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        _debug_img_path = os.path.join(_debug_dir, "debug_gui_input.png")
        _debug_tspl_path = os.path.join(_debug_dir, "debug_gui_output.bin")
        img.save(_debug_img_path)
        with open(_debug_tspl_path, "wb") as _f:
            _f.write(data)
        send_to_printer(req.printer_name, data)
        return PrintResponse(success=True, message=f"已发送 {req.copies} 份到 {req.printer_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/templates", response_model=TemplateListResponse)
def get_templates():
    index_data = _read_index()
    templates = []
    for entry in index_data:
        preview = None
        tpl = _read_template(entry["id"])
        if tpl:
            preview_path = os.path.join(_TEMPLATES_DIR, entry["id"], "preview.png")
            if os.path.exists(preview_path):
                with open(preview_path, "rb") as f:
                    preview = base64.b64encode(f.read()).decode("ascii")
        templates.append(TemplateListItem(
            id=entry["id"],
            name=entry.get("name", entry["id"]),
            labelWidthMm=entry.get("labelWidthMm", 40),
            labelHeightMm=entry.get("labelHeightMm", 30),
            dpi=entry.get("dpi", 203),
            preview=preview,
        ))
    return TemplateListResponse(success=True, templates=templates)


@app.get("/api/templates/{tpl_id}")
def get_template(tpl_id: str):
    tpl = _read_template(tpl_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return {**tpl, "id": tpl_id, "path": tpl_id}


@app.post("/api/templates/save", response_model=TemplateSaveResponse)
def save_template(req: TemplateSaveRequest):
    tpl_id = _safe_id(req.name)
    tpl_dir = os.path.join(_TEMPLATES_DIR, tpl_id)
    os.makedirs(tpl_dir, exist_ok=True)

    tpl_data = TemplateDef(
        version="1.0",
        name=req.name,
        labelOptions=req.labelOptions,
        canvasJson=req.canvasJson,
        slots=req.slots,
    )
    _write_template(tpl_id, tpl_data.model_dump(mode="json", by_alias=True, exclude_none=True))

    if req.preview_base64:
        preview_path = os.path.join(tpl_dir, "preview.png")
        with open(preview_path, "wb") as f:
            f.write(base64.b64decode(req.preview_base64))

    index_data = _read_index()
    existing = [e for e in index_data if e["id"] == tpl_id]
    entry = {
        "id": tpl_id,
        "name": req.name,
        "labelWidthMm": req.labelOptions.label_width_mm,
        "labelHeightMm": req.labelOptions.label_height_mm,
        "dpi": req.labelOptions.dpi,
    }
    if existing:
        existing[0].update(entry)
    else:
        index_data.append(entry)
    _write_index(index_data)

    return TemplateSaveResponse(success=True, id=tpl_id, name=req.name)


@app.put("/api/templates/index")
def update_index(data: dict):
    _write_index(data.get("templates", []))
    return {"success": True}


@app.post("/api/render-template")
def render_template(req: TemplateRenderRequest):
    try:
        tpl = req.template_json
        opts = req.options or tpl.get("labelOptions", {})
        if hasattr(opts, "model_dump"):
            opts = opts.model_dump(mode="json", by_alias=True)
        label_width_mm = opts.get("labelWidthMm", opts.get("label_width_mm", 40))
        label_height_mm = opts.get("labelHeightMm", opts.get("label_height_mm", 30))
        dpi = opts.get("dpi", 203)
        label_width_px = int(label_width_mm / 25.4 * dpi)
        label_height_px = int(label_height_mm / 25.4 * dpi)

        canvas = tpl.get("canvasJson", tpl.get("canvas_json", {}))
        slots_list = tpl.get("slots", [])
        rendered = render_canvas(canvas, label_width_px, label_height_px,
                                 slot_values=req.slots, slots_list=slots_list)
        return {"success": True, "image_base64": image_to_base64(rendered),
                "width": rendered.width, "height": rendered.height}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/template-print", response_model=PrintResponse)
def template_print(req: TemplateRenderRequest):
    try:
        tpl = req.template_json
        opts_data = req.options or tpl.get("labelOptions", {})
        if hasattr(opts_data, "model_dump"):
            opts_data = opts_data.model_dump(mode="json", by_alias=True)

        opts = ImageOptions(**opts_data)

        label_width_px = int(opts.label_width_mm / 25.4 * opts.dpi)
        label_height_px = int(opts.label_height_mm / 25.4 * opts.dpi)

        canvas = tpl.get("canvasJson", tpl.get("canvas_json", {}))
        slots_list = tpl.get("slots", [])
        rendered = render_canvas(canvas, label_width_px, label_height_px,
                                 slot_values=req.slots, slots_list=slots_list)
        rendered = rendered.convert("RGBA")

        bw = process_image(
            rendered,
            threshold=opts.threshold,
            contrast=opts.contrast,
            brightness=opts.brightness,
            rotation=opts.rotation,
            invert=opts.invert,
            dither=opts.dither,
            label_width_mm=opts.label_width_mm,
            label_height_mm=opts.label_height_mm,
            dpi=opts.dpi,
        )
        printer = getattr(req, "printer_name", None) or "CHITENG-CT221D"
        copies = getattr(req, "copies", 1) or 1
        data = generate_tspl_bytes(
            bw,
            label_width_mm=opts.label_width_mm,
            label_height_mm=opts.label_height_mm,
            copies=copies,
        )
        send_to_printer(printer, data)
        return PrintResponse(success=True, message=f"已发送 {copies} 份模板打印到 {printer}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8477, access_log=False)
