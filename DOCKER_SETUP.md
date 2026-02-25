# Docker 开发环境配置指南

## 快速开始

### 1. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，选择模型配置方案
# 方案 1: 本地 Ollama 模型（推荐，无需联网）
USE_OLLAMA=true
OLLAMA_HOST=http://localhost:11434
OLLAMA_LLM_MODEL=qwen3:4b
OLLAMA_EMBEDDING_MODEL=qwen3-embedding:4b

# 方案 2: 在线 DashScope 模型（需要阿里云 API Key）
# USE_OLLAMA=false
# DASHSCOPE_API_KEY=your_dashscope_api_key_here
```

### 2. 启动服务

**使用本地 Ollama 模型（推荐）：**

```bash
# 启动 Ollama 和 Qdrant
docker-compose up -d ollama qdrant

# 下载所需模型（首次使用需要）
docker exec -it rag_ollama ollama pull qwen3:4b
docker exec -it rag_ollama ollama pull qwen3-embedding:4b

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

**使用在线 DashScope 模型：**

```bash
# 仅启动 Qdrant（仅向量数据库）
docker-compose up -d qdrant

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f qdrant
```

### 2. 修改代码连接 Qdrant 服务器

修改 `rag_knowledge_base/rag_knowledge.py` 中的初始化部分：

```python
# 方式一：从环境变量读取 Qdrant URL（推荐）
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")

self.vector_store = QdrantStore(
    url=qdrant_url,  # 连接到 Docker 中的 Qdrant
    collection_name=collection_name,
    dimensions=self.dimensions
)

# 方式二：本地文件模式（无需 Docker）
# location="./persist_data/vector_store"
```

### 3. 在宿主机运行应用（开发推荐）

```bash
# 加载环境变量
export $(cat .env | xargs)

# 运行应用
python rag_knowledge_base/main.py
```

## 目录访问说明

### Volume 挂载映射

| 宿主机路径 | 容器内路径 | 用途 |
|-----------|-----------|------|
| `./qdrant_storage` | `/qdrant/storage` | Qdrant 向量数据持久化 |
| `./ollama_models` | `/root/.ollama` | Ollama 模型文件持久化 |
| `./data` | `/app/data` | 应用数据文件 |
| `./persist_data` | `/app/persist_data` | 应用持久化数据 |
| `./rag_knowledge_base` | `/app/rag_knowledge_base` | 代码（开发时挂载） |

### 访问容器内的文件

```bash
# 进入正在运行的容器
docker exec -it rag_qdrant /bin/sh

# 在容器内查看文件
ls -la /qdrant/storage

# 退出容器
exit

# 直接在宿主机查看（通过 Volume 挂载）
ls -la ./qdrant_storage
```

### 备份数据

```bash
# 方法1：直接复制宿主机挂载的目录
cp -r qdrant_storage qdrant_storage_backup_$(date +%Y%m%d)

# 方法2：使用 docker cp 从容器复制
docker cp rag_qdrant:/qdrant/storage ./qdrant_backup

# 方法3：导出为 tar 包
docker run --rm \
  --volumes-from rag_qdrant \
  -v $(pwd):/backup \
  busybox \
  tar czf /backup/qdrant_backup.tar.gz /qdrant/storage
```

## 常用命令

### 容器管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 停止并删除数据卷（清空数据）
docker-compose down -v

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f qdrant
```

### 进入容器调试

```bash
# 进入 Qdrant 容器
docker exec -it rag_qdrant /bin/sh

# 查看 Qdrant 配置
cat /qdrant/config/config.yaml

# 测试 API
curl http://localhost:6333/collections

# 查看集合详情
curl http://localhost:6333/collections/rag_knowledge_base
```

### Ollama 管理

```bash
# 进入 Ollama 容器
docker exec -it rag_ollama /bin/sh

# 列出已下载的模型
ollama list

# 下载新模型
ollama pull qwen3:4b
ollama pull qwen3-embedding:4b

# 删除模型
ollama rm qwen3:4b

# 查看模型信息
ollama show qwen3:4b
```

### 数据管理

```bash
# 查看宿主机上的数据大小
du -sh qdrant_storage

# 清理 Qdrant 日志（如果占用空间过大）
docker exec rag_qdrant rm -rf /qdrant/storage/logs/*.log

# 重置所有数据（谨慎操作）
rm -rf qdrant_storage/*
docker-compose restart qdrant
```

## 两种开发模式对比

### 模式一：宿主机运行 + Docker Qdrant（推荐开发使用）

优点：
- 代码修改立即生效，无需重新构建镜像
- 调试方便，可直接使用 IDE
- Python 环境由宿主机管理

缺点：
- 需要本地安装 Python 依赖
- 团队环境一致性稍差

```bash
# 仅启动 Qdrant
docker-compose up -d qdrant

# 在宿主机运行应用
python rag_knowledge_base/main.py
```

### 模式二：全 Docker 运行（推荐生产使用）

优点：
- 环境完全一致
- 易于部署和扩展
- 不依赖宿主机 Python 环境

缺点：
- 代码修改需要重启容器
- 调试相对复杂

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看应用日志
docker-compose logs -f rag_app

# 进入应用容器调试
docker exec -it rag_app /bin/bash
```

## 跨平台注意事项

### macOS
- Docker Desktop 会自动处理文件挂载权限
- 性能较好，可直接使用

### Linux
- 可能需要处理文件权限问题
- 如果需要非 root 用户运行：

```yaml
# docker-compose.yml 中添加
services:
  qdrant:
    user: "${UID}:${GID}"
```

### Windows (WSL2)
- 确保项目放在 WSL2 文件系统中（`/home/username/...`）
- 不要放在 `/mnt/c/`（性能差）

## 故障排查

### Qdrant 启动失败

```bash
# 检查端口占用
lsof -i :6333

# 查看错误日志
docker-compose logs qdrant
```

### 应用无法连接 Qdrant

```bash
# 测试连接
curl http://localhost:6333/healthz

# 检查防火墙
sudo lsof -i :6333
```

### Ollama 连接问题

```bash
# 测试 Ollama API
curl http://localhost:11434/api/tags

# 检查 Ollama 日志
docker-compose logs -f ollama

# 重启 Ollama 服务
docker-compose restart ollama

# 确认模型已下载
docker exec rag_ollama ollama list
```

### Ollama 模型下载慢

```bash
# 配置镜像加速（在宿主机执行）
export OLLAMA_HOST=http://localhost:11434

# 或者修改 docker-compose.yml 添加环境变量
environment:
  - OLLAMA_ORIGINS=*
  - OLLAMA_HOST=0.0.0.0
```

### 数据丢失

- 确保使用了 `volumes` 挂载
- 检查宿主机目录权限
- 不要删除 `qdrant_storage` 目录

## 生产部署建议

1. **使用 Docker Swarm 或 Kubernetes** 管理多节点
2. **配置 Qdrant 集群模式** 提高可用性
3. **定期备份** `qdrant_storage` 目录
4. **使用外部存储**（如 NFS、云存储）存放数据
5. **配置监控和告警**
