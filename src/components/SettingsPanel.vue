<template>
  <div class="panel-section">
    <h3>图像设置</h3>
    <el-form label-width="80px" size="small">
      <el-form-item label="标签宽(mm)">
        <el-input-number v-model="imageOptions.labelWidthMm" :min="10" :max="200" size="small" style="width:80px" controls-position="right" />
      </el-form-item>
      <el-form-item label="标签高(mm)">
        <el-input-number v-model="imageOptions.labelHeightMm" :min="10" :max="200" size="small" style="width:80px" controls-position="right" />
      </el-form-item>
      <el-form-item label="DPI">
        <el-select v-model="imageOptions.dpi" size="small" style="width:100px">
          <el-option :value="203" label="203" />
          <el-option :value="300" label="300" />
          <el-option :value="600" label="600" />
        </el-select>
      </el-form-item>
    </el-form>
    <el-collapse>
      <el-collapse-item title="高级处理" name="advanced">
        <el-form label-width="80px" size="small">
          <el-form-item label="抖动">
            <el-switch v-model="imageOptions.dither" size="small" active-text="Floyd-Steinberg" />
          </el-form-item>
          <el-form-item label="阈值" v-if="!imageOptions.dither">
            <el-slider v-model="imageOptions.threshold" :max="255" :show-tooltip="false" size="small" />
            <span class="value-tag">{{ imageOptions.threshold }}</span>
          </el-form-item>
          <el-form-item label="对比度">
            <el-slider v-model="imageOptions.contrast" :min="0.5" :max="3.0" :step="0.1" :show-tooltip="false" size="small" />
            <span class="value-tag">{{ imageOptions.contrast.toFixed(1) }}</span>
          </el-form-item>
          <el-form-item label="亮度">
            <el-slider v-model="imageOptions.brightness" :min="0.3" :max="2.0" :step="0.1" :show-tooltip="false" size="small" />
            <span class="value-tag">{{ imageOptions.brightness.toFixed(1) }}</span>
          </el-form-item>
          <el-form-item label="方向">
            <el-select v-model="imageOptions.rotation" size="small" style="width:100px">
              <el-option :value="0" label="0°" />
              <el-option :value="90" label="90°" />
              <el-option :value="180" label="180°" />
              <el-option :value="270" label="270°" />
            </el-select>
          </el-form-item>
          <el-form-item label="反色">
            <el-switch v-model="imageOptions.invert" size="small" />
          </el-form-item>
        </el-form>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
defineProps({
  imageOptions: { type: Object, required: true },
})
</script>

<style scoped>
.panel-section { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.panel-section h3 { font-size: 13px; font-weight: 600; margin-bottom: 10px; color: #303133; }
.value-tag { display: inline-block; width: 30px; text-align: right; font-size: 11px; color: #409eff; margin-left: 6px; }
</style>
