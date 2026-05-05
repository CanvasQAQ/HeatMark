<template>
  <div class="app-root">
    <TitleBar />

    <div class="app-body">
      <div class="editor-area">
        <CanvasEditor ref="editorRef" @canvas-changed="onCanvasChanged" />
      </div>

      <div class="side-panel">
        <div class="panel-section">
          <h3>🎛 图像设置</h3>
          <el-form label-width="80px" size="small">
            <el-form-item label="标签宽(mm)">
              <el-input-number v-model="store.imageOptions.labelWidthMm" :min="10" :max="200" size="small" style="width:80px" controls-position="right" />
            </el-form-item>
            <el-form-item label="标签高(mm)">
              <el-input-number v-model="store.imageOptions.labelHeightMm" :min="10" :max="200" size="small" style="width:80px" controls-position="right" />
            </el-form-item>
            <el-form-item label="DPI">
              <el-select v-model="store.imageOptions.dpi" size="small" style="width:100px">
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
                  <el-switch v-model="store.imageOptions.dither" size="small" active-text="Floyd-Steinberg" />
                </el-form-item>
                <el-form-item label="阈值" v-if="!store.imageOptions.dither">
                  <el-slider v-model="store.imageOptions.threshold" :max="255" :show-tooltip="false" size="small" />
                  <span class="value-tag">{{ store.imageOptions.threshold }}</span>
                </el-form-item>
                <el-form-item label="对比度">
                  <el-slider v-model="store.imageOptions.contrast" :min="0.5" :max="3.0" :step="0.1" :show-tooltip="false" size="small" />
                  <span class="value-tag">{{ store.imageOptions.contrast.toFixed(1) }}</span>
                </el-form-item>
                <el-form-item label="亮度">
                  <el-slider v-model="store.imageOptions.brightness" :min="0.3" :max="2.0" :step="0.1" :show-tooltip="false" size="small" />
                  <span class="value-tag">{{ store.imageOptions.brightness.toFixed(1) }}</span>
                </el-form-item>
                <el-form-item label="方向">
                  <el-select v-model="store.imageOptions.rotation" size="small" style="width:100px">
                    <el-option :value="0" label="0°" />
                    <el-option :value="90" label="90°" />
                    <el-option :value="180" label="180°" />
                    <el-option :value="270" label="270°" />
                  </el-select>
                </el-form-item>
                <el-form-item label="反色">
                  <el-switch v-model="store.imageOptions.invert" size="small" />
                </el-form-item>
              </el-form>
            </el-collapse-item>
          </el-collapse>
        </div>

        <div class="panel-section">
          <h3>👁 预览</h3>
          <div class="preview-box" @click="refreshPreview">
            <div v-if="previewLoading" class="preview-loading"><LoadingOne theme="outline" size="20" spin/></div>
            <img v-else-if="previewDataUrl" :src="previewDataUrl" class="preview-img" />
            <div v-else class="preview-empty">点击刷新预览</div>
          </div>
          <div class="preview-info" v-if="previewInfo">
            {{ previewInfo.width }}×{{ previewInfo.height }}px | {{ previewInfo.bytesPerRow }}B/行
          </div>
        </div>

        <div class="panel-section">
          <el-button @click="saveTSPL" style="width:100%"><Save theme="outline" size="14"/> 导出 TSPL 代码</el-button>
        </div>
      </div>
    </div>

    <div class="app-bottom">
      <div class="bottom-left">
        <span class="dot" :class="backendStatus"></span>
        <span class="backend-text">{{ backendStatus === 'online' ? '后端在线' : backendStatus === 'checking' ? '检测中' : '离线' }}</span>
        <el-button v-if="backendStatus === 'offline'" size="small" @click="restartBackend" :loading="restarting" style="margin-left:8px">重启后端</el-button>
        <span class="pixel-info">{{ pixelInfo.text }}</span>
      </div>
      <div class="bottom-right">
        <el-select v-model="store.printerName" size="small" style="width:200px" filterable placeholder="选择打印机">
          <el-option v-for="p in store.printers" :key="p" :value="p" :label="p" />
        </el-select>
        <el-input-number v-model="store.copies" :min="1" :max="999" size="small" style="width:80px;margin-left:8px" controls-position="right" />
        <el-button type="primary" size="small" @click="handlePrint" :loading="printing" style="margin-left:8px">
          <Printer theme="outline" size="14"/> 打印
        </el-button>
        <span class="status-text">{{ store.statusMsg }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useCanvasStore } from './stores/canvas.js'
import { getPrinters, healthCheck, printLabel, processImage } from './api/backend.js'
import { ElMessage } from 'element-plus'
import CanvasEditor from './components/CanvasEditor.vue'
import TitleBar from './components/TitleBar.vue'
import { LoadingOne, Save, Printer } from '@icon-park/vue-next'

const store = useCanvasStore()
const editorRef = ref(null)
const backendStatus = ref('checking')
const restarting = ref(false)
const printing = ref(false)
const previewDataUrl = ref(null)
const previewLoading = ref(false)
const previewInfo = ref(null)

let debounceTimer = null
let backendMonitor = null

const pixelInfo = computed(() => {
  const { w, h } = store.getLabelPixelSize()
  return { text: `${w}×${h}px | ${Math.ceil(w/8)}B/行 | DPI:${store.imageOptions.dpi}` }
})

onMounted(async () => {
  checkBackend()
  backendMonitor = setInterval(checkBackend, 5000)

  try {
    const res = await getPrinters()
    store.printers = res.data.printers
    if (store.printers.length && !store.printers.includes(store.printerName)) {
      store.printerName = store.printers[0]
    }
  } catch {}

  if (window.electronAPI) {
    window.electronAPI.onBackendStatus((status) => {
      backendStatus.value = status
    })
  }
})

onUnmounted(() => {
  if (backendMonitor) clearInterval(backendMonitor)
})

async function checkBackend() {
  try {
    await healthCheck()
    backendStatus.value = 'online'
  } catch {
    backendStatus.value = 'offline'
  }
}

async function restartBackend() {
  if (window.electronAPI) {
    restarting.value = true
    try {
      await window.electronAPI.restartBackend()
      await new Promise((r) => setTimeout(r, 3000))
      await checkBackend()
    } finally {
      restarting.value = false
    }
  }
}

function onCanvasChanged() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => { refreshPreview() }, 400)
}

async function refreshPreview() {
  if (!editorRef.value) return
  const b64 = await editorRef.value.getCanvasImageBase64()
  if (!b64) return

  previewLoading.value = true
  try {
    const res = await processImage(b64, store.imageOptions)
    previewDataUrl.value = 'data:image/png;base64,' + res.data.image_base64
    previewInfo.value = {
      width: res.data.width, height: res.data.height,
      bytesPerRow: res.data.bytes_per_row,
    }
  } catch (e) {
    ElMessage.error('预览处理失败')
  } finally {
    previewLoading.value = false
  }
}

async function handlePrint() {
  if (!editorRef.value) return
  const b64 = await editorRef.value.getCanvasImageBase64()
  if (!b64) { ElMessage.warning('画布为空'); return }
  printing.value = true
  store.statusMsg = '打印中...'
  try {
    const res = await printLabel(b64, store.imageOptions, store.printerName, store.copies)
    store.statusMsg = res.data.message
    ElMessage.success(res.data.message)
  } catch (e) {
    store.statusMsg = '打印失败: ' + (e.response?.data?.detail || e.message)
    ElMessage.error(store.statusMsg)
  } finally {
    printing.value = false
  }
}

async function saveTSPL() {
  if (!editorRef.value) return
  const b64 = await editorRef.value.getCanvasImageBase64()
  if (!b64) { ElMessage.warning('画布为空'); return }
  try {
    const res = await processImage(b64, store.imageOptions)
    const text = `SIZE ${store.imageOptions.labelWidthMm} mm,${store.imageOptions.labelHeightMm} mm\r\n` +
      `GAP 2 mm,0 mm\r\nDENSITY 8\r\nDIRECTION 1\r\nCLS\r\n` +
      `BITMAP 0,0,${res.data.bytes_per_row},${res.data.height},0,\r\n` +
      `[${res.data.bytes_per_row * res.data.height} bytes binary bitmap data]\r\n` +
      `PRINT 1\r\n`
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'label.tspl.txt'; a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('已导出')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

watch(
  () => ({ ...store.imageOptions }),
  () => {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => refreshPreview(), 300)
  },
  { deep: true }
)
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
.panel-section { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.panel-section h3 { font-size: 13px; font-weight: 600; margin-bottom: 10px; color: #303133; }
.app-bottom { display: flex; align-items: center; justify-content: space-between; height: 36px; padding: 0 12px; background: #fff; border-top: 1px solid #e4e7ed; flex-shrink: 0; }
.bottom-left { display: flex; align-items: center; gap: 6px; }
.bottom-right { display: flex; align-items: center; gap: 4px; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot.online { background: #67c23a; }
.dot.offline { background: #f56c6c; }
.dot.checking { background: #e6a23c; animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0.4; } }
.backend-text { font-size: 12px; color: #909399; }
.pixel-info { font-size: 12px; color: #909399; margin-left: 12px; }
.status-text { font-size: 12px; color: #909399; margin-left: 8px; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.preview-box { width: 100%; min-height: 100px; background: #f5f7fa; border-radius: 4px; display: flex; align-items: center; justify-content: center; cursor: pointer; border: 1px dashed #dcdfe6; overflow: hidden; }
.preview-box:hover { border-color: #409eff; }
.preview-img { width: 100%; display: block; image-rendering: pixelated; }
.preview-empty { color: #c0c4cc; font-size: 12px; }
.preview-loading { color: #909399; }
.preview-info { font-size: 11px; color: #909399; text-align: center; margin-top: 4px; }
.value-tag { display: inline-block; width: 30px; text-align: right; font-size: 11px; color: #409eff; margin-left: 6px; }
</style>
