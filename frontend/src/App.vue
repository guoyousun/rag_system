<template>
  <el-container class="app-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <h2>🏭 工业软件平台</h2>
        <p class="subtitle">多模式协同智能问答</p>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        router
        class="menu"
      >
        <el-menu-item index="/">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能问答</span>
        </el-menu-item>
        
        <el-menu-item index="/knowledge">
          <el-icon><FolderOpened /></el-icon>
          <span>知识库管理</span>
        </el-menu-item>
        
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
      
      <div class="sidebar-footer">
        <p>版本 v1.0.0</p>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped lang="scss">
.app-container {
  height: 100vh;
}

.sidebar {
  background: linear-gradient(180deg, #1e3a5f 0%, #2c5282 100%);
  color: white;
  display: flex;
  flex-direction: column;
  
  .logo {
    padding: 30px 20px;
    text-align: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    h2 {
      margin: 0 0 8px 0;
      font-size: 20px;
      font-weight: 600;
    }
    
    .subtitle {
      margin: 0;
      font-size: 12px;
      opacity: 0.8;
    }
  }
  
  .menu {
    flex: 1;
    background: transparent;
    border-right: none;
    padding: 20px 0;
    
    :deep(.el-menu-item) {
      color: rgba(255, 255, 255, 0.8);
      
      &:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white;
      }
      
      &.is-active {
        background: rgba(255, 255, 255, 0.15) !important;
        color: white;
      }
      
      .el-icon {
        margin-right: 10px;
      }
    }
  }
  
  .sidebar-footer {
    padding: 20px;
    text-align: center;
    font-size: 12px;
    opacity: 0.6;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
}

.main-content {
  padding: 0;
  background: #f5f7fa;
}
</style>
