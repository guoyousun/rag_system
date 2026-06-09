import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatAPI } from '@/api'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const isLoading = ref(false)
  const currentMessage = ref('')

  // 添加用户消息
  function addUserMessage(content) {
    messages.value.push({
      role: 'user',
      content: content,
      timestamp: new Date().toISOString()
    })
  }

  // 添加AI消息
  function addAIMessage(content) {
    messages.value.push({
      role: 'assistant',
      content: content,
      timestamp: new Date().toISOString()
    })
  }

  // 流式发送消息
  async function sendMessageStream(content) {
    if (!content.trim()) return
    
    addUserMessage(content)
    isLoading.value = true
    currentMessage.value = ''
    
    // 添加一个空的AI消息用于流式更新
    const aiMessageIndex = messages.value.length
    messages.value.push({
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true
    })
    
    try {
      const response = await chatAPI.sendMessage(content)
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        currentMessage.value += chunk
        
        // 更新最后一条消息
        messages.value[aiMessageIndex].content = currentMessage.value
      }
      
      messages.value[aiMessageIndex].isStreaming = false
    } catch (error) {
      console.error('发送消息失败:', error)
      messages.value[aiMessageIndex].content = '抱歉，发生了错误，请稍后重试。'
      messages.value[aiMessageIndex].isStreaming = false
    } finally {
      isLoading.value = false
      currentMessage.value = ''
    }
  }

  // 清空聊天记录
  function clearMessages() {
    messages.value = []
  }

  return {
    messages,
    isLoading,
    currentMessage,
    addUserMessage,
    addAIMessage,
    sendMessageStream,
    clearMessages
  }
})
