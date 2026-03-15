import axios from 'axios'
import type { ChatResponse, Document, DocumentStats } from '../types'

// 自动检测环境：开发模式使用代理，生产模式使用相对路径
const isDev = import.meta.env.DEV
const baseURL = isDev ? '/api' : '/api'

const client = axios.create({
  baseURL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  // 聊天
  async chat(message: string): Promise<ChatResponse> {
    const response = await client.post<ChatResponse>('/chat', { message })
    return response.data
  },

  // 上传文档
  async uploadDocument(file: File): Promise<{ success: boolean; message: string }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await client.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // 获取文档列表
  async getDocuments(): Promise<Document[]> {
    const response = await client.get<Document[]>('/docs')
    return response.data
  },

  // 删除文档
  async deleteDocument(docId: string): Promise<{ success: boolean }> {
    const response = await client.delete(`/docs/${docId}`)
    return response.data
  },

  // 获取统计信息
  async getStats(): Promise<DocumentStats> {
    const response = await client.get<DocumentStats>('/stats')
    return response.data
  },
}
