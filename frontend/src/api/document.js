import request from './request'

// 上传文档（multipart，后端异步处理）
export const uploadDocument = (file) => {
  const form = new FormData()
  form.append('file', file)
  return request.post('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000
  })
}

export const listDocuments = () => request.get('/documents')

export const getDocument = (id) => request.get(`/documents/${id}`)

export const deleteDocument = (id) => request.delete(`/documents/${id}`)

export const reprocessDocument = (id) => request.post(`/documents/${id}/reprocess`)
