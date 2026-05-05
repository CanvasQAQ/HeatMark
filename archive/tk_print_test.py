import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import win32print
import csv

class TSPLDesigner:
    def __init__(self, root):
        self.root = root
        self.root.title("TSPL 标签可视化设计器")
        self.root.geometry("1200x700")
        
        # 标签物理尺寸 (mm)
        self.label_width_mm = 40
        self.label_height_mm = 30
        # 屏幕缩放比例 (像素/mm)
        self.scale = 10
        
        # 元素列表
        self.elements = []
        self.selected_element = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        
        self.setup_ui()
        
    def setup_ui(self):
        # ===== 左侧：工具栏 =====
        left_frame = ttk.Frame(self.root, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(left_frame, text="添加元素", font=("", 12, "bold")).pack(pady=5)
        
        ttk.Button(left_frame, text="📝 添加文本", 
                   command=self.add_text).pack(fill=tk.X, pady=2)
        ttk.Button(left_frame, text="📊 添加条形码", 
                   command=self.add_barcode).pack(fill=tk.X, pady=2)
        ttk.Button(left_frame, text="🔲 添加矩形", 
                   command=self.add_rect).pack(fill=tk.X, pady=2)
        ttk.Button(left_frame, text="➖ 添加线条", 
                   command=self.add_line).pack(fill=tk.X, pady=2)
        
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Label(left_frame, text="元素列表", font=("", 12, "bold")).pack(pady=5)
        
        # 元素列表框
        self.element_listbox = tk.Listbox(left_frame, height=10)
        self.element_listbox.pack(fill=tk.X, pady=2)
        self.element_listbox.bind('<<ListboxSelect>>', self.on_listbox_select)
        
        ttk.Button(left_frame, text="🗑️ 删除选中", 
                   command=self.delete_selected).pack(fill=tk.X, pady=2)
        ttk.Button(left_frame, text="⬆️ 上移", 
                   command=self.move_up).pack(fill=tk.X, pady=2)
        ttk.Button(left_frame, text="⬇️ 下移", 
                   command=self.move_down).pack(fill=tk.X, pady=2)
        
        # ===== 中间：画布 =====
        center_frame = ttk.Frame(self.root)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(center_frame, text="标签预览 (40mm × 30mm)", 
                  font=("", 12, "bold")).pack(pady=5)
        
        # 画布容器（带滚动条）
        canvas_frame = ttk.Frame(center_frame, relief=tk.SUNKEN, borderwidth=2)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas_w = int(self.label_width_mm * self.scale)
        canvas_h = int(self.label_height_mm * self.scale)
        
        self.canvas = tk.Canvas(canvas_frame, width=canvas_w, height=canvas_h, 
                                bg="white", cursor="crosshair")
        self.canvas.pack(padx=10, pady=10)
        
        # 绑定事件
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # 绘制网格
        self.draw_grid()
        
        # ===== 右侧：属性面板 =====
        right_frame = ttk.Frame(self.root, width=280)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(right_frame, text="属性编辑", font=("", 12, "bold")).pack(pady=5)
        
        # 属性编辑区
        self.prop_frame = ttk.LabelFrame(right_frame, text="选中元素属性")
        self.prop_frame.pack(fill=tk.X, pady=5)
        
        self.prop_entries = {}
        
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # 操作按钮
        ttk.Label(right_frame, text="操作", font=("", 12, "bold")).pack(pady=5)
        
        ttk.Button(right_frame, text="👁️ 预览TSPL代码", 
                   command=self.preview_tspl).pack(fill=tk.X, pady=2)
        ttk.Button(right_frame, text="📋 复制TSPL代码", 
                   command=self.copy_tspl).pack(fill=tk.X, pady=2)
        ttk.Button(right_frame, text="💾 导出TSPL文件", 
                   command=self.export_tspl).pack(fill=tk.X, pady=2)
        ttk.Button(right_frame, text="🖨️ 直接打印", 
                   command=self.print_label).pack(fill=tk.X, pady=2)
        
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # CSV批量打印
        ttk.Label(right_frame, text="批量打印", font=("", 12, "bold")).pack(pady=5)
        ttk.Button(right_frame, text="📂 加载CSV批量打印", 
                   command=self.batch_print).pack(fill=tk.X, pady=2)
        
    def draw_grid(self):
        """绘制网格线"""
        w = int(self.label_width_mm * self.scale)
        h = int(self.label_height_mm * self.scale)
        
        # 每10mm画一条线
        for x in range(0, w + 1, 10 * self.scale):
            self.canvas.create_line(x, 0, x, h, fill="#ddd", tags="grid")
        for y in range(0, h + 1, 10 * self.scale):
            self.canvas.create_line(0, y, w, y, fill="#ddd", tags="grid")
        
        # 边框
        self.canvas.create_rectangle(0, 0, w - 1, h - 1, outline="black", width=2)
    
    def add_text(self):
        """添加文本元素"""
        element = {
            "type": "text",
            "x": 20,
            "y": 20,
            "content": "示例文本",
            "font_size": 2,  # TSPL字体大小 1-5
            "rotation": 0
        }
        self.elements.append(element)
        self.refresh_canvas()
        self.update_listbox()
    
    def add_barcode(self):
        """添加条形码元素"""
        element = {
            "type": "barcode",
            "x": 20,
            "y": 100,
            "content": "1234567890",
            "height": 40,
            "barcode_type": "128",
            "rotation": 0
        }
        self.elements.append(element)
        self.refresh_canvas()
        self.update_listbox()
    
    def add_rect(self):
        """添加矩形"""
        element = {
            "type": "rect",
            "x": 10,
            "y": 10,
            "width": 100,
            "height": 50,
            "thickness": 1
        }
        self.elements.append(element)
        self.refresh_canvas()
        self.update_listbox()
    
    def add_line(self):
        """添加线条"""
        element = {
            "type": "line",
            "x": 10,
            "y": 10,
            "x2": 100,
            "y2": 10,
            "thickness": 1
        }
        self.elements.append(element)
        self.refresh_canvas()
        self.update_listbox()
    
    def refresh_canvas(self):
        """刷新画布显示"""
        self.canvas.delete("element")
        
        for i, elem in enumerate(self.elements):
            x = elem["x"] * self.scale / 8  # TSPL单位转像素
            y = elem["y"] * self.scale / 8
            
            if elem["type"] == "text":
                font_size = max(8, elem["font_size"] * 6)
                text_id = self.canvas.create_text(
                    x + 5, y + 5, anchor=tk.NW,
                    text=elem["content"],
                    font=("", font_size),
                    tags=("element", f"elem_{i}")
                )
                
            elif elem["type"] == "barcode":
                h = elem["height"] * self.scale / 8
                # 绘制条形码模拟
                self.canvas.create_rectangle(
                    x + 5, y + 5, x + 100, y + h,
                    fill="black", outline="",
                    tags=("element", f"elem_{i}")
                )
                # 条形码文字
                self.canvas.create_text(
                    x + 50, y + h + 10, anchor=tk.N,
                    text=elem["content"],
                    font=("", 8),
                    tags=("element", f"elem_{i}")
                )
                
            elif elem["type"] == "rect":
                w = elem["width"] * self.scale / 8
                h = elem["height"] * self.scale / 8
                self.canvas.create_rectangle(
                    x, y, x + w, y + h,
                    outline="black", width=elem["thickness"],
                    tags=("element", f"elem_{i}")
                )
                
            elif elem["type"] == "line":
                x2 = elem["x2"] * self.scale / 8
                y2 = elem["y2"] * self.scale / 8
                self.canvas.create_line(
                    x, y, x2, y2,
                    width=elem["thickness"],
                    tags=("element", f"elem_{i}")
                )
        
        # 选中高亮
        if self.selected_element is not None:
            self.highlight_selected()
    
    def highlight_selected(self):
        """高亮选中的元素"""
        if self.selected_element is None:
            return
        elem = self.elements[self.selected_element]
        x = elem["x"] * self.scale / 8
        y = elem["y"] * self.scale / 8
        
        # 绘制选中框
        self.canvas.create_rectangle(
            x - 2, y - 2, x + 120, y + 30,
            outline="red", width=2, dash=(4, 4),
            tags="selection"
        )
    
    def on_canvas_click(self, event):
        """画布点击事件"""
        self.canvas.delete("selection")
        
        # 查找点击的元素
        clicked = self.canvas.find_closest(event.x, event.y)
        for i, elem in enumerate(self.elements):
            x = elem["x"] * self.scale / 8
            y = elem["y"] * self.scale / 8
            if abs(event.x - x) < 100 and abs(event.y - y) < 30:
                self.selected_element = i
                self.highlight_selected()
                self.show_properties(i)
                self.element_listbox.selection_clear(0, tk.END)
                self.element_listbox.selection_set(i)
                self.drag_data["item"] = i
                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y
                return
        
        self.selected_element = None
        self.clear_properties()
    
    def on_canvas_drag(self, event):
        """拖拽移动元素"""
        if self.drag_data["item"] is None:
            return
        
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        
        elem = self.elements[self.drag_data["item"]]
        elem["x"] += dx * 8 / self.scale
        elem["y"] += dy * 8 / self.scale
        
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        
        self.refresh_canvas()
        self.show_properties(self.drag_data["item"])
    
    def on_canvas_release(self, event):
        """释放鼠标"""
        self.drag_data["item"] = None
    
    def update_listbox(self):
        """更新元素列表"""
        self.element_listbox.delete(0, tk.END)
        for i, elem in enumerate(self.elements):
            icon = {"text": "📝", "barcode": "📊", "rect": "🔲", "line": "➖"}
            self.element_listbox.insert(tk.END, 
                f"{icon.get(elem['type'], '?')} {elem['type']}: {elem.get('content', '')[:15]}")
    
    def on_listbox_select(self, event):
        """列表框选中事件"""
        selection = self.element_listbox.curselection()
        if selection:
            idx = selection[0]
            self.selected_element = idx
            self.canvas.delete("selection")
            self.highlight_selected()
            self.show_properties(idx)
    
    def show_properties(self, index):
        """显示元素属性"""
        self.clear_properties()
        elem = self.elements[index]
        
        row = 0
        for key, value in elem.items():
            ttk.Label(self.prop_frame, text=f"{key}:").grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=2)
            entry = ttk.Entry(self.prop_frame, width=20)
            entry.insert(0, str(value))
            entry.grid(row=row, column=1, padx=5, pady=2)
            self.prop_entries[key] = entry
            row += 1
        
        ttk.Button(self.prop_frame, text="✅ 应用修改", 
                   command=lambda: self.apply_properties(index)).grid(
                   row=row, column=0, columnspan=2, pady=10)
    
    def clear_properties(self):
        """清空属性面板"""
        for widget in self.prop_frame.winfo_children():
            widget.destroy()
        self.prop_entries.clear()
    
    def apply_properties(self, index):
        """应用属性修改"""
        elem = self.elements[index]
        for key, entry in self.prop_entries.items():
            value = entry.get()
            if key in ["x", "y", "x2", "y2", "width", "height", 
                       "font_size", "height", "thickness", "rotation"]:
                try:
                    value = int(value)
                except:
                    pass
            elem[key] = value
        self.refresh_canvas()
        self.update_listbox()
    
    def delete_selected(self):
        """删除选中元素"""
        if self.selected_element is not None:
            del self.elements[self.selected_element]
            self.selected_element = None
            self.refresh_canvas()
            self.update_listbox()
            self.clear_properties()
    
    def move_up(self):
        """上移元素"""
        if self.selected_element and self.selected_element > 0:
            i = self.selected_element
            self.elements[i], self.elements[i-1] = self.elements[i-1], self.elements[i]
            self.selected_element -= 1
            self.refresh_canvas()
            self.update_listbox()
    
    def move_down(self):
        """下移元素"""
        if self.selected_element is not None and self.selected_element < len(self.elements) - 1:
            i = self.selected_element
            self.elements[i], self.elements[i+1] = self.elements[i+1], self.elements[i]
            self.selected_element += 1
            self.refresh_canvas()
            self.update_listbox()
    
    def generate_tspl(self, data=None):
        """生成TSPL代码"""
        data = data or {}
        
        lines = [
            "CODEPAGE 936",
            f"SIZE {self.label_width_mm} mm,{self.label_height_mm} mm",
            "GAP 2 mm,0 mm",
            "CLS",
            ""
        ]
        
        for elem in self.elements:
            content = elem.get("content", "")
            # 替换变量
            for key, value in data.items():
                content = content.replace(f"{{{key}}}", str(value))
            
            if elem["type"] == "text":
                lines.append(
                    f'TEXT {elem["x"]},{elem["y"]},"{elem["font_size"]}",'
                    f'{elem["rotation"]},1,1,"{content}"'
                )
            elif elem["type"] == "barcode":
                lines.append(
                    f'BARCODE {elem["x"]},{elem["y"]},"{elem["barcode_type"]}",'
                    f'{elem["height"]},{elem["rotation"]},0,2,4,"{content}"'
                )
            elif elem["type"] == "rect":
                x2 = elem["x"] + elem["width"]
                y2 = elem["y"] + elem["height"]
                lines.append(f'BOX {elem["x"]},{elem["y"]},{x2},{y2},{elem["thickness"]}')
            elif elem["type"] == "line":
                lines.append(
                    f'LINE {elem["x"]},{elem["y"]},{elem["x2"]},{elem["y2"]},{elem["thickness"]}'
                )
        
        lines.extend(["", "PRINT 1"])
        return "\n".join(lines)
    
    def preview_tspl(self):
        """预览TSPL代码"""
        code = self.generate_tspl()
        
        preview = tk.Toplevel(self.root)
        preview.title("TSPL代码预览")
        preview.geometry("500x400")
        
        text = tk.Text(preview, font=("Consolas", 11))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert("1.0", code)
    
    def copy_tspl(self):
        """复制TSPL代码"""
        code = self.generate_tspl()
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        messagebox.showinfo("成功", "TSPL代码已复制到剪贴板！")
    
    def export_tspl(self):
        """导出TSPL文件"""
        code = self.generate_tspl()
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("TSPL文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filepath:
            with open(filepath, 'w', encoding='gbk') as f:
                f.write(code)
            messagebox.showinfo("成功", f"已导出到: {filepath}")
    
    def print_label(self):
        """直接打印"""
        printer_name = "CHITENG-CT221D"  # 修改为你的打印机名称
        
        try:
            code = self.generate_tspl()
            hprinter = win32print.OpenPrinter(printer_name)
            win32print.StartDocPrinter(hprinter, 1, ("TSPL Print", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, code.encode('gbk'))
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            win32print.ClosePrinter(hprinter)
            messagebox.showinfo("成功", "打印已发送！")
        except Exception as e:
            messagebox.showerror("错误", f"打印失败: {e}")
    
    def batch_print(self):
        """批量打印"""
        filepath = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if not filepath:
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                labels = list(reader)
            
            printer_name = "CHITENG-CT221D"
            hprinter = win32print.OpenPrinter(printer_name)
            win32print.StartDocPrinter(hprinter, 1, ("Batch Print", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            
            for label in labels:
                code = self.generate_tspl(label)
                win32print.WritePrinter(hprinter, code.encode('gbk'))
            
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            win32print.ClosePrinter(hprinter)
            
            messagebox.showinfo("成功", f"已打印 {len(labels)} 张标签！")
        except Exception as e:
            messagebox.showerror("错误", f"批量打印失败: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TSPLDesigner(root)
    root.mainloop()
