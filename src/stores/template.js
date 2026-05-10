import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { getTemplates, getTemplate, saveTemplate } from '../api/backend.js'

export const useTemplateStore = defineStore('template', () => {
  const templateList = ref([])
  const currentTemplateId = ref(null)
  const currentTemplateName = ref('')
  const currentTemplatePath = ref('')
  const slots = reactive([])
  const showSelector = ref(false)
  const pendingSlotId = ref('')

  async function fetchTemplateList() {
    try {
      const res = await getTemplates()
      templateList.value = res.data.templates
    } catch {
      templateList.value = []
    }
  }

  async function loadTemplate(id) {
    try {
      const res = await getTemplate(id)
      const tpl = res.data
      currentTemplateId.value = tpl.id || id
      currentTemplateName.value = tpl.name
      currentTemplatePath.value = tpl.path || id
      slots.splice(0, slots.length, ...(tpl.slots || []))
      return {
        labelOptions: tpl.labelOptions,
        canvasJson: tpl.canvasJson,
        slots: tpl.slots || [],
      }
    } catch {
      return null
    }
  }

  async function persistTemplate(name, labelOptions, canvasJson, slotDefs, previewBase64) {
    const body = {
      name,
      labelOptions,
      canvasJson,
      slots: slotDefs,
      preview_base64: previewBase64 || null,
    }
    const res = await saveTemplate(body)
    if (res.data.success) {
      await fetchTemplateList()
      currentTemplateId.value = res.data.id
      currentTemplateName.value = res.data.name
      slots.splice(0, slots.length, ...slotDefs)
    }
    return res.data
  }

  function setShowSelector(val) {
    showSelector.value = val
  }

  function addSlot(id, label, defaultText) {
    const existing = slots.findIndex(s => s.id === id)
    if (existing >= 0) {
      slots[existing] = { id, label: label || id, defaultText: defaultText || '' }
    } else {
      slots.push({ id, label: label || id, defaultText: defaultText || '' })
    }
  }

  function removeSlot(id) {
    const idx = slots.findIndex(s => s.id === id)
    if (idx >= 0) slots.splice(idx, 1)
  }

  function syncSlotsFromCanvas(slotDefs) {
    const existing = {}
    for (const s of slots) {
      existing[s.id] = s
    }
    slots.splice(0, slots.length)
    for (const s of slotDefs) {
      const prev = existing[s.id]
      slots.push({
        id: s.id,
        label: prev?.label || s.label || s.id,
        defaultText: s.defaultText || '',
      })
    }
  }

  return {
    templateList,
    currentTemplateId,
    currentTemplateName,
    currentTemplatePath,
    slots,
    showSelector,
    pendingSlotId,
    fetchTemplateList,
    loadTemplate,
    persistTemplate,
    setShowSelector,
    addSlot,
    removeSlot,
    syncSlotsFromCanvas,
  }
})
