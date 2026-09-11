<template>
  <div class="page-container">
    <!-- 上传区 -->
    <el-card class="upload-card" shadow="never">
      <el-upload
        drag
        multiple
        :auto-upload="false"
        :show-file-list="false"
        accept=".txt,.md,.pdf,.docx"
        :on-change="onFileChange"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文档到此处，或 <em>点击选择文件</em></div>
        <template #tip>
          <div class="el-upload__tip">
            支持 .txt / .md / .pdf / .docx，单个文件不超过 50MB；上传后自动执行
            「解析 → 分块 → 向量化 → 图谱构建」
          </div>
        </template>
      </el-upload>
    </el-card>

    <!-- 文档列表 -->
    <el-card shadow="never" class="list-card">
      <template #header>
        <div class="card-head">
          <span>文档库（{{ documents.length }}）</span>
          <el-button :icon="Refresh" circle size="small" @click="load" />
        </div>
      </template>

      <el-table :data="documents" v-loading="loading">
        <el-table-column prop="filename" label="文件名" min-width="240" show-overflow-tooltip />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.file_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="100">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-tag :type="statusMeta[row.status]?.type || 'info'" size="small" effect="light">
              {{ statusMeta[row.status]?.text || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="分块/实体" width="120">
          <template #default="{ row }">{{ row.chunk_count }} / {{ row.entity_count }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :icon="View" @click="showDetail(row)">分块</el-button>
            <el-button
              v-if="row.status === 'failed'"
              size="small"
              type="warning"
              :icon="RefreshRight"
              @click="reprocess(row)"
            >
              重试
            </el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无文档，请先上传工业领域资料" />
        </template>
      </el-table>
    </el-card>

    <!-- 分块详情抽屉 -->
    <el-drawer v-model="detailVisible" :title="detailDoc?.filename" size="50%">
      <div class="chunk-list">
        <el-collapse>
          <el-collapse-item v-for="chunk in detailChunks" :key="chunk.id" :name="chunk.id">
            <template #title>
              <span class="chunk-title">片段 #{{ chunk.chunk_index + 1 }}</span>
            </template>
            <div class="chunk-content">{{ chunk.content }}</div>
          </el-collapse-item>
        </el-collapse>
        <el-empty v-if="!detailChunks.length" description="暂无分块（文档可能处理失败）" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  UploadFilled, Refresh, RefreshRight, View, Delete
} from '@element-plus/icons-vue'
import {
  deleteDocument, getDocument, listDocuments, reprocessDocument, uploadDocument
} from '../api/document'

const documents = ref([])
const loading = ref(false)
const detailVisible = ref(false)
const detailDoc = ref(null)
const detailChunks = ref([])

const statusMeta = reactive({
  uploaded: { text: '待处理', type: 'info' },
  parsing: { text: '解析中', type: 'warning' },
  vectorizing: { text: '向量化中', type: 'warning' },
  kg_building: { text: '图谱构建中', type: 'warning' },
  ready: { text: '已完成', type: 'success' },
  failed: { text: '处理失败', type: 'danger' }
})

let pollTimer = null

onMounted(() => {
  load()
  // 后台处理期间轮询状态
  pollTimer = setInterval(load, 5000)
})
onBeforeUnmount(() => clearInterval(pollTimer))

async function load() {
  loading.value = true
  try {
    documents.value = await listDocuments()
  } finally {
    loading.value = false
  }
}

async function onFileChange(file) {
  // 同名文件预检（后端 409 兜底）
  const dup = documents.value.find((d) => d.filename === file.name)
  if (dup) {
    ElMessage.warning(`已存在同名文件「${file.name}」，请先删除原文件或重命名后再上传`)
    return
  }
  try {
    await uploadDocument(file.raw)
    ElMessage.success(`「${file.name}」上传成功，后台处理中`)
  } catch (e) {
    // 拦截器已提示
  }
  await load()
}

async function showDetail(row) {
  detailDoc.value = row
  const detail = await getDocument(row.id)
  detailChunks.value = detail.chunks || []
  detailVisible.value = true
}

async function reprocess(row) {
  await ElMessageBox.confirm(`重新处理「${row.filename}」？将清空旧分块/向量/图谱后重跑。`, '提示', { type: 'warning' })
  await reprocessDocument(row.id)
  ElMessage.success('已开始重新处理')
  load()
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除「${row.filename}」？将同时清理向量与图谱数据。`, '警告', { type: 'error' })
  await deleteDocument(row.id)
  ElMessage.success('已删除')
  load()
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let v = bytes
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i++
  }
  return `${v.toFixed(1)} ${units[i]}`
}

function formatTime(t) {
  return t ? t.replace('T', ' ').slice(0, 19) : '-'
}
</script>

<style scoped>
.upload-card {
  margin-bottom: 16px;
}
.list-card :deep(.el-card__header) {
  padding: 12px 20px;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chunk-title {
  font-size: 13px;
  color: #2563eb;
}
.chunk-content {
  font-size: 13px;
  color: #475569;
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
