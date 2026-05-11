import { ref, onUnmounted } from 'vue'
import { healthCheck } from '../api/backend.js'

export function useBackendStatus() {
  const backendStatus = ref('checking')
  let monitor = null

  async function check() {
    try {
      await healthCheck()
      backendStatus.value = 'online'
    } catch {
      backendStatus.value = 'offline'
    }
  }

  function startPolling(interval = 5000) {
    stopPolling()
    check()
    monitor = setInterval(check, interval)
  }

  function stopPolling() {
    if (monitor) { clearInterval(monitor); monitor = null }
  }

  onUnmounted(() => stopPolling())

  return { backendStatus, check, startPolling, stopPolling }
}
