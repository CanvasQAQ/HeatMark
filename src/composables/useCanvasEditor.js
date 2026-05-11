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

  let onCanvasChangedCb = null
  function onCanvasChanged(fn) { onCanvasChangedCb = fn }

  function _callCanvasChanged() {
    saveStateToStore()
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

    fabricCanvas.on('object:scaling', (e) => {
      if (e.target instanceof IText && _scalingData === null) {
        _scalingData = {
          initialFontSize: e.target.fontSize,
          initialWidth: e.target.width,
          corner: e.transform?.corner,
        }
      }
    })

    function finalizeTextScale(obj) {
      if (!_scalingData) return
      const { corner, initialFontSize } = _scalingData
      if (corner === 'ml' || corner === 'mr') {
        obj.scaleX = 1
        obj.scaleY = 1
        obj.setCoords()
      } else {
        const capturedScaleX = obj.scaleX
        const capturedScaleY = obj.scaleY
        obj.scaleX = 1
        obj.scaleY = 1
        const scale = (corner === 'mt' || corner === 'mb')
          ? Math.abs(capturedScaleY)
          : Math.max(Math.abs(capturedScaleX), Math.abs(capturedScaleY))
        obj.fontSize = Math.max(6, Math.round(initialFontSize * scale))
        obj.initDimensions()
        obj.setCoords()
      }
      _scalingData = null
    }

    fabricCanvas.on('object:modified', (e) => {
      if (e.target instanceof IText) {
        finalizeTextScale(e.target)
        fabricCanvas.requestRenderAll()
        emitSelection()
        _callCanvasChanged()
      } else {
        _callCanvasChanged()
      }
    })
    fabricCanvas.on('object:removed', _callCanvasChanged)
    fabricCanvas.on('text:changed', _callCanvasChanged)

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
    fabricCanvas.setWidth(w)
    fabricCanvas.setHeight(h)
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
