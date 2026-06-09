import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    console.log('Request:', config)
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('Response Error:', error)
    return Promise.reject(error)
  }
)

// 聊天相关API（修复版 - 使用axios并正确处理流式响应）
export const chatAPI = {
  // 发送消息（流式）
  async sendMessage(message) {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'text/plain'
        },
        body: JSON.stringify({ message })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return response
    } catch (error) {
      console.error('Chat API Error:', error)
      throw error
    }
  }
}

// 文件上传相关API（修复版）
export const uploadAPI = {
  // 上传文件
  async uploadFile(file, onProgress) {
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await axios.post('/api/upload', formData, {
        headers: { 
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(percent)
          }
        }
      })
      
      return response.data
    } catch (error) {
      console.error('Upload API Error:', error)
      throw error
    }
  },
  
  // 批量上传文件
  async uploadFiles(files, onProgress) {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    
    try {
      const response = await axios.post('/api/upload/batch', formData, {
        headers: { 
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(percent)
          }
        }
      })
      
      return response.data
    } catch (error) {
      console.error('Batch Upload API Error:', error)
      throw error
    }
  }
}

// 知识库管理API（修复版）
export const knowledgeAPI = {
  // 获取文档列表
  async getDocuments() {
    try {
      const response = await api.get('/documents')
      return response
    } catch (error) {
      console.error('Get Documents API Error:', error)
      throw error
    }
  },
  
  // 删除文档
  async deleteDocument(md5) {
    try {
      const response = await api.delete(`/documents/${md5}`)
      return response
    } catch (error) {
      console.error('Delete Document API Error:', error)
      throw error
    }
  },
  
  // 触发向量化
  async vectorize() {
    try {
      const response = await api.post('/vectorize')
      return response
    } catch (error) {
      console.error('Vectorize API Error:', error)
      throw error
    }
  },
  
  // 获取向量化进度
  async getVectorizeProgress() {
    try {
      const response = await api.get('/vectorize/progress')
      return response
    } catch (error) {
      console.error('Get Progress API Error:', error)
      throw error
    }
  }
}

// 统计信息API（修复版）
export const statsAPI = {
  // 获取系统统计
  async getStats() {
    try {
      const response = await api.get('/stats')
      return response
    } catch (error) {
      console.error('Get Stats API Error:', error)
      throw error
    }
  }
}

export default api
