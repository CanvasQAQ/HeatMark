<template>
  <div class="editor-toolbar">
    <el-button-group>
      <el-button size="small" @click="$emit('add-text')"><EditTwo theme="outline" size="14" :strokeWidth="3"/> 文字</el-button>
      <el-button size="small" @click="$emit('add-rect')"><Rectangle theme="outline" size="14" :strokeWidth="3"/> 矩形</el-button>
      <el-button size="small" @click="$emit('add-line')"><DividingLine theme="outline" size="14" :strokeWidth="3"/> 线条</el-button>
      <el-button size="small" @click="$emit('add-image')"><Pic theme="outline" size="14" :strokeWidth="3"/> 贴图</el-button>
    </el-button-group>
    <el-button-group style="margin-left: 12px;">
      <el-button size="small" @click="$emit('undo')" :disabled="!canUndo">撤销</el-button>
      <el-button size="small" @click="$emit('redo')" :disabled="!canRedo">重做</el-button>
    </el-button-group>
    <el-button-group style="margin-left: 12px;">
      <el-button size="small" @click="$emit('bring-forward')" :disabled="!hasSelection">上移</el-button>
      <el-button size="small" @click="$emit('send-backward')" :disabled="!hasSelection">下移</el-button>
    </el-button-group>
    <el-button size="small" style="margin-left: 12px;" @click="$emit('delete')" :disabled="!hasSelection">
      <DeleteOne theme="outline" size="14" :strokeWidth="3"/> 删除
    </el-button>
    <el-button size="small" type="danger" style="margin-left: 12px;" @click="$emit('clear')">清空</el-button>
  </div>
</template>

<script setup>
import { EditTwo, Rectangle, DividingLine, Pic, DeleteOne } from '@icon-park/vue-next'

defineProps({
  hasSelection: { type: Boolean, default: false },
  canUndo: { type: Boolean, default: false },
  canRedo: { type: Boolean, default: false },
})
defineEmits(['add-text', 'add-rect', 'add-line', 'add-image', 'undo', 'redo', 'delete', 'bring-forward', 'send-backward', 'clear'])
</script>

<style scoped>
.editor-toolbar { display: flex; align-items: center; padding: 8px 12px; background: #f5f7fa; border-bottom: 1px solid #e4e7ed; flex-wrap: wrap; gap: 4px; }
</style>
