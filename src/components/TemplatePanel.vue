<template>
  <div class="panel-section">
    <h3>模板</h3>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <el-button size="small" @click="$emit('open-selector')">选择模板</el-button>
      <el-button size="small" type="success" @click="$emit('save')">另存为模板</el-button>
    </div>
  </div>

  <div class="panel-section" v-if="slots.length > 0">
    <h3>占位符槽位</h3>
    <div class="slot-list">
      <div v-for="slot in slots" :key="slot.id" class="slot-item">
        <div class="slot-name">{{ slot.id }}</div>
        <el-input
          size="small"
          :model-value="slotTexts[slot.id]"
          @input="(val) => $emit('slot-input', slot.id, val)"
          @focus="$emit('slot-focus', slot.id)"
          @blur="$emit('slot-blur', slot.id)"
          class="slot-text-input"
          :placeholder="slot.label || slot.id"
        />
        <el-button size="small" type="danger" circle @click="$emit('remove-slot', slot.id)" class="slot-del-btn">×</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  slots: { type: Array, default: () => [] },
  slotTexts: { type: Object, default: () => ({}) },
})
defineEmits(['open-selector', 'save', 'slot-input', 'slot-focus', 'slot-blur', 'remove-slot'])
</script>

<style scoped>
.panel-section { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.panel-section h3 { font-size: 13px; font-weight: 600; margin-bottom: 10px; color: #303133; }
.slot-list { max-height: 200px; overflow-y: auto; }
.slot-item { display: flex; align-items: center; gap: 6px; padding: 4px 0; border-bottom: 1px solid #f0f0f0; }
.slot-item:last-child { border-bottom: none; }
.slot-name { font-size: 12px; font-weight: 600; color: #409eff; min-width: 70px; flex-shrink: 0; }
.slot-text-input { flex: 1; min-width: 0; }
.slot-del-btn { flex-shrink: 0; }
</style>
