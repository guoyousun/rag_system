# 项目文件结构说明

## 📁 完整目录树

```
Multi_Mode_Agent/
│
├── 📄 README.md                    # 原项目说明（Streamlit版本）
├── 📄 README_VUE.md                # Vue版本完整说明 ⭐
├── 📄 INSTALL.md                   # 详细安装指南 ⭐
├── 📄 QUICKSTART.md                # 快速开始指南 ⭐
├── 📄 PROJECT_SUMMARY.md           # 项目总结 ⭐
├── 📄 STRUCTURE.md                 # 本文件
│
├── 🔧 start.bat                    # Windows启动脚本 ⭐
├── 🔧 start.sh                     # Linux/Mac启动脚本 ⭐
├── 📋 .gitignore                   # Git忽略配置
│
├── 🐍 backend_api.py               # FastAPI后端服务 ⭐⭐⭐
├── 🐍 app.py                       # Streamlit旧版前端（保留）
├── 📋 requirements.txt             # Python依赖（已更新）
├── 📋 .env                         # 环境变量（需手动创建）
│
├── 📂 frontend/                    # Vue 3前端项目 ⭐⭐⭐
│   ├── 📋 package.json            # 前端依赖配置
│   ├── 📋 vite.config.js          # Vite构建配置
│   ├── 📄 index.html              # HTML入口
│   │
│   └── 📂 src/
│       ├── 📄 main.js             # Vue应用入口
│       ├── 📄 App.vue             # 主应用组件（含侧边栏）
│       │
│       ├── 📂 api/                # API接口层
│       │   └── 📄 index.js        # Axios封装和API定义
│       │
│       ├── 📂 router/             # 路由配置
│       │   └── 📄 index.js        # Vue Router配置
│       │
│       ├── 📂 stores/             # Pinia状态管理
│       │   ├── 📄 chat.js         # 聊天状态管理
│       │   └── 📄 knowledge.js    # 知识库状态管理
│       │
│       └── 📂 views/              # 页面组件
│           ├── 📄 Home.vue        # 智能问答页面 ⭐
│           ├── 📄 Knowledge.vue   # 知识库管理页面 ⭐
│           └── 📄 Settings.vue    # 系统设置页面
│
├── 📂 agent/                      # 智能体核心逻辑
│   ├── 📂 tools/
│   │   ├── 📄 agent_tools.py      # 工具定义（rag_summarize等）
│   │   └── 📄 middleware.py       # 中间件（日志、提示词切换）
│   └── 📄 react_agent.py          # ReAct智能体实现
│
├── 📂 rag/                        # RAG检索服务
│   ├── 📄 rag_service.py          # 检索总结服务
│   └── 📄 vector_store.py         # Chroma向量库操作
│
├── 📂 model/                      # 模型工厂
│   └── 📄 factory.py              # LLM和Embedding模型实例化
│
├── 📂 config/                     # YAML配置文件
│   ├── 📄 agent.yml               # 智能体配置
│   ├── 📄 chroma.yml              # 向量数据库配置
│   ├── 📄 prompts.yml             # 提示词路径配置
│   └── 📄 rag.yml                 # RAG检索配置
│
├── 📂 prompts/                    # 提示词模板
│   ├── 📄 main_prompt.txt         # 主系统提示词
│   ├── 📄 rag_summarize.txt       # RAG总结提示词
│   └── 📄 report_prompt.txt       # 报告生成提示词
│
├── 📂 utils/                      # 工具函数
│   ├── 📄 config_handler.py       # 配置加载器
│   ├── 📄 file_handler.py         # 文件处理器（PDF/TXT）
│   ├── 📄 logger_handler.py       # 日志管理器
│   ├── 📄 path_tool.py            # 路径工具
│   └── 📄 prompt_loader.py        # 提示词加载器
│
├── 📂 data/                       # 知识库原始数据
│   ├── 📄 众包模式.txt
│   ├── 📄 众创模式.txt
│   └── 📄 众扶模式.txt
│
├── 📂 uploads/                    # 上传文件目录（自动创建）⚠️
├── 📂 chroma_db/                  # 向量数据库（自动创建）⚠️
├── 📂 logs/                       # 日志目录（自动创建）⚠️
└── 📄 md5.text                    # 文件MD5记录（自动创建）
```

**图例：**
- ⭐ 重要文件
- ⭐⭐⭐ 核心文件
- ⚠️ 运行时自动生成

---

## 🎯 核心文件说明

### 1. 前端核心 (frontend/)

#### `src/main.js`
```javascript
// Vue应用入口
// - 注册Element Plus
// - 配置Pinia状态管理
// - 配置Vue Router
// - 注册所有图标
```

#### `src/App.vue`
```vue
<!-- 主应用布局 -->
<!-- - 左侧导航菜单（3个页面） -->
<!-- - 右侧内容区（router-view） -->
<!-- - 渐变色侧边栏 -->
```

#### `src/views/Home.vue` (智能问答页)
```vue
<!-- 核心功能 -->
- 流式对话界面
- Markdown渲染
- 快捷问题推荐
- 聊天记录管理
- 自动滚动
```

#### `src/views/Knowledge.vue` (知识库管理页)
```vue
<!-- 核心功能 -->
- 拖拽/点击上传
- 批量文件上传
- 实时进度显示
- 文档列表表格
- 搜索过滤
- 向量化进度条
- 统计卡片
```

#### `src/stores/chat.js`
```javascript
// 聊天状态管理
- messages: 消息数组
- isLoading: 加载状态
- sendMessageStream(): 流式发送
- clearMessages(): 清空
```

#### `src/stores/knowledge.js`
```javascript
// 知识库状态管理
- documents: 文档列表
- uploadingFiles: 上传队列
- vectorizeProgress: 进度
- uploadFile(): 上传
- startVectorize(): 向量化
```

#### `src/api/index.js`
```javascript
// API接口封装
- chatAPI: 聊天接口
- uploadAPI: 上传接口
- knowledgeAPI: 知识库接口
- statsAPI: 统计接口
```

---

### 2. 后端核心 (根目录)

#### `backend_api.py` (FastAPI服务)
```python
# 8个API接口
1. POST /api/chat - 智能问答（流式）
2. POST /api/upload - 单文件上传
3. POST /api/upload/batch - 批量上传
4. POST /api/vectorize - 触发向量化
5. GET /api/vectorize/progress - 获取进度
6. GET /api/documents - 文档列表
7. DELETE /api/documents/{md5} - 删除文档
8. GET /api/stats - 系统统计

# 核心功能
- CORS跨域支持
- 异步后台任务
- 文件类型验证
- MD5去重
- 进度追踪
- 错误处理
```

---

### 3. 智能体核心 (agent/)

#### `react_agent.py`
```python
# ReAct智能体
- execute_stream(): 流式执行
- execute_sync(): 同步执行
- 工具调用规划
- 中间件集成
```

#### `tools/agent_tools.py`
```python
# 5个核心工具
1. rag_summarize() - RAG检索
2. get_user_id() - 获取用户ID
3. get_current_time() - 获取时间
4. fetch_user_records() - 查询记录
5. fill_context_for_report() - 报告标记
```

#### `tools/middleware.py`
```python
# 3个中间件
1. monitor_tool - 工具调用监控
2. log_before_model - 模型调用前日志
3. report_prompt_switch - 提示词动态切换
```

---

### 4. RAG服务 (rag/)

#### `vector_store.py`
```python
# 向量库操作
- ChromaDB初始化
- 文档加载（PDF/TXT）
- 文本分片
- 向量嵌入
- MD5去重
- 检索器
```

#### `rag_service.py`
```python
# RAG总结服务
- 文档检索
- 上下文组装
- 提示词模板
- 模型调用
- 答案生成
```

---

## 🔄 数据流向

### 文件上传流程
```
用户选择文件
    ↓
前端校验（格式、大小）
    ↓
POST /api/upload
    ↓
后端保存文件到uploads/
    ↓
计算MD5
    ↓
返回成功响应
    ↓
前端刷新文档列表
```

### 向量化流程
```
用户点击"开始向量化"
    ↓
POST /api/vectorize
    ↓
后台任务启动
    ↓
扫描uploads/目录
    ↓
逐个文件处理：
  - 加载文档
  - 文本分片
  - 生成向量
  - 存入ChromaDB
    ↓
更新进度状态
    ↓
GET /api/vectorize/progress（轮询）
    ↓
前端显示进度条
    ↓
完成后刷新文档列表
```

### 智能问答流程
```
用户输入问题
    ↓
POST /api/chat
    ↓
ReAct智能体分析
    ↓
调用工具（rag_summarize等）
    ↓
RAG检索相关文档
    ↓
LLM生成回答
    ↓
流式返回前端
    ↓
Markdown渲染展示
```

---

## 📊 技术栈映射

### 前端技术栈
```
Vue 3
  ├─ Composition API
  ├─ Element Plus (UI组件)
  ├─ Pinia (状态管理)
  ├─ Vue Router (路由)
  ├─ Axios (HTTP请求)
  ├─ Marked (Markdown)
  └─ Vite (构建工具)
```

### 后端技术栈
```
FastAPI
  ├─ Uvicorn (ASGI服务器)
  ├─ LangChain (LLM框架)
  ├─ LangGraph (智能体)
  ├─ ChromaDB (向量数据库)
  ├─ PyPDF (PDF解析)
  ├─ python-docx (Word解析)
  └─ DashScope (通义千问)
```

---

## 🎨 样式文件组织

### SCSS结构
```scss
// 每个.vue文件内嵌<style scoped lang="scss">
// 使用scoped避免样式污染
// 使用变量统一管理颜色

$primary-color: #409EFF;
$success-color: #67C23A;
$warning-color: #E6A23C;
$danger-color: #F56C6C;
$info-color: #909399;
```

---

## 🔐 安全考虑

### 前端安全
- CORS配置
- XSS防护（Markdown渲染时）
- 文件大小限制
- 文件类型白名单

### 后端安全
- 文件扩展名验证
- MD5防重复
- 异常捕获
- 日志记录
- API限流（待实现）

---

## 🚀 性能优化点

### 前端优化
1. **路由懒加载**
   ```javascript
   component: () => import('@/views/Home.vue')
   ```

2. **组件按需导入**
   ```javascript
   // Element Plus按需引入（可配置）
   ```

3. **防抖节流**
   - 搜索框输入防抖
   - 滚动事件节流

4. **虚拟滚动**
   - 大数据量表格（待实现）

### 后端优化
1. **异步处理**
   ```python
   background_tasks.add_task(process_vectorization)
   ```

2. **流式响应**
   ```python
   StreamingResponse(generate_response())
   ```

3. **连接池**
   - ChromaDB持久化连接

4. **缓存机制**
   - 检索结果缓存（待实现）

---

## 📝 配置优先级

### 环境变量 (.env)
```bash
DASHSCOPE_API_KEY=sk-xxx  # 最高优先级
```

### YAML配置 (config/*.yml)
```yaml
# 中等优先级，可覆盖默认值
chroma.yml:
  chunk_size: 200
  k: 3
```

### 代码默认值
```python
# 最低优先级
chunk_size = 200  # 如果YAML未配置
```

---

## 🧪 测试建议

### 前端测试
```bash
# 单元测试（待添加）
npm run test:unit

# E2E测试（待添加）
npm run test:e2e
```

### 后端测试
```bash
# pytest（待添加）
pytest tests/
```

### 手动测试清单
- [ ] 文件上传（各种格式）
- [ ] 批量上传
- [ ] 向量化进度
- [ ] 智能问答
- [ ] 文档删除
- [ ] 搜索过滤
- [ ] 清空聊天

---

## 📦 部署架构

### 开发环境
```
前端: localhost:3000 (Vite Dev Server)
后端: localhost:8000 (Uvicorn)
```

### 生产环境（建议）
```
Nginx (反向代理)
  ├─ 前端静态文件 (dist/)
  └─ 后端API代理 → Gunicorn + Uvicorn Workers
       └─ FastAPI应用
            └─ ChromaDB (持久化)
```

---

## 🔍 调试技巧

### 前端调试
```javascript
// 浏览器控制台
console.log('State:', chatStore.messages)

// Vue DevTools
// 查看组件树、状态、事件
```

### 后端调试
```python
# 日志查看
tail -f logs/*.log

# API测试
curl http://localhost:8000/docs
```

---

**这就是完整的项目结构说明！** 📚
