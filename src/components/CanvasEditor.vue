<template>
  <div class="editor-container">
    <div class="editor-toolbar">
      <el-button-group>
        <el-button size="small" @click="addText"><EditTwo theme="outline" size="14" :strokeWidth="3"/> 文字</el-button>
        <el-button size="small" @click="addRect"><Rectangle theme="outline" size="14" :strokeWidth="3"/> 矩形</el-button>
        <el-button size="small" @click="addLine"><DividingLine theme="outline" size="14" :strokeWidth="3"/> 线条</el-button>
        <el-button size="small" @click="addImage"><Pic theme="outline" size="14" :strokeWidth="3"/> 贴图</el-button>
      </el-button-group>
      <el-button-group style="margin-left: 12px;">
        <el-button size="small" @click="deleteSelected" :disabled="!hasSelection">
          <DeleteOne theme="outline" size="14" :strokeWidth="3"/> 删除
        </el-button>
        <el-button size="small" @click="bringForward" :disabled="!hasSelection">上移</el-button>
        <el-button size="small" @click="sendBackward" :disabled="!hasSelection">下移</el-button>
      </el-button-group>
      <el-button size="small" type="danger" style="margin-left: 12px;" @click="clearCanvas">清空</el-button>
    </div>
    <div class="canvas-wrapper" ref="canvasWrapper">
      <canvas id="fabric-canvas"></canvas>
    </div>
    <input type="file" ref="imageInput" accept="image/*" style="display: none" @change="onImageSelected" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useCanvasStore } from '../stores/canvas.js'
import { Canvas, StaticCanvas, Rect, Line, FabricImage, IText, Textbox } from 'fabric'
import { EditTwo, Rectangle, DividingLine, Pic, DeleteOne } from '@icon-park/vue-next'

const store = useCanvasStore()
const emit = defineEmits(['canvas-changed', 'selection-changed'])
const canvasWrapper = ref(null)
const imageInput = ref(null)
let fabricCanvas = null
const hasSelection = ref(false)

function emitChange() {
  saveState()
  emit('canvas-changed')
}

function emitSelection() {
  const active = fabricCanvas.getActiveObject()
  if (active instanceof IText) {
    store.selectedObjectType = 'text'
    store.selectedFontSize = active.fontSize
    store.selectedFontFamily = active.fontFamily
  } else {
    store.selectedObjectType = active ? active.type : null
  }
  emit('selection-changed', active)
}


onMounted(() => {
  nextTick(() => initCanvas())
  window.addEventListener('resize', resizeCanvas)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCanvas)
  if (fabricCanvas) fabricCanvas.dispose()
})

watch(() => store.effectiveCanvasSize, () => {
  if (fabricCanvas) {
    initCanvas()
  }
}, { deep: true })

watch(() => store.imageOptions.displayScale, () => {
  if (fabricCanvas) {
    resizeCanvas()
  }
})

function initCanvas() {
  const { w, h } = store.effectiveCanvasSize

  if (fabricCanvas) {
    fabricCanvas.dispose()
    fabricCanvas = null
  }

  let el = document.getElementById('fabric-canvas')
  if (el) {
    el.remove()
  }
  el = document.createElement('canvas')
  el.id = 'fabric-canvas'
  if (canvasWrapper.value) {
    canvasWrapper.value.appendChild(el)
  }

  fabricCanvas = new Canvas(el, {
    width: w,
    height: h,
    backgroundColor: '#ffffff',
    selection: true,
    preserveObjectStacking: true,
  })

  let _scalingData = null

  fabricCanvas.on('selection:created', () => { _scalingData = null; hasSelection.value = true; emitSelection() })
  fabricCanvas.on('selection:updated', () => { _scalingData = null; hasSelection.value = true; emitSelection() })
  fabricCanvas.on('selection:cleared', () => { _scalingData = null; hasSelection.value = false; emitSelection() })

  fabricCanvas.on('mouse:up', (e) => {
    if (e.target) {
      nextTick(() => emitSelection())
    }
  })

  fabricCanvas.on('object:added', emitChange)

  // 拖动开始时记录初始状态
  fabricCanvas.on('object:scaling', (e) => {
    if (e.target instanceof IText && _scalingData === null) {
      _scalingData = {
        initialFontSize: e.target.fontSize,
        initialWidth: e.target.width,
        corner: e.transform?.corner,
      }
    }
  })

  // 拖动结束：将 scale 归一化为 fontSize 或 width
  function finalizeTextScale(obj) {
    if (!_scalingData) return
    const { corner, initialFontSize } = _scalingData

    if (corner === 'ml' || corner === 'mr') {
      // 水平控制点 → Fabric.js 的 changeWidth 已直接修改了 obj.width
      // 文字在拖动过程中已经自动换行，只需更新控制点位置
      obj.scaleX = 1
      obj.scaleY = 1
      obj.setCoords()
    } else {
      // 垂直控制点或四角 → 将 scale 固化为字号
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
    }
    emitChange()
  })
  fabricCanvas.on('object:removed', emitChange)
  fabricCanvas.on('text:changed', emitChange)

  resizeCanvas()
  emit('canvas-changed')
}

function resizeCanvas() {
  if (!fabricCanvas || !canvasWrapper.value) return
  const wrapper = canvasWrapper.value
  const { w, h } = store.effectiveCanvasSize
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
  text._getMinWidth = function() { return 1 }
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
  imageInput.value.click()
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
  const active = fabricCanvas.getActiveObject()
  if (active) { fabricCanvas.remove(active); fabricCanvas.discardActiveObject() }
}

function bringForward() {
  const active = fabricCanvas.getActiveObject()
  if (active) {
    fabricCanvas.bringObjectForward(active)
    fabricCanvas.requestRenderAll()
    emitChange()
  }
}

function sendBackward() {
  const active = fabricCanvas.getActiveObject()
  if (active) {
    fabricCanvas.sendObjectBackwards(active)
    fabricCanvas.requestRenderAll()
    emitChange()
  }
}

function clearCanvas() {
  fabricCanvas.clear()
  fabricCanvas.backgroundColor = '#ffffff'
  fabricCanvas.renderAll()
}

function loadFromJSON(canvasJson) {
  if (!fabricCanvas || !canvasJson) return
  return fabricCanvas.loadFromJSON(canvasJson).then(() => {
    const objects = fabricCanvas.getObjects()
    for (const obj of objects) {
      if (obj.slotId) {
        obj.set({
          stroke: '#409eff',
          strokeWidth: 1,
          strokeDashArray: [4, 2],
        })
      }
    }
    fabricCanvas.requestRenderAll()
    resizeCanvas()
    emitChange()
  })
}

function markAsSlot(obj, slotId) {
  if (!obj || !(obj instanceof IText)) return
  obj.set('slotId', slotId)
  obj.set('slotLabel', slotId)
  obj.set({
    stroke: '#409eff',
    strokeWidth: 1,
    strokeDashArray: [4, 2],
  })
  fabricCanvas.requestRenderAll()
  emitChange()
}

function unmarkSlot(obj) {
  if (!obj) return
  obj.set({
    slotId: null,
    slotLabel: null,
    stroke: null,
    strokeWidth: 0,
    strokeDashArray: null,
  })
  fabricCanvas.requestRenderAll()
  emitChange()
}

function getSlots() {
  if (!fabricCanvas) return []
  const slots = []
  for (const obj of fabricCanvas.getObjects()) {
    if (obj.slotId && obj instanceof IText) {
      slots.push({
        id: obj.slotId,
        label: obj.slotLabel || obj.slotId,
        defaultText: obj.text,
      })
    }
  }
  return slots
}

function getCanvasObjects() {
  return fabricCanvas ? fabricCanvas.getObjects() : []
}

function saveState() {
  if (!fabricCanvas) return
  // Ensure all slot objects have their custom properties properly set
  for (const obj of fabricCanvas.getObjects()) {
    if (obj.slotId) {
      obj.set({ slotId: obj.slotId, slotLabel: obj.slotLabel || obj.slotId })
    }
  }
  const objectsData = fabricCanvas.getObjects().map(obj => {
    return obj.toObject(['slotId', 'slotLabel'])
  })
  const { w, h } = store.effectiveCanvasSize
  const json = {
    version: fabricCanvas.version || '6.9.1',
    objects: objectsData,
    width: w,
    height: h
  }
  store.canvasJson = JSON.stringify(json)
}

function getCanvasImageBase64() {
  return new Promise((resolve, reject) => {
    try {
      if (!fabricCanvas) {
        reject(new Error('Canvas not initialized'))
        return
      }
      const json = fabricCanvas.toJSON(['slotId', 'slotLabel'])
      if (!json || !json.objects) {
        resolve(null)
        return
      }
      const { w, h } = store.effectiveCanvasSize
      const offscreen = new StaticCanvas(null, {
        width: w,
        height: h,
        backgroundColor: '#ffffff',
      })
      offscreen.loadFromJSON(json).then(() => {
        offscreen.renderAll()
        const dataUrl = offscreen.toDataURL({ format: 'png', multiplier: 1, enableRetinaScaling: false })
        offscreen.dispose()
        resolve(dataUrl.split(',')[1])
      }).catch(reject)
    } catch (e) {
      reject(e)
    }
  })
}

function setFontSize(size) {
  const active = fabricCanvas.getActiveObject()
  if (active instanceof IText) {
    active.fontSize = size
    active.setCoords()
    fabricCanvas.requestRenderAll()
    emitChange()
    emitSelection()
  }
}

function setFontFamily(family) {
  const active = fabricCanvas.getActiveObject()
  if (active instanceof IText) {
    active.fontFamily = family
    active.setCoords()
    fabricCanvas.requestRenderAll()
    emitChange()
    emitSelection()
  }
}

defineExpose({ getCanvasImageBase64, clearCanvas, setFontSize, setFontFamily, loadFromJSON, markAsSlot, unmarkSlot, getSlots, getCanvasObjects, resizeCanvas })
</script>

<style scoped>
.editor-container { display: flex; flex-direction: column; height: 100%; }
.editor-toolbar { display: flex; align-items: center; padding: 8px 12px; background: #f5f7fa; border-bottom: 1px solid #e4e7ed; flex-wrap: wrap; gap: 4px; }
.canvas-wrapper { flex: 1; display: flex; align-items: center; justify-content: center; overflow: hidden; background: #e8e8e8; padding: 4px; }
.canvas-wrapper :deep(canvas) { box-shadow: 0 2px 12px rgba(0,0,0,0.15); }
</style>
