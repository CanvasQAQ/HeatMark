import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8477/api',
  timeout: 30000,
})

export function getPrinters() {
  return api.get('/printers')
}

export function processImage(imageBase64, options) {
  return api.post('/process', {
    image_base64: imageBase64,
    options
  })
}

export function printLabel(imageBase64, options, printerName, copies) {
  return api.post('/print', {
    image_base64: imageBase64,
    options,
    printer_name: printerName,
    copies
  })
}

export function healthCheck() {
  return api.get('/health')
}

export function getTemplates() {
  return api.get('/templates')
}

export function getTemplate(id) {
  return api.get(`/templates/${encodeURIComponent(id)}`)
}

export function saveTemplate(body) {
  return api.post('/templates/save', body)
}

export function updateIndex(data) {
  return api.put('/templates/index', data)
}

