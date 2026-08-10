import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 60000,
})

// 自动携带登录 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 流式请求：基于 fetch + ReadableStream，逐段回调增量文本
export async function streamRequest(
  path: string,
  options: { body?: unknown; formData?: FormData },
  onDelta: (text: string) => void
): Promise<any> {
  const token = localStorage.getItem('token') || ''
  const headers: Record<string, string> = { Authorization: `Bearer ${token}` }
  let body: BodyInit | undefined
  if (options.formData) {
    body = options.formData
  } else {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(options.body ?? {})
  }

  const res = await fetch(path, { method: 'POST', headers, body })
  if (!res.ok || !res.body) {
    throw new Error(`HTTP ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let result: any = null

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''
    for (const part of parts) {
      if (!part.startsWith('data:')) continue
      try {
        const data = JSON.parse(part.slice(5).trim())
        if (data.type === 'delta') onDelta(data.content ?? '')
        else if (data.type === 'done') result = data
        else if (data.type === 'error') throw new Error(data.message || '生成失败')
      } catch (error: any) {
        if (!(error instanceof SyntaxError)) throw error
      }
    }
  }

  if (!result) throw new Error('流式生成未完成')
  return result
}

export default api
