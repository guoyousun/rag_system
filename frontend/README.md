# 前端项目 - Vue 3 + Element Plus

## 🚀 快速启动

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build

# 预览构建结果
npm run preview
```

## 📦 技术栈

- **框架**: Vue 3.4+
- **构建工具**: Vite 5
- **UI库**: Element Plus 2.5+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.2+
- **HTTP客户端**: Axios 1.6+
- **样式预处理器**: SCSS/Sass

## ⚠️ 常见问题

### SCSS 错误
如果遇到 `sass-embedded not found` 错误：
```bash
npm install -D sass
```

### 端口被占用
修改 `vite.config.js` 中的 `server.port`

### API 连接失败
确保后端服务运行在 `http://localhost:8000`

## 🔧 配置

- **开发服务器**: http://localhost:3000
- **API代理**: /api → http://localhost:8000
- **别名**: @ → src目录

##  项目结构

```
src/
├── api/           # API接口
├── router/        # 路由配置
├── stores/        # Pinia状态管理
├── views/         # 页面组件
│   ├── Home.vue   # 智能问答
│   ├── Knowledge.vue # 知识库管理
│   ── Settings.vue  # 系统设置
├── App.vue        # 主应用
└── main.js        # 入口文件
```

## 📖 更多文档

查看项目根目录的文档：
- [README_VUE.md](../README_VUE.md)
- [INSTALL.md](../INSTALL.md)
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
