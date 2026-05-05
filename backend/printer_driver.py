import win32print


def list_printers() -> list[str]:
    try:
        return [p[2] for p in win32print.EnumPrinters(2)]
    except Exception:
        return []


def send_to_printer(printer_name: str, data: bytes):
    hprinter = win32print.OpenPrinter(printer_name)
    try:
        win32print.StartDocPrinter(hprinter, 1, ("TSPL Image Print", None, "RAW"))
        win32print.StartPagePrinter(hprinter)
        win32print.WritePrinter(hprinter, data)
        win32print.EndPagePrinter(hprinter)
        win32print.EndDocPrinter(hprinter)
    finally:
        win32print.ClosePrinter(hprinter)
