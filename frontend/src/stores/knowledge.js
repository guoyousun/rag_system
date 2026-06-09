import { defineStore } from 'pinia'
import { ref } from 'vue'
import { uploadAPI, knowledgeAPI, statsAPI } from '@/api'
import { ElMessage } from 'element-plus'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const documents = ref([])
  const uploadingFiles = ref([])
  const vectorizeProgress = ref(0)
  const isVectorizing = ref(false)
  const stats = ref({})

  // 获取文档列表
  async function fetchDocuments() {
    try {
      const response = await knowledgeAPI.getDocuments()
      documents.value = response.data || []
    } catch (error) {
      console.error('获取文档列表失败:', error)
      ElMessage.error('获取文档列表失败')
    }
  }

  // 上传文件（改进版）
  async function uploadFile(file) {
    const uploadItem = {
      file,
      name: file.name,
      size: file.size,
      progress: 0,
      status: 'uploading'
    }
    
    uploadingFiles.value.push(uploadItem)
    
    try {
      await uploadAPI.uploadFile(file, (progress) => {
        uploadItem.progress = progress
      })
      
      uploadItem.status = 'success'
      // 不在这里显示消息，等批量上传完成后统一显示
      
      // 刷新文档列表
      await fetchDocuments()
      
      return { success: true, file: file.name }
    } catch (error) {
      uploadItem.status = 'error'
      console.error('上传失败:', error)
      return { success: false, file: file.name, error: error.message }
    }
  }

  // 批量上传文件（改进版）
  async function uploadFiles(files) {
    if (!files || files.length === 0) {
      ElMessage.warning('请选择要上传的文件')
      return
    }
    
    const results = []
    let successCount = 0
    let failCount = 0
    
    for (const file of files) {
      const result = await uploadFile(file)
      results.push(result)
      
      if (result.success) {
        successCount++
      } else {
        failCount++
      }
    }
    
    // 清除上传记录
    clearUploadingFiles()
    
    // 根据结果显示不同的消息
    if (failCount === 0) {
      // 全部成功
      ElMessage.success(`成功上传 ${successCount} 个文件`)
    } else if (successCount === 0) {
      // 全部失败
      ElMessage.error(`上传失败：${failCount} 个文件`)
    } else {
      // 部分成功
      ElMessage.warning({
        message: `上传完成：${successCount} 个成功，${failCount} 个失败`,
        duration: 5000
      })
    }
    
    // 刷新统计信息
    await fetchStats()
    
    return {
      total: files.length,
      success: successCount,
      failed: failCount,
      results
    }
  }

  // 删除文档
  async function deleteDocument(md5) {
    try {
      await knowledgeAPI.deleteDocument(md5)
      ElMessage.success('文档删除成功')
      await fetchDocuments()
    } catch (error) {
      ElMessage.error('文档删除失败')
      console.error('删除失败:', error)
    }
  }

  // 触发向量化
  async function startVectorize() {
    try {
      isVectorizing.value = true
      vectorizeProgress.value = 0
      
      await knowledgeAPI.vectorize()
      
      // 轮询获取进度
      const pollProgress = async () => {
        if (!isVectorizing.value) return
        
        try {
          const response = await knowledgeAPI.getVectorizeProgress()
          vectorizeProgress.value = response.progress || 0
          
          if (response.status === 'completed') {
            isVectorizing.value = false
            ElMessage.success('向量化完成')
            await fetchDocuments()
          } else if (response.status === 'failed') {
            isVectorizing.value = false
            ElMessage.error('向量化失败')
          } else {
            setTimeout(pollProgress, 1000)
          }
        } catch (error) {
          console.error('获取进度失败:', error)
        }
      }
      
      pollProgress()
    } catch (error) {
      isVectorizing.value = false
      ElMessage.error('启动向量化失败')
      console.error('向量化失败:', error)
    }
  }

  // 获取统计信息
  async function fetchStats() {
    try {
      const response = await statsAPI.getStats()
      stats.value = response.data || {}
    } catch (error) {
      console.error('获取统计信息失败:', error)
    }
  }

  // 清除上传记录
  function clearUploadingFiles() {
    uploadingFiles.value = []
  }

  return {
    documents,
    uploadingFiles,
    vectorizeProgress,
    isVectorizing,
    stats,
    fetchDocuments,
    uploadFile,
    uploadFiles,
    deleteDocument,
    startVectorize,
    fetchStats,
    clearUploadingFiles
  }
})
