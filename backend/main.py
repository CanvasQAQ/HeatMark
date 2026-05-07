from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import PrintRequest, ProcessRequest, ProcessResponse, PrintResponse, PrinterListResponse
from image_processor import base64_to_image, image_to_base64, process_image
from tspl_generator import generate_tspl_bytes
from printer_driver import list_printers, send_to_printer

app = FastAPI(title="HeatMark - Thermal Label Printer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        send_to_printer(req.printer_name, data)
        return PrintResponse(success=True, message=f"已发送 {req.copies} 份到 {req.printer_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8477, access_log=False)
