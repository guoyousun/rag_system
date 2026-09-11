# 工业软件平台多模式协同智能问答系统

基于 **BM25 关键词检索 + 向量检索 + 知识图谱检索** 三种检索模式协同融合的工业垂直领域智能问答系统。

## 技术架构

| 层 | 技术选型 |
|---|---|
| 前端 | Vue3 + Vite + Element Plus + Pinia + ECharts |
| 后端 | FastAPI + SQLAlchemy 2.0 + Pydantic v2 |
| 大模型 | 千问（Qwen，OpenAI SDK 兼容端点） |
| 嵌入模型 | 千问 text-embedding-v3 |
| 关键词检索 | jieba 分词 + rank_bm25（BM25Okapi） |
| 向量检索 | Chroma（余弦相似度） |
| 知识图谱 | Neo4j（实体-关系-证据分块） |
| 缓存 | Redis（热点问答缓存 + JWT 黑名单） |
| 持久化 | MySQL 8.0（用户/文档/分块/会话） |
| 认证 | JWT（PyJWT + bcrypt） |

## 目录结构

```
Multi_Mode_Agent/
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── core/                # 配置(config) / 安全(security) / 依赖注入(deps)
│   │   ├── database/            # MySQL / Redis / Neo4j / Chroma 四类存储连接
│   │   ├── models/              # SQLAlchemy ORM（user/document/chat）
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── services/            # 业务服务层
│   │   │   ├── llm_service.py         # 千问 LLM（OpenAI 库）
│   │   │   ├── embedding_service.py   # 千问 Embedding
│   │   │   ├── document_parser.py     # 文档解析（txt/md/pdf/docx）
│   │   │   ├── text_splitter.py       # 递归分块
│   │   │   ├── document_pipeline.py   # 文档处理流水线（状态机）
│   │   │   ├── bm25_service.py        # 检索方式① BM25
│   │   │   ├── vector_service.py      # 检索方式② 向量
│   │   │   ├── kg_service.py          # 检索方式③ 知识图谱
│   │   │   ├── fusion_service.py      # RRF 加权融合
│   │   │   └── rag_service.py         # RAG 问答编排
│   │   └── api/v1/              # 路由（auth/documents/chats/search）
│   ├── scripts/                 # init_db / init_kg / seed_demo
│   ├── uploads/                 # 上传文档存储（运行期生成）
│   ├── data/chroma/             # Chroma 持久化（运行期生成）
│   ├── .env                     # 环境配置（需填写千问 Key）
│   └── requirements.txt
├── frontend/                    # Vue3 前端
│   └── src/
│       ├── api/                 # axios 封装与接口
│       ├── store/               # Pinia（用户状态）
│       ├── router/              # 路由与守卫
│       └── views/               # 登录/注册/对话/文档/图谱/个人中心
├── docker-compose.yml           # MySQL + Redis + Neo4j 一键启动
└── README.md
```

## 快速开始

### 1. 启动基础设施（MySQL / Redis / Neo4j）

```bash
docker compose up -d
```

> 如本机已安装对应服务可跳过；确保与 `backend/.env` 中密码一致。

### 2. 配置后端环境

```bash
cd backend
cp .env.example .env
# 编辑 .env，填写:
#   - QWEN_API_KEY（阿里云百炼: https://bailian.console.aliyun.com/）
#   - MySQL / Neo4j 密码（与 docker compose 一致）
```

### 3. 安装依赖并初始化

```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt

python scripts/init_db.py        # 建 MySQL 表
python scripts/init_kg.py        # 建 Neo4j 约束
python scripts/seed_demo.py      # (可选) 生成示例用户 admin/admin123 + 示例文档
```

### 4. 启动后端

```bash
uvicorn app.main:app --reload --port 8000
# API 文档: http://127.0.0.1:8000/docs
# 健康检查: http://127.0.0.1:8000/api/v1/health
```

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
# 打开 http://localhost:5173 ，使用 admin / admin123 登录
```

## 核心流程

### 文档处理流水线

```
上传 → 解析(txt/md/pdf/docx) → 清洗 → 递归分块(500字/重叠50)
     → 分块落 MySQL → 千问Embedding入Chroma → LLM实体抽取 → Neo4j图谱
     → 状态机: uploaded→parsing→vectorizing→kg_building→ready / failed
```

### 三路协同检索 + RRF 融合

```
用户问题
  ├─ BM25检索    jieba分词 → BM25Okapi → 候选分块(top10)
  ├─ 向量检索    千问Embedding → Chroma 余弦相似度 → 候选分块(top10)
  └─ 图谱检索    实体链接(jieba+实体名匹配) → 一跳邻居扩展 → 证据分块(top10)
       ↓
  RRF融合: score = Σ wᵢ/(k+rankᵢ)  → 取 top6 分块
       ↓
  千问生成（带参考资料与历史上下文）→ 答案 + 引用来源 + 各检索路命中统计
```

### 认证与安全

- 注册 → 登录（JWT）→ 退出（jti 黑名单入 Redis）→ 修改密码（token_version 自增，旧 token 全部失效）
- 密码 bcrypt 加盐哈希；所有业务接口需 Bearer Token

## API 一览（前缀 /api/v1）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /auth/register | 注册 |
| POST | /auth/login | 登录 |
| POST | /auth/logout | 退出（黑名单） |
| POST | /auth/change-password | 修改密码 |
| GET | /auth/me | 当前用户 |
| POST | /documents/upload | 上传文档（异步处理） |
| GET | /documents | 文档列表 |
| GET | /documents/{id} | 文档详情（含分块） |
| DELETE | /documents/{id} | 删除文档（级联清理） |
| POST | /documents/{id}/reprocess | 重新处理 |
| POST | /chats | 创建会话 |
| GET | /chats | 会话列表 |
| POST | /chats/{id}/messages | 发送问题（多模式检索+生成） |
| POST | /chats/{id}/messages/stream | SSE 流式问答 |
| POST | /search | 三路检索对比调试 |
| GET | /graph | 知识图谱概览（前端可视化） |

## 常见问题

- **文档处理失败**：在「文档管理」点击重试；或查看 `error_msg` 字段定位原因（常见：LLM Key 未配置、Neo4j 未启动、PDF 为扫描件）。
- **三路检索某一路报错**：系统自动降级，其余路正常参与融合；可用 `POST /search` 分别验证各路。
- **修改 .env 后需重启后端**（config 使用 lru_cache）。
