import { ref } from 'vue'
import { printLabel, processImage } from '../api/backend.js'
import { useCanvasStore } from '../stores/canvas.js'

export function usePrint() {
  const store = useCanvasStore()
  const printing = ref(false)

  async function doPrint(getBase64Fn) {
    if (!getBase64Fn) return
    const b64 = await getBase64Fn()
    if (!b64) { store.statusMsg = '画布为空'; return false }
    printing.value = true
    store.statusMsg = '打印中...'
    try {
      const res = await printLabel(b64, store.imageOptions, store.printerName, store.copies)
      store.statusMsg = res.data.message
      return true
    } catch (e) {
      store.statusMsg = '打印失败: ' + (e.response?.data?.detail || e.message)
      return false
    } finally {
      printing.value = false
    }
  }

  async function doExportTSPL(getBase64Fn) {
    if (!getBase64Fn) return
    const b64 = await getBase64Fn()
    if (!b64) { store.statusMsg = '画布为空'; return }
    try {
      const res = await processImage(b64, store.imageOptions)
      const text =
        `SIZE ${store.imageOptions.labelWidthMm} mm,${store.imageOptions.labelHeightMm} mm\r\n` +
        `GAP 2 mm,0 mm\r\nDENSITY 8\r\nDIRECTION 1\r\nCLS\r\n` +
        `BITMAP 0,0,${res.data.bytes_per_row},${res.data.height},0,\r\n` +
        `[${res.data.bytes_per_row * res.data.height} bytes binary bitmap data]\r\n` +
        `PRINT 1\r\n`
      const blob = new Blob([text], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = 'label.tspl.txt'; a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      store.statusMsg = '导出失败: ' + (e.message || '')
    }
  }

  return { printing, doPrint, doExportTSPL }
}
