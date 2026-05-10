# HeatMark - 热敏标签打印工具

基于 **Electron + Vue 3 + Python FastAPI** 的所见即所得标签打印工具，支持 Canvas 画布编辑、模板系统、实时预览、Floyd-Steinberg 抖动二值化、命令行批量打印，通过 TSPL 协议驱动热敏标签打印机。

目前支持机型：**驰腾 CHITENG-CT221D**

## 技术栈

| 层 | 技术 | 用途 |
|---|---|---|
| 桌面壳 | Electron | 跨平台桌面应用 |
| 前端 | Vue 3 + Element Plus + Fabric.js + IconPark | 画布编辑器、设置面板、图标 |
| 后端 | Python FastAPI (port 8477) | 图像处理、TSPL 生成、打印驱动 |
| 图像处理 | Pillow (PIL) | 图片二值化、抖动、对比度/亮度调整 |
| 打印机驱动 | pywin32 (win32print) | Windows 打印驱动 |

## 快速开始

### 环境要求

- **Node.js** >= 18
- **Python** >= 3.10
- **Windows**（打印机驱动依赖）

### 安装

```bash
# 安装 Node 依赖
npm install

# 安装 Python 后端依赖
pip install -r backend/requirements.txt
```

### 启动方式

**方式一：Electron 一体化（推荐）**
```bash
npm run dev
```
Electron 会自动拉起 Python 后端，关闭窗口时自动清理。

**方式二：打包发布**
```bash
npm run dist
```

**方式三：前后端分离（调试用）**
```bash
# 终端1：启动后端
cd backend
python main.py

# 终端2：启动前端
npx vite
# 浏览器打开 http://localhost:5173
```

## 项目结构

```
HeatMark/
├── backend/                     # Python 后端
│   ├── main.py                  # FastAPI 入口（端口 8477）
│   ├── models.py                # Pydantic 数据模型
│   ├── image_processor.py       # 图像处理核心
│   ├── tspl_generator.py        # TSPL 协议生成
│   ├── printer_driver.py        # Windows 打印驱动
│   ├── canvas_renderer.py       # 服务端 Canvas 渲染（模板用）
│   └── requirements.txt
├── src/                         # Vue 前端
│   ├── main.js                  # Vue 入口
│   ├── App.vue                  # 主布局
│   ├── api/backend.js           # API 客户端
│   ├── stores/canvas.js         # Pinia 画布状态管理
│   ├── stores/template.js       # Pinia 模板状态管理
│   └── components/
│       ├── TitleBar.vue         # 自定义无边框标题栏
│       ├── CanvasEditor.vue     # Fabric.js 画布编辑器
│       └── TemplateSelector.vue # 模板选择器
├── templates/                   # 模板文件（JSON + 预览图）
│   ├── index.json               # 模板索引
│   └── <tpl_id>/
│       ├── template.json        # 模板定义
│       └── preview.png          # 预览图
├── electron/                    # Electron 主进程
│   ├── main.js                  # 主进程入口
│   ├── preload.js               # IPC 桥接
│   └── icon/                    # 应用图标
├── heatmark-cli.py              # 命令行打印工具
├── package.json
├── vite.config.js
├── index.html
├── doc/                         # 文档
│   └── ARCHITECTURE.md          # 架构文档（供 AI 阅读）
└── archive/                     # 旧版原型（存档）
```

## 功能概览

### Canvas 编辑器
- 添加文字、矩形、线条元素
- 拖入外部图片作为贴图
- 对象选中、拖拽、缩放、旋转
- 图层上移/下移、删除

### 模板系统
- 模板选择器：浏览、选择预设模板
- 占位符槽位：标记文字对象为动态占位符，实时填充内容
- 模板保存：将当前画布另存为模板
- 模板索引：`templates/index.json` 管理模板列表

### 命令行工具（CLI）
- 基于模板的命令行打印：`python heatmark-cli.py -t 模板名 --slots key=value --print`
- CSV 批量打印：`python heatmark-cli.py -t 模板名 --csv data.csv --print`
- 输出 PNG 预览：`python heatmark-cli.py -t 模板名 --slots key=value --output result.png`

### 图像处理
- **Floyd-Steinberg 抖动**：通过点阵密度模拟灰度（默认开启）
- **简单二值化**：按阈值黑白转换（关闭抖动后可用）
- 对比度/亮度调整（滑块）
- 方向切换（0°/90°/180°/270°，联动画布宽高）
- 反色

### 标签设置
- 标签尺寸（mm）：默认 40×30
- 打印 DPI：203/300/600

### 打印
- 系统打印机列表（默认 CHITENG-CT221D）
- 份数设置（1-999）
- 一键打印

### 预览
- 右侧实时预览（Canvas 变化 400ms 防抖刷新）
- 设置参数变化自动刷新（300ms 防抖）
- 显示处理后像素尺寸和每行字节数

### 导出
- 保存 TSPL 代码为文本文件

## API 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| GET | `/api/printers` | 获取打印机列表 |
| POST | `/api/process` | 处理图片（返回二值化结果 base64） |
| POST | `/api/print` | 打印标签 |
| GET | `/api/templates` | 获取模板列表 |
| GET | `/api/templates/{id}` | 获取单个模板详情 |
| POST | `/api/templates/save` | 保存模板 |
| PUT | `/api/templates/index` | 更新模板索引 |
| POST | `/api/render-template` | 渲染模板（返回 base64） |
| POST | `/api/template-print` | 基于模板打印 |

## 热敏打印机支持

当前驱动基于 Windows `win32print`，主力适配 **驰腾 CHITENG-CT221D**。

TSPL BITMAP 指令参数：
- 位极性：1 = 白色（不打印），0 = 黑色（打印）
- 打印方向：自动 180° 旋转修正
- 编码：GBK

## 维护

修改代码后请同步更新 `README.md` 和 `doc/ARCHITECTURE.md`。
