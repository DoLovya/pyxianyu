# ---- 构建阶段：安装 Node.js ----
FROM python:3.12-slim

# 安装 Node.js 18.x
RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制依赖文件，利用 Docker 层缓存
COPY requirements.txt package*.json* ./

RUN pip install --no-cache-dir -r requirements.txt
RUN npm install 2>/dev/null || true

# 复制项目文件
COPY . .

# 默认运行主进程（接收消息 + 自动回复）
CMD ["python", "goofish_live.py"]

# --- 构建 & 运行 ---
# docker build -t xianyuapis .
# docker run -it --env-file .env xianyuapis
