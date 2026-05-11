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
