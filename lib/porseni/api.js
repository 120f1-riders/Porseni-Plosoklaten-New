export const getToken = () => (typeof window !== 'undefined' ? localStorage.getItem('porseni_token') : null)
export const setToken = (t) => { if (typeof window !== 'undefined') localStorage.setItem('porseni_token', t) }
export const clearToken = () => { if (typeof window !== 'undefined') localStorage.removeItem('porseni_token') }

export async function api(path, { method = 'GET', body, isForm = false } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers['Authorization'] = 'Bearer ' + token
  let payload
  if (isForm) {
    payload = body
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  const res = await fetch('/api' + path, { method, headers, body: payload })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || 'Terjadi kesalahan')
  return data
}

export async function uploadFile(file, folderPath) {
  const fd = new FormData()
  fd.append('file', file)
  if (folderPath) fd.append('folder_path', folderPath)
  return api('/upload', { method: 'POST', body: fd, isForm: true })
}

export const fileUrl = (id) => (id ? '/api/files/' + id : null)
