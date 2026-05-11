# HeatMark 前端架构重构 v2.0 — 设计文档

> 日期：2026-05-11 | 范围：前端全面重构 | 基于：App.vue 组件拆分 + 全面前端重构

---

## 1. 目标

将当前 566 行单文件 `App.vue` 拆分为独立组件，提取业务逻辑到 Composables，修复 Canvas 状态丢失和撤销/重做缺失问题。

## 2. 组件树

```
App.vue (布局壳 ~60行)
├── TitleBar.vue                        [已有，不变]
├── TemplateSelector.vue                [已有，不变]
│
├── <main class="app-body">
│   ├── CanvasEditor.vue                [重构]
│   │   └── EditorToolbar.vue           [新]
│   │
│   └── <aside class="side-panel">
│       ├── SettingsPanel.vue           [新]
│       ├── TextSettingsPanel.vue       [新]
│       ├── TemplatePanel.vue           [新]
│       ├── SlotMarkerPanel.vue         [新]
│       ├── PreviewPanel.vue            [新]
│       └── ExportButton.vue            [新]
│
└── BottomBar.vue                       [新]
```

### 组件职责

| 组件 | 职责 | Props | Emits |
|------|------|-------|-------|
| `App.vue` | 布局壳，协调子组件通信 | — | — |
| `CanvasEditor.vue` | Fabric.js 画布管理，不销毁重建 | — | `canvas-changed`, `selection-changed` |
| `EditorToolbar.vue` | 添加元素、删除、图层、撤销/重做 | `hasSelection`, `canUndo`, `canRedo` | `add-text`, `add-rect`, `add-line`, `add-image`, `delete`, `bring-forward`, `send-backward`, `undo`, `redo`, `clear` |
| `SettingsPanel.vue` | 标签尺寸、DPI、抖动/阈值/对比度/亮度/方向/反色 | `imageOptions` | `update:options` |
| `TextSettingsPanel.vue` | 字体/字号设置，仅选中文字时显示 | `selectedType`, `fontSize`, `fontFamily` | `update:font-size`, `update:font-family` |
| `TemplatePanel.vue` | 模板选择/另存、槽位列表编辑 | `slots`, `slotTexts`, `focusedSlotId` | `open-selector`, `save`, `slot-input`, `slot-remove` |
| `SlotMarkerPanel.vue` | 标记/取消占位符 UI | `selectedObject` | `mark`, `unmark` |
| `PreviewPanel.vue` | 预览图展示 + 像素信息 | `previewDataUrl`, `previewInfo`, `loading` | `refresh` |
| `ExportButton.vue` | 导出 TSPL 按钮 | — | `export` |
| `BottomBar.vue` | 后端状态、缩放滑块、打印机选择、份数、打印按钮 | `backendStatus`, `displayScale`, `printerName`, `printers`, `copies`, `statusMsg`, `printing` | `restart`, `update:scale`, `update:printer`, `update:copies`, `print` |

## 3. Composable 层

所有业务逻辑从组件提取到 composables，存放在 `src/composables/`：

| Composable | 职责 | 文件 |
|---|---|---|
| `useCanvasEditor()` | Canvas 生命周期（创建/销毁）、对象增删改、缩放控制 | `composables/useCanvasEditor.js` |
| `useCanvasHistory()` | 撤销/重做栈（命令模式，每次操作 push state） | `composables/useCanvasHistory.js` |
| `usePreview()` | 防抖预览、base64 生成、处理结果缓存 | `composables/usePreview.js` |
| `usePrint()` | 打印请求、TSPL 导出 | `composables/usePrint.js` |
| `useSettings()` | 图像选项读写、DPI/尺寸联动 watch | `composables/useSettings.js` |
| `useTemplates()` | 模板加载/保存/槽位管理 | `composables/useTemplates.js` |
| `useBackendStatus()` | 后端健康轮询 + Electron IPC 监听 | `composables/useBackendStatus.js` |

### 数据流原则

- App.vue 调用 composables，获取所有响应式状态和方法
- App.vue 通过 props 分发数据给子组件
- 子组件通过 emits 通知 App.vue 执行 composable 方法
- 组件**不直接**访问 Pinia stores（可访问 API 层）
- Pinia stores 仅做持久化共享状态容器，逻辑在 composables 中

## 4. Pinia Store 精简

### canvas store (`src/stores/canvas.js`)

```javascript
// 仅保留共享状态字段
{
  imageOptions: { ... },   // 图像处理参数
  printerName: '',         // 当前打印机
  printers: [],            // 打印机列表
  copies: 1,               // 打印份数
  previewImage: null,      // 预览图 base64
  processedInfo: {...},    // 处理结果信息
  statusMsg: '',           // 状态消息
  selectedObjectType: null,// 选中对象类型
  selectedFontSize: 24,    // 选中字号
  selectedFontFamily: '',  // 选中字体
}
// 移除: canvasJson, getLabelPixelSize, effectiveCanvasSize
```

### template store (`src/stores/template.js`)

```javascript
// 保持不变，但方法标记为 @deprecated（逻辑移到 useTemplates）
{
  templateList: [],
  currentTemplateId: null,
  currentTemplateName: '',
  currentTemplatePath: '',
  slots: [],
  showSelector: false,
  pendingSlotId: '',
}
```

## 5. Canvas 状态管理修复

### 问题
当前 `initCanvas()` 在 `effectiveCanvasSize` 变化时调用 `fabricCanvas.dispose()` + 重建 DOM canvas 元素，丢失所有对象状态。

### 修复方案
1. Canvas 仅创建一次（onMounted）
2. 尺寸变化时调用 Fabric 的 `setWidth`/`setHeight` 而非销毁重建
3. 保留所有对象，仅调整画布缓冲区大小
4. 如果新尺寸小于旧尺寸，裁剪超出边界的对象（给出警告）

```javascript
// useCanvasEditor.js 核心逻辑
function resizeCanvas(newW, newH) {
  if (!fabricCanvas) return
  const oldW = fabricCanvas.width
  const oldH = fabricCanvas.height
  fabricCanvas.setWidth(newW)
  fabricCanvas.setHeight(newH)
  // 裁剪超出对象
  for (const obj of fabricCanvas.getObjects()) {
    if (obj.left + obj.width * obj.scaleX > newW || 
        obj.top + obj.height * obj.scaleY > newH) {
      // 移到边界内
      obj.set({ left: Math.min(obj.left, newW - obj.width), 
                top: Math.min(obj.top, newH - obj.height) })
    }
  }
  fabricCanvas.renderAll()
}
```

## 6. 撤销/重做设计

### 命令模式 UndoStack

```javascript
// useCanvasHistory.js
function useCanvasHistory(fabricCanvas) {
  const undoStack = ref([])
  const redoStack = ref([])
  const MAX_HISTORY = 50

  function saveState() {
    const json = fabricCanvas.toJSON(['slotId', 'slotLabel'])
    undoStack.value.push(JSON.stringify(json))
    if (undoStack.value.length > MAX_HISTORY) undoStack.value.shift()
    redoStack.value = []
  }

  function undo() {
    if (!undoStack.value.length) return
    const current = JSON.stringify(fabricCanvas.toJSON(['slotId', 'slotLabel']))
    redoStack.value.push(current)
    const prev = undoStack.value.pop()
    fabricCanvas.loadFromJSON(JSON.parse(prev)).then(renderAndRestore)
  }

  function redo() {
    if (!redoStack.value.length) return
    const current = JSON.stringify(fabricCanvas.toJSON(['slotId', 'slotLabel']))
    undoStack.value.push(current)
    const next = redoStack.value.pop()
    fabricCanvas.loadFromJSON(JSON.parse(next)).then(renderAndRestore)
  }

  function renderAndRestore() {
    // 恢复占位符对象的蓝色虚线边框标记（与 loadFromJSON 后逻辑一致）
    for (const obj of fabricCanvas.getObjects()) {
      if (obj.slotId) {
        obj.set({ stroke: '#409eff', strokeWidth: 1, strokeDashArray: [4, 2] })
      }
    }
    fabricCanvas.renderAll()
  }

  return { undo, redo, saveState, canUndo, canRedo }
}
```

**触发时机**：每次 `object:modified`、`object:added`、`object:removed` 事件后自动调用 `saveState()`。

### 键盘快捷键

```
Ctrl+Z / Cmd+Z  → undo()
Ctrl+Y / Cmd+Y  → redo()
Delete / Backspace → deleteSelected()
```

## 7. 文件变更清单

| 操作 | 文件 | 说明 |
|------|------|------|
| 重构 | `src/App.vue` | 566行 → ~60行布局壳 |
| 重构 | `src/components/CanvasEditor.vue` | 分离工具栏，修复状态丢失 |
| 新增 | `src/components/EditorToolbar.vue` | 工具栏组件 |
| 新增 | `src/components/SettingsPanel.vue` | 图像设置面板 |
| 新增 | `src/components/TextSettingsPanel.vue` | 文字设置面板 |
| 新增 | `src/components/TemplatePanel.vue` | 模板+槽位面板 |
| 新增 | `src/components/SlotMarkerPanel.vue` | 占位符标记面板 |
| 新增 | `src/components/PreviewPanel.vue` | 预览面板 |
| 新增 | `src/components/ExportButton.vue` | 导出按钮 |
| 新增 | `src/components/BottomBar.vue` | 底部状态栏+打印 |
| 新增 | `src/composables/useCanvasEditor.js` | Canvas 生命周期 |
| 新增 | `src/composables/useCanvasHistory.js` | 撤销/重做 |
| 新增 | `src/composables/usePreview.js` | 预览逻辑+防抖 |
| 新增 | `src/composables/usePrint.js` | 打印+导出 |
| 新增 | `src/composables/useSettings.js` | 图像选项管理 |
| 新增 | `src/composables/useTemplates.js` | 模板管理 |
| 新增 | `src/composables/useBackendStatus.js` | 后端状态 |
| 修改 | `src/stores/canvas.js` | 精简字段 |
| 删除 | — | 不删除已有文件 |

## 8. 不在本次范围

- TypeScript 迁移（后续迭代）
- 单元测试（后续迭代）
- 后端重构（独立议题）
- 新图形类型（圆形、条码、二维码）
- 多语言支持
- Electron 打包优化

## 9. 验证标准

重构完成后，以下功能必须正常工作：
1. Canvas 编辑：添加文字/矩形/线条/贴图，选中/拖拽/缩放/旋转
2. 图层上移/下移/删除
3. 切换标签尺寸/DIP 不丢失画布对象
4. 撤销/重做恢复画布状态
5. Ctrl+Z/Y/Delete 快捷键
6. 预览实时刷新（400ms 防抖）
7. 图像设置变更自动刷新预览
8. 模板选择/加载/另存
9. 占位符标记/编辑/取消
10. 打印和导出 TSPL
