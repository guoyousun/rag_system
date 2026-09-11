import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 120000
})

// 请求拦截：附加 JWT
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('qa_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：统一错误提示 + 401 跳登录
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    if (status === 401) {
      localStorage.removeItem('qa_token')
      localStorage.removeItem('qa_user')
      if (router.currentRoute.value.name !== 'Login') {
        ElMessage.error(detail || '登录已过期，请重新登录')
        router.push({ name: 'Login' })
      }
    } else {
      const msg = typeof detail === 'string' ? detail : (error.message || '请求失败')
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default request
