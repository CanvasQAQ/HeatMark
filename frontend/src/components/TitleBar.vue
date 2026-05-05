<template>
  <div class="titlebar" @dblclick="toggleMaximize">
    <div class="titlebar-drag">
      <span class="titlebar-title">HeatMark - 热敏标签打印工具</span>
    </div>
    <div class="titlebar-actions">
      <button class="tb-btn" @click="minimize" title="最小化">
        <svg width="12" height="12"><rect y="5" width="12" height="1.5" fill="currentColor"/></svg>
      </button>
      <button class="tb-btn" @click="toggleMaximize" :title="isMaxed ? '还原' : '最大化'">
        <svg v-if="!isMaxed" width="12" height="12"><rect x="1" y="1" width="10" height="10" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
        <svg v-else width="12" height="12"><rect x="3" y="0" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1.5"/><rect x="0" y="3" width="8" height="8" fill="#2c2c2c" stroke="currentColor" stroke-width="1.5"/></svg>
      </button>
      <button class="tb-btn tb-close" @click="closeWindow" title="关闭">
        <svg width="12" height="12"><line x1="1" y1="1" x2="11" y2="11" stroke="currentColor" stroke-width="1.5"/><line x1="11" y1="1" x2="1" y2="11" stroke="currentColor" stroke-width="1.5"/></svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const isMaxed = ref(false)
const isElectron = !!window.electronAPI

function minimize() {
  if (isElectron) window.electronAPI.windowMinimize()
}

async function toggleMaximize() {
  if (isElectron) {
    await window.electronAPI.windowMaximize()
    isMaxed.value = await window.electronAPI.windowIsMaximized()
  }
}

function closeWindow() {
  if (isElectron) window.electronAPI.windowClose()
}

onMounted(async () => {
  if (isElectron) {
    isMaxed.value = await window.electronAPI.windowIsMaximized()
    window.electronAPI.onWindowMaximized((flag) => {
      isMaxed.value = flag
    })
  }
})
</script>

<style scoped>
.titlebar {
  display: flex;
  align-items: center;
  height: 32px;
  background: #2c2c2c;
  color: #ccc;
  user-select: none;
  flex-shrink: 0;
}
.titlebar-drag {
  flex: 1;
  -webkit-app-region: drag;
  height: 100%;
  display: flex;
  align-items: center;
  padding-left: 12px;
}
.titlebar-title {
  font-size: 12px;
  color: #999;
}
.titlebar-actions {
  display: flex;
  height: 100%;
  -webkit-app-region: no-drag;
}
.tb-btn {
  width: 46px;
  height: 100%;
  border: none;
  background: transparent;
  color: #999;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}
.tb-btn:hover {
  background: rgba(255,255,255,0.1);
  color: #fff;
}
.tb-close:hover {
  background: #e81123;
  color: #fff;
}
</style>
