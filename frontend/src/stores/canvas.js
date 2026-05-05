import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'

export const useCanvasStore = defineStore('canvas', () => {
  const imageOptions = reactive({
    threshold: 128,
    contrast: 1.0,
    brightness: 1.0,
    rotation: 0,
    invert: false,
    dither: true,
    labelWidthMm: 40,
    labelHeightMm: 30,
    dpi: 203,
  })

  const printerName = ref('CHITENG-CT221D')
  const printers = ref([])
  const copies = ref(1)
  const previewImage = ref(null)
  const processedInfo = ref({ width: 0, height: 0, bytesPerRow: 0 })
  const statusMsg = ref('就绪')
  const canvasJson = ref(null)

  function getLabelPixelSize() {
    const w = Math.round(imageOptions.labelWidthMm / 25.4 * imageOptions.dpi)
    const h = Math.round(imageOptions.labelHeightMm / 25.4 * imageOptions.dpi)
    return { w, h }
  }

  const effectiveCanvasSize = computed(() => {
    const { w, h } = getLabelPixelSize()
    if ([90, 270].includes(imageOptions.rotation)) {
      return { w: h, h: w }
    }
    return { w, h }
  })

  return {
    imageOptions,
    printerName,
    printers,
    copies,
    previewImage,
    processedInfo,
    statusMsg,
    canvasJson,
    getLabelPixelSize,
    effectiveCanvasSize,
  }
})
