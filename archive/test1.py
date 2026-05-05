import win32print
import csv

printer_name = "CHITENG-CT221D"  # 按实际名称修改

# TSPL 模板
tspl_template = """
CODEPAGE 936
SIZE 40 mm,30 mm
GAP 2 mm,0 mm
CLS

TEXT 20,20,"3",0,1,1,"{name}"
TEXT 20,60,"2",0,1,1,"$  {price}"
BARCODE 20,100,"128",40,0,0,2,4,"{barcode}"
TEXT 20,155,"1",0,1,1,"{barcode}"

PRINT 1
"""

# 读取标签数据（CSV格式：name,price,barcode）
with open('labels.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    labels = list(reader)

# 打印
hprinter = win32print.OpenPrinter(printer_name)
try:
    win32print.StartDocPrinter(hprinter, 1, ("BatchPrint TSPL", None, "RAW"))
    win32print.StartPagePrinter(hprinter)

    for label in labels:
        cmd = tspl_template.format(**label)
        # 关键：使用 GBK 编码发送中文
        win32print.WritePrinter(hprinter, cmd.encode('gbk'))

    win32print.EndPagePrinter(hprinter)
    win32print.EndDocPrinter(hprinter)
finally:
    win32print.ClosePrinter(hprinter)

print("打印完成！")
