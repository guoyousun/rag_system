import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatAPI } from '@/api'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const isLoading = ref(false)
  const currentMessage = ref('')
  const chunkCount = ref(0)

  function addUserMessage(content) {
    messages.value.push({
      role: 'user',
      content: content,
      timestamp: new Date().toISOString()
    })
  }

  function addAIMessage(content) {
    messages.value.push({
      role: 'assistant',
      content: content,
      timestamp: new Date().toISOString()
    })
  }

  async function sendMessageStream(content) {
    if (!content.trim()) return

    console.log('[Chat Store] 发送消息:', content.substring(0, 60))

    addUserMessage(content)
    isLoading.value = true
    currentMessage.value = ''
    chunkCount.value = 0

    const aiMessageIndex = messages.value.length
    messages.value.push({
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true
    })

    try {
      const response = await chatAPI.sendMessage(content)
      console.log('[Chat Store] 收到响应, status:', response.status, 'ok:', response.ok)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('[Chat Store] 响应异常:', errorText)
        throw new Error(`服务器响应错误: ${response.status}`)
      }

      if (!response.body) {
        console.error('[Chat Store] response.body 为 null，尝试使用 text()')
        const textContent = await response.text()
        currentMessage.value = textContent
        messages.value[aiMessageIndex].content = textContent
        messages.value[aiMessageIndex].isStreaming = false
        console.log('[Chat Store] 非流式响应完成，内容长度:', textContent.length)
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')

      console.log('[Chat Store] 开始流式读取...')

      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          console.log('[Chat Store] 流读取完成，总块数:', chunkCount.value)
          break
        }

        if (value) {
          const chunk = decoder.decode(value, { stream: true })
          if (chunk) {
            chunkCount.value++
            currentMessage.value += chunk
            messages.value[aiMessageIndex].content = currentMessage.value

            if (chunkCount.value % 10 === 0) {
              console.log('[Chat Store] 已接收', chunkCount.value, '块, 当前总长度:', currentMessage.value.length)
            }
          }
        }
      }

      const finalChunk = decoder.decode()
      if (finalChunk) {
        currentMessage.value += finalChunk
        messages.value[aiMessageIndex].content = currentMessage.value
      }

      if (!currentMessage.value.trim()) {
        console.warn('[Chat Store] 响应内容为空，使用默认提示')
        currentMessage.value = '（系统未能生成有效回答，请尝试重新提问或稍后再试）'
        messages.value[aiMessageIndex].content = currentMessage.value
      }

      messages.value[aiMessageIndex].isStreaming = false
      console.log('[Chat Store] 流式接收完成，总内容长度:', currentMessage.value.length)
    } catch (error) {
      console.error('[Chat Store] 发送消息失败:', error)
      messages.value[aiMessageIndex].content = '抱歉，发生了错误：' + error.message + '。请稍后重试。'
      messages.value[aiMessageIndex].isStreaming = false
    } finally {
      isLoading.value = false
      currentMessage.value = ''
    }
  }

  function clearMessages() {
    messages.value = []
  }

  return {
    messages,
    isLoading,
    currentMessage,
    chunkCount,
    addUserMessage,
    addAIMessage,
    sendMessageStream,
    clearMessages
  }
})