<template>
  <div class="panel-section" v-if="selectedType === 'text'">
    <h3>文字设置</h3>
    <el-form label-width="60px" size="small">
      <el-form-item label="字体">
        <el-select :model-value="fontFamily" size="small" style="width:160px" @change="$emit('update:fontFamily', $event)">
          <el-option value="Microsoft YaHei" label="微软雅黑" />
          <el-option value="SimSun" label="宋体" />
          <el-option value="SimHei" label="黑体" />
          <el-option value="KaiTi" label="楷体" />
          <el-option value="FangSong" label="仿宋" />
          <el-option value="Arial" label="Arial" />
          <el-option value="Times New Roman" label="Times New Roman" />
          <el-option value="Courier New" label="Courier New" />
          <el-option value="Verdana" label="Verdana" />
        </el-select>
      </el-form-item>
      <el-form-item label="字号">
        <el-input-number :model-value="fontSize" :min="6" :max="200" :step="1" size="small" style="width:100px" controls-position="right" @change="$emit('update:fontSize', $event)" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
defineProps({
  selectedType: { type: String, default: null },
  fontSize: { type: Number, default: 24 },
  fontFamily: { type: String, default: 'Microsoft YaHei' },
})
defineEmits(['update:fontSize', 'update:fontFamily'])
</script>

<style scoped>
.panel-section { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.panel-section h3 { font-size: 13px; font-weight: 600; margin-bottom: 10px; color: #303133; }
</style>
