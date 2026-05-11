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
      const objects = getSlotsFn()
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
