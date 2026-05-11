<template>
  <template v-if="selectedObject && selectedObjectType === 'text' && !selectedObject.slotId">
    <div class="panel-section">
      <h3>设为占位符</h3>
      <el-form label-width="60px" size="small">
        <el-form-item label="槽位ID">
          <el-input :model-value="slotEditId" size="small" placeholder="例如: productName" @input="$emit('update:slotEditId', $event)" />
        </el-form-item>
        <el-form-item label="标签名">
          <el-input :model-value="slotEditLabel" size="small" placeholder="显示名称" @input="$emit('update:slotEditLabel', $event)" />
        </el-form-item>
        <el-button size="small" type="primary" @click="$emit('mark')" style="width:100%">
          标记为占位符
        </el-button>
      </el-form>
    </div>
  </template>

  <template v-if="selectedObject && selectedObject.slotId">
    <div class="panel-section">
      <h3>占位符: {{ selectedObject.slotId }}</h3>
      <el-button size="small" type="warning" @click="$emit('unmark')" style="width:100%">
        取消占位符
      </el-button>
    </div>
  </template>
</template>

<script setup>
defineProps({
  selectedObject: { type: Object, default: null },
  selectedObjectType: { type: String, default: null },
  slotEditId: { type: String, default: '' },
  slotEditLabel: { type: String, default: '' },
})
defineEmits(['mark', 'unmark', 'update:slotEditId', 'update:slotEditLabel'])
</script>

<style scoped>
.panel-section { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.panel-section h3 { font-size: 13px; font-weight: 600; margin-bottom: 10px; color: #303133; }
</style>
