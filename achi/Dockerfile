# ===== 构建阶段 =====
FROM python:3.12-slim AS builder

WORKDIR /app

# 系统依赖：Chrome（Selenium）+ 编译工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 先只复制依赖文件，利用 Docker 层缓存
COPY pyproject.toml uv.lock* ./
# 用 uv sync 安装依赖（会自动生成 lockfile 如果没有的话）
RUN uv sync --frozen 2>/dev/null || uv sync

# ===== 运行阶段 =====
FROM python:3.12-slim

WORKDIR /app

# 从 builder 复制 Chrome
COPY --from=builder /usr/bin/google-chrome-stable /usr/bin/google-chrome-stable
COPY --from=builder /opt/google /opt/google

# 从 builder 复制虚拟环境
COPY --from=builder /app/.venv /app/.venv

# 复制应用代码
COPY . .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# MCP stdio 模式（默认）
CMD ["python", "server.py"]
