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
