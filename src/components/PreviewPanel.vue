<template>
  <div class="panel-section">
    <h3>预览</h3>
    <div class="preview-box" @click="$emit('refresh')">
      <div v-if="loading" class="preview-loading"><LoadingOne theme="outline" size="20" spin/></div>
      <img v-else-if="dataUrl" :src="dataUrl" class="preview-img" />
      <div v-else class="preview-empty">点击刷新预览</div>
    </div>
    <div class="preview-info" v-if="info">
      {{ info.width }}×{{ info.height }}px | {{ info.bytesPerRow }}B/行
    </div>
  </div>
</template>

<script setup>
import { LoadingOne } from '@icon-park/vue-next'

defineProps({
  dataUrl: { type: String, default: null },
  info: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})
defineEmits(['refresh'])
</script>

<style scoped>
.panel-section { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.panel-section h3 { font-size: 13px; font-weight: 600; margin-bottom: 10px; color: #303133; }
.preview-box { width: 100%; min-height: 100px; background: #f5f7fa; border-radius: 4px; display: flex; align-items: center; justify-content: center; cursor: pointer; border: 1px dashed #dcdfe6; overflow: hidden; }
.preview-box:hover { border-color: #409eff; }
.preview-img { width: 100%; display: block; image-rendering: pixelated; }
.preview-empty { color: #c0c4cc; font-size: 12px; }
.preview-loading { color: #909399; }
.preview-info { font-size: 11px; color: #909399; text-align: center; margin-top: 4px; }
</style>
