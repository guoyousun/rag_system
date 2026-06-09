<template>
  <div class="home-container">
    <!-- 顶部标题栏 -->
    <div class="header">
      <h1>🤖 智能问答系统</h1>
      <el-button @click="clearChat" size="small">
        <el-icon><Delete /></el-icon>
        清空对话
      </el-button>
    </div>

    <!-- 聊天区域 -->
    <div class="chat-area" ref="chatAreaRef">
      <div v-if="messages.length === 0" class="welcome-screen">
        <el-icon :size="80" color="#409EFF"><ChatDotRound /></el-icon>
        <h2>欢迎使用工业软件平台智能问答系统</h2>
        <p>我可以帮您解答以下问题：</p>
        <div class="quick-questions">
          <el-tag 
            v-for="question in quickQuestions" 
            :key="question"
            class="question-tag"
            @click="sendQuickQuestion(question)"
          >
            {{ question }}
          </el-tag>
        </div>
      </div>

      <div v-else class="messages-container">
        <div 
          v-for="(message, index) in messages" 
          :key="index"
          :class="['message', message.role]"
        >
          <div class="message-avatar">
            <el-icon v-if="message.role === 'user'" :size="32">
              <User />
            </el-icon>
            <el-icon v-else :size="32" color="#409EFF">
              <ChatDotRound />
            </el-icon>
          </div>
          
          <div class="message-content">
            <div class="message-header">
              <span class="role">{{ message.role === 'user' ? '您' : 'AI助手' }}</span>
              <span class="time">{{ formatTime(message.timestamp) }}</span>
            </div>
            
            <div class="message-body" v-html="renderMarkdown(message.content)"></div>
            
            <div v-if="message.isStreaming" class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="3"
        placeholder="请输入您的问题...（支持Shift+Enter换行，Enter发送）"
        @keydown.enter.exact.prevent="sendMessage"
        :disabled="isLoading"
      />
      
      <div class="input-actions">
        <div class="tips">
          <el-icon><InfoFilled /></el-icon>
          <span>按 Enter 发送，Shift + Enter 换行</span>
        </div>
        
        <el-button 
          type="primary" 
          @click="sendMessage"
          :loading="isLoading"
          :disabled="!inputMessage.trim()"
        >
          <el-icon><Promotion /></el-icon>
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'

const chatStore = useChatStore()
const inputMessage = ref('')
const chatAreaRef = ref(null)

const messages = ref(chatStore.messages)
const isLoading = ref(chatStore.isLoading)

// 快捷问题
const quickQuestions = [
  '智能制造中的数字孪生技术如何应用？',
  '我想参与制造业数字化转型的众包项目，有什么建议？',
  '众创方案的专业指导流程是什么？',
  '政府扶持政策有哪些？如何申请？',
  '给我生成我的使用报告'
]

// 监听消息变化，自动滚动到底部
watch(messages, () => {
  nextTick(() => {
    if (chatAreaRef.value) {
      chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
    }
  })
}, { deep: true })

// 渲染Markdown
const renderMarkdown = (content) => {
  if (!content) return ''
  return marked.parse(content)
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  const message = inputMessage.value.trim()
  inputMessage.value = ''
  
  await chatStore.sendMessageStream(message)
}

// 发送快捷问题
const sendQuickQuestion = (question) => {
  inputMessage.value = question
  sendMessage()
}

// 清空聊天
const clearChat = () => {
  chatStore.clearMessages()
  ElMessage.success('聊天记录已清空')
}
</script>

<style scoped lang="scss">
.home-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: white;
}

.header {
  padding: 20px 30px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  
  h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
  }
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 30px;
  
  .welcome-screen {
    text-align: center;
    padding: 80px 20px;
    
    h2 {
      margin: 30px 0 15px;
      color: #303133;
      font-size: 24px;
    }
    
    p {
      color: #606266;
      margin-bottom: 30px;
    }
    
    .quick-questions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      justify-content: center;
      max-width: 800px;
      margin: 0 auto;
      
      .question-tag {
        cursor: pointer;
        padding: 12px 20px;
        font-size: 14px;
        transition: all 0.3s;
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
        }
      }
    }
  }
  
  .messages-container {
    .message {
      display: flex;
      margin-bottom: 24px;
      animation: fadeIn 0.3s ease-in;
      
      &.user {
        flex-direction: row-reverse;
        
        .message-content {
          background: #ecf5ff;
          margin-right: 12px;
        }
      }
      
      &.assistant {
        .message-content {
          background: #f4f4f5;
          margin-left: 12px;
        }
      }
      
      .message-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: white;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        flex-shrink: 0;
      }
      
      .message-content {
        max-width: 70%;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        
        .message-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          font-size: 12px;
          
          .role {
            font-weight: 600;
            color: #303133;
          }
          
          .time {
            color: #909399;
          }
        }
        
        .message-body {
          color: #606266;
          line-height: 1.8;
          font-size: 14px;
          
          :deep(p) {
            margin: 8px 0;
          }
          
          :deep(code) {
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
          }
          
          :deep(pre) {
            background: #282c34;
            color: #abb2bf;
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 12px 0;
            
            code {
              background: transparent;
              padding: 0;
            }
          }
          
          :deep(ul), :deep(ol) {
            padding-left: 24px;
            margin: 8px 0;
          }
          
          :deep(li) {
            margin: 4px 0;
          }
        }
        
        .typing-indicator {
          display: flex;
          gap: 4px;
          margin-top: 8px;
          
          span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #909399;
            animation: typing 1.4s infinite;
            
            &:nth-child(2) {
              animation-delay: 0.2s;
            }
            
            &:nth-child(3) {
              animation-delay: 0.4s;
            }
          }
        }
      }
    }
  }
}

.input-area {
  padding: 20px 30px;
  border-top: 1px solid #e4e7ed;
  background: white;
  
  .input-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 12px;
    
    .tips {
      display: flex;
      align-items: center;
      gap: 6px;
      color: #909399;
      font-size: 12px;
    }
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-8px);
  }
}
</style>
