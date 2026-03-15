#!/bin/bash
# RPG Chat 后台启动脚本

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在项目根目录
if [ ! -f "api_server.py" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

echo -e "${GREEN}🚀 启动 RPG Chat 服务...${NC}"

# 检查是否已在运行
PID=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$PID" ]; then
    echo -e "${YELLOW}⚠️  服务已在运行 (PID: $PID)${NC}"
    echo "   访问: http://localhost:8000"
    echo "   停止: kill $PID"
    exit 0
fi

# 后台启动
nohup python api_server.py > server.log 2>&1 &

# 等待服务启动
sleep 2

# 检查是否启动成功
NEW_PID=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$NEW_PID" ]; then
    echo -e "${GREEN}✅ 服务已启动！${NC}"
    echo "   PID: $NEW_PID"
    echo "   访问: http://localhost:8000"
    echo ""
    echo "📋 常用命令："
    echo "   查看日志: tail -f server.log"
    echo "   停止服务: kill $NEW_PID"
    echo "   查看状态: ps aux | grep api_server"
else
    echo "❌ 启动失败，查看日志: cat server.log"
    exit 1
fi
