import { useEffect, useRef, useState, useCallback } from 'react'
import Phaser from 'phaser'
import { ChatScene } from './game/ChatScene'
import { ChatInput } from './components/ChatInput'
import { DocPanel } from './components/DocPanel'
import { StatusBar } from './components/StatusBar'
import type { ChatMessage, RobotStatus } from './types'
import { api } from './api'

function App() {
  const gameRef = useRef<Phaser.Game | null>(null)
  const sceneRef = useRef<ChatScene | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [robotStatus, setRobotStatus] = useState<RobotStatus>('idle')
  const [isProcessing, setIsProcessing] = useState(false)

  // 初始化 Phaser 游戏
  useEffect(() => {
    const config: Phaser.Types.Core.GameConfig = {
      type: Phaser.AUTO,
      width: window.innerWidth,
      height: window.innerHeight,
      parent: 'game-container',
      pixelArt: true,
      backgroundColor: '#2d3436',
      scene: ChatScene,
      physics: {
        default: 'arcade',
        arcade: { gravity: { x: 0, y: 0 } }
      }
    }

    gameRef.current = new Phaser.Game(config)

    // 获取场景引用
    const checkScene = setInterval(() => {
      const scene = gameRef.current?.scene.getScene('ChatScene') as ChatScene
      if (scene) {
        sceneRef.current = scene
        // 设置场景回调
        scene.setCallbacks({
          onPlayerMessage: handlePlayerMessage,
          onNPCAnimationComplete: () => setRobotStatus('idle')
        })
        clearInterval(checkScene)
      }
    }, 100)

    // 响应窗口大小变化
    const handleResize = () => {
      gameRef.current?.scale.resize(window.innerWidth, window.innerHeight)
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      gameRef.current?.destroy(true)
    }
  }, [])

  // 处理玩家消息
  const handlePlayerMessage = useCallback(async (text: string) => {
    if (!text.trim() || isProcessing) return

    // 添加玩家消息到列表
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: Date.now()
    }
    setMessages(prev => [...prev, userMessage])
    setIsProcessing(true)
    setRobotStatus('thinking')

    // 在场景中显示玩家对话气泡
    sceneRef.current?.showPlayerDialog(text)

    try {
      // 调用后端 API
      const response = await api.chat(text)

      // 切换到说话状态
      setRobotStatus('speaking')

      // 添加 AI 消息
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: Date.now()
      }
      setMessages(prev => [...prev, aiMessage])

      // 在场景中显示 NPC 对话（带打字机效果）
      sceneRef.current?.showNPCDialog(response.answer, () => {
        setRobotStatus('idle')
        setIsProcessing(false)
      })
    } catch (error) {
      console.error('Chat error:', error)
      sceneRef.current?.showNPCDialog('抱歉，我遇到了一些问题...', () => {
        setRobotStatus('idle')
        setIsProcessing(false)
      })
    }
  }, [isProcessing])

  // 同步机器人状态到场景
  useEffect(() => {
    sceneRef.current?.setRobotStatus(robotStatus)
  }, [robotStatus])

  return (
    <div className="app">
      {/* Phaser 游戏容器 */}
      <div id="game-container" className="game-container" />

      {/* React UI 覆盖层 */}
      <div className="ui-overlay">
        <StatusBar
          robotStatus={robotStatus}
          messageCount={messages.length}
        />
        <DocPanel />
        <ChatInput
          onSend={handlePlayerMessage}
          disabled={isProcessing}
          placeholder={isProcessing ? 'AI 思考中...' : '输入消息开始对话...'}
        />
      </div>
    </div>
  )
}

export default App
