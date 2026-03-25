import { useState } from 'react'
import { generateThread } from '../api/generation'
import { createPost, publishNow } from '../api/posts'

export default function ThreadBuilder() {
  const [article, setArticle] = useState('')
  const [platform, setPlatform] = useState('threads')
  const [maxChars, setMaxChars] = useState(500)
  const [segments, setSegments] = useState([])
  const [threadGroupId, setThreadGroupId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [toast, setToast] = useState(null)

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  const handleSplit = async () => {
    if (!article.trim()) return
    setLoading(true)
    setSegments([])
    try {
      const res = await generateThread({ article, platform, max_chars_per_segment: maxChars })
      setSegments(res.data.segments.map(s => ({ content: s, edited: false })))
      setThreadGroupId(res.data.thread_group_id)
    } catch (e) {
      showToast(e?.response?.data?.detail || '拆分失敗', 'error')
    }
    setLoading(false)
  }

  const handlePublishAll = async () => {
    if (!segments.length) return
    setPublishing(true)
    try {
      const posts = []
      for (let i = 0; i < segments.length; i++) {
        const post = await createPost({
          content: segments[i].content,
          platform,
          thread_group_id: threadGroupId,
          thread_sequence_order: i,
          is_thread_parent: i === 0,
        })
        posts.push(post.data)
      }
      // Publish all in sequence
      for (const post of posts) {
        await publishNow(post.id)
        await new Promise(r => setTimeout(r, 2000))
      }
      showToast(`✅ 已發布 ${posts.length} 篇串文！`)
    } catch (e) {
      showToast(e?.response?.data?.detail || '發布失敗', 'error')
    }
    setPublishing(false)
  }

  const handleSaveAll = async () => {
    for (let i = 0; i < segments.length; i++) {
      await createPost({
        content: segments[i].content,
        platform,
        thread_group_id: threadGroupId,
        thread_sequence_order: i,
        is_thread_parent: i === 0,
      })
    }
    showToast(`已儲存 ${segments.length} 篇到文案庫`)
  }

  return (
    <div>
      <h1 className="page-title">🧵 長文自動分篇</h1>
      <div className="grid-2" style={{ alignItems: 'start' }}>

        {/* Left: Input */}
        <div className="card">
          <div className="form-group">
            <label>目標平台</label>
            <select value={platform} onChange={e => {
              setPlatform(e.target.value)
              setMaxChars(e.target.value === 'threads' ? 500 : 2000)
            }}>
              <option value="threads">Threads (500字/篇)</option>
              <option value="facebook">Facebook (2000字/篇)</option>
            </select>
          </div>

          <div className="form-group">
            <label>每篇最大字數：{maxChars}</label>
            <input type="range" min={100} max={platform === 'threads' ? 500 : 5000}
              step={50} value={maxChars}
              onChange={e => setMaxChars(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--primary)', background: 'none', border: 'none', padding: '4px 0' }} />
          </div>

          <div className="form-group">
            <label>長文內容</label>
            <textarea
              value={article}
              onChange={e => setArticle(e.target.value)}
              placeholder="貼上你的長文、文章或報告，AI 將自動拆分成連續的串文..."
              rows={14}
            />
            <div className="text-small text-muted mt-4">{article.length} 字</div>
          </div>

          <button className="btn-primary w-full" onClick={handleSplit} disabled={loading || !article.trim()}>
            {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> 拆分中...</> : '🔪 AI 自動拆分'}
          </button>
        </div>

        {/* Right: Preview */}
        <div>
          {segments.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>🧵</div>
              <div>貼上長文並點擊「AI 自動拆分」</div>
              <div>AI 將保留敘事脈絡，智慧分段</div>
            </div>
          ) : (
            <div>
              <div className="flex-between mb-12">
                <div className="section-title" style={{ margin: 0 }}>預覽：{segments.length} 篇串文</div>
                <div className="flex gap-8">
                  <button className="btn-secondary" style={{ fontSize: 13 }} onClick={handleSaveAll}>💾 存文案庫</button>
                  <button className="btn-success" style={{ fontSize: 13 }} onClick={handlePublishAll} disabled={publishing}>
                    {publishing ? '發布中...' : '▶ 全部發布'}
                  </button>
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {segments.map((seg, idx) => (
                  <div key={idx} className="card" style={{ position: 'relative' }}>
                    <div className="flex-between mb-8">
                      <span style={{ background: 'var(--primary)', color: '#fff', borderRadius: '50%', width: 24, height: 24, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700 }}>
                        {idx + 1}
                      </span>
                      <span className="text-small text-muted">{seg.content.length} 字</span>
                    </div>
                    <textarea
                      value={seg.content}
                      onChange={e => setSegments(prev => prev.map((s, i) => i === idx ? { ...s, content: e.target.value } : s))}
                      rows={Math.min(8, Math.max(3, Math.ceil(seg.content.length / 50)))}
                      style={{ fontSize: 13 }}
                    />
                    {idx < segments.length - 1 && (
                      <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: 8 }}>↓</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}
    </div>
  )
}
