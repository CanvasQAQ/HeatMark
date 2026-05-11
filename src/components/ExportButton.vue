<template>
  <div class="panel-section">
    <el-button @click="$emit('export')" style="width:100%">
      <Save theme="outline" size="14"/> 导出 TSPL 代码
    </el-button>
  </div>
</template>

<script setup>
import { Save } from '@icon-park/vue-next'
defineEmits(['export'])
</script>

<style scoped>
.panel-section { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
</style>
