import { computed } from 'vue'
import { useCanvasStore } from '../stores/canvas.js'

export function useSettings() {
  const store = useCanvasStore()

  function getLabelPixelSize() {
    const w = Math.round(store.imageOptions.labelWidthMm / 25.4 * store.imageOptions.dpi)
    const h = Math.round(store.imageOptions.labelHeightMm / 25.4 * store.imageOptions.dpi)
    return { w, h }
  }

  const effectiveCanvasSize = computed(() => {
    const { w, h } = getLabelPixelSize()
    if ([90, 270].includes(store.imageOptions.rotation)) {
      return { w: h, h: w }
    }
    return { w, h }
  })

  const pixelInfo = computed(() => {
    const { w, h } = getLabelPixelSize()
    return { text: `${w}×${h}px | ${Math.ceil(w / 8)}B/行 | DPI:${store.imageOptions.dpi}` }
  })

  return {
    imageOptions: store.imageOptions,
    effectiveCanvasSize,
    pixelInfo,
    getLabelPixelSize,
  }
}
