from pydantic import BaseModel, Field


class ImageOptions(BaseModel):
    threshold: int = Field(default=128, ge=0, le=255)
    contrast: float = Field(default=1.0, ge=0.5, le=3.0)
    brightness: float = Field(default=1.0, ge=0.3, le=2.0)
    rotation: int = Field(default=0, ge=0, le=270)
    invert: bool = False
    dither: bool = False
    label_width_mm: int = Field(default=40, ge=10, le=200, validation_alias="labelWidthMm")
    label_height_mm: int = Field(default=30, ge=10, le=200, validation_alias="labelHeightMm")
    dpi: int = Field(default=203, ge=100, le=600)


class PrintRequest(BaseModel):
    image_base64: str
    options: ImageOptions = ImageOptions()
    printer_name: str = "CHITENG-CT221D"
    copies: int = Field(default=1, ge=1, le=999)


class ProcessRequest(BaseModel):
    image_base64: str
    options: ImageOptions = ImageOptions()


class ProcessResponse(BaseModel):
    success: bool
    image_base64: str
    width: int
    height: int
    bytes_per_row: int


class PrintResponse(BaseModel):
    success: bool
    message: str


class PrinterListResponse(BaseModel):
    success: bool
    printers: list[str]
