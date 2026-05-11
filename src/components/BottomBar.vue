<template>
  <div class="app-bottom">
    <div class="bottom-left">
      <span class="dot" :class="backendStatus"></span>
      <span class="backend-text">{{ backendStatus === 'online' ? '后端在线' : backendStatus === 'checking' ? '检测中' : '离线' }}</span>
      <el-button v-if="backendStatus === 'offline'" size="small" @click="$emit('restart')" :loading="restarting" style="margin-left:8px">重启后端</el-button>
      <span class="pixel-info">{{ pixelInfo }}</span>
    </div>
    <div class="bottom-right">
      <span class="zoom-control">
        <span class="zoom-label">缩放</span>
        <el-slider :model-value="displayScale" :min="100" :max="300" :step="10" :show-tooltip="false" size="small" style="width:100px;flex-shrink:0" @update:model-value="$emit('update:displayScale', $event)" />
        <span class="zoom-value">{{ displayScale }}%</span>
      </span>
      <el-select :model-value="printerName" size="small" style="width:200px;margin-left:12px" filterable placeholder="选择打印机" @change="$emit('update:printerName', $event)">
        <el-option v-for="p in printers" :key="p" :value="p" :label="p" />
      </el-select>
      <el-input-number :model-value="copies" :min="1" :max="999" size="small" style="width:80px;margin-left:8px" controls-position="right" @change="$emit('update:copies', $event)" />
      <el-button type="primary" size="small" @click="$emit('print')" :loading="printing" style="margin-left:8px">
        <Printer theme="outline" size="14"/> 打印
      </el-button>
      <span class="status-text">{{ statusMsg }}</span>
    </div>
  </div>
</template>

<script setup>
import { Printer } from '@icon-park/vue-next'

defineProps({
  backendStatus: { type: String, default: 'checking' },
  restarting: { type: Boolean, default: false },
  pixelInfo: { type: String, default: '' },
  displayScale: { type: Number, default: 100 },
  printerName: { type: String, default: '' },
  printers: { type: Array, default: () => [] },
  copies: { type: Number, default: 1 },
  printing: { type: Boolean, default: false },
  statusMsg: { type: String, default: '就绪' },
})
defineEmits(['restart', 'update:displayScale', 'update:printerName', 'update:copies', 'print'])
</script>

<style scoped>
.app-bottom { display: flex; align-items: center; justify-content: space-between; height: 36px; padding: 0 12px; background: #fff; border-top: 1px solid #e4e7ed; flex-shrink: 0; }
.bottom-left { display: flex; align-items: center; gap: 6px; }
.bottom-right { display: flex; align-items: center; gap: 4px; }
.zoom-control { display: flex; align-items: center; gap: 6px; }
.zoom-label { font-size: 12px; color: #909399; flex-shrink: 0; white-space: nowrap; margin-right: 4px; }
.zoom-value { font-size: 12px; color: #409eff; min-width: 36px; text-align: right; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot.online { background: #67c23a; }
.dot.offline { background: #f56c6c; }
.dot.checking { background: #e6a23c; animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0.4; } }
.backend-text { font-size: 12px; color: #909399; }
.pixel-info { font-size: 12px; color: #909399; margin-left: 12px; }
.status-text { font-size: 12px; color: #909399; margin-left: 8px; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
