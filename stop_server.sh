#!/bin/bash
# RPG Chat 停止脚本

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# 查找占用 8000 端口的进程
PID=$(lsof -ti:8000 2>/dev/null)

if [ -z "$PID" ]; then
    echo "ℹ️  服务未运行"
    exit 0
fi

echo "🛑 正在停止服务 (PID: $PID)..."
kill $PID

# 等待进程结束
sleep 1

# 检查是否还在运行
if lsof -ti:8000 >/dev/null 2>&1; then
    echo -e "${RED}⚠️  进程仍在运行，强制停止...${NC}"
    kill -9 $PID 2>/dev/null
fi

echo -e "${GREEN}✅ 服务已停止${NC}"

# 显示最后的日志
echo ""
echo "📋 最后几行日志："
tail -n 5 server.log 2>/dev/null || echo "无日志文件"
