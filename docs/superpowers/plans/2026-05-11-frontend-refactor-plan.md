# HeatMark Frontend Refactor v2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor HeatMark frontend from a single 566-line App.vue into composables-driven component architecture with undo/redo and Canvas state preservation.

**Architecture:** Composables handle all business logic; components are pure UI (props in, emits out); Pinia stores become thin state containers. App.vue becomes a ~60-line layout shell.

**Tech Stack:** Vue 3 Composition API, Pinia, Fabric.js v6, Element Plus, Axios, @icon-park/vue-next

---

### Task 1: Create `useBackendStatus` composable

**Files:**
- Create: `src/composables/useBackendStatus.js`

- [ ] **Step 1: Write the composable**

```javascript
import { ref, onUnmounted } from 'vue'
import { healthCheck } from '../api/backend.js'

export function useBackendStatus() {
  const backendStatus = ref('checking')
  let monitor = null

  async function check() {
    try {
      await healthCheck()
      backendStatus.value = 'online'
    } catch {
      backendStatus.value = 'offline'
    }
  }

  function startPolling(interval = 5000) {
    stopPolling()
    check()
    monitor = setInterval(check, interval)
  }

  function stopPolling() {
    if (monitor) { clearInterval(monitor); monitor = null }
  }

  onUnmounted(() => stopPolling())

  return { backendStatus, check, startPolling, stopPolling }
}
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/composables/useBackendStatus.js"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/composables/useBackendStatus.js
git commit -m "feat: add useBackendStatus composable"
```

---

### Task 2: Create `useCanvasHistory` composable

**Files:**
- Create: `src/composables/useCanvasHistory.js`

- [ ] **Step 1: Write the composable**

```javascript
import { ref, computed } from 'vue'

export function useCanvasHistory(fabricCanvasRef) {
  const undoStack = ref([])
  const redoStack = ref([])
  const MAX_HISTORY = 50

  const canUndo = computed(() => undoStack.value.length > 0)
  const canRedo = computed(() => redoStack.value.length > 0)

  function saveState() {
    const canvas = fabricCanvasRef.value
    if (!canvas) return
    const json = JSON.stringify(canvas.toJSON(['slotId', 'slotLabel']))
    undoStack.value.push(json)
    if (undoStack.value.length > MAX_HISTORY) undoStack.value.shift()
    redoStack.value = []
  }

  function restoreSlotHighlights(canvas) {
    for (const obj of canvas.getObjects()) {
      if (obj.slotId) {
        obj.set({ stroke: '#409eff', strokeWidth: 1, strokeDashArray: [4, 2] })
      }
    }
  }

  function undo() {
    const canvas = fabricCanvasRef.value
    if (!canvas || undoStack.value.length === 0) return
    const current = JSON.stringify(canvas.toJSON(['slotId', 'slotLabel']))
    redoStack.value.push(current)
    const prev = undoStack.value.pop()
    canvas.loadFromJSON(JSON.parse(prev)).then(() => {
      restoreSlotHighlights(canvas)
      canvas.requestRenderAll()
    })
  }

  function redo() {
    const canvas = fabricCanvasRef.value
    if (!canvas || redoStack.value.length === 0) return
    const current = JSON.stringify(canvas.toJSON(['slotId', 'slotLabel']))
    undoStack.value.push(current)
    const next = redoStack.value.pop()
    canvas.loadFromJSON(JSON.parse(next)).then(() => {
      restoreSlotHighlights(canvas)
      canvas.requestRenderAll()
    })
  }

  return { undo, redo, saveState, canUndo, canRedo }
}
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/composables/useCanvasHistory.js"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/composables/useCanvasHistory.js
git commit -m "feat: add useCanvasHistory composable with undo/redo"
```

---

### Task 3: Create `useSettings` composable

**Files:**
- Create: `src/composables/useSettings.js`

- [ ] **Step 1: Write the composable**

```javascript
import { computed } from 'vue'
import { useCanvasStore } from '../stores/canvas.js'

export function useSettings() {
  const store = useCanvasStore()

  function getLabelPixelSize() {
    const w = Math.round(store.imageOptions.labelWidthMm / 25.4 * store.imageOptions.dpi)
    const h = Math.round(store.imageOptions.labelHeightMm / 25.4 * store.imageOptions.dpi)
    return { w, h }
  }

  const effectiveCanvasSize = computed(() => {
    const { w, h } = getLabelPixelSize()
    if ([90, 270].includes(store.imageOptions.rotation)) {
      return { w: h, h: w }
    }
    return { w, h }
  })

  const pixelInfo = computed(() => {
    const { w, h } = getLabelPixelSize()
    return { text: `${w}×${h}px | ${Math.ceil(w / 8)}B/行 | DPI:${store.imageOptions.dpi}` }
  })

  return {
    imageOptions: store.imageOptions,
    effectiveCanvasSize,
    pixelInfo,
    getLabelPixelSize,
  }
}
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/composables/useSettings.js"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/composables/useSettings.js
git commit -m "feat: add useSettings composable"
```

---

### Task 4: Create `usePreview` composable

**Files:**
- Create: `src/composables/usePreview.js`

- [ ] **Step 1: Write the composable**

```javascript
import { ref } from 'vue'
import { processImage } from '../api/backend.js'
import { useCanvasStore } from '../stores/canvas.js'

export function usePreview() {
  const store = useCanvasStore()
  const previewDataUrl = ref(null)
  const previewLoading = ref(false)
  const previewInfo = ref(null)
  let debounceTimer = null

  async function refreshPreview(getBase64Fn) {
    if (!getBase64Fn) return
    previewLoading.value = true
    try {
      const b64 = await getBase64Fn()
      if (!b64) { previewLoading.value = false; return }
      const res = await processImage(b64, store.imageOptions)
      previewDataUrl.value = 'data:image/png;base64,' + res.data.image_base64
      previewInfo.value = {
        width: res.data.width,
        height: res.data.height,
        bytesPerRow: res.data.bytes_per_row,
      }
      store.processedInfo = previewInfo.value
    } catch (e) {
      console.error('Preview error:', e)
    } finally {
      previewLoading.value = false
    }
  }

  function schedulePreview(getBase64Fn, delay = 400) {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => refreshPreview(getBase64Fn), delay)
  }

  function cancelPreview() {
    if (debounceTimer) { clearTimeout(debounceTimer); debounceTimer = null }
  }

  return { previewDataUrl, previewLoading, previewInfo, refreshPreview, schedulePreview, cancelPreview }
}
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/composables/usePreview.js"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/composables/usePreview.js
git commit -m "feat: add usePreview composable"
```

---

### Task 5: Create `usePrint` composable

**Files:**
- Create: `src/composables/usePrint.js`

- [ ] **Step 1: Write the composable**

```javascript
import { ref } from 'vue'
import { printLabel, processImage } from '../api/backend.js'
import { useCanvasStore } from '../stores/canvas.js'

export function usePrint() {
  const store = useCanvasStore()
  const printing = ref(false)

  async function doPrint(getBase64Fn) {
    if (!getBase64Fn) return
    const b64 = await getBase64Fn()
    if (!b64) { store.statusMsg = '画布为空'; return false }
    printing.value = true
    store.statusMsg = '打印中...'
    try {
      const res = await printLabel(b64, store.imageOptions, store.printerName, store.copies)
      store.statusMsg = res.data.message
      return true
    } catch (e) {
      store.statusMsg = '打印失败: ' + (e.response?.data?.detail || e.message)
      return false
    } finally {
      printing.value = false
    }
  }

  async function doExportTSPL(getBase64Fn) {
    if (!getBase64Fn) return
    const b64 = await getBase64Fn()
    if (!b64) { store.statusMsg = '画布为空'; return }
    try {
      const res = await processImage(b64, store.imageOptions)
      const text =
        `SIZE ${store.imageOptions.labelWidthMm} mm,${store.imageOptions.labelHeightMm} mm\r\n` +
        `GAP 2 mm,0 mm\r\nDENSITY 8\r\nDIRECTION 1\r\nCLS\r\n` +
        `BITMAP 0,0,${res.data.bytes_per_row},${res.data.height},0,\r\n` +
        `[${res.data.bytes_per_row * res.data.height} bytes binary bitmap data]\r\n` +
        `PRINT 1\r\n`
      const blob = new Blob([text], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = 'label.tspl.txt'; a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      store.statusMsg = '导出失败: ' + (e.message || '')
    }
  }

  return { printing, doPrint, doExportTSPL }
}
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/composables/usePrint.js"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/composables/usePrint.js
git commit -m "feat: add usePrint composable"
```

---

### Task 6: Create `useTemplates` composable

**Files:**
- Create: `src/composables/useTemplates.js`

- [ ] **Step 1: Write the composable**

```javascript
import { ref, reactive } from 'vue'
import { useTemplateStore } from '../stores/template.js'
import { useCanvasStore } from '../stores/canvas.js'
import { ElMessage, ElMessageBox } from 'element-plus'

export function useTemplates() {
  const tplStore = useTemplateStore()
  const canvasStore = useCanvasStore()

  const slotTexts = reactive({})
  const focusedSlotId = ref(null)
  const slotTimers = {}

  function initSlotTexts(getObjectsFn) {
    if (!getObjectsFn) return
    const objects = getObjectsFn()
    for (const obj of objects) {
      if (obj.slotId && obj.text !== undefined) {
        slotTexts[obj.slotId] = obj.text
      }
    }
  }

  function refreshSlotTexts(getObjectsFn) {
    if (!getObjectsFn) return
    const objects = getObjectsFn()
    for (const obj of objects) {
      if (obj.slotId && obj.slotId !== focusedSlotId.value && obj.text !== undefined) {
        slotTexts[obj.slotId] = obj.text
      }
    }
  }

  function setSlotText(slotId, text, getObjectsFn) {
    if (!getObjectsFn) return
    const objects = getObjectsFn()
    const obj = objects.find(o => o.slotId === slotId)
    if (obj) {
      obj.set('text', text)
      obj.initDimensions()
      obj.setCoords()
      obj.canvas?.requestRenderAll()
    }
  }

  function handleSlotInput(slotId, text, getObjectsFn) {
    if (slotTimers[slotId]) clearTimeout(slotTimers[slotId])
    slotTimers[slotId] = setTimeout(() => {
      setSlotText(slotId, text, getObjectsFn)
      slotTimers[slotId] = null
    }, 150)
  }

  function handleSlotBlur(slotId, getObjectsFn) {
    const text = slotTexts[slotId] || ''
    setSlotText(slotId, text, getObjectsFn)
  }

  async function handleTemplateSelect(templateId, loadCanvasFn, getObjectsFn, resizeCanvasFn) {
    tplStore.setShowSelector(false)
    if (templateId === null) return
    if (!templateId || templateId === 'empty') {
      tplStore.currentTemplateId = 'empty'
      tplStore.currentTemplateName = '空白模板'
      tplStore.slots.splice(0, tplStore.slots.length)
      return
    }

    const data = await tplStore.loadTemplate(templateId)
    if (!data) { ElMessage.error('加载模板失败'); return }

    if (data.labelOptions) {
      const opts = data.labelOptions
      canvasStore.imageOptions.labelWidthMm = opts.labelWidthMm || opts.label_width_mm || 40
      canvasStore.imageOptions.labelHeightMm = opts.labelHeightMm || opts.label_height_mm || 30
      canvasStore.imageOptions.dpi = opts.dpi || 203
      canvasStore.imageOptions.threshold = opts.threshold ?? 128
      canvasStore.imageOptions.contrast = opts.contrast ?? 1.0
      canvasStore.imageOptions.brightness = opts.brightness ?? 1.0
      canvasStore.imageOptions.rotation = opts.rotation ?? 0
      canvasStore.imageOptions.invert = opts.invert ?? false
      canvasStore.imageOptions.dither = opts.dither ?? true
    }

    if (data.canvasJson && loadCanvasFn) {
      await loadCanvasFn(data.canvasJson)
      if (resizeCanvasFn) resizeCanvasFn()
      initSlotTexts(getObjectsFn)
    }
  }

  async function handleSaveTemplate(getObjectsFn, getSlotsFn, getBase64Fn) {
    if (!getSlotsFn) return
    try {
      const { value } = await ElMessageBox.prompt('请输入模板名称', '保存模板', {
        confirmButtonText: '保存',
        cancelButtonText: '取消',
        inputPlaceholder: '模板名称',
      })
      if (!value) return

      const canvasJson = JSON.parse(canvasStore.canvasJson || '{}')
      const slotDefs = getSlotsFn()
      tplStore.syncSlotsFromCanvas(slotDefs)

      let previewBase64 = null
      try { previewBase64 = await getBase64Fn() } catch {}

      const result = await tplStore.persistTemplate(value, canvasStore.imageOptions, canvasJson, slotDefs, previewBase64)
      if (result.success) {
        ElMessage.success(`模板 "${result.name}" 已保存`)
      }
    } catch (e) {
      if (e !== 'cancel') {
        ElMessage.error('保存模板失败: ' + (e.message || e))
      }
    }
  }

  function handleOpenSelector() {
    tplStore.fetchTemplateList()
    tplStore.setShowSelector(true)
  }

  function handleRemoveSlot(slotId, unmarkSlotFn, getSlotsFn) {
    if (unmarkSlotFn && getSlotsFn) {
      const objects = getSlotsFn() // ambiguous naming in CanvasEditor - getCanvasObjects
      for (const obj of (objects || [])) {
        if (obj.slotId === slotId) { unmarkSlotFn(obj, true); break }
      }
    }
    const slotDefs = getSlotsFn ? getSlotsFn() : []
    tplStore.syncSlotsFromCanvas(slotDefs)
    delete slotTexts[slotId]
  }

  return {
    slotTexts,
    focusedSlotId,
    tplStore,
    initSlotTexts,
    refreshSlotTexts,
    handleSlotInput,
    handleSlotBlur,
    handleTemplateSelect,
    handleSaveTemplate,
    handleOpenSelector,
    handleRemoveSlot,
  }
}
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/composables/useTemplates.js"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/composables/useTemplates.js
git commit -m "feat: add useTemplates composable"
```

---

### Task 7: Create `useCanvasEditor` composable

**Files:**
- Create: `src/composables/useCanvasEditor.js`

- [ ] **Step 1: Write the composable**

```javascript
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Canvas, StaticCanvas, Rect, Line, FabricImage, IText, Textbox } from 'fabric'
import { useCanvasStore } from '../stores/canvas.js'
import { useCanvasHistory } from './useCanvasHistory.js'
import { useSettings } from './useSettings.js'

export function useCanvasEditor() {
  const store = useCanvasStore()
  const { effectiveCanvasSize } = useSettings()
  const canvasWrapper = ref(null)
  const imageInput = ref(null)
  const fabricCanvasRef = ref(null)
  let fabricCanvas = null
  const hasSelection = ref(false)
  const selectedFabricObject = ref(null)
  const { undo, redo, saveState, canUndo, canRedo } = useCanvasHistory(fabricCanvasRef)

  function emitSelection() {
    const active = fabricCanvas?.getActiveObject()
    if (active instanceof IText) {
      store.selectedObjectType = 'text'
      store.selectedFontSize = active.fontSize
      store.selectedFontFamily = active.fontFamily
    } else {
      store.selectedObjectType = active ? active.type : null
    }
    selectedFabricObject.value = active
  }

  function notifyChange() {
    saveState()
    // caller hooks into canvas-changed via a callback, set externally
  }

  let onCanvasChangedCb = null
  function onCanvasChanged(fn) { onCanvasChangedCb = fn }

  function _callCanvasChanged() {
    saveState()
    if (onCanvasChangedCb) onCanvasChangedCb()
  }

  function initCanvas() {
    const { w, h } = effectiveCanvasSize.value

    if (fabricCanvas) {
      fabricCanvas.dispose()
      fabricCanvas = null
    }

    let el = document.getElementById('fabric-canvas')
    if (el) el.remove()
    el = document.createElement('canvas')
    el.id = 'fabric-canvas'
    if (canvasWrapper.value) canvasWrapper.value.appendChild(el)

    fabricCanvas = new Canvas(el, {
      width: w,
      height: h,
      backgroundColor: '#ffffff',
      selection: true,
      preserveObjectStacking: true,
    })
    fabricCanvasRef.value = fabricCanvas

    let _scalingData = null

    fabricCanvas.on('selection:created', () => { _scalingData = null; hasSelection.value = true; emitSelection() })
    fabricCanvas.on('selection:updated', () => { _scalingData = null; hasSelection.value = true; emitSelection() })
    fabricCanvas.on('selection:cleared', () => { _scalingData = null; hasSelection.value = false; emitSelection() })

    fabricCanvas.on('mouse:up', (e) => {
      if (e.target) nextTick(() => emitSelection())
    })

    fabricCanvas.on('object:added', _callCanvasChanged)
    fabricCanvas.on('object:modified', (e) => {
      if (e.target instanceof IText) {
        _callCanvasChanged()
        emitSelection()
      } else {
        _callCanvasChanged()
      }
    })
    fabricCanvas.on('object:removed', _callCanvasChanged)
    fabricCanvas.on('text:changed', _callCanvasChanged)

    // keyboard shortcuts
    function onKeyDown(e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') { e.preventDefault(); undo() }
      if ((e.ctrlKey || e.metaKey) && e.key === 'y') { e.preventDefault(); redo() }
      if (e.key === 'Delete' || e.key === 'Backspace') {
        const active = fabricCanvas?.getActiveObject()
        if (active && document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
          e.preventDefault()
          fabricCanvas.remove(active)
          fabricCanvas.discardActiveObject()
          _callCanvasChanged()
        }
      }
    }
    document.addEventListener('keydown', onKeyDown)
    fabricCanvas._keydownHandler = onKeyDown

    resizeCanvas()
    _callCanvasChanged()
  }

  function resizeCanvas() {
    if (!fabricCanvas || !canvasWrapper.value) return
    const { w, h } = effectiveCanvasSize.value
    const scale = (store.imageOptions.displayScale || 100) / 100
    const cssW = Math.round(w * scale)
    const cssH = Math.round(h * scale)
    fabricCanvas.setZoom(1)
    fabricCanvas.setDimensions({ width: cssW, height: cssH }, { cssOnly: true })
    fabricCanvas.renderAll()
  }

  function addText() {
    const text = new Textbox('双击编辑', {
      left: 20, top: 20, fontSize: 24, fill: '#000000',
      fontFamily: 'Arial, Microsoft YaHei, sans-serif',
      width: 300,
      splitByGrapheme: true,
    })
    text._getMinWidth = function () { return 1 }
    fabricCanvas.add(text)
    text.initDimensions()
    text.setCoords()
    fabricCanvas.setActiveObject(text)
    fabricCanvas.requestRenderAll()
    nextTick(() => emitSelection())
  }

  function addRect() {
    const rect = new Rect({
      left: 20, top: 20, width: 80, height: 40,
      fill: 'transparent', stroke: '#000000', strokeWidth: 2,
    })
    fabricCanvas.add(rect)
    fabricCanvas.setActiveObject(rect)
    nextTick(() => emitSelection())
  }

  function addLine() {
    const line = new Line([10, 10, 100, 10], { stroke: '#000000', strokeWidth: 2 })
    fabricCanvas.add(line)
    fabricCanvas.setActiveObject(line)
    nextTick(() => emitSelection())
  }

  function addImage() {
    imageInput.value?.click()
  }

  function onImageSelected(e) {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      FabricImage.fromURL(ev.target.result).then((img) => {
        const maxW = fabricCanvas.width * 0.8
        const maxH = fabricCanvas.height * 0.8
        if (img.width > maxW || img.height > maxH) {
          img.scale(Math.min(maxW / img.width, maxH / img.height))
        }
        img.set({ left: 10, top: 10 })
        fabricCanvas.add(img)
        fabricCanvas.setActiveObject(img)
        nextTick(() => emitSelection())
      })
    }
    reader.readAsDataURL(file)
    imageInput.value.value = ''
  }

  function deleteSelected() {
    const active = fabricCanvas?.getActiveObject()
    if (active) { fabricCanvas.remove(active); fabricCanvas.discardActiveObject(); _callCanvasChanged() }
  }

  function bringForward() {
    const active = fabricCanvas?.getActiveObject()
    if (active) { fabricCanvas.bringObjectForward(active); fabricCanvas.requestRenderAll(); _callCanvasChanged() }
  }

  function sendBackward() {
    const active = fabricCanvas?.getActiveObject()
    if (active) { fabricCanvas.sendObjectBackwards(active); fabricCanvas.requestRenderAll(); _callCanvasChanged() }
  }

  function clearCanvas() {
    fabricCanvas?.clear()
    if (fabricCanvas) { fabricCanvas.backgroundColor = '#ffffff'; fabricCanvas.renderAll() }
    _callCanvasChanged()
  }

  function loadFromJSON(canvasJson) {
    if (!fabricCanvas || !canvasJson) return Promise.resolve()
    return fabricCanvas.loadFromJSON(canvasJson).then(() => {
      for (const obj of fabricCanvas.getObjects()) {
        if (obj.slotId) {
          obj.set({ stroke: '#409eff', strokeWidth: 1, strokeDashArray: [4, 2] })
        }
      }
      fabricCanvas.requestRenderAll()
      resizeCanvas()
      _callCanvasChanged()
    })
  }

  function markAsSlot(obj, slotId) {
    if (!obj || !(obj instanceof IText)) return
    obj.set('slotId', slotId)
    obj.set('slotLabel', slotId)
    obj.set({ stroke: '#409eff', strokeWidth: 1, strokeDashArray: [4, 2] })
    fabricCanvas.requestRenderAll()
    _callCanvasChanged()
  }

  function unmarkSlot(obj) {
    if (!obj) return
    obj.set({ slotId: null, slotLabel: null, stroke: null, strokeWidth: 0, strokeDashArray: null })
    fabricCanvas.requestRenderAll()
    _callCanvasChanged()
  }

  function getSlots() {
    if (!fabricCanvas) return []
    const slots = []
    for (const obj of fabricCanvas.getObjects()) {
      if (obj.slotId && obj instanceof IText) {
        slots.push({ id: obj.slotId, label: obj.slotLabel || obj.slotId, defaultText: obj.text })
      }
    }
    return slots
  }

  function getCanvasObjects() {
    return fabricCanvas ? fabricCanvas.getObjects() : []
  }

  function setFontSize(size) {
    const active = fabricCanvas?.getActiveObject()
    if (active instanceof IText) {
      active.fontSize = size
      active.setCoords()
      fabricCanvas.requestRenderAll()
      _callCanvasChanged()
      emitSelection()
    }
  }

  function setFontFamily(family) {
    const active = fabricCanvas?.getActiveObject()
    if (active instanceof IText) {
      active.fontFamily = family
      active.setCoords()
      fabricCanvas.requestRenderAll()
      _callCanvasChanged()
      emitSelection()
    }
  }

  function getCanvasImageBase64() {
    return new Promise((resolve, reject) => {
      try {
        if (!fabricCanvas) { reject(new Error('Canvas not initialized')); return }
        const json = fabricCanvas.toJSON(['slotId', 'slotLabel'])
        if (!json || !json.objects) { resolve(null); return }
        const { w, h } = effectiveCanvasSize.value
        const offscreen = new StaticCanvas(null, { width: w, height: h, backgroundColor: '#ffffff' })
        offscreen.loadFromJSON(json).then(() => {
          offscreen.renderAll()
          const dataUrl = offscreen.toDataURL({ format: 'png', multiplier: 1, enableRetinaScaling: false })
          offscreen.dispose()
          resolve(dataUrl.split(',')[1])
        }).catch(reject)
      } catch (e) { reject(e) }
    })
  }

  function saveStateToStore() {
    if (!fabricCanvas) return
    for (const obj of fabricCanvas.getObjects()) {
      if (obj.slotId) {
        obj.set({ slotId: obj.slotId, slotLabel: obj.slotLabel || obj.slotId })
      }
    }
    const objectsData = fabricCanvas.getObjects().map(obj => obj.toObject(['slotId', 'slotLabel']))
    const { w, h } = effectiveCanvasSize.value
    store.canvasJson = JSON.stringify({ version: fabricCanvas.version || '6.9.1', objects: objectsData, width: w, height: h })
  }

  // wire saveStateToStore into change callback
  const _originalChangeCb = _callCanvasChanged
  function _callCanvasChanged() {
    saveStateToStore()
    saveState()
    if (onCanvasChangedCb) onCanvasChangedCb()
  }

  onMounted(() => {
    nextTick(() => initCanvas())
    window.addEventListener('resize', resizeCanvas)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', resizeCanvas)
    if (fabricCanvas?._keydownHandler) {
      document.removeEventListener('keydown', fabricCanvas._keydownHandler)
    }
    fabricCanvas?.dispose()
  })

  watch(effectiveCanvasSize, () => {
    if (fabricCanvas) resizeCanvas()
  }, { deep: true })

  watch(() => store.imageOptions.displayScale, () => {
    if (fabricCanvas) resizeCanvas()
  })

  return {
    canvasWrapper,
    imageInput,
    hasSelection,
    selectedFabricObject,
    canUndo,
    canRedo,
    undo,
    redo,
    initCanvas,
    resizeCanvas,
    addText,
    addRect,
    addLine,
    addImage,
    onImageSelected,
    deleteSelected,
    bringForward,
    sendBackward,
    clearCanvas,
    loadFromJSON,
    markAsSlot,
    unmarkSlot,
    getSlots,
    getCanvasObjects,
    setFontSize,
    setFontFamily,
    getCanvasImageBase64,
    onCanvasChanged,
    emitSelection,
  }
}
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/composables/useCanvasEditor.js"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/composables/useCanvasEditor.js
git commit -m "feat: add useCanvasEditor composable with keyboard shortcuts and history"
```

---

### Task 8: Create `SettingsPanel.vue`

**Files:**
- Create: `src/components/SettingsPanel.vue`

- [ ] **Step 1: Write the component**

```vue
<template>
  <div class="panel-section">
    <h3>图像设置</h3>
    <el-form label-width="80px" size="small">
      <el-form-item label="标签宽(mm)">
        <el-input-number v-model="imageOptions.labelWidthMm" :min="10" :max="200" size="small" style="width:80px" controls-position="right" />
      </el-form-item>
      <el-form-item label="标签高(mm)">
        <el-input-number v-model="imageOptions.labelHeightMm" :min="10" :max="200" size="small" style="width:80px" controls-position="right" />
      </el-form-item>
      <el-form-item label="DPI">
        <el-select v-model="imageOptions.dpi" size="small" style="width:100px">
          <el-option :value="203" label="203" />
          <el-option :value="300" label="300" />
          <el-option :value="600" label="600" />
        </el-select>
      </el-form-item>
    </el-form>
    <el-collapse>
      <el-collapse-item title="高级处理" name="advanced">
        <el-form label-width="80px" size="small">
          <el-form-item label="抖动">
            <el-switch v-model="imageOptions.dither" size="small" active-text="Floyd-Steinberg" />
          </el-form-item>
          <el-form-item label="阈值" v-if="!imageOptions.dither">
            <el-slider v-model="imageOptions.threshold" :max="255" :show-tooltip="false" size="small" />
            <span class="value-tag">{{ imageOptions.threshold }}</span>
          </el-form-item>
          <el-form-item label="对比度">
            <el-slider v-model="imageOptions.contrast" :min="0.5" :max="3.0" :step="0.1" :show-tooltip="false" size="small" />
            <span class="value-tag">{{ imageOptions.contrast.toFixed(1) }}</span>
          </el-form-item>
          <el-form-item label="亮度">
            <el-slider v-model="imageOptions.brightness" :min="0.3" :max="2.0" :step="0.1" :show-tooltip="false" size="small" />
            <span class="value-tag">{{ imageOptions.brightness.toFixed(1) }}</span>
          </el-form-item>
          <el-form-item label="方向">
            <el-select v-model="imageOptions.rotation" size="small" style="width:100px">
              <el-option :value="0" label="0°" />
              <el-option :value="90" label="90°" />
              <el-option :value="180" label="180°" />
              <el-option :value="270" label="270°" />
            </el-select>
          </el-form-item>
          <el-form-item label="反色">
            <el-switch v-model="imageOptions.invert" size="small" />
          </el-form-item>
        </el-form>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
defineProps({
  imageOptions: { type: Object, required: true },
})
</script>

<style scoped>
.panel-section { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.panel-section h3 { font-size: 13px; font-weight: 600; margin-bottom: 10px; color: #303133; }
.value-tag { display: inline-block; width: 30px; text-align: right; font-size: 11px; color: #409eff; margin-left: 6px; }
</style>
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/components/SettingsPanel.vue"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/components/SettingsPanel.vue
git commit -m "feat: add SettingsPanel component"
```

---

### Task 9: Create `TextSettingsPanel.vue`

**Files:**
- Create: `src/components/TextSettingsPanel.vue`

- [ ] **Step 1: Write the component**

```vue
<template>
  <div class="panel-section" v-if="selectedType === 'text'">
    <h3>文字设置</h3>
    <el-form label-width="60px" size="small">
      <el-form-item label="字体">
        <el-select :model-value="fontFamily" size="small" style="width:160px" @change="$emit('update:fontFamily', $event)">
          <el-option value="Microsoft YaHei" label="微软雅黑" />
          <el-option value="SimSun" label="宋体" />
          <el-option value="SimHei" label="黑体" />
          <el-option value="KaiTi" label="楷体" />
          <el-option value="FangSong" label="仿宋" />
          <el-option value="Arial" label="Arial" />
          <el-option value="Times New Roman" label="Times New Roman" />
          <el-option value="Courier New" label="Courier New" />
          <el-option value="Verdana" label="Verdana" />
        </el-select>
      </el-form-item>
      <el-form-item label="字号">
        <el-input-number :model-value="fontSize" :min="6" :max="200" :step="1" size="small" style="width:100px" controls-position="right" @change="$emit('update:fontSize', $event)" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
defineProps({
  selectedType: { type: String, default: null },
  fontSize: { type: Number, default: 24 },
  fontFamily: { type: String, default: 'Microsoft YaHei' },
})
defineEmits(['update:fontSize', 'update:fontFamily'])
</script>

<style scoped>
.panel-section { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.panel-section h3 { font-size: 13px; font-weight: 600; margin-bottom: 10px; color: #303133; }
</style>
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/components/TextSettingsPanel.vue"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/components/TextSettingsPanel.vue
git commit -m "feat: add TextSettingsPanel component"
```

---

### Task 10: Create `PreviewPanel.vue`

**Files:**
- Create: `src/components/PreviewPanel.vue`

- [ ] **Step 1: Write the component**

```vue
<template>
  <div class="panel-section">
    <h3>预览</h3>
    <div class="preview-box" @click="$emit('refresh')">
      <div v-if="loading" class="preview-loading"><LoadingOne theme="outline" size="20" spin/></div>
      <img v-else-if="dataUrl" :src="dataUrl" class="preview-img" />
      <div v-else class="preview-empty">点击刷新预览</div>
    </div>
    <div class="preview-info" v-if="info">
      {{ info.width }}×{{ info.height }}px | {{ info.bytesPerRow }}B/行
    </div>
  </div>
</template>

<script setup>
import { LoadingOne } from '@icon-park/vue-next'

defineProps({
  dataUrl: { type: String, default: null },
  info: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})
defineEmits(['refresh'])
</script>

<style scoped>
.panel-section { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.panel-section h3 { font-size: 13px; font-weight: 600; margin-bottom: 10px; color: #303133; }
.preview-box { width: 100%; min-height: 100px; background: #f5f7fa; border-radius: 4px; display: flex; align-items: center; justify-content: center; cursor: pointer; border: 1px dashed #dcdfe6; overflow: hidden; }
.preview-box:hover { border-color: #409eff; }
.preview-img { width: 100%; display: block; image-rendering: pixelated; }
.preview-empty { color: #c0c4cc; font-size: 12px; }
.preview-loading { color: #909399; }
.preview-info { font-size: 11px; color: #909399; text-align: center; margin-top: 4px; }
</style>
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/components/PreviewPanel.vue"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/components/PreviewPanel.vue
git commit -m "feat: add PreviewPanel component"
```

---

### Task 11: Create `ExportButton.vue`

**Files:**
- Create: `src/components/ExportButton.vue`

- [ ] **Step 1: Write the component**

```vue
<template>
  <div class="panel-section">
    <el-button @click="$emit('export')" style="width:100%">
      <Save theme="outline" size="14"/> 导出 TSPL 代码
    </el-button>
  </div>
</template>

<script setup>
import { Save } from '@icon-park/vue-next'
defineEmits(['export'])
</script>

<style scoped>
.panel-section { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
</style>
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/components/ExportButton.vue"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/components/ExportButton.vue
git commit -m "feat: add ExportButton component"
```

---

### Task 12: Create `SlotMarkerPanel.vue`

**Files:**
- Create: `src/components/SlotMarkerPanel.vue`

- [ ] **Step 1: Write the component**

```vue
<template>
  <template v-if="selectedObject && selectedObjectType === 'text' && !selectedObject.slotId">
    <div class="panel-section">
      <h3>设为占位符</h3>
      <el-form label-width="60px" size="small">
        <el-form-item label="槽位ID">
          <el-input :model-value="slotEditId" size="small" placeholder="例如: productName" @input="$emit('update:slotEditId', $event)" />
        </el-form-item>
        <el-form-item label="标签名">
          <el-input :model-value="slotEditLabel" size="small" placeholder="显示名称" @input="$emit('update:slotEditLabel', $event)" />
        </el-form-item>
        <el-button size="small" type="primary" @click="$emit('mark')" style="width:100%">
          标记为占位符
        </el-button>
      </el-form>
    </div>
  </template>

  <template v-if="selectedObject && selectedObject.slotId">
    <div class="panel-section">
      <h3>占位符: {{ selectedObject.slotId }}</h3>
      <el-button size="small" type="warning" @click="$emit('unmark')" style="width:100%">
        取消占位符
      </el-button>
    </div>
  </template>
</template>

<script setup>
defineProps({
  selectedObject: { type: Object, default: null },
  selectedObjectType: { type: String, default: null },
  slotEditId: { type: String, default: '' },
  slotEditLabel: { type: String, default: '' },
})
defineEmits(['mark', 'unmark', 'update:slotEditId', 'update:slotEditLabel'])
</script>

<style scoped>
.panel-section { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.panel-section h3 { font-size: 13px; font-weight: 600; margin-bottom: 10px; color: #303133; }
</style>
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/components/SlotMarkerPanel.vue"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/components/SlotMarkerPanel.vue
git commit -m "feat: add SlotMarkerPanel component"
```

---

### Task 13: Create `EditorToolbar.vue`

**Files:**
- Create: `src/components/EditorToolbar.vue`

- [ ] **Step 1: Write the component**

```vue
<template>
  <div class="editor-toolbar">
    <el-button-group>
      <el-button size="small" @click="$emit('add-text')"><EditTwo theme="outline" size="14" :strokeWidth="3"/> 文字</el-button>
      <el-button size="small" @click="$emit('add-rect')"><Rectangle theme="outline" size="14" :strokeWidth="3"/> 矩形</el-button>
      <el-button size="small" @click="$emit('add-line')"><DividingLine theme="outline" size="14" :strokeWidth="3"/> 线条</el-button>
      <el-button size="small" @click="$emit('add-image')"><Pic theme="outline" size="14" :strokeWidth="3"/> 贴图</el-button>
    </el-button-group>
    <el-button-group style="margin-left: 12px;">
      <el-button size="small" @click="$emit('undo')" :disabled="!canUndo">撤销</el-button>
      <el-button size="small" @click="$emit('redo')" :disabled="!canRedo">重做</el-button>
    </el-button-group>
    <el-button-group style="margin-left: 12px;">
      <el-button size="small" @click="$emit('bring-forward')" :disabled="!hasSelection">上移</el-button>
      <el-button size="small" @click="$emit('send-backward')" :disabled="!hasSelection">下移</el-button>
    </el-button-group>
    <el-button size="small" style="margin-left: 12px;" @click="$emit('delete')" :disabled="!hasSelection">
      <DeleteOne theme="outline" size="14" :strokeWidth="3"/> 删除
    </el-button>
    <el-button size="small" type="danger" style="margin-left: 12px;" @click="$emit('clear')">清空</el-button>
  </div>
</template>

<script setup>
import { EditTwo, Rectangle, DividingLine, Pic, DeleteOne } from '@icon-park/vue-next'

defineProps({
  hasSelection: { type: Boolean, default: false },
  canUndo: { type: Boolean, default: false },
  canRedo: { type: Boolean, default: false },
})
defineEmits(['add-text', 'add-rect', 'add-line', 'add-image', 'undo', 'redo', 'delete', 'bring-forward', 'send-backward', 'clear'])
</script>

<style scoped>
.editor-toolbar { display: flex; align-items: center; padding: 8px 12px; background: #f5f7fa; border-bottom: 1px solid #e4e7ed; flex-wrap: wrap; gap: 4px; }
</style>
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/components/EditorToolbar.vue"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/components/EditorToolbar.vue
git commit -m "feat: add EditorToolbar component"
```

---

### Task 14: Create `TemplatePanel.vue`

**Files:**
- Create: `src/components/TemplatePanel.vue`

- [ ] **Step 1: Write the component**

```vue
<template>
  <div class="panel-section">
    <h3>模板</h3>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <el-button size="small" @click="$emit('open-selector')">选择模板</el-button>
      <el-button size="small" type="success" @click="$emit('save')">另存为模板</el-button>
    </div>
  </div>

  <div class="panel-section" v-if="slots.length > 0">
    <h3>占位符槽位</h3>
    <div class="slot-list">
      <div v-for="slot in slots" :key="slot.id" class="slot-item">
        <div class="slot-name">{{ slot.id }}</div>
        <el-input
          size="small"
          :model-value="slotTexts[slot.id]"
          @input="(val) => $emit('slot-input', slot.id, val)"
          @focus="$emit('slot-focus', slot.id)"
          @blur="$emit('slot-blur', slot.id)"
          class="slot-text-input"
          :placeholder="slot.label || slot.id"
        />
        <el-button size="small" type="danger" circle @click="$emit('remove-slot', slot.id)" class="slot-del-btn">×</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  slots: { type: Array, default: () => [] },
  slotTexts: { type: Object, default: () => ({}) },
})
defineEmits(['open-selector', 'save', 'slot-input', 'slot-focus', 'slot-blur', 'remove-slot'])
</script>

<style scoped>
.panel-section { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.panel-section h3 { font-size: 13px; font-weight: 600; margin-bottom: 10px; color: #303133; }
.slot-list { max-height: 200px; overflow-y: auto; }
.slot-item { display: flex; align-items: center; gap: 6px; padding: 4px 0; border-bottom: 1px solid #f0f0f0; }
.slot-item:last-child { border-bottom: none; }
.slot-name { font-size: 12px; font-weight: 600; color: #409eff; min-width: 70px; flex-shrink: 0; }
.slot-text-input { flex: 1; min-width: 0; }
.slot-del-btn { flex-shrink: 0; }
</style>
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/components/TemplatePanel.vue"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/components/TemplatePanel.vue
git commit -m "feat: add TemplatePanel component"
```

---

### Task 15: Create `BottomBar.vue`

**Files:**
- Create: `src/components/BottomBar.vue`

- [ ] **Step 1: Write the component**

```vue
<template>
  <div class="app-bottom">
    <div class="bottom-left">
      <span class="dot" :class="backendStatus"></span>
      <span class="backend-text">{{ backendStatus === 'online' ? '后端在线' : backendStatus === 'checking' ? '检测中' : '离线' }}</span>
      <el-button v-if="backendStatus === 'offline'" size="small" @click="$emit('restart')" :loading="restarting" style="margin-left:8px">重启后端</el-button>
      <span class="pixel-info">{{ pixelInfo }}</span>
    </div>
    <div class="bottom-right">
      <span class="zoom-control">
        <span class="zoom-label">缩放</span>
        <el-slider :model-value="displayScale" :min="100" :max="300" :step="10" :show-tooltip="false" size="small" style="width:100px" @change="$emit('update:displayScale', $event)" />
        <span class="zoom-value">{{ displayScale }}%</span>
      </span>
      <el-select :model-value="printerName" size="small" style="width:200px;margin-left:12px" filterable placeholder="选择打印机" @change="$emit('update:printerName', $event)">
        <el-option v-for="p in printers" :key="p" :value="p" :label="p" />
      </el-select>
      <el-input-number :model-value="copies" :min="1" :max="999" size="small" style="width:80px;margin-left:8px" controls-position="right" @change="$emit('update:copies', $event)" />
      <el-button type="primary" size="small" @click="$emit('print')" :loading="printing" style="margin-left:8px">
        <Printer theme="outline" size="14"/> 打印
      </el-button>
      <span class="status-text">{{ statusMsg }}</span>
    </div>
  </div>
</template>

<script setup>
import { Printer } from '@icon-park/vue-next'

defineProps({
  backendStatus: { type: String, default: 'checking' },
  restarting: { type: Boolean, default: false },
  pixelInfo: { type: String, default: '' },
  displayScale: { type: Number, default: 100 },
  printerName: { type: String, default: '' },
  printers: { type: Array, default: () => [] },
  copies: { type: Number, default: 1 },
  printing: { type: Boolean, default: false },
  statusMsg: { type: String, default: '就绪' },
})
defineEmits(['restart', 'update:displayScale', 'update:printerName', 'update:copies', 'print'])
</script>

<style scoped>
.app-bottom { display: flex; align-items: center; justify-content: space-between; height: 36px; padding: 0 12px; background: #fff; border-top: 1px solid #e4e7ed; flex-shrink: 0; }
.bottom-left { display: flex; align-items: center; gap: 6px; }
.bottom-right { display: flex; align-items: center; gap: 4px; }
.zoom-control { display: flex; align-items: center; gap: 6px; }
.zoom-label { font-size: 12px; color: #909399; }
.zoom-value { font-size: 12px; color: #409eff; min-width: 36px; text-align: right; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot.online { background: #67c23a; }
.dot.offline { background: #f56c6c; }
.dot.checking { background: #e6a23c; animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0.4; } }
.backend-text { font-size: 12px; color: #909399; }
.pixel-info { font-size: 12px; color: #909399; margin-left: 12px; }
.status-text { font-size: 12px; color: #909399; margin-left: 8px; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
```

- [ ] **Step 2: Verify file created**

Run: `Test-Path -LiteralPath "src/components/BottomBar.vue"`
Expected: True

- [ ] **Step 3: Commit**

```bash
git add src/components/BottomBar.vue
git commit -m "feat: add BottomBar component"
```

---

### Task 16: Rewrite `CanvasEditor.vue` as thin wrapper

**Files:**
- Modify: `src/components/CanvasEditor.vue`

- [ ] **Step 1: Read current file**

Read `src/components/CanvasEditor.vue` to confirm current content.

- [ ] **Step 2: Rewrite the component**

Replace entire content of `src/components/CanvasEditor.vue` with:

```vue
<template>
  <div class="editor-container">
    <EditorToolbar
      :hasSelection="hasSelection"
      :canUndo="canUndo"
      :canRedo="canRedo"
      @add-text="addText"
      @add-rect="addRect"
      @add-line="addLine"
      @add-image="addImage"
      @undo="undo"
      @redo="redo"
      @delete="deleteSelected"
      @bring-forward="bringForward"
      @send-backward="sendBackward"
      @clear="clearCanvas"
    />
    <div class="canvas-wrapper" ref="canvasWrapperRef">
      <canvas id="fabric-canvas"></canvas>
    </div>
    <input type="file" ref="imageInputRef" accept="image/*" style="display: none" @change="onImageSelected" />
  </div>
</template>

<script setup>
import { useCanvasEditor } from '../composables/useCanvasEditor.js'
import EditorToolbar from './EditorToolbar.vue'

const {
  canvasWrapper,
  imageInput,
  hasSelection,
  selectedFabricObject,
  canUndo,
  canRedo,
  undo,
  redo,
  addText,
  addRect,
  addLine,
  addImage,
  onImageSelected,
  deleteSelected,
  bringForward,
  sendBackward,
  clearCanvas,
  loadFromJSON,
  markAsSlot,
  unmarkSlot,
  getSlots,
  getCanvasObjects,
  setFontSize,
  setFontFamily,
  getCanvasImageBase64,
  resizeCanvas,
  onCanvasChanged,
} = useCanvasEditor()

const canvasWrapperRef = canvasWrapper
const imageInputRef = imageInput

const emit = defineEmits(['canvas-changed', 'selection-changed'])

// Wire composable callback to parent emit
onCanvasChanged(() => emit('canvas-changed'))

defineExpose({
  getCanvasImageBase64,
  clearCanvas,
  setFontSize,
  setFontFamily,
  loadFromJSON,
  markAsSlot,
  unmarkSlot,
  getSlots,
  getCanvasObjects,
  resizeCanvas,
})
</script>

<style scoped>
.editor-container { display: flex; flex-direction: column; height: 100%; }
.canvas-wrapper { flex: 1; display: flex; align-items: center; justify-content: center; overflow: hidden; background: #e8e8e8; padding: 4px; }
.canvas-wrapper :deep(canvas) { box-shadow: 0 2px 12px rgba(0,0,0,0.15); }
</style>
```

- [ ] **Step 3: Verify the file writes successfully**

Run: `Test-Path -LiteralPath "src/components/CanvasEditor.vue"`
Expected: True

- [ ] **Step 4: Commit**

```bash
git add src/components/CanvasEditor.vue
git commit -m "refactor: rewrite CanvasEditor as thin composable wrapper"
```

---

### Task 17: Rewrite `App.vue` as orchestration shell

**Files:**
- Modify: `src/App.vue`

- [ ] **Step 1: Read current file**

Read `src/App.vue` to confirm current content.

- [ ] **Step 2: Replace entire content**

```vue
<template>
  <div class="app-root">
    <TitleBar />

    <TemplateSelector
      v-if="tplStore.showSelector"
      @select="(id) => tplMgr.handleTemplateSelect(id, editorRef?.loadFromJSON, editorRef?.getCanvasObjects, editorRef?.resizeCanvas)"
    />

    <div class="app-body">
      <div class="editor-area">
        <CanvasEditor ref="editorRef" @canvas-changed="onCanvasChanged" @selection-changed="onSelectionChanged" />
      </div>

      <div class="side-panel">
        <SettingsPanel :imageOptions="store.imageOptions" />
        <TextSettingsPanel
          :selectedType="store.selectedObjectType"
          :fontSize="store.selectedFontSize"
          :fontFamily="store.selectedFontFamily"
          @update:fontSize="(v) => editorRef?.setFontSize(v)"
          @update:fontFamily="(v) => editorRef?.setFontFamily(v)"
        />
        <TemplatePanel
          :slots="tplStore.slots"
          :slotTexts="tplMgr.slotTexts"
          @open-selector="tplMgr.handleOpenSelector()"
          @save="tplMgr.handleSaveTemplate(editorRef?.getCanvasObjects, editorRef?.getSlots, editorRef?.getCanvasImageBase64)"
          @slot-input="(id, val) => tplMgr.handleSlotInput(id, val, editorRef?.getCanvasObjects)"
          @slot-focus="(id) => tplMgr.focusedSlotId = id"
          @slot-blur="(id) => tplMgr.handleSlotBlur(id, editorRef?.getCanvasObjects)"
          @remove-slot="(id) => tplMgr.handleRemoveSlot(id, editorRef?.unmarkSlot, editorRef?.getSlots)"
        />
        <SlotMarkerPanel
          :selectedObject="selectedFabricObject"
          :selectedObjectType="store.selectedObjectType"
          :slotEditId="slotEditId"
          :slotEditLabel="slotEditLabel"
          @update:slotEditId="(v) => slotEditId = v"
          @update:slotEditLabel="(v) => slotEditLabel = v"
          @mark="handleMarkSlot"
          @unmark="handleUnmarkSlot"
        />
        <PreviewPanel
          :dataUrl="previewMgr.previewDataUrl.value"
          :info="previewMgr.previewInfo.value"
          :loading="previewMgr.previewLoading.value"
          @refresh="() => previewMgr.refreshPreview(editorRef?.getCanvasImageBase64)"
        />
        <ExportButton @export="() => printMgr.doExportTSPL(editorRef?.getCanvasImageBase64)" />
      </div>
    </div>

    <BottomBar
      :backendStatus="backendMgr.backendStatus.value"
      :restarting="restarting"
      :pixelInfo="settingsMgr.pixelInfo.value.text"
      :displayScale="store.imageOptions.displayScale"
      :printerName="store.printerName"
      :printers="store.printers"
      :copies="store.copies"
      :printing="printMgr.printing.value"
      :statusMsg="store.statusMsg"
      @restart="restartBackend"
      @update:displayScale="(v) => store.imageOptions.displayScale = v"
      @update:printerName="(v) => store.printerName = v"
      @update:copies="(v) => store.copies = v"
      @print="() => printMgr.doPrint(editorRef?.getCanvasImageBase64)"
    />
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useCanvasStore } from './stores/canvas.js'
import { useTemplateStore } from './stores/template.js'
import { getPrinters } from './api/backend.js'
import { ElMessage } from 'element-plus'
import CanvasEditor from './components/CanvasEditor.vue'
import TitleBar from './components/TitleBar.vue'
import TemplateSelector from './components/TemplateSelector.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import TextSettingsPanel from './components/TextSettingsPanel.vue'
import TemplatePanel from './components/TemplatePanel.vue'
import SlotMarkerPanel from './components/SlotMarkerPanel.vue'
import PreviewPanel from './components/PreviewPanel.vue'
import ExportButton from './components/ExportButton.vue'
import BottomBar from './components/BottomBar.vue'
import { usePreview } from './composables/usePreview.js'
import { usePrint } from './composables/usePrint.js'
import { useSettings } from './composables/useSettings.js'
import { useTemplates } from './composables/useTemplates.js'
import { useBackendStatus } from './composables/useBackendStatus.js'

const store = useCanvasStore()
const tplStore = useTemplateStore()

const previewMgr = usePreview()
const printMgr = usePrint()
const settingsMgr = useSettings()
const backendMgr = useBackendStatus()
const tplMgr = useTemplates()

const editorRef = ref(null)
const restarting = ref(false)
const selectedFabricObject = ref(null)
const slotEditId = ref('')
const slotEditLabel = ref('')

function onCanvasChanged() {
  previewMgr.schedulePreview(() => editorRef.value?.getCanvasImageBase64())
  tplMgr.refreshSlotTexts(() => editorRef.value?.getCanvasObjects())
}

function onSelectionChanged(obj) {
  selectedFabricObject.value = obj
}

function handleMarkSlot() {
  if (!editorRef.value || !selectedFabricObject.value) return
  const id = slotEditId.value.trim()
  if (!id) { ElMessage.warning('请输入槽位ID'); return }
  editorRef.value.markAsSlot(selectedFabricObject.value, id)
  if (slotEditLabel.value) {
    selectedFabricObject.value.set('slotLabel', slotEditLabel.value.trim())
  }
  const slotDefs = editorRef.value.getSlots()
  tplStore.syncSlotsFromCanvas(slotDefs)
  slotEditId.value = ''
  slotEditLabel.value = ''
  tplMgr.initSlotTexts(() => editorRef.value?.getCanvasObjects())
  ElMessage.success(`已标记为占位符: ${id}`)
}

function handleUnmarkSlot() {
  if (!editorRef.value || !selectedFabricObject.value) return
  editorRef.value.unmarkSlot(selectedFabricObject.value)
  const slotDefs = editorRef.value.getSlots()
  tplStore.syncSlotsFromCanvas(slotDefs)
  tplMgr.initSlotTexts(() => editorRef.value?.getCanvasObjects())
  ElMessage.success('已取消占位符')
}

async function restartBackend() {
  if (window.electronAPI) {
    restarting.value = true
    try {
      await window.electronAPI.restartBackend()
      await new Promise((r) => setTimeout(r, 3000))
      await backendMgr.check()
    } finally {
      restarting.value = false
    }
  }
}

watch(
  () => ({ ...store.imageOptions }),
  () => { previewMgr.schedulePreview(() => editorRef.value?.getCanvasImageBase64(), 300) },
  { deep: true }
)

onMounted(async () => {
  backendMgr.startPolling()

  try {
    const res = await getPrinters()
    store.printers = res.data.printers
    if (store.printers.length && !store.printers.includes(store.printerName)) {
      store.printerName = store.printers[0]
    }
  } catch {}

  await tplStore.fetchTemplateList()
  tplStore.setShowSelector(true)

  if (window.electronAPI) {
    window.electronAPI.onBackendStatus((status) => {
      backendMgr.backendStatus.value = status
    })
  }
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Microsoft YaHei', Arial, sans-serif; overflow: hidden; background: #f0f2f5; }
#app { height: 100vh; display: flex; flex-direction: column; }
</style>

<style scoped>
.app-root { display: flex; flex-direction: column; height: 100vh; }
.app-body { flex: 1; display: flex; overflow: hidden; }
.editor-area { flex: 1; min-width: 0; background: #fff; margin: 8px; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.side-panel { width: 300px; min-width: 280px; margin: 8px 8px 8px 0; overflow-y: auto; }
</style>
```

- [ ] **Step 3: Verify the file**

Run: `Test-Path -LiteralPath "src/App.vue"`
Expected: True

- [ ] **Step 4: Commit**

```bash
git add src/App.vue
git commit -m "refactor: rewrite App.vue as 60-line orchestration shell"
```

---

### Task 18: Final integration — verify build and fix issues

**Files:**
- None new, check build

- [ ] **Step 1: Run Vite build to check for errors**

```bash
npx vite build
```

Expected: Build succeeds, no errors.

- [ ] **Step 2: If build fails, fix issues**

Common issues to check:
- Import paths in composables/components
- Missing `reactive` import in useTemplates
- `canvasWrapper` ref forwarding in CanvasEditor
- Fabric.js `StaticCanvas` import

- [ ] **Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: build integration fixes for frontend refactor"
```

- [ ] **Step 4: Run dev mode verification**

```bash
npm run dev
```

Expected: Electron window opens, Canvas editor works, preview refreshes, printing works, templates load/save, undo/redo with Ctrl+Z/Y/Delete, slot editing works.

- [ ] **Step 5: Update architecture doc**

Update `doc/ARCHITECTURE.md` sections 2.2 and 6 to reflect new component/composable structure.

- [ ] **Step 6: Final commit**

```bash
git add doc/ARCHITECTURE.md
git commit -m "docs: update architecture doc for frontend v2.0 refactor"
```
