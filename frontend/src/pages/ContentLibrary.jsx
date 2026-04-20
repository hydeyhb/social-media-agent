import { useEffect, useState } from 'react'
import { listPosts, publishNow, schedulePost, cancelSchedule, deletePost, updatePost } from '../api/posts'

const STATUS_LABELS = { draft: '草稿', scheduled: '排程中', published: '已發布', failed: '失敗' }

export default function ContentLibrary() {
  const [posts, setPosts] = useState([])
  const [filter, setFilter] = useState({ status: '', platform: '' })
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null)
  const [scheduleTime, setScheduleTime] = useState({})
  const [toast, setToast] = useState(null)
  const [previewSrc, setPreviewSrc] = useState(null)

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 2500)
  }

  const load = async () => {
    setLoading(true)
    const params = {}
    if (filter.status) params.status = filter.status
    if (filter.platform) params.platform = filter.platform
    const res = await listPosts(params).catch(() => ({ data: [] }))
    setPosts(res.data)
    setLoading(false)
  }
  useEffect(() => { load() }, [filter])

  const handlePublishNow = async (id) => {
    try {
      await publishNow(id)
      showToast('貼文已立即發布！')
      load()
    } catch (e) {
      showToast(e?.response?.data?.detail || '發布失敗', 'error')
    }
  }

  const handleSchedule = async (id) => {
    const time = scheduleTime[id]
    if (!time) return
    try {
      await schedulePost(id, new Date(time).toISOString())
      showToast('排程已設定！')
      load()
    } catch {
      showToast('排程設定失敗', 'error')
    }
  }

  const handleCancelSchedule = async (id) => {
    await cancelSchedule(id)
    showToast('排程已取消')
    load()
  }

  const handleDelete = async (id) => {
    if (!confirm('確定刪除此貼文？')) return
    await deletePost(id)
    showToast('已刪除')
    load()
  }

  const handleSaveEdit = async () => {
    if (!editing) return
    await updatePost(editing.id, { content: editing.content })
    setEditing(null)
    showToast('已更新')
    load()
  }

  return (
    <div>
      <h1 className="page-title">📚 文案庫</h1>

      {/* Filters */}
      <div className="card mb-16">
        <div className="flex gap-12 flex-wrap">
          <select value={filter.status} onChange={e => setFilter({ ...filter, status: e.target.value })} style={{ width: 140 }}>
            <option value="">全部狀態</option>
            {Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
          <select value={filter.platform} onChange={e => setFilter({ ...filter, platform: e.target.value })} style={{ width: 140 }}>
            <option value="">全部平台</option>
            <option value="facebook">Facebook</option>
            <option value="threads">Threads</option>
            <option value="both">兩個平台</option>
          </select>
          <button className="btn-secondary" onClick={load}>🔄 重整</button>
          <div className="text-muted flex-center" style={{ marginLeft: 'auto' }}>共 {posts.length} 篇</div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}><div className="spinner" /></div>
      ) : posts.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
          沒有貼文。請至「AI 生成」頁面產生文案。
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {posts.map((p) => (
            <div key={p.id} className="card">
              <div className="flex-between mb-8">
                <div className="flex gap-8 flex-center">
                  <span className={`tag tag-${p.platform}`}>{p.platform === 'both' ? '兩平台' : p.platform}</span>
                  <span className={`tag tag-${p.status}`}>{STATUS_LABELS[p.status] || p.status}</span>
                </div>
                <div className="text-small text-muted">
                  {p.created_at ? new Date(p.created_at).toLocaleDateString('zh-TW') : ''}
                </div>
              </div>

              {editing?.id === p.id ? (
                <div>
                  <textarea value={editing.content} onChange={e => setEditing({ ...editing, content: e.target.value })} rows={5} />
                  <div className="flex gap-8 mt-8">
                    <button className="btn-primary" onClick={handleSaveEdit}>💾 儲存</button>
                    <button className="btn-secondary" onClick={() => setEditing(null)}>取消</button>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                  {p.media_asset?.url && (
                    <img
                      src={p.media_asset.url}
                      alt="post media"
                      onClick={() => setPreviewSrc(p.media_asset.url)}
                      style={{ width: 120, height: 120, objectFit: 'cover', borderRadius: 8, cursor: 'zoom-in', flexShrink: 0 }}
                    />
                  )}
                  <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7, flex: 1 }}>{p.content}</div>
                </div>
              )}

              {p.status === 'scheduled' && p.scheduled_at && (
                <div className="text-small text-warning mt-8">
                  ⏰ 排程時間：{new Date(p.scheduled_at).toLocaleString('zh-TW')}
                </div>
              )}

              {p.error_message && (
                <div className="text-small text-danger mt-8">❌ {p.error_message}</div>
              )}

              {/* Actions */}
              <div className="flex gap-8 mt-16 flex-wrap">
                {p.status === 'draft' && (
                  <>
                    <button className="btn-success" style={{ fontSize: 13 }} onClick={() => handlePublishNow(p.id)}>▶ 立即發布</button>
                    <div className="flex gap-8">
                      <input
                        type="datetime-local"
                        style={{ width: 200, padding: '6px 10px', fontSize: 13 }}
                        value={scheduleTime[p.id] || ''}
                        onChange={e => setScheduleTime({ ...scheduleTime, [p.id]: e.target.value })}
                      />
                      <button className="btn-warning" style={{ fontSize: 13 }} onClick={() => handleSchedule(p.id)}>⏰ 排程</button>
                    </div>
                  </>
                )}
                {p.status === 'scheduled' && (
                  <button className="btn-secondary" style={{ fontSize: 13 }} onClick={() => handleCancelSchedule(p.id)}>取消排程</button>
                )}
                {p.status !== 'published' && (
                  <button className="btn-secondary" style={{ fontSize: 13 }} onClick={() => setEditing(p)}>✏️ 編輯</button>
                )}
                <button className="btn-danger" style={{ fontSize: 13 }} onClick={() => handleDelete(p.id)}>🗑 刪除</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {previewSrc && (
        <div
          onClick={() => setPreviewSrc(null)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, cursor: 'zoom-out' }}
        >
          <img src={previewSrc} alt="preview" style={{ maxWidth: '90%', maxHeight: '90%', borderRadius: 8 }} />
        </div>
      )}

      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}
    </div>
  )
}
