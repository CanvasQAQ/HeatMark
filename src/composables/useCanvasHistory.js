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
