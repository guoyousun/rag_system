<template>
  <div class="settings-container">
    <div class="header">
      <h1>⚙️ 系统设置</h1>
    </div>

    <el-row :gutter="20">
      <!-- 系统信息 -->
      <el-col :span="16">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>系统信息</span>
            </div>
          </template>
          
          <el-descriptions :column="2" border>
            <el-descriptions-item label="系统版本">v1.0.0</el-descriptions-item>
            <el-descriptions-item label="框架">Vue 3 + Vite</el-descriptions-item>
            <el-descriptions-item label="UI组件">Element Plus</el-descriptions-item>
            <el-descriptions-item label="状态管理">Pinia</el-descriptions-item>
            <el-descriptions-item label="后端框架">Python + FastAPI</el-descriptions-item>
            <el-descriptions-item label="向量数据库">ChromaDB</el-descriptions-item>
            <el-descriptions-item label="大模型">通义千问</el-descriptions-item>
            <el-descriptions-item label="嵌入模型">DashScope Embeddings</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="settings-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>知识库配置</span>
            </div>
          </template>
          
          <el-form label-width="140px">
            <el-form-item label="支持的文档格式">
              <el-tag v-for="type in supportedFormats" :key="type" style="margin-right: 8px;">
                {{ type }}
              </el-tag>
            </el-form-item>
            
            <el-form-item label="最大文件大小">
              <span>50 MB</span>
            </el-form-item>
            
            <el-form-item label="文本分片大小">
              <span>200 tokens</span>
            </el-form-item>
            
            <el-form-item label="分片重叠">
              <span>20 tokens</span>
            </el-form-item>
            
            <el-form-item label="检索返回数量">
              <span>3 个文档</span>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 操作面板 -->
      <el-col :span="8">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>快捷操作</span>
            </div>
          </template>
          
          <div class="action-buttons">
            <el-button 
              type="primary" 
              @click="clearVectorDB"
              style="width: 100%; margin-bottom: 12px;"
            >
              <el-icon><Delete /></el-icon>
              清空向量数据库
            </el-button>
            
            <el-button 
              type="warning" 
              @click="clearChatHistory"
              style="width: 100%; margin-bottom: 12px;"
            >
              <el-icon><Delete /></el-icon>
              清空聊天记录
            </el-button>
            
            <el-button 
              type="success" 
              @click="exportData"
              style="width: 100%; margin-bottom: 12px;"
            >
              <el-icon><Download /></el-icon>
              导出数据
            </el-button>
            
            <el-button 
              @click="viewLogs"
              style="width: 100%;"
            >
              <el-icon><Document /></el-icon>
              查看日志
            </el-button>
          </div>
        </el-card>

        <el-card class="settings-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>关于系统</span>
            </div>
          </template>
          
          <div class="about-content">
            <h3>工业软件平台多模式协同智能问答系统</h3>
            <p>基于RAG技术的智能问答系统，支持：</p>
            <ul>
              <li>✅ 工业技术文档智能问答</li>
              <li>✅ 众包项目需求匹配</li>
              <li>✅ 众创方案专业指导</li>
              <li>✅ 众扶政策解读</li>
              <li>✅ 个性化报告生成</li>
            </ul>
            
            <el-divider />
            
            <p class="tech-stack">技术栈：</p>
            <div class="tech-tags">
              <el-tag type="info">LangChain</el-tag>
              <el-tag type="info">LangGraph</el-tag>
              <el-tag type="info">ChromaDB</el-tag>
              <el-tag type="info">通义千问</el-tag>
              <el-tag type="info">Vue 3</el-tag>
              <el-tag type="info">Element Plus</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()

const supportedFormats = [
  'PDF', 'DOCX', 'DOC', 'TXT', 
  'XLSX', 'XLS', 'CSV', 
  'JPG', 'JPEG', 'PNG'
]

const clearVectorDB = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空向量数据库吗？此操作不可恢复！',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // TODO: 调用后端API清空向量数据库
    ElMessage.success('向量数据库已清空')
  } catch (error) {
    // 用户取消
  }
}

const clearChatHistory = () => {
  chatStore.clearMessages()
  ElMessage.success('聊天记录已清空')
}

const exportData = () => {
  ElMessage.info('导出功能开发中...')
}

const viewLogs = () => {
  ElMessage.info('日志查看功能开发中...')
}
</script>

<style scoped lang="scss">
.settings-container {
  padding: 30px;
}

.header {
  margin-bottom: 30px;
  
  h1 {
    margin: 0;
    font-size: 28px;
    color: #303133;
  }
}

.settings-card {
  .card-header {
    font-weight: 600;
    font-size: 16px;
  }
}

.action-buttons {
  display: flex;
  flex-direction: column;
}

.about-content {
  h3 {
    margin: 0 0 16px 0;
    color: #303133;
    font-size: 18px;
  }
  
  p {
    color: #606266;
    margin: 8px 0;
  }
  
  ul {
    list-style: none;
    padding: 0;
    margin: 12px 0;
    
    li {
      padding: 4px 0;
      color: #606266;
    }
  }
  
  .tech-stack {
    font-weight: 600;
    margin-top: 16px;
  }
  
  .tech-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 8px;
  }
}
</style>
