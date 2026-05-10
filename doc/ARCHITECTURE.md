# HeatMark - 热敏标签打印工具 · 架构文档

> 本文档供 AI / LLM 在参与项目开发时阅读，了解项目整体架构、文件职责、数据流和约定。

---

## 1. 整体架构

```
┌─────────────────────────────────────────────────────┐
│  Electron (Desktop Shell)                           │
│  ┌───────────────────────────────────────────────┐  │
│  │  Vue 3 + Element Plus (UI Layer)              │  │
│  │  ┌──────────────┐  ┌───────────────────────┐  │  │
│  │  │ CanvasEditor │  │ App.vue (right panel) │  │  │
│  │  │ (Fabric.js)  │  │  设置/预览/打印/保存  │  │  │
│  │  └──────────────┘  │  模板/占位符/槽位     │  │  │
│  │  ┌─────────────────────────────────────────┐ │  │
│  │  │ TemplateSelector / TemplateStore        │ │  │
│  │  └─────────────────────────────────────────┘ │  │
│  │           ↕ HTTP direct (localhost:8477)        │  │
│  └───────────────────────────────────────────────┘  │
│           ↕ IPC (backend-status, restart-backend)   │
│  ┌───────────────────────────────────────────────┐  │
│  │  Python FastAPI (Backend Server :8477)         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────┐ │  │
│  │  │image_pro │  │tspl_gen  │  │printer_drive│ │  │
│  │  │cessor.py │  │erator.py │  │r.py         │ │  │
│  │  └──────────┘  └──────────┘  └─────────────┘ │  │
│  │  ┌──────────────────────────────────────────┐ │  │
│  │  │ canvas_renderer.py (PIL Canvas渲染)      │ │  │
│  │  └──────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────┘  │
│           ↕ CLI                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  heatmark-cli.py (命令行批量打印工具)          │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 通信方式

| 通道 | 方向 | 用途 |
|---|---|---|
| HTTP direct | 前端 → 后端 (127.0.0.1:8477) | 图片处理、TSPL 生成、打印 |
| IPC | Electron main ↔ renderer | 后端状态监控、重启后端 |

### 关键设计点

1. **前端直接用绝对 URL 访问后端**：`http://127.0.0.1:8477/api/*`，不依赖 Vite proxy
2. **后端 CORS 全开**：生产环境应限制为 `127.0.0.1` 和 `localhost`
3. **Electron 启动时自动拉起 Python**：作为子进程管理，关闭时一同 kill
4. **浮端口清理**：启动和关闭时都会用 `netstat` + `taskkill` 清理 8477 端口

---

## 2. 文件职责

### 2.1 后端（Python）

| 文件 | 职责 | 核心输出 |
|---|---|---|
| `backend/main.py` | FastAPI 应用，路由注册，CORS 配置，模板管理 API | 10 个 API 端点 |
| `backend/models.py` | Pydantic 请求/响应模型，参数校验 | 12 个数据模型 |
| `backend/image_processor.py` | 图片处理流水线：旋转→缩放→灰度→增强→二值化/抖动→反色 | `process_image()` |
| `backend/tspl_generator.py` | 位图→TSPL BITMAP 二进制指令生成，180° 方向修正 | `generate_tspl_bytes()` |
| `backend/printer_driver.py` | Windows 打印机枚举和 RAW 数据发送 | `list_printers()`, `send_to_printer()` |
| `backend/canvas_renderer.py` | 服务端 Canvas JSON → PIL Image 渲染，支持旋转/透明度/换行 | `render_canvas()` |

### 2.2 前端（Vue + Electron）

| 文件 | 类型 | 职责 |
|---|---|---|
| `src/App.vue` | Vue SFC | 主布局，所有业务逻辑（预览、打印、保存、模板管理、占位符编辑） |
| `src/components/CanvasEditor.vue` | Vue SFC | Fabric.js 画布编辑器，支持占位符标记、模板加载/保存 |
| `src/components/TemplateSelector.vue` | Vue SFC | 模板浏览器弹窗，展示模板列表和预览 |
| `src/stores/canvas.js` | Pinia Store | 全局状态：图像选项、打印机、份数、状态消息 |
| `src/stores/template.js` | Pinia Store | 模板状态：模板列表、当前模板、占位符槽位 |
| `src/api/backend.js` | JS Module | Axios 封装，对后端 10 个 API 的调用函数 |
| `electron/main.js` | Node.js | Electron 主进程：Python 生命周期、端口管理、IPC |
| `electron/preload.js` | Node.js | 安全桥接，暴露 `window.electronAPI` 给渲染进程 |

### 2.3 命令行工具

| 文件 | 职责 |
|---|---|
| `heatmark-cli.py` | 基于模板的命令行打印工具，支持单行槽位赋值、CSV 批量打印、PNG 预览输出 |

### 2.4 模板文件

| 路径 | 职责 |
|---|---|
| `templates/index.json` | 模板索引，列表所有可用模板的 id/name/尺寸/DPI |
| `templates/<id>/template.json` | 模板定义：labelOptions + canvasJson + slots |
| `templates/<id>/preview.png` | 模板预览图（可选，base64 存储或 PNG 文件） |

---

## 3. API 详细说明

Base URL: `http://127.0.0.1:8477/api`

### GET /api/health
- 返回：`{"status": "ok"}`
- 用途：Electron 主进程 3 秒轮询判断后端是否存活

### GET /api/printers
- 返回：`{"success": true, "printers": ["CHITENG-CT221D", ...]}`

### POST /api/process
- 请求体：
```json
{
  "image_base64": "<base64 encoded PNG>",
  "options": {
    "threshold": 128,
    "contrast": 1.0,
    "brightness": 1.0,
    "rotation": 0,
    "invert": false,
    "dither": true,
    "label_width_mm": 40,
    "label_height_mm": 30,
    "dpi": 203
  }
}
```
- 返回：`{"success": true, "image_base64": "...", "width": 320, "height": 240, "bytes_per_row": 40}`

### POST /api/print
- 请求体（在 process 基础上增加）：
```json
{
  "printer_name": "CHITENG-CT221D",
  "copies": 1
}
```
- 返回：`{"success": true, "message": "已发送 1 份到 CHITENG-CT221D"}`

### Template API

### GET /api/templates
- 返回：`{"success": true, "templates": [...TemplateListItem]}`

### GET /api/templates/{tpl_id}
- 返回：模板完整 JSON（含 labelOptions, canvasJson, slots）

### POST /api/templates/save
- 请求体：`{ name, labelOptions, canvasJson, slots, preview_base64 }`
- 返回：`{"success": true, "id": "..", "name": ".."}`

### PUT /api/templates/index
- 请求体：`{ "templates": [...] }`
- 用途：前端更新模板索引顺序

### POST /api/render-template
- 请求体：`{ template_json, slots: {...}, options }`
- 返回：`{"success": true, "image_base64": "...", "width": 320, "height": 240}`

### POST /api/template-print
- 请求体：`{ template_json, slots: {...}, options }`
- 返回：`{"success": true, "message": "已发送 1 份模板打印到 CHITENG-CT221D"}`

### 数据流：打印链路

```
Canvas.toDataURL(PNG)
  → base64
  → POST /api/print { image_base64, options, printer_name, copies }
  → process_image()     # 旋转/缩放/灰度/增强/二值化 or 抖动/反色
  → generate_tspl_bytes() # 180° 旋转 → BITMAP 二进制指令
  → send_to_printer()      # win32print RAW 发送
```

### 数据流：模板链路

```
TemplateSelector → loadTemplate(id)
  → GET /api/templates/{id} → 获取模板 JSON
  → CanvasEditor.loadFromJSON(canvasJson) → 加载画布 + 高亮占位符
  → slotTexts 绑定 → 用户输入 → setSlotText() 实时更新画布文字

保存模板：
  CanvasEditor.toJSON(['slotId', 'slotLabel']) → canvasJson
  + labelOptions + previewBase64
  → POST /api/templates/save → 写入 templates/<id>/template.json

CLI 打印：
  heatmark-cli.py → render_canvas() → process_image() → generate_tspl_bytes() → send_to_printer()
```

---

## 4. 图像处理流水线

```
输入: PIL Image (RGBA)
  │
  ├─ 1. rotate(rotation)                    # 用户指定的旋转
  ├─ 2. resize(label_width_px, label_height_px)  # 缩放到标签像素尺寸
  ├─ 3. convert("L")                        # 转灰度
  ├─ 4. ImageEnhance.Brightness.enhance()   # 亮度调整
  ├─ 5. ImageEnhance.Contrast.enhance()     # 对比度调整
  ├─ 6a. [dither ON] Floyd-Steinberg dither  # 误差扩散抖动
  └─ 6b. [dither OFF] point() threshold     # 简单二值化
  ├─ 7. [invert ON] ImageOps.invert()       # 反色
  │
输出: PIL Image (mode '1', 纯黑白)
```

---

## 5. TSPL BITMAP 二进制格式

### 位极性

该打印机（CHITENG-CT221D）的 BITMAP 位极性为：
- **bit = 1** → 白色（不打印墨点）
- **bit = 0** → 黑色（打印墨点）

因此在 `image_to_bitmap_bytes()` 中，亮色像素（`>= 128`）置位为 1，深色像素保持 0。

### 数据格式

```
BITMAP 0,0,<bytes_per_row>,<height>,0,<binary_data>
```

- `bytes_per_row` = `(width + 7) // 8`（每行字节数，向上取整到字节边界）
- 二进制数据按行从上到下排列，每行从左到右排列
- MSB first（每字节先填高位）

### 指令序列

```
SIZE <w> mm,<h> mm\r\n
GAP 2 mm,0 mm\r\n
DENSITY 8\r\n
DIRECTION 1\r\n
CLS\r\n
BITMAP 0,0,<w_byte>,<h>,0,<binary>\r\n
PRINT <copies>\r\n
```

### 方向修正

TSPL 打印头物理方向与图片方向不同，`generate_tspl_bytes()` 在生成 BITMAP 前对图片做 `rotate(180)` 修正。

---

## 6. 前端状态管理（Pinia Store）

### 6.1 Canvas Store（`useCanvasStore`）

Store 名称：`canvas`（`useCanvasStore`）

```javascript
imageOptions: {
  threshold:    128,     // 0-255, 抖动关闭时有效
  contrast:     1.0,     // 0.5-3.0
  brightness:   1.0,     // 0.3-2.0
  rotation:     0,       // 0/90/180/270
  invert:       false,
  dither:       true,    // 默认开启 Floyd-Steinberg
  labelWidthMm: 40,
  labelHeightMm:30,
  dpi:          203,
}
printerName:   'CHITENG-CT221D'
printers:      []
copies:        1
statusMsg:     '就绪'
```

`getLabelPixelSize()` 计算像素尺寸：`round(mm / 25.4 * dpi)`

### 6.2 Template Store（`useTemplateStore`）

Store 名称：`template`（`useTemplateStore`）

```javascript
templateList:        []        // 模板列表
currentTemplateId:   null      // 当前加载的模板 ID
currentTemplateName: ''        // 当前模板名称
currentTemplatePath: ''        // 当前模板文件路径
slots:               []        // 占位符槽位数组 [{ id, label, defaultText }]
showSelector:        false     // 模板选择器弹窗可见性
pendingSlotId:       ''        // 待操作的槽位 ID
```

关键方法：
- `fetchTemplateList()`：从 `/api/templates` 拉取列表
- `loadTemplate(id)`：加载模板完整数据（labelOptions + canvasJson + slots）
- `persistTemplate(...)`：保存模板到后端
- `syncSlotsFromCanvas(slotDefs)`：从画布同步槽位定义
- `addSlot(id, label, defaultText)` / `removeSlot(id)`：管理槽位

---

## 7. Canvas 编辑器（Fabric.js v6）

### 导入

```javascript
import { Canvas, Rect, Line, FabricImage, IText, StaticCanvas } from 'fabric'
```

### 事件流

```
Canvas 操作 (add/modify/remove)
  → 'object:added' / 'object:modified' / 'object:removed'
  → emit('canvas-changed')
  → App.vue onCanvasChanged() [400ms debounce]
  → refreshPreview() → POST /api/process → 更新预览图

对象选中 (selection:created / selection:updated / selection:cleared)
  → emit('selection-changed', activeObject)
  → App.vue onSelectionChanged(obj) → 显示占位符标记 UI
```

### 占位符（Slot）系统

文字对象可被标记为"占位符"：
- `markAsSlot(obj, slotId)`：设置 `slotId` 属性，显示蓝色虚线边框
- `unmarkSlot(obj)`：清除 `slotId` 属性，移除占位符样式
- `getSlots()`：导出当前画布中所有占位符定义
- 序列化时保存 `slotId` 和 `slotLabel` 属性（通过 `toJSON(['slotId', 'slotLabel'])`）

### 模板加载

`loadFromJSON(canvasJson)` 在已有画布上重新加载对象，自动高亮占位符对象的蓝色虚线边框。

### 图片导出

`getCanvasImageBase64()` 使用 `StaticCanvas` 离屏渲染，避免缩放/选中框干扰输出。

### 对外接口（defineExpose）

| 方法 | 说明 |
|---|---|
| `getCanvasImageBase64()` | 返回 Canvas 的 PNG base64（不含 `data:image/...` 前缀） |
| `clearCanvas()` | 清空画布 |
| `loadFromJSON(canvasJson)` | 从 JSON 恢复画布对象（用于模板加载） |
| `markAsSlot(obj, slotId)` | 标记文字对象为占位符 |
| `unmarkSlot(obj)` | 取消占位符标记 |
| `getSlots()` | 获取所有占位符定义 |
| `getCanvasObjects()` | 获取画布中所有对象 |
| `resizeCanvas()` | 适配容器尺寸后重渲染 |

---

## 8. Electron 主进程生命周期

```
app.whenReady()
  → checkBackendHealth()          # 检查是否已有后端运行
  → [不存在] killPortProcess()    # 清 8477 端口
  → [不存在] startPythonBackend() # 启动 Python 后端
  → [已存在] 复用
  → startBackendMonitor()         # 每 3s 轮询健康状态
  → createWindow()                # 打开 BrowserWindow
  → [dev] loadURL('http://localhost:5173')
  → [prod] loadFile('dist/index.html')

app.on('window-all-closed')
  → killPythonBackend()
  → killPortProcess()
  → app.quit()
```

### IPC 通道

| 通道 | 方向 | 触发 | 用途 |
|---|---|---|---|
| `backend-status` | main → renderer | 3s 轮询 | 更新头部绿点 |
| `backend-log` | main → renderer | Python 输出 | 调试日志 |
| `restart-backend` | renderer → main | 用户点击 | 重启 Python |
| `get-backend-status` | renderer → main | 初始化 | 获取当前状态 |

---

## 9. 服务端 Canvas 渲染（canvas_renderer.py）

`canvas_renderer.py` 在服务端（无浏览器环境）将 Fabric.js Canvas JSON 渲染为 PIL Image，供模板打印和 CLI 使用。

### 支持的图形类型

| 类型 | 支持属性 |
|---|---|
| Text / Textbox / IText | text, fontFamily, fontSize, fill, textAlign, width, 旋转, 透明度, 换行 |
| Rect | fill, stroke, strokeWidth, 旋转, 透明度 |
| Line | x1, y1, x2, y2, stroke, strokeWidth, 旋转 |
| Image | src (data: URL), 缩放, 旋转, 透明度 |

### 字体映射

默认映射常见 Windows 字体路径：
- Microsoft YaHei → `msyh.ttc`
- SimSun → `simsun.ttc`
- SimHei → `simhei.ttf`
- Arial → `arial.ttf`

### 占位符替换

`render_canvas(canvas_json, w, h, slot_values={})` 自动将对象中 `slotId` 匹配的文本替换为 `slot_values` 中的值。

---

## 10. CLI 工具（heatmark-cli.py）

命令行批量打印工具，独立于 Electron GUI 运行。

```
python heatmark-cli.py -t 模板名 --slots key=value ... [--print] [--output file.png]
python heatmark-cli.py -t 模板名 --csv data.csv --print [--copies 1] [--printer NAME]
```

核心流程：`render_canvas()` → `process_image()` → `generate_tspl_bytes()` → `send_to_printer()`

---

## 11. 约定与注意事项

### 前端
- API 调用统一走 `src/api/backend.js`，不要直接在组件中写 `axios.get`
- 状态统一放 Pinia store `canvas.js`，避免 props drilling
- Canvas 编辑器的 `getCanvasImageBase64()` 返回纯 base64（不含前缀）

### 后端
- 所有参数校验用 Pydantic 模型定义在 `models.py`
- 图片处理逻辑集中在 `image_processor.py`，TSPL 生成在 `tspl_generator.py`
- 不要修改 BITMAP 位极性（1=白, 0=黑），这是打印机验证过的

### 跨平台
- 当前打印机驱动仅支持 Windows（`pywin32`）
- Mac 迁移时需替换 `printer_driver.py` 的实现（如 CUPS）
- 前端和图像处理逻辑是跨平台的

---

## 12. [!IMPORTANT] 代码修改后的强制要求

**任何代码修改完成后，必须执行以下操作：**

1. **更新 `README.md`**：如果修改影响了功能描述、启动方式、项目结构、API 接口、依赖项
2. **更新 `doc/ARCHITECTURE.md`（本文档）**：如果修改影响了架构设计、数据流、API 格式、文件职责、技术约定
3. 通知用户文档已同步更新

**此要求对 AI 和人类开发者均适用。**
