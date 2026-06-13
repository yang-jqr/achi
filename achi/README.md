# achi — AI 求职助手

> 基于 MCP + RAG 的智能简历优化系统，Docker 容器化部署。

## 技术栈

| 层级 | 技术 |
|------|------|
| 大模型 | DeepSeek API（Function Calling） |
| RAG 管道 | LangChain + Qdrant 向量数据库 + BGE 中文向量模型 |
| Agent 协议 | MCP（Server/Client，支持 stdio / HTTP+SSE / Streamable HTTP） |
| 数据抓取 | Selenium / Playwright（51job、BOSS直聘） |
| 容器化 | Docker 多阶段构建 + Docker Compose 编排 |
| 语言 | Python 3.12 |

## 架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  MCP Client  │────▶│  MCP Server  │────▶│  DeepSeek API │
│  (Claude等)  │     │  (FastMCP)   │     │              │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐
                    │    Qdrant    │
                    │  向量数据库   │
                    └──────────────┘
```

## 快速启动

```bash
# 1. 创建 .env 文件
echo "deepseek=你的API_KEY" > .env

# 2. 一键启动（Qdrant + MCP Server）
docker compose up -d

# 3. 验证
curl http://localhost:8000/
```

服务运行在 `http://localhost:8000`。

## 项目结构

```
achi/
├── server.py              # MCP Server 入口
├── tools/                 # MCP 工具（岗位搜索、简历优化）
├── llm/                   # LLM 客户端（DeepSeek）
├── prompt/                # 提示词模板
├── qdrant/                # 向量数据库操作
├── src/                   # 爬虫 + 简历工具
├── Dockerfile             # 多阶段构建
├── docker-compose.yml     # 编排 Qdrant + MCP Server
└── .dockerignore          # 密钥不入镜像
```

## 技能展示

- **RAG 应用开发**：LangChain + Qdrant 语义检索管道
- **Agent 开发**：MCP 协议 Server/Client 实现
- **容器化部署**：多阶段 Docker 构建 + Compose 多服务编排
- **数据工程**：Selenium 反爬对抗 + 结构化提取
