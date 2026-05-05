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
import { Canvas, Rect, Line, FabricImage, IText } from 'fabric'
import { EditTwo, Rectangle, DividingLine, Pic, DeleteOne } from '@icon-park/vue-next'

const store = useCanvasStore()
const emit = defineEmits(['canvas-changed'])
const canvasWrapper = ref(null)
const imageInput = ref(null)
let fabricCanvas = null
const hasSelection = ref(false)


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

function initCanvas() {
  if (fabricCanvas) {
    fabricCanvas.dispose()
    fabricCanvas = null
  }
  const { w, h } = store.effectiveCanvasSize
  fabricCanvas = new Canvas('fabric-canvas', {
    width: w,
    height: h,
    backgroundColor: '#ffffff',
    selection: true,
    preserveObjectStacking: true,
  })

  fabricCanvas.on('selection:created', () => { hasSelection.value = true })
  fabricCanvas.on('selection:updated', () => { hasSelection.value = true })
  fabricCanvas.on('selection:cleared', () => { hasSelection.value = false })

  const emitChange = () => {
    saveState()
    emit('canvas-changed')
  }
  fabricCanvas.on('object:added', emitChange)
  fabricCanvas.on('object:modified', emitChange)
  fabricCanvas.on('object:removed', emitChange)

  resizeCanvas()
  emit('canvas-changed')
}

function resizeCanvas() {
  if (!fabricCanvas || !canvasWrapper.value) return
  const wrapper = canvasWrapper.value
  const maxW = wrapper.clientWidth - 8
  const maxH = wrapper.clientHeight - 8
  const scale = Math.min(maxW / fabricCanvas.width, maxH / fabricCanvas.height, 2)
  fabricCanvas.setZoom(scale)
  fabricCanvas.setWidth(fabricCanvas.width * scale)
  fabricCanvas.setHeight(fabricCanvas.height * scale)
  fabricCanvas.renderAll()
}

function addText() {
  const text = new IText('双击编辑', {
    left: 20, top: 20, fontSize: 24, fill: '#000000',
    fontFamily: 'Arial, Microsoft YaHei, sans-serif',
  })
  fabricCanvas.add(text)
  fabricCanvas.setActiveObject(text)
}

function addRect() {
  const rect = new Rect({
    left: 20, top: 20, width: 80, height: 40,
    fill: 'transparent', stroke: '#000000', strokeWidth: 2,
  })
  fabricCanvas.add(rect)
  fabricCanvas.setActiveObject(rect)
}

function addLine() {
  const line = new Line([10, 10, 100, 10], { stroke: '#000000', strokeWidth: 2 })
  fabricCanvas.add(line)
  fabricCanvas.setActiveObject(line)
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
  if (active) fabricCanvas.bringForward(active)
}

function sendBackward() {
  const active = fabricCanvas.getActiveObject()
  if (active) fabricCanvas.sendBackwards(active)
}

function clearCanvas() {
  fabricCanvas.clear()
  fabricCanvas.backgroundColor = '#ffffff'
  fabricCanvas.renderAll()
}

function saveState() {
  if (fabricCanvas) store.canvasJson = JSON.stringify(fabricCanvas.toJSON())
}

function getCanvasImageBase64() {
  return new Promise((resolve) => {
    const dataUrl = fabricCanvas.toDataURL({ format: 'png', multiplier: 1, enableRetinaScaling: false })
    resolve(dataUrl.split(',')[1])
  })
}

defineExpose({ getCanvasImageBase64, clearCanvas })
</script>

<style scoped>
.editor-container { display: flex; flex-direction: column; height: 100%; }
.editor-toolbar { display: flex; align-items: center; padding: 8px 12px; background: #f5f7fa; border-bottom: 1px solid #e4e7ed; flex-wrap: wrap; gap: 4px; }
.canvas-wrapper { flex: 1; display: flex; align-items: center; justify-content: center; overflow: hidden; background: #e8e8e8; padding: 4px; }
.canvas-wrapper :deep(canvas) { box-shadow: 0 2px 12px rgba(0,0,0,0.15); }
</style>
