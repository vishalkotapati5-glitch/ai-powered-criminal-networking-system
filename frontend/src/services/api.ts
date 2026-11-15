const API_URL = import.meta.env.VITE_API_URL || '/api'

export function setToken(token: string | null) {
  if (token) localStorage.setItem('access_token', token)
  else localStorage.removeItem('access_token')
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('access_token')
  const headers = new Headers(init.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const response = await fetch(`${API_URL}${path}`, { ...init, headers })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export async function downloadReport(reference: string, format: 'csv' | 'pdf') {
  const response = await fetch(`${API_URL}/reports/${reference}/download?format=${format}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` },
  })
  if (!response.ok) throw new Error('Could not download report')
  const url = URL.createObjectURL(await response.blob())
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = format === 'csv' ? `${reference}.csv.zip` : `${reference}.pdf`
  anchor.click()
  URL.revokeObjectURL(url)
}
