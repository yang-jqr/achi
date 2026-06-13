# ===== 构建阶段 =====
FROM python:3.12-slim AS builder

WORKDIR /app

# 系统依赖（去掉了 Chrome——Docker Desktop VM 连不上 Google 源）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 先只复制依赖文件，利用 Docker 层缓存
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen 2>/dev/null || uv sync

# ===== 运行阶段 =====
FROM python:3.12-slim

WORKDIR /app

# 从 builder 复制虚拟环境
COPY --from=builder /app/.venv /app/.venv

# 复制应用代码
COPY . .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# MCP stdio 模式（默认）
CMD ["python", "server.py"]
