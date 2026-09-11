import request from './request'

// 会话管理
export const createConversation = (title = '新对话') =>
  request.post('/chats', { title })

export const listConversations = () => request.get('/chats')

export const deleteConversation = (id) => request.delete(`/chats/${id}`)

export const listMessages = (convId) => request.get(`/chats/${convId}/messages`)

// 问答
export const sendMessage = (convId, content) =>
  request.post(`/chats/${convId}/messages`, { content })

// 检索调试
export const debugSearch = (query, topK = 5) =>
  request.post('/search', { query, top_k: topK })

// 知识图谱概览
export const getGraphOverview = (limit = 80) =>
  request.get('/graph', { params: { limit } })
