import type { RobotStatus } from '../types'

interface StatusBarProps {
  robotStatus: RobotStatus
  messageCount: number
}

const statusLabels: Record<RobotStatus, string> = {
  idle: '🟢 待机中',
  thinking: '🤔 思考中...',
  speaking: '💬 回复中...',
}

export function StatusBar({ robotStatus, messageCount }: StatusBarProps) {
  return (
    <div className="status-bar">
      <div className="status-item">
        <span className={`status-indicator ${robotStatus}`} />
        <span>{statusLabels[robotStatus]}</span>
      </div>
      <div className="status-item">
        <span>💬 对话数: {messageCount}</span>
      </div>
      <div className="status-item">
        <span>🎮 RPG Chat v0.1</span>
      </div>
    </div>
  )
}
