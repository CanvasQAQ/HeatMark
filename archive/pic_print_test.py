import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageEnhance
import win32print
import csv
import os


class TSPLImagePrinter:
    """TSPL 图片打印工具 —— 所见即所得"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("TSPL 图片标签打印工具")
        self.root.geometry("1100x750")
        
        # 标签参数
        self.label_width_mm = 40
        self.label_height_mm = 30
        self.dpi = 203  # 热敏打印机常见DPI
        
        # 计算像素尺寸
        self.label_width_px = int(self.label_width_mm / 25.4 * self.dpi)
        self.label_height_px = int(self.label_height_mm / 25.4 * self.dpi)
        
        # 图片
        self.base_image = None       # 原始设计图
        self.processed_image = None  # 处理后预览图
        
        # 变量占位符
        self.variables = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        # ===== 顶部工具栏 =====
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="📂 加载图片设计", 
                   command=self.load_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🎨 在线设计器", 
                   command=self.open_online_editor).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ 内置简易编辑器", 
                   command=self.open_built_in_editor).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Label(toolbar, text="打印机:").pack(side=tk.LEFT)
        self.printer_var = tk.StringVar(value="CHITENG-CT221D")
        printer_combo = ttk.Combobox(toolbar, textvariable=self.printer_var, 
                                      width=25, state="readonly")
        printers = [p[2] for p in win32print.EnumPrinters(2)]
        printer_combo['values'] = printers
        printer_combo.pack(side=tk.LEFT, padx=5)
        if "CHITENG-CT221D" in printers:
            printer_combo.set("CHITENG-CT221D")
        elif printers:
            printer_combo.current(0)
        
        # ===== 主体区域 =====
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- 左侧：图片预览 ---
        left = ttk.LabelFrame(main_frame, text="标签预览")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.preview_label = tk.Label(left, text="请加载图片设计", 
                                       bg="#f0f0f0", width=50, height=20)
        self.preview_label.pack(padx=10, pady=10)
        
        # --- 右侧：设置和操作 ---
        right = ttk.Frame(main_frame, width=300)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        # 图片处理设置
        settings = ttk.LabelFrame(right, text="图片处理设置")
        settings.pack(fill=tk.X, pady=5)
        
        ttk.Label(settings, text="二值化阈值:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.threshold_var = tk.IntVar(value=128)
        ttk.Scale(settings, from_=0, to=255, variable=self.threshold_var,
                  command=lambda v: self.update_preview()).grid(row=0, column=1, padx=5)
        self.threshold_label = ttk.Label(settings, text="128")
        self.threshold_label.grid(row=0, column=2)
        
        ttk.Label(settings, text="对比度:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.contrast_var = tk.DoubleVar(value=1.0)
        ttk.Scale(settings, from_=0.5, to=3.0, variable=self.contrast_var,
                  command=lambda v: self.update_preview()).grid(row=1, column=1, padx=5)
        
        ttk.Label(settings, text="亮度:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.brightness_var = tk.DoubleVar(value=1.0)
        ttk.Scale(settings, from_=0.3, to=2.0, variable=self.brightness_var,
                  command=lambda v: self.update_preview()).grid(row=2, column=1, padx=5)
        
        ttk.Label(settings, text="旋转:").grid(row=3, column=0, sticky=tk.W, padx=5)
        self.rotation_var = tk.IntVar(value=0)
        ttk.Combobox(settings, textvariable=self.rotation_var,
                     values=[0, 90, 180, 270], width=5, state="readonly"
                     ).grid(row=3, column=1, sticky=tk.W, padx=5)
        
        self.invert_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings, text="反色（白底黑字）", 
                         variable=self.invert_var,
                         command=self.update_preview).grid(row=4, column=0, columnspan=3, sticky=tk.W, padx=5)
        
        self.dither_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings, text="Floyd-Steinberg 抖动（灰度模拟）", 
                         variable=self.dither_var,
                         command=self.update_preview).grid(row=5, column=0, columnspan=3, sticky=tk.W, padx=5)
        
        # 变量替换
        var_frame = ttk.LabelFrame(right, text="变量替换 (用于批量打印)")
        var_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(var_frame, text="在图片中使用{变量名}\n批量打印时自动替换", 
                  foreground="gray").pack(padx=5)
        
        entries_frame = ttk.Frame(var_frame)
        entries_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.var_entries = {}
        for i, var_name in enumerate(["name", "price", "barcode"]):
            ttk.Label(entries_frame, text=f"{{{var_name}}}:").grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2)
            entry = ttk.Entry(entries_frame, width=20)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.var_entries[var_name] = entry
        
        # 操作按钮
        action = ttk.LabelFrame(right, text="操作")
        action.pack(fill=tk.X, pady=5)
        
        ttk.Button(action, text="👁️ 刷新预览", 
                   command=self.update_preview).pack(fill=tk.X, pady=2)
        ttk.Button(action, text="🖨️ 打印单张", 
                   command=self.print_single).pack(fill=tk.X, pady=2)
        ttk.Button(action, text="📊 打印份数:", 
                   command=self.print_multi).pack(fill=tk.X, pady=2)
        
        copies_frame = ttk.Frame(action)
        copies_frame.pack(fill=tk.X)
        ttk.Label(copies_frame, text="份数:").pack(side=tk.LEFT, padx=5)
        self.copies_var = tk.IntVar(value=1)
        ttk.Spinbox(copies_frame, from_=1, to=999, textvariable=self.copies_var,
                     width=5).pack(side=tk.LEFT)
        
        ttk.Separator(action, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        ttk.Button(action, text="📂 CSV批量打印", 
                   command=self.batch_print).pack(fill=tk.X, pady=2)
        ttk.Button(action, text="💾 保存TSPL代码", 
                   command=self.save_tspl).pack(fill=tk.X, pady=2)
        
        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.root, textvariable=self.status_var, 
                  relief=tk.SUNKEN).pack(fill=tk.X, padx=5, pady=2)
    
    def load_image(self):
        """加载图片"""
        filepath = filedialog.askopenfilename(
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"),
                ("所有文件", "*.*")
            ]
        )
        if filepath:
            self.base_image = Image.open(filepath).convert("RGBA")
            self.status_var.set(f"已加载: {os.path.basename(filepath)} "
                                f"({self.base_image.size[0]}×{self.base_image.size[1]})")
            self.update_preview()
    
    def open_online_editor(self):
        """推荐在线设计工具"""
        import webbrowser
        urls = {
            "Canva": "https://www.canva.com",
            "Figma": "https://www.figma.com",
            "稿定设计": "https://www.gaoding.com",
        }
        
        win = tk.Toplevel(self.root)
        win.title("推荐在线设计工具")
        win.geometry("350x200")
        
        ttk.Label(win, text="推荐使用以下工具设计标签:", 
                  font=("", 11)).pack(pady=10)
        ttk.Label(win, text=f"画布尺寸建议: {self.label_width_mm}mm × {self.label_height_mm}mm\n"
                            f"像素: {self.label_width_px} × {self.label_height_px}px @203DPI",
                  foreground="blue").pack(pady=5)
        
        for name, url in urls.items():
            ttk.Button(win, text=f"打开 {name}", 
                       command=lambda u=url: webbrowser.open(u)).pack(pady=2)
    
    def open_built_in_editor(self):
        """内置简易标签编辑器"""
        editor = tk.Toplevel(self.root)
        editor.title("简易标签编辑器")
        editor.geometry("600x500")
        
        canvas_w, canvas_h = self.label_width_px, self.label_height_px
        
        # 创建画布
        img = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        canvas = tk.Canvas(editor, width=canvas_w, height=canvas_h, bg="white")
        canvas.pack(padx=10, pady=10)
        
        # 工具栏
        tools = ttk.Frame(editor)
        tools.pack(fill=tk.X, padx=10)
        
        elements = []
        
        def refresh():
            nonlocal img, draw
            img = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
            draw = ImageDraw.Draw(img)
            
            canvas.delete("all")
            
            for elem in elements:
                if elem["type"] == "text":
                    try:
                        font = ImageFont.truetype("msyh.ttc", elem["size"])
                    except:
                        font = ImageFont.load_default()
                    
                    draw.text((elem["x"], elem["y"]), elem["text"], 
                              fill="black", font=font)
                    
                    # 在Canvas上显示
                    canvas.create_text(elem["x"], elem["y"], anchor=tk.NW,
                                       text=elem["text"], font=("", elem["size"] // 2))
                    
                elif elem["type"] == "rect":
                    draw.rectangle([elem["x"], elem["y"], 
                                    elem["x"] + elem["w"], elem["y"] + elem["h"]],
                                   outline="black", width=elem.get("width", 1))
                    canvas.create_rectangle(elem["x"], elem["y"],
                                            elem["x"] + elem["w"], elem["y"] + elem["h"],
                                            outline="black")
                    
                elif elem["type"] == "line":
                    draw.line([elem["x"], elem["y"], elem["x2"], elem["y2"]],
                              fill="black", width=elem.get("width", 1))
                    canvas.create_line(elem["x"], elem["y"], elem["x2"], elem["y2"])
        
        def add_text():
            text = simple_input("输入文本内容", "示例文本")
            if text:
                size = simple_input("字体大小(像素)", "24")
                try:
                    size = int(size)
                except:
                    size = 24
                elements.append({"type": "text", "x": 20, "y": 20, 
                                "text": text, "size": size})
                refresh()
        
        def add_rect():
            elements.append({"type": "rect", "x": 10, "y": 10, "w": 100, "h": 50})
            refresh()
        
        def add_line():
            elements.append({"type": "line", "x": 10, "y": 10, "x2": 100, "y2": 10})
            refresh()
        
        def simple_input(title, default=""):
            d = tk.Toplevel(editor)
            d.title(title)
            d.geometry("300x100")
            result = tk.StringVar(value=default)
            ttk.Entry(d, textvariable=result, width=30).pack(pady=10)
            def ok():
                d.destroy()
            ttk.Button(d, text="确定", command=ok).pack()
            d.wait_window()
            return result.get()
        
        def apply_to_main():
            """将编辑结果应用到主窗口"""
            self.base_image = img.copy()
            self.update_preview()
            editor.destroy()
            messagebox.showinfo("成功", "设计已应用到主窗口！")
        
        ttk.Button(tools, text="📝 添加文字", command=add_text).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools, text="🔲 矩形", command=add_rect).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools, text="➖ 线条", command=add_line).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools, text="✅ 应用到主窗口", command=apply_to_main).pack(side=tk.RIGHT, padx=2)
    
    def process_image(self, image=None):
        """处理图片：调整、二值化"""
        if image is None:
            image = self.base_image
        
        if image is None:
            return None
        
        img = image.copy()
        
        # 旋转
        rotation = self.rotation_var.get()
        if rotation:
            img = img.rotate(rotation, expand=True, fillcolor=(255, 255, 255, 255))
        
        # 调整到标签尺寸
        img = img.resize((self.label_width_px, self.label_height_px), Image.LANCZOS)
        
        # 转灰度
        gray = img.convert("L")
        
        # 亮度调整
        brightness = self.brightness_var.get()
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(gray)
            gray = enhancer.enhance(brightness)
        
        # 对比度调整
        contrast = self.contrast_var.get()
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(gray)
            gray = enhancer.enhance(contrast)
        
        # 二值化
        threshold = self.threshold_var.get()
        self.threshold_label.config(text=str(int(threshold)))
        
        if self.dither_var.get():
            # Floyd-Steinberg 抖动（纯Python实现）
            w, h = gray.size
            pixels = list(gray.getdata())
            pixels = [float(p) for p in pixels]
            
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
            bw = Image.new('L', (w, h))
            bw.putdata(pixels)
            bw = bw.point(lambda x: 0 if x < 128 else 255, '1')
        else:
            bw = gray.point(lambda x: 0 if x < threshold else 255, '1')
        
        # 反色
        if self.invert_var.get():
            from PIL import ImageOps
            bw = ImageOps.invert(bw.convert("L")).point(lambda x: 0 if x < 128 else 255, '1')
        
        return bw
    
    def update_preview(self):
        """更新预览"""
        if self.base_image is None:
            return
        
        self.processed_image = self.process_image()
        
        # 缩放显示
        display = self.processed_image.convert("RGB")
        # 放大到合适大小显示
        scale = min(400 / display.width, 300 / display.height)
        new_w = int(display.width * scale)
        new_h = int(display.height * scale)
        display = display.resize((new_w, new_h), Image.NEAREST)
        
        self.photo = ImageTk.PhotoImage(display)
        self.preview_label.config(image=self.photo, text="", width=new_w, height=new_h)
    
    def image_to_tspl_bitmap_bytes(self, image):
        """
        将黑白图片转换为TSPL BITMAP指令的二进制数据
        
        返回 (header_bytes, bitmap_bytes):
          header_bytes: "BITMAP 0,0,bytes_per_row,height,0," 的GBK编码
          bitmap_bytes: 原始位图二进制数据
        """
        if image is None:
            return b"", b""
        
        bw = image if image.mode == '1' else self.process_image(image)
        
        # 转为灰度图以便正确读取像素值（mode '1' 的像素值可能不是精确的0/255）
        gray = bw.convert("L")
        
        width, height = gray.size
        bytes_per_row = (width + 7) // 8
        
        header = f"BITMAP 0,0,{bytes_per_row},{height},0,"
        header_bytes = header.encode('gbk')
        
        pixels = gray.load()
        bitmap_data = bytearray()
        
        # 从顶部到底部读取
        for y in range(height):
            for byte_idx in range(bytes_per_row):
                byte_val = 0
                for bit in range(8):
                    x = byte_idx * 8 + bit
                    if x < width:
                        if pixels[x, y] >= 128:  # 亮色像素=bit 1（不打印），深色=bit 0（打印黑点）
                            byte_val |= (1 << (7 - bit))
                bitmap_data.append(byte_val)
        
        return header_bytes, bytes(bitmap_data)
    
    def generate_tspl_bytes(self, image=None, copies=1):
        """生成完整TSPL指令的二进制数据（文本用GBK编码，位图用原始二进制）"""
        if image is None:
            image = self.processed_image
        
        if image is None:
            return b""
        
        # 旋转180°修正TSPL打印方向
        image = image.rotate(180, expand=True)
        
        header_text = (
            f"SIZE {self.label_width_mm} mm,{self.label_height_mm} mm\r\n"
            "GAP 2 mm,0 mm\r\n"
            "DENSITY 8\r\n"
            "DIRECTION 1\r\n"
            "CLS\r\n"
        )
        
        footer_text = f"\r\nPRINT {copies}\r\n"
        
        header_bytes = header_text.encode('gbk')
        bitmap_header, bitmap_data = self.image_to_tspl_bitmap_bytes(image)
        footer_bytes = footer_text.encode('gbk')
        
        return header_bytes + bitmap_header + bitmap_data + footer_bytes
    
    def send_to_printer(self, data_bytes):
        """发送二进制数据到打印机"""
        printer_name = self.printer_var.get()
        
        hprinter = win32print.OpenPrinter(printer_name)
        try:
            win32print.StartDocPrinter(hprinter, 1, ("TSPL Image Print", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, data_bytes)
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
        finally:
            win32print.ClosePrinter(hprinter)
    
    def print_single(self):
        """打印单张"""
        if self.base_image is None:
            messagebox.showwarning("提示", "请先加载图片！")
            return
        
        try:
            data = self.generate_tspl_bytes(copies=self.copies_var.get())
            self.send_to_printer(data)
            self.status_var.set(f"已发送 {self.copies_var.get()} 份到打印机")
            messagebox.showinfo("成功", "打印已发送！")
        except Exception as e:
            messagebox.showerror("错误", f"打印失败: {e}")
    
    def print_multi(self):
        """打印多份"""
        self.print_single()
    
    def batch_print(self):
        """CSV批量打印（每行不同图片或变量）"""
        filepath = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if not filepath:
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            printer_name = self.printer_var.get()
            hprinter = win32print.OpenPrinter(printer_name)
            
            win32print.StartDocPrinter(hprinter, 1, ("Batch Print", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            
            count = 0
            for row in rows:
                # 如果CSV中有image列，使用不同图片
                if "image" in row and row["image"] and os.path.exists(row["image"]):
                    img = Image.open(row["image"]).convert("RGBA")
                    processed = self.process_image(img)
                else:
                    processed = self.processed_image
                
                copies = int(row.get("copies", 1))
                data = self.generate_tspl_bytes(processed, copies)
                win32print.WritePrinter(hprinter, data)
                count += copies
            
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            win32print.ClosePrinter(hprinter)
            
            self.status_var.set(f"批量打印完成: {count} 张")
            messagebox.showinfo("成功", f"已打印 {count} 张标签！")
            
        except Exception as e:
            messagebox.showerror("错误", f"批量打印失败: {e}")
    
    def save_tspl(self):
        """保存TSPL代码（可读文本格式，仅供参考）"""
        if self.processed_image is None:
            messagebox.showwarning("提示", "请先加载图片！")
            return
        
        # 生成可读的TSPL文本（位图数据用hex表示）
        image = self.processed_image.rotate(180, expand=True)
        bw = image if image.mode == '1' else self.process_image(image)
        gray = bw.convert("L")
        width, height = gray.size
        bytes_per_row = (width + 7) // 8
        
        pixels = gray.load()
        hex_lines = []
        for y in range(height):
            row_bytes = []
            for byte_idx in range(bytes_per_row):
                byte_val = 0
                for bit in range(8):
                    x = byte_idx * 8 + bit
                    if x < width:
                        if pixels[x, y] >= 128:
                            byte_val |= (1 << (7 - bit))
                row_bytes.append(byte_val)
            hex_lines.append("".join(f"{b:02X}" for b in row_bytes))
        
        tspl_text = (
            f"SIZE {self.label_width_mm} mm,{self.label_height_mm} mm\r\n"
            "GAP 2 mm,0 mm\r\n"
            "DENSITY 8\r\n"
            "DIRECTION 1\r\n"
            "CLS\r\n"
            f"BITMAP 0,0,{bytes_per_row},{height},0,\r\n"
            + "\r\n".join(hex_lines) +
            f"\r\nPRINT 1\r\n"
        )
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("TSPL文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filepath:
            with open(filepath, 'w', encoding='gbk') as f:
                f.write(tspl_text)
            messagebox.showinfo("成功", f"TSPL代码已保存到:\n{filepath}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TSPLImagePrinter(root)
    root.mainloop()
