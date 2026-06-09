# 快速开始 - 5分钟上手Vue前端版本

## 🚀 超快速启动（3步）

### 第1步：安装依赖

```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install && cd ..
```

### 第2步：配置API Key

创建 `.env` 文件：
```env
DASHSCOPE_API_KEY=sk-your-api-key-here
```

[获取API Key](https://dashscope.console.aliyun.com/)

### 第3步：启动系统

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh && ./start.sh
```

访问 http://localhost:3000 开始使用！

---

## 📖 主要功能

### 1️⃣ 智能问答
- 点击"智能问答"菜单
- 输入问题或点击快捷问题
- 实时流式响应

### 2️⃣ 文件上传
- 点击"知识库管理"菜单
- 点击"上传文件"按钮
- 拖拽或选择文件（支持PDF/Word/Excel/TXT/图片）
- 点击"开始上传"

### 3️⃣ 向量化处理
- 上传文件后
- 点击"开始向量化"按钮
- 观察进度条等待完成

### 4️⃣ 查看文档
- 在知识库管理页面
- 查看所有已上传的文档
- 支持搜索和删除

---

## 💡 使用示例

### 示例1：技术咨询
```
问：智能制造中的数字孪生技术如何应用？
答：[AI助手基于知识库生成专业回答]
```

### 示例2：政策解读
```
问：政府扶持政策有哪些？如何申请？
答：[AI助手检索相关政策并总结]
```

### 示例3：报告生成
```
问：给我生成我的使用报告
答：[AI助手自动生成结构化报告]
```

---

## 🔧 常用操作

### 清空聊天记录
智能问答页面 → 右上角"清空对话"按钮

### 删除文档
知识库管理 → 找到文档 → 点击"删除"按钮

### 刷新文档列表
知识库管理 → 点击"刷新"按钮

### 查看API文档
浏览器访问：http://localhost:8000/docs

---

## ⚠️ 注意事项

1. **首次使用需要初始化向量数据库**
   ```bash
   python rag/vector_store.py
   ```

2. **文件格式限制**
   - 支持：PDF, DOCX, TXT, XLSX, CSV, JPG, PNG
   - 单个文件最大50MB

3. **向量化时间**
   - 小文件（<1MB）：几秒
   - 中等文件（1-10MB）：几十秒
   - 大文件（>10MB）：几分钟

4. **网络要求**
   - 需要访问通义千问API
   - 确保网络连接正常

---

## 🆘 遇到问题？

### 检查清单

- [ ] Python 3.10+ 已安装
- [ ] Node.js 16+ 已安装
- [ ] API Key 已配置
- [ ] 依赖已全部安装
- [ ] 端口8000和3000未被占用

### 查看日志

```bash
# 后端日志
cat logs/*.log

# 前端控制台
浏览器 F12 → Console
```

### 重启服务

```bash
# 停止所有服务（Ctrl+C）

# 重新启动
start.bat  # Windows
./start.sh # Linux/Mac
```

---

## 📚 更多资源

- [完整文档](README_VUE.md)
- [安装指南](INSTALL.md)
- [API文档](http://localhost:8000/docs)

---

**开始探索吧！** 🎉
