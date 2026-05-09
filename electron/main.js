const { app, BrowserWindow, ipcMain } = require('electron')
const { spawn, execSync } = require('child_process')
const path = require('path')
const http = require('http')

const BACKEND_PORT = 8477
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}/api/health`

let mainWindow = null
let pythonProcess = null
let backendReady = false

function getBackendDir() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend')
  }
  return path.join(__dirname, '..', 'backend')
}

function killPortProcess() {
  try {
    const cmd = `netstat -ano | findstr :${BACKEND_PORT} | findstr LISTENING`
    const output = execSync(cmd, { encoding: 'utf8', timeout: 3000 })
    const lines = output.trim().split('\r\n')
    for (const line of lines) {
      const parts = line.trim().split(/\s+/)
      const pid = parts[parts.length - 1]
      if (pid && pid !== '0') {
        try { execSync(`taskkill /F /PID ${pid}`, { timeout: 3000 }) } catch {}
      }
    }
  } catch {}
}

function startPythonBackend() {
  if (pythonProcess) return

  const backendDir = getBackendDir()
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3'

  console.log('[Backend] Starting Python backend...')
  pythonProcess = spawn(pythonCmd, ['main.py'], {
    cwd: backendDir,
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
  })

  pythonProcess.stdout.on('data', (d) => {
    const msg = d.toString().trim()
    console.log(`[Python] ${msg}`)
    if (mainWindow) mainWindow.webContents.send('backend-log', msg)
  })

  pythonProcess.stderr.on('data', (d) => {
    const msg = d.toString().trim()
    console.log(`[Python] ${msg}`)
    if (mainWindow) mainWindow.webContents.send('backend-log', msg)
  })

  pythonProcess.on('close', (code) => {
    console.log(`[Python] exited (code ${code})`)
    backendReady = false
    if (mainWindow) mainWindow.webContents.send('backend-status', 'offline')
    pythonProcess = null
    if (code !== 0 && mainWindow) {
      mainWindow.webContents.send('backend-log', '后端进程异常退出，请点击"重启后端"')
    }
  })
}

function killPythonBackend() {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
}

function checkBackendHealth() {
  return new Promise((resolve) => {
    const req = http.get(BACKEND_URL, { timeout: 2000 }, (res) => {
      let body = ''
      res.on('data', (c) => { body += c })
      res.on('end', () => {
        try { resolve(JSON.parse(body).status === 'ok') } catch { resolve(false) }
      })
    })
    req.on('error', () => resolve(false))
    req.on('timeout', () => { req.destroy(); resolve(false) })
  })
}

function startBackendMonitor() {
  setInterval(async () => {
    const healthy = await checkBackendHealth()
    if (healthy !== backendReady) {
      backendReady = healthy
      if (mainWindow) {
        mainWindow.webContents.send('backend-status', healthy ? 'online' : 'offline')
      }
    }
  }, 3000)
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 500,
    frame: false,
    titleBarStyle: 'hidden',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    title: 'HeatMark - 热敏标签打印工具',
  })

  const isDev = !app.isPackaged || process.argv.includes('--dev')
  const vitePort = 5173

  if (isDev) {
    mainWindow.loadURL(`http://localhost:${vitePort}`)
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  mainWindow.on('closed', () => { mainWindow = null })

  mainWindow.on('maximize', () => {
    mainWindow.webContents.send('window-maximized', true)
  })
  mainWindow.on('unmaximize', () => {
    mainWindow.webContents.send('window-maximized', false)
  })
}

ipcMain.handle('restart-backend', async () => {
  killPythonBackend()
  killPortProcess()
  await new Promise((r) => setTimeout(r, 1000))
  startPythonBackend()
  return true
})

ipcMain.handle('get-backend-status', async () => {
  return backendReady ? 'online' : 'offline'
})

ipcMain.handle('window-minimize', () => {
  if (mainWindow) mainWindow.minimize()
})

ipcMain.handle('window-maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize()
    } else {
      mainWindow.maximize()
    }
  }
})

ipcMain.handle('window-close', () => {
  if (mainWindow) mainWindow.close()
})

ipcMain.handle('window-is-maximized', () => {
  return mainWindow ? mainWindow.isMaximized() : false
})

app.whenReady().then(async () => {
  const existingOk = await checkBackendHealth()

  if (!existingOk) {
    killPortProcess()
    await new Promise((r) => setTimeout(r, 500))
    startPythonBackend()
  } else {
    backendReady = true
    console.log('[Backend] Using existing backend on port', BACKEND_PORT)
  }

  startBackendMonitor()

  let attempts = 0
  while (attempts < 30) {
    const healthy = await checkBackendHealth()
    if (healthy) {
      backendReady = true
      break
    }
    await new Promise((r) => setTimeout(r, 500))
    attempts++
  }

  createWindow()

  if (mainWindow) {
    mainWindow.webContents.on('did-finish-load', () => {
      mainWindow.webContents.send('backend-status', backendReady ? 'online' : 'offline')
    })
  }
})

app.on('window-all-closed', () => {
  killPythonBackend()
  killPortProcess()
  app.quit()
})

app.on('before-quit', () => {
  killPythonBackend()
  killPortProcess()
})
