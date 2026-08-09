FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir .

# 默认运行主进程（接收消息 + 自动回复）
CMD ["python", "-m", "pyxianyu.xianyu_live"]

# --- 构建 & 运行 ---
# docker build -t pyxianyu .
# docker run -it --env-file .env pyxianyu
