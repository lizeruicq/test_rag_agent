import { useState, KeyboardEvent } from 'react'

interface ChatInputProps {
  onSend: (text: string) => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({ onSend, disabled, placeholder }: ChatInputProps) {
  const [text, setText] = useState('')

  const handleSend = () => {
    if (text.trim() && !disabled) {
      onSend(text.trim())
      setText('')
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-input-container">
      <input
        type="text"
        className="chat-input"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || '输入消息...'}
        disabled={disabled}
        maxLength={2000}
      />
      <button
        className="send-button"
        onClick={handleSend}
        disabled={disabled || !text.trim()}
      >
        {disabled ? '⚔️ ...' : '⚔️ 发送'}
      </button>
    </div>
  )
}
