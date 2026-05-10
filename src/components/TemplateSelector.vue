<template>
  <el-dialog
    v-model="visible"
    title="选择模板"
    width="640px"
    :close-on-click-modal="false"
    :show-close="true"
    @close="handleClose"
  >
    <div class="template-grid">
      <div
        v-for="tpl in store.templateList"
        :key="tpl.id"
        class="template-card"
        :class="{ selected: selectedId === tpl.id }"
        @click="selectedId = tpl.id"
        @dblclick="confirmSelect"
      >
        <div class="template-preview">
          <img v-if="tpl.preview" :src="'data:image/png;base64,' + tpl.preview" />
          <div v-else class="template-placeholder">
            <span>{{ tpl.labelWidthMm }}×{{ tpl.labelHeightMm }}mm</span>
          </div>
        </div>
        <div class="template-name">{{ tpl.name }}</div>
        <div class="template-meta">{{ tpl.labelWidthMm }}×{{ tpl.labelHeightMm }}mm | {{ tpl.dpi }}DPI</div>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="confirmSelect" :disabled="!selectedId">
          选择模板
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useTemplateStore } from '../stores/template.js'

const emit = defineEmits(['select'])
const store = useTemplateStore()
const visible = ref(true)
const selectedId = ref(null)

watch(() => store.templateList, () => {
  if (store.templateList.length > 0 && !selectedId.value) {
    selectedId.value = store.templateList[0]?.id
  }
})

function confirmSelect() {
  if (selectedId.value) {
    emit('select', selectedId.value)
    visible.value = false
  }
}

function handleClose() {
  visible.value = false
  emit('select', null)
}
</script>

<style scoped>
.template-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  max-height: 400px;
  overflow-y: auto;
}
.template-card {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 8px;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.template-card:hover {
  border-color: #409eff;
}
.template-card.selected {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}
.template-preview {
  width: 100%;
  height: 100px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  margin-bottom: 8px;
}
.template-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  image-rendering: pixelated;
}
.template-placeholder {
  color: #c0c4cc;
  font-size: 13px;
}
.template-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  text-align: center;
}
.template-meta {
  font-size: 11px;
  color: #909399;
  text-align: center;
  margin-top: 2px;
}
</style>
