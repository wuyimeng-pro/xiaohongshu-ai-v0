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

export default api
