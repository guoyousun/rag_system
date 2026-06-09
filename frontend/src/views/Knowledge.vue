<template>
  <div class="knowledge-container">
    <div class="header">
      <h1>📚 知识库管理</h1>
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>
        上传文件
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon :size="40" color="#409EFF"><Document /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ documents.length }}</div>
              <div class="stat-label">文档总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon :size="40" color="#67C23A"><Files /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ formatSize(totalSize) }}</div>
              <div class="stat-label">总大小</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon :size="40" color="#E6A23C"><Histogram /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.vectorCount || 0 }}</div>
              <div class="stat-label">向量数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon :size="40" color="#F56C6C"><Clock /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ lastUpdateTime }}</div>
              <div class="stat-label">最后更新</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button 
        type="success" 
        @click="handleVectorize"
        :loading="isVectorizing"
      >
        <el-icon><Refresh /></el-icon>
        {{ isVectorizing ? '向量化中...' : '开始向量化' }}
      </el-button>
      
      <el-button @click="refreshDocuments">
        <el-icon><RefreshRight /></el-icon>
        刷新
      </el-button>
      
      <el-progress 
        v-if="isVectorizing"
        :percentage="vectorizeProgress"
        :stroke-width="18"
        style="width: 300px; margin-left: 20px;"
      />
    </div>

    <!-- 文档列表 -->
    <el-card class="document-list">
      <template #header>
        <div class="card-header">
          <span>文档列表</span>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索文档..."
            prefix-icon="Search"
            style="width: 250px;"
            clearable
          />
        </div>
      </template>
      
      <el-table 
        :data="filteredDocuments" 
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="name" label="文件名" min-width="200">
          <template #default="{ row }">
            <div class="file-name">
              <el-icon :size="20" :color="getFileIconColor(row.name)">
                <component :is="getFileIcon(row.name)" />
              </el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ getFileType(row.name) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="uploadTime" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.uploadTime) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="row.status === 'vectorized' ? 'success' : 'warning'"
              size="small"
            >
              {{ row.status === 'vectorized' ? '已向量化' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="danger" 
              size="small"
              @click="handleDelete(row)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="filteredDocuments.length === 0" description="暂无文档" />
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传文件"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-upload
        ref="uploadRef"
        class="upload-area"
        drag
        multiple
        :auto-upload="false"
        :on-change="handleFileChange"
        :before-upload="beforeUpload"
        accept=".pdf,.docx,.doc,.txt,.xlsx,.xls,.csv,.jpg,.jpeg,.png"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF、Word、TXT、Excel、图片等格式，单个文件不超过50MB
          </div>
        </template>
      </el-upload>
      
      <!-- 文件列表预览 -->
      <div v-if="selectedFiles.length > 0" class="file-preview">
        <h4>已选择 {{ selectedFiles.length }} 个文件：</h4>
        <el-table :data="selectedFiles" max-height="200">
          <el-table-column prop="name" label="文件名" />
          <el-table-column prop="size" label="大小" width="100">
            <template #default="{ row }">
              {{ formatSize(row.size) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ $index }">
              <el-button 
                type="danger" 
                size="small" 
                link
                @click="removeFile($index)"
              >
                移除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleUpload"
          :loading="uploading"
          :disabled="selectedFiles.length === 0"
        >
          开始上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useKnowledgeStore } from '@/stores/knowledge'
import { ElMessage, ElMessageBox } from 'element-plus'

const knowledgeStore = useKnowledgeStore()

const showUploadDialog = ref(false)
const selectedFiles = ref([])
const uploading = ref(false)
const loading = ref(false)
const searchKeyword = ref('')

// 计算属性
const documents = computed(() => knowledgeStore.documents)
const stats = computed(() => knowledgeStore.stats)
const isVectorizing = computed(() => knowledgeStore.isVectorizing)
const vectorizeProgress = computed(() => knowledgeStore.vectorizeProgress)

const filteredDocuments = computed(() => {
  if (!searchKeyword.value) return documents.value
  
  const keyword = searchKeyword.value.toLowerCase()
  return documents.value.filter(doc => 
    doc.name && doc.name.toLowerCase().includes(keyword)
  )
})

const totalSize = computed(() => {
  return documents.value.reduce((sum, doc) => sum + (doc.size || 0), 0)
})

const lastUpdateTime = computed(() => {
  if (documents.value.length === 0) return '-'
  const lastDoc = documents.value[documents.value.length - 1]
  return formatTime(lastDoc.uploadTime)
})

// 生命周期
onMounted(() => {
  refreshDocuments()
  fetchStats()
})

// 方法
const refreshDocuments = async () => {
  loading.value = true
  await knowledgeStore.fetchDocuments()
  loading.value = false
}

const fetchStats = async () => {
  await knowledgeStore.fetchStats()
}

const handleFileChange = (file, fileList) => {
  // 更新选中的文件列表
  selectedFiles.value = fileList.map(f => f.raw).filter(Boolean)
}

const beforeUpload = (file) => {
  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
    'image/jpeg',
    'image/png',
    'image/jpg'
  ]
  
  const isAllowed = allowedTypes.includes(file.type) || 
    file.name.match(/\.(pdf|docx|doc|txt|xlsx|xls|csv|jpg|jpeg|png)$/i)
  
  if (!isAllowed) {
    ElMessage.error('不支持的文件格式')
    return false
  }
  
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过50MB')
    return false
  }
  
  return true
}

const removeFile = (index) => {
  selectedFiles.value.splice(index, 1)
}

const handleUpload = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  
  uploading.value = true
  
  try {
    // uploadFiles 内部已经处理了消息显示
    const result = await knowledgeStore.uploadFiles(selectedFiles.value)
    
    // 关闭对话框并清空选择
    showUploadDialog.value = false
    selectedFiles.value = []
    
    // 如果有失败的文件，显示详细结果
    if (result && result.failed > 0) {
      console.log('上传结果:', result)
    }
  } catch (error) {
    console.error('上传异常:', error)
    ElMessage.error('上传过程发生错误')
  } finally {
    uploading.value = false
  }
}

const handleVectorize = async () => {
  await knowledgeStore.startVectorize()
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${row.name}" 吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await knowledgeStore.deleteDocument(row.md5 || row.id)
  } catch (error) {
    // 用户取消或删除失败
  }
}

// 工具函数
const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

const getFileType = (filename) => {
  if (!filename) return '未知'
  const ext = filename.split('.').pop().toLowerCase()
  const typeMap = {
    pdf: 'PDF',
    doc: 'Word',
    docx: 'Word',
    txt: '文本',
    xls: 'Excel',
    xlsx: 'Excel',
    csv: 'CSV',
    jpg: '图片',
    jpeg: '图片',
    png: '图片'
  }
  return typeMap[ext] || ext.toUpperCase()
}

const getFileIcon = (filename) => {
  if (!filename) return 'Document'
  const ext = filename.split('.').pop().toLowerCase()
  const iconMap = {
    pdf: 'Document',
    doc: 'Document',
    docx: 'Document',
    txt: 'Document',
    xls: 'Grid',
    xlsx: 'Grid',
    csv: 'Grid',
    jpg: 'Picture',
    jpeg: 'Picture',
    png: 'Picture'
  }
  return iconMap[ext] || 'Document'
}

const getFileIconColor = (filename) => {
  if (!filename) return '#909399'
  const ext = filename.split('.').pop().toLowerCase()
  const colorMap = {
    pdf: '#F56C6C',
    doc: '#409EFF',
    docx: '#409EFF',
    txt: '#909399',
    xls: '#67C23A',
    xlsx: '#67C23A',
    csv: '#67C23A',
    jpg: '#E6A23C',
    jpeg: '#E6A23C',
    png: '#E6A23C'
  }
  return colorMap[ext] || '#909399'
}
</script>

<style scoped lang="scss">
.knowledge-container {
  padding: 30px;
  height: 100vh;
  overflow-y: auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  
  h1 {
    margin: 0;
    font-size: 28px;
    color: #303133;
  }
}

.stats-row {
  margin-bottom: 30px;
  
  .stat-card {
    :deep(.el-card__body) {
      padding: 20px;
    }
    
    .stat-content {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .stat-info {
        flex: 1;
        
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: #303133;
          margin-bottom: 4px;
        }
        
        .stat-label {
          font-size: 14px;
          color: #909399;
        }
      }
    }
  }
}

.action-bar {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  gap: 12px;
}

.document-list {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .file-name {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.upload-area {
  margin: 20px 0;
  
  :deep(.el-upload-dragger) {
    padding: 40px;
  }
}

.file-preview {
  margin-top: 20px;
  
  h4 {
    margin: 0 0 12px 0;
    color: #606266;
    font-size: 14px;
  }
}
</style>
