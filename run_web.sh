#!/bin/bash
# Streamlit 启动脚本

cd "$(dirname "$0")"

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# 确保目录存在
mkdir -p ./data/uploaded

# 启动 Streamlit
echo "🚀 启动 RAG Web 界面..."
echo "📍 访问地址: http://localhost:8501"
echo ""

streamlit run app.py --server.port=8501 --server.address=localhost
