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
