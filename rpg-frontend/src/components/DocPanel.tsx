import { useState, useCallback, useEffect } from 'react'
import { api } from '../api'
import type { Document, DocumentStats } from '../types'

export function DocPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const [docs, setDocs] = useState<Document[]>([])
  const [stats, setStats] = useState<DocumentStats>({ totalFiles: 0, totalSize: 0 })
  const [isUploading, setIsUploading] = useState(false)

  const loadDocs = useCallback(async () => {
    try {
      const [docsData, statsData] = await Promise.all([
        api.getDocuments(),
        api.getStats(),
      ])
      setDocs(docsData)
      setStats(statsData)
    } catch (error) {
      console.error('Failed to load docs:', error)
    }
  }, [])

  useEffect(() => {
    if (isOpen) {
      loadDocs()
    }
  }, [isOpen, loadDocs])

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    try {
      const result = await api.uploadDocument(file)
      if (result.success) {
        await loadDocs()
      }
      alert(result.message)
    } catch (error) {
      alert('上传失败: ' + (error as Error).message)
    } finally {
      setIsUploading(false)
      // 清空 input
      e.target.value = ''
    }
  }

  const handleDelete = async (docId: string) => {
    if (!confirm('确定要删除这个文档吗？')) return

    try {
      await api.deleteDocument(docId)
      await loadDocs()
    } catch (error) {
      alert('删除失败: ' + (error as Error).message)
    }
  }

  return (
    <div className="doc-panel">
      <div className="doc-panel-header">
        <span className="doc-panel-title">📁 文档管理</span>
        <button
          className="doc-panel-toggle"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? '▼' : '▶'}
        </button>
      </div>

      {isOpen && (
        <div className="doc-panel-content">
          <label className="doc-upload-area">
            <input
              type="file"
              accept=".txt,.pdf,.docx,.xlsx,.xls"
              onChange={handleFileUpload}
              disabled={isUploading}
              style={{ display: 'none' }}
            />
            <div>
              {isUploading ? (
                <p>⏳ 上传中...</p>
              ) : (
                <>
                  <p>📤 点击或拖拽上传文档</p>
                  <p style={{ fontSize: '12px', opacity: 0.7, marginTop: '8px' }}>
                    支持: TXT, PDF, DOCX, XLSX, XLS
                  </p>
                </>
              )}
            </div>
          </label>

          <div className="doc-list">
            {docs.map((doc) => (
              <div key={doc.id} className="doc-item">
                <span className="doc-item-name" title={doc.name}>
                  📄 {doc.name}
                </span>
                <button
                  className="doc-item-delete"
                  onClick={() => handleDelete(doc.id)}
                >
                  删除
                </button>
              </div>
            ))}
            {docs.length === 0 && (
              <p style={{ textAlign: 'center', color: 'var(--pixel-text)', opacity: 0.7 }}>
                暂无文档
              </p>
            )}
          </div>

          <div className="doc-stats">
            <div className="doc-stat">
              <span className="doc-stat-value">{stats.totalFiles}</span>
              <span className="doc-stat-label">文件数</span>
            </div>
            <div className="doc-stat">
              <span className="doc-stat-value">
                {(stats.totalSize / 1024).toFixed(1)}KB
              </span>
              <span className="doc-stat-label">总大小</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
