# RPG Chat - 2D 像素风聊天界面

基于 React + Phaser 的 RPG 风格 RAG 知识库聊天系统。

![RPG Chat Preview](./docs/rpg-preview.png)

## ✨ 特性

- 🎮 **2D RPG 像素风格** - 玩家角色与 AI 机器人在游戏场景中对话
- 🤖 **机器人动画状态** - 待机(idle) / 思考(thinking) / 说话(speaking) 三种状态
- 💬 **对话气泡系统** - 带打字机效果的弹出式对话
- ✨ **粒子特效** - 发送消息时的视觉反馈
- 📁 **文档管理面板** - 上传/删除/查看知识库文档
- ⚡ **实时状态同步** - React UI 与 Phaser 场景双向通信

## 🏗️ 架构

```
┌─────────────────────────────────────────────┐
│  前端 (React + Phaser)                       │
│  ┌───────────────────────────────────────┐  │
│  │  Phaser Canvas                        │  │
│  │  - ChatScene.ts (游戏场景)             │  │
│  │  - 玩家角色 (蓝色冒险者)                │  │
│  │  - NPC机器人 (紫色AI助手)              │  │
│  │  - 对话气泡 + 粒子特效                  │  │
│  └───────────────────────────────────────┘  │
│                ↑                            │
│  ┌─────────────┴───────────────────────┐    │
│  │  React UI Overlay                   │    │
│  │  - StatusBar (状态栏)               │    │
│  │  - ChatInput (输入框)               │    │
│  │  - DocPanel (文档管理)              │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
                     ↑↓ HTTP/WebSocket
┌─────────────────────────────────────────────┐
│  后端 (FastAPI)                              │
│  - /api/chat      - 对话接口                 │
│  - /api/upload    - 文档上传                 │
│  - /api/docs      - 文档列表                 │
│  - /api/delete    - 删除文档                 │
│  - /api/stats     - 统计信息                 │
└─────────────────────────────────────────────┘
```

## 🚀 快速开始

### 方式一：单命令启动（推荐，像 Copaw 一样）

```bash
# 1. 确保虚拟环境已激活
source .venv/bin/activate

# 2. 安装前端依赖（首次运行）
cd rpg-frontend && npm install

# 3. 回到根目录，启动服务
cd ..
python api_server.py
```

第一次启动会自动构建前端，之后访问：
**http://localhost:8000**

### 方式二：开发模式（热更新）

适合开发调试，前后端分开启动：

```bash
# 终端 1：启动后端（仅 API，不构建前端）
python api_server.py --dev

# 终端 2：启动前端（热更新）
cd rpg-frontend
npm run dev
```

访问 http://localhost:5173

**区别说明：**

| 模式 | 后端角色 | 前端来源 | 访问地址 |
|------|---------|---------|----------|
| 生产模式 | API + 前端静态文件 | `rpg-frontend/dist` | `localhost:8000` |
| 开发模式 | 仅 API | Vite 开发服务器 | `localhost:5173` |

## 📁 项目结构

```
rpg-frontend/
├── src/
│   ├── game/
│   │   └── ChatScene.ts      # Phaser 游戏场景
│   ├── components/
│   │   ├── ChatInput.tsx     # 聊天输入框
│   │   ├── DocPanel.tsx      # 文档管理面板
│   │   └── StatusBar.tsx     # 状态栏
│   ├── api/
│   │   └── index.ts          # API 客户端
│   ├── types/
│   │   └── index.ts          # TypeScript 类型
│   ├── App.tsx               # 主应用组件
│   └── index.css             # 全局样式
├── package.json
├── vite.config.ts
└── index.html

api_server.py                 # FastAPI 后端
```

## 🎮 游戏场景说明

### ChatScene.ts 核心功能

| 功能 | 描述 |
|------|------|
| `createPlayer()` | 创建玩家角色（蓝色冒险者） |
| `createNPC()` | 创建 AI 机器人（紫色机器人带天线） |
| `showPlayerDialog(text)` | 显示玩家对话气泡 |
| `showNPCDialog(text, onComplete)` | 显示 NPC 对话（打字机效果） |
| `setRobotStatus(status)` | 切换机器人动画状态 |
| `playParticleEffect()` | 播放金色粒子特效 |

### 机器人状态动画

- **idle**: 轻微上下浮动 + 暗淡光晕
- **thinking**: 左右摇晃 + 脉冲发光
- **speaking**: 缩放弹跳 + 稳定光晕

## 🔌 API 接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/chat` | POST | 发送消息获取回复 |
| `/api/upload` | POST | 上传文档到知识库 |
| `/api/docs` | GET | 获取所有文档列表 |
| `/api/docs/{id}` | DELETE | 删除指定文档 |
| `/api/stats` | GET | 获取文档统计信息 |
| `/api/health` | GET | 健康检查 |

## 🎨 像素风设计

- **配色**: 深色背景(#2d3436) + 高饱和度像素色
- **字体**: 'Press Start 2P' (英文) + 'Noto Sans SC' (中文)
- **边框**: 4px 实线边框模拟像素感
- **动画**: 使用 Phaser Tween 实现平滑动画

## 🔧 自定义配置

### 修改场景布局

编辑 `src/game/ChatScene.ts`:

```typescript
private readonly PLAYER_X = 200    // 玩家 X 位置
private readonly NPC_X = 600       // NPC X 位置
private readonly GROUND_Y = 400    // 地面 Y 位置
private readonly SCALE = 3         // 角色缩放
```

### 修改主题颜色

编辑 `src/index.css`:

```css
:root {
  --pixel-bg: #2d3436;
  --pixel-accent: #00b894;
  --pixel-warning: #fdcb6e;
  /* ... */
}
```

## 📦 技术栈

- **React 18** - UI 框架
- **Phaser 3** - 2D 游戏引擎
- **Vite** - 构建工具
- **TypeScript** - 类型安全
- **FastAPI** - 后端 API

## 📝 许可证

与原项目保持一致
