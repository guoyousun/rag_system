<template>
  <div class="chat-page">
    <!-- 会话列表 -->
    <div class="conv-panel">
      <el-button type="primary" class="new-btn" :icon="Plus" @click="newConversation">
        新建对话
      </el-button>
      <div class="conv-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conv-item"
          :class="{ active: conv.id === currentId }"
          @click="switchConversation(conv.id)"
        >
          <span class="conv-title">{{ conv.title }}</span>
          <el-icon class="del" @click.stop="removeConversation(conv.id)"><Delete /></el-icon>
        </div>
        <el-empty v-if="!conversations.length" description="暂无会话" :image-size="60" />
      </div>
    </div>

    <!-- 对话区 -->
    <div class="chat-main">
      <div ref="msgBox" class="msg-area">
        <el-empty
          v-if="!messages.length"
          description="上传工业领域文档后，即可开始多模式协同问答"
        >
          <div class="welcome">
            <p>系统支持三种检索模式：</p>
            <p>· <b>BM25 关键词检索</b> — 精确匹配文档片段</p>
            <p>· <b>向量语义检索</b> — 千问 Embedding 语义相似</p>
            <p>· <b>知识图谱检索</b> — Neo4j 实体关系推理</p>
          </div>
        </el-empty>

        <template v-for="msg in messages" :key="msg.id || msg._localId">
          <div class="msg-row" :class="msg.role">
            <div class="bubble" :class="msg.role">
              <div class="msg-text">{{ msg.content }}</div>
              <!-- 引用来源 -->
              <div v-if="msg.role === 'assistant' && msg.sources?.length" class="sources">
                <el-divider content-position="left">引用来源（{{ msg.sources.length }}）</el-divider>
                <div v-for="(src, i) in msg.sources.slice(0, 3)" :key="i" class="source-card">
                  <div class="src-head">
                    <el-tag size="small" type="info">{{ src.filename }}</el-tag>
                    <span class="src-score">相关度 {{ (src.score * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="src-content">{{ src.content }}</div>
                </div>
              </div>
              <!-- 检索统计 -->
              <div v-if="msg.role === 'assistant' && msg.retrieval_stats" class="stats">
                <el-tag size="small" type="warning" effect="plain">BM25 ×{{ msg.retrieval_stats.bm25 }}</el-tag>
                <el-tag size="small" type="success" effect="plain">向量 ×{{ msg.retrieval_stats.vector }}</el-tag>
                <el-tag size="small" type="danger" effect="plain">图谱 ×{{ msg.retrieval_stats.kg }}</el-tag>
                <el-tag v-if="msg.retrieval_stats.cache_hit" size="small" type="info" effect="plain">缓存命中</el-tag>
              </div>
            </div>
          </div>
        </template>

        <!-- 生成中 -->
        <div v-if="loading" class="msg-row assistant">
          <div class="bubble assistant typing">
            <span class="dot" /><span class="dot" /><span class="dot" />
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <el-input
          v-model="input"
          type="textarea"
          :rows="3"
          resize="none"
          placeholder="请输入你的问题，Enter 发送，Shift+Enter 换行"
          :disabled="loading"
          @keydown.enter.exact.prevent="send"
        />
        <div class="input-actions">
          <span class="hint">多模式协同检索：BM25 + 向量 + 知识图谱</span>
          <el-button type="primary" :icon="Promotion" :loading="loading" @click="send">
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Promotion } from '@element-plus/icons-vue'
import {
  createConversation,
  deleteConversation,
  listConversations,
  listMessages,
  sendMessage
} from '../api/chat'

const conversations = ref([])
const currentId = ref(null)
const messages = ref([])
const input = ref('')
const loading = ref(false)
const msgBox = ref()

let localSeq = 0

onMounted(async () => {
  await loadConversations()
  if (conversations.value.length) {
    await switchConversation(conversations.value[0].id)
  }
})

async function loadConversations() {
  conversations.value = await listConversations()
}

async function newConversation() {
  const conv = await createConversation()
  conversations.value.unshift(conv)
  await switchConversation(conv.id)
}

async function switchConversation(id) {
  currentId.value = id
  messages.value = await listMessages(id)
  scrollBottom()
}

async function removeConversation(id) {
  await ElMessageBox.confirm('删除该会话及全部消息？', '提示', { type: 'warning' })
  await deleteConversation(id)
  conversations.value = conversations.value.filter((c) => c.id !== id)
  if (currentId.value === id) {
    currentId.value = null
    messages.value = []
    if (conversations.value.length) {
      await switchConversation(conversations.value[0].id)
    }
  }
}

async function send() {
  const content = input.value.trim()
  if (!content || loading.value) return
  if (!currentId.value) {
    await newConversation()
  }
  input.value = ''
  messages.value.push({ id: null, _localId: ++localSeq, role: 'user', content })
  scrollBottom()

  loading.value = true
  try {
    const resp = await sendMessage(currentId.value, content)
    messages.value.push({
      id: resp.message_id,
      role: 'assistant',
      content: resp.answer,
      sources: resp.sources,
      retrieval_stats: resp.retrieval_stats
    })
  } catch (e) {
    // 错误提示已由拦截器统一处理
  } finally {
    loading.value = false
    scrollBottom()
  }
}

function scrollBottom() {
  nextTick(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
  })
}
</script>

<style scoped>
.chat-page {
  display: flex;
  height: 100%;
}
.conv-panel {
  width: 240px;
  border-right: 1px solid #e2e8f0;
  background: #fff;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.new-btn {
  width: 100%;
}
.conv-list {
  flex: 1;
  overflow: auto;
}
.conv-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #334155;
  margin-bottom: 4px;
}
.conv-item:hover {
  background: #f1f5f9;
}
.conv-item.active {
  background: #eff6ff;
  color: #2563eb;
}
.conv-title {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conv-item .del {
  opacity: 0;
}
.conv-item:hover .del {
  opacity: 1;
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.msg-area {
  flex: 1;
  overflow: auto;
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.welcome {
  color: #64748b;
  font-size: 14px;
  line-height: 1.9;
}
.msg-row {
  display: flex;
}
.msg-row.user {
  justify-content: flex-end;
}
.bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.7;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}
.bubble.user {
  background: #2563eb;
  color: #fff;
  border-top-right-radius: 2px;
}
.bubble.assistant {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-top-left-radius: 2px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.sources {
  margin-top: 10px;
}
.src-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.src-score {
  font-size: 12px;
  color: #94a3b8;
}
.src-content {
  font-size: 12px;
  color: #64748b;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.stats {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}
.typing {
  display: flex;
  gap: 6px;
  align-items: center;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
  animation: bounce 1.2s infinite;
}
.dot:nth-child(2) {
  animation-delay: 0.15s;
}
.dot:nth-child(3) {
  animation-delay: 0.3s;
}
@keyframes bounce {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-6px);
  }
}
.input-area {
  padding: 12px 24px 16px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}
.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.hint {
  font-size: 12px;
  color: #94a3b8;
}
</style>
