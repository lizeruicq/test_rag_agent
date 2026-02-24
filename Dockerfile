FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY rag_knowledge_base/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY rag_knowledge_base/ ./rag_knowledge_base/

# 创建数据目录
RUN mkdir -p /app/data /app/persist_data

# 默认命令
CMD ["python", "rag_knowledge_base/main.py"]
