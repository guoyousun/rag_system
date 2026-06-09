# 安装指南 - Vue前端版本

## 📋 目录

1. [环境准备](#环境准备)
2. [后端安装](#后端安装)
3. [前端安装](#前端安装)
4. [配置说明](#配置说明)
5. [启动系统](#启动系统)
6. [验证安装](#验证安装)
7. [常见问题](#常见问题)

---

## 环境准备

### 必需软件

#### 1. Python 3.10+

**Windows:**
```bash
# 下载并安装Python
# 访问 https://www.python.org/downloads/
# 安装时勾选 "Add Python to PATH"

# 验证安装
python --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version
```

**Mac:**
```bash
# 使用Homebrew
brew install python3
python3 --version
```

#### 2. Node.js 16+

**Windows/Mac/Linux:**
```bash
# 下载并安装Node.js
# 访问 https://nodejs.org/
# 推荐LTS版本

# 验证安装
node --version
npm --version
```

---

## 后端安装

### 步骤1: 克隆项目

```bash
git clone <repository-url>
cd Multi_Mode_Agent
```

### 步骤2: 创建虚拟环境

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 步骤3: 安装Python依赖

```bash
pip install -r requirements.txt
```

如果遇到网络问题，可以使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 步骤4: 配置API密钥

在项目根目录创建 `.env` 文件：

```bash
# Windows
notepad .env

# Linux/Mac
nano .env
```

添加以下内容（替换为你的API Key）：

```env
DASHSCOPE_API_KEY=sk-your-api-key-here
```

**获取API Key:**
1. 访问 [阿里云DashScope控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录账号
3. 进入"API密钥管理"
4. 创建新的API Key
5. 复制Key到 `.env` 文件

---

## 前端安装

### 步骤1: 进入前端目录

```bash
cd frontend
```

### 步骤2: 安装依赖

```bash
npm install
```

如果速度较慢，可以使用淘宝镜像：

```bash
npm config set registry https://registry.npmmirror.com
npm install
```

或使用yarn：

```bash
npm install -g yarn
yarn install
```

---

## 配置说明

### 后端配置

#### 1. Chroma向量数据库配置

编辑 `config/chroma.yml`:

```yaml
collection_name: agent              # 集合名称
persist_directory: ./chroma_db      # 持久化目录
k: 3                                # 检索返回数量
data_path: data                     # 知识库数据路径
md5_hex_store: md5.text             # MD5存储文件
allow_knowledge_file_type:          # 允许的文件类型
  - txt
  - pdf
  - docx
  - xlsx

chunk_size: 200                     # 文本分片大小
chunk_overlap: 20                   # 分片重叠
separators:                         # 分隔符
  - "\n\n"
  - "\n"
  - "."
  - "。"
  - " "
```

#### 2. 提示词配置

编辑 `config/prompts.yml`:

```yaml
main_prompt_path: prompts/main_prompt.txt
rag_summarize_prompt_path: prompts/rag_summarize.txt
report_prompt_path: prompts/report_prompt.txt
```

### 前端配置

#### Vite代理配置

编辑 `frontend/vite.config.js`:

```javascript
server: {
  port: 3000,  // 前端端口
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // 后端地址
      changeOrigin: true
    }
  }
}
```

如需修改端口，编辑此文件后重启开发服务器。

---

## 启动系统

### 方式一：使用启动脚本（推荐）

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### 方式二：手动启动

#### 终端1 - 启动后端

```bash
# 激活虚拟环境
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

python backend_api.py
```

#### 终端2 - 启动前端

```bash
cd frontend
npm run dev
```

### 访问系统

打开浏览器访问：
- 前端界面：http://localhost:3000
- API文档：http://localhost:8000/docs

---

## 验证安装

### 1. 检查后端服务

访问 http://localhost:8000，应该看到：

```json
{
  "message": "工业软件平台智能问答系统API",
  "version": "1.0.0",
  "status": "running"
}
```

### 2. 检查API文档

访问 http://localhost:8000/docs，应该看到Swagger UI界面。

### 3. 检查前端界面

访问 http://localhost:3000，应该看到智能问答界面。

### 4. 测试文件上传

1. 进入"知识库管理"页面
2. 点击"上传文件"按钮
3. 选择一个PDF或TXT文件
4. 确认上传成功

### 5. 测试向量化

1. 上传文件后
2. 点击"开始向量化"按钮
3. 观察进度条是否正常显示

### 6. 测试智能问答

1. 进入"智能问答"页面
2. 输入问题："众包的流程是什么？"
3. 确认收到流式响应

---

## 常见问题

### Q1: pip install 失败

**错误信息：**
```
Could not find a version that satisfies the requirement
```

**解决方案：**
```bash
# 升级pip
python -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: npm install 失败

**错误信息：**
```
npm ERR! code ERESOLVE
```

**解决方案：**
```bash
# 清除缓存
npm cache clean --force

# 删除node_modules重新安装
rm -rf node_modules package-lock.json
npm install

# 或使用legacy-peer-deps
npm install --legacy-peer-deps
```

### Q3: 端口被占用

**错误信息：**
```
Address already in use
```

**解决方案：**

修改端口配置：

**后端** (`backend_api.py`):
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # 改为8001
```

**前端** (`frontend/vite.config.js`):
```javascript
server: {
  port: 3001,  // 改为3001
  ...
}
```

### Q4: API Key无效

**错误信息：**
```
AuthenticationError: Invalid API key
```

**解决方案：**
1. 检查 `.env` 文件是否存在
2. 确认API Key格式正确（以 `sk-` 开头）
3. 确认API Key未过期
4. 重启后端服务

### Q5: 向量数据库初始化失败

**错误信息：**
```
ChromaDB initialization failed
```

**解决方案：**
```bash
# 删除旧的向量数据库
rm -rf chroma_db

# 重新初始化
python rag/vector_store.py
```

### Q6: 文件上传失败

**可能原因：**
1. 文件格式不支持
2. 文件过大（超过50MB）
3. uploads目录权限不足

**解决方案：**
```bash
# 创建uploads目录
mkdir uploads

# 设置权限（Linux/Mac）
chmod 755 uploads
```

### Q7: 中文乱码

**解决方案：**

确保所有文本文件使用UTF-8编码：

1. 检查 `.env` 文件编码
2. 检查提示词文件编码
3. 在代码中明确指定编码：
```python
open(file, 'r', encoding='utf-8')
```

### Q8: 内存不足

**症状：**
- 程序崩溃
- 响应缓慢

**解决方案：**

1. 减小 `chunk_size`（在 `config/chroma.yml`）
2. 减少检索数量 `k`
3. 增加系统内存
4. 关闭其他占用内存的程序

---

## 性能优化建议

### 1. 使用GPU加速（可选）

如果有NVIDIA GPU，可以安装CUDA版本的依赖：

```bash
pip uninstall faiss-cpu
pip install faiss-gpu
```

### 2. 启用缓存

安装Redis（可选）：

```bash
# Ubuntu
sudo apt install redis-server

# Mac
brew install redis
```

### 3. 生产部署

**后端：**
```bash
# 使用Gunicorn
pip install gunicorn
gunicorn backend_api:app -w 4 -k uvicorn.workers.UvicornWorker
```

**前端：**
```bash
cd frontend
npm run build

# 使用Nginx托管dist目录
```

---

## 下一步

安装完成后，请阅读：

1. [README_VUE.md](README_VUE.md) - 完整功能说明
2. [API文档](http://localhost:8000/docs) - 接口详细说明
3. 使用系统，体验智能问答功能

---

**祝您安装顺利！** 🎉

如有问题，请提交Issue或查看日志文件 `logs/`。
