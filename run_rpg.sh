#!/bin/bash
# RPG Chat 启动脚本

echo "🎮 启动 RPG Chat 系统..."
echo ""

# 检查虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 创建必要的目录
mkdir -p data/uploaded
mkdir -p persist_data

# 安装前端依赖
echo "📦 安装前端依赖..."
cd rpg-frontend
npm install

echo ""
echo "✅ 安装完成！"
echo ""
echo "启动方式："
echo ""
echo "1️⃣  启动后端（终端1）："
echo "   cd $(dirname $0)"
echo "   python api_server.py"
echo ""
echo "2️⃣  启动前端（终端2）："
echo "   cd $(dirname $0)/rpg-frontend"
echo "   npm run dev"
echo ""
echo "然后访问：http://localhost:5173"
echo ""
