// 类型定义

export type RobotStatus = 'idle' | 'thinking' | 'speaking'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

export interface Document {
  id: string
  name: string
  md5: string
  partsCount: number
  size: number
  uploadedAt: string
}

export interface ChatResponse {
  answer: string
  sources?: string[]
}

export interface DocumentStats {
  totalFiles: number
  totalSize: number
}

// Phaser 场景回调接口
export interface ChatSceneCallbacks {
  onPlayerMessage: (text: string) => void
  onNPCAnimationComplete: () => void
}
