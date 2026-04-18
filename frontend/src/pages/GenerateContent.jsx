import { useState } from 'react'
import { generateSingle } from '../api/generation'
import { createPost } from '../api/posts'
import { getAllBrands } from '../api/brand'
import { useEffect } from 'react'

export default function GenerateContent() {
  const [mode, setMode] = useState('single')
  const [topic, setTopic] = useState('')
  const [bulkTopics, setBulkTopics] = useState('')
  const [platform, setPlatform] = useState('both')
  const [personaId, setPersonaId] = useState('')
  const [personas, setPersonas] = useState([])
  const [generated, setGenerated] = useState([])
  const [loading, setLoading] = useState(false)
  const [streamProgress, setStreamProgress] = useState(0)
  const [toast, setToast] = useState(null)
  const [withImage, setWithImage] = useState(false)
  const [provider, setProvider] = useState('openai')
  const [previewSrc, setPreviewSrc] = useState(null)

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 2500)
  }

  useEffect(() => {
    getAllBrands().then(r => {
      setPersonas(r.data)
      const active = r.data.find(p => p.is_active)
      if (active) setPersonaId(String(active.id))
    }).catch(() => {})
  }, [])

  const handleSingle = async () => {
    if (!topic.trim()) return
    setLoading(true)
    setGenerated([])
    try {
      const res = await generateSingle({
        topic,
        platform,
        persona_id: personaId ? Number(personaId) : null,
        with_image: withImage,
        provider,
      })
      setGenerated([{ content: res.data.content, image: res.data.image, approved: false, saved: false }])
      if (withImage && res.data.image?.error) {
        showToast(`圖片生成失敗：${res.data.image.error}`, 'error')
      }
    } catch (e) {
      showToast(e?.response?.data?.detail || '生成失敗', 'error')
    }
    setLoading(false)
  }

  const handleBulk = async () => {
    const topics = bulkTopics.split('\n').map(t => t.trim()).filter(Boolean)
    if (!topics.length) return
    setLoading(true)
    setGenerated([])
    setStreamProgress(0)

    const url = `/api/generate/bulk`
    const token = localStorage.getItem('token')
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        topics,
        platform,
        persona_id: personaId ? Number(personaId) : null,
        with_image: withImage,
        provider,
      }),
    })

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}))
      showToast(errBody.detail || `批量生成失敗 (${res.status})`, 'error')
      setLoading(false)
      return
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value)
      const lines = buffer.split('\n')
      buffer = lines.pop()
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.done) { setLoading(false); break }
          if (typeof data.content === 'string') {
            setGenerated(prev => [...prev, { content: data.content, image: null, approved: false, saved: false }])
            setStreamProgress(data.index + 1)
          } else if (data.image !== undefined) {
            setGenerated(prev => prev.map((g, i) => i === data.index ? { ...g, image: data.image } : g))
          }
        } catch {}
      }
    }
    setLoading(false)
  }

  const handleSaveToLibrary = async (idx) => {
    const item = generated[idx]
    try {
      await createPost({
        content: item.content,
        platform,
        brand_persona_id: personaId ? Number(personaId) : null,
        media_asset_id: item.image?.asset_id || null,
      })
      setGenerated(prev => prev.map((g, i) => i === idx ? { ...g, saved: true } : g))
      showToast('已加入文案庫！')
    } catch {
      showToast('儲存失敗', 'error')
    }
  }

  const handleSaveAll = async () => {
    for (let i = 0; i < generated.length; i++) {
      if (!generated[i].saved) await handleSaveToLibrary(i)
    }
    showToast(`已全部儲存 ${generated.length} 篇到文案庫！`)
  }

  return (
    <div>
      <h1 className="page-title">✨ AI 文案生成</h1>

      <div className="card mb-16">
        {/* Mode Tabs */}
        <div className="flex gap-8 mb-16">
          <button className={mode === 'single' ? 'btn-primary' : 'btn-secondary'} onClick={() => setMode('single')}>單篇生成</button>
          <button className={mode === 'bulk' ? 'btn-primary' : 'btn-secondary'} onClick={() => setMode('bulk')}>批量生成（最多50篇）</button>
        </div>

        <div className="grid-2 mb-16">
          <div className="form-group">
            <label>平台</label>
            <select value={platform} onChange={e => setPlatform(e.target.value)}>
              <option value="both">兩個平台</option>
              <option value="facebook">Facebook</option>
              <option value="threads">Threads</option>
            </select>
          </div>
          <div className="form-group">
            <label>品牌人設</label>
            <select value={personaId} onChange={e => setPersonaId(e.target.value)}>
              <option value="">使用預設 (使用中人設)</option>
              {personas.map(p => <option key={p.id} value={p.id}>{p.name}{p.is_active ? ' ✅' : ''}</option>)}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label>AI 模型</label>
          <select value={provider} onChange={e => setProvider(e.target.value)}>
            <option value="openai">OpenAI (GPT-4o-mini)</option>
            <option value="gemini">Google Gemini (2.5 Pro / Imagen)</option>
          </select>
        </div>

        {mode === 'single' ? (
          <div className="form-group">
            <label>貼文主題</label>
            <textarea value={topic} onChange={e => setTopic(e.target.value)} placeholder="例：夏日新品上市、品牌週年慶優惠、新門市開幕..." rows={3} />
          </div>
        ) : (
          <div className="form-group">
            <label>批量主題（每行一個主題，最多50行）</label>
            <textarea value={bulkTopics} onChange={e => setBulkTopics(e.target.value)}
              placeholder={'夏日新品上市\n品牌週年慶\n客戶見證分享\n新服務介紹\n...'} rows={8} />
            <div className="text-small text-muted mt-8">已輸入 {bulkTopics.split('\n').filter(Boolean).length} 個主題</div>
          </div>
        )}

        <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input
            id="with-image"
            type="checkbox"
            checked={withImage}
            onChange={e => setWithImage(e.target.checked)}
            style={{ width: 'auto', margin: 0 }}
          />
          <label htmlFor="with-image" style={{ margin: 0, cursor: 'pointer' }}>
            🖼 同時生成精緻配圖
            <span className="text-small text-muted" style={{ marginLeft: 8 }}>
              （每則多約 10–20 秒，HD 品質，無文字浮水印）
            </span>
          </label>
        </div>

        <div className="flex gap-8">
          <button
            className="btn-primary"
            onClick={mode === 'single' ? handleSingle : handleBulk}
            disabled={loading || (mode === 'single' ? !topic.trim() : !bulkTopics.trim())}
          >
            {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> 生成中...{mode === 'bulk' ? ` (${streamProgress})` : ''}</> : '🪄 開始生成'}
          </button>
          {generated.length > 0 && !loading && (
            <button className="btn-success" onClick={handleSaveAll}>💾 全部存入文案庫</button>
          )}
        </div>
      </div>

      {/* Results */}
      {generated.length > 0 && (
        <div>
          <div className="section-title mb-8">生成結果 ({generated.length} 篇)</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {generated.map((item, idx) => (
              <div key={idx} className="card" style={{ borderLeft: item.saved ? '3px solid var(--success)' : '3px solid var(--border)' }}>
                <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', marginBottom: 12 }}>
                  {item.image?.url && (
                    <img
                      src={item.image.url}
                      alt="AI generated"
                      onClick={() => setPreviewSrc(item.image.url)}
                      style={{ width: 160, height: 160, objectFit: 'cover', borderRadius: 8, cursor: 'zoom-in', flexShrink: 0 }}
                    />
                  )}
                  {withImage && !item.image?.url && !item.image?.error && (
                    <div style={{ width: 160, height: 160, borderRadius: 8, background: 'var(--surface2)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <span className="spinner" />
                    </div>
                  )}
                  {item.image?.error && (
                    <div style={{ width: 160, padding: 8, borderRadius: 8, background: 'var(--surface2)', flexShrink: 0, fontSize: 12, color: 'var(--text-muted)' }}>
                      圖片生成失敗：<br />{item.image.error}
                    </div>
                  )}
                  <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7, flex: 1 }}>{item.content}</div>
                </div>
                <div className="flex gap-8">
                  {!item.saved ? (
                    <button className="btn-success" style={{ fontSize: 13 }} onClick={() => handleSaveToLibrary(idx)}>💾 存入文案庫</button>
                  ) : (
                    <span className="text-success text-small">✅ 已存入</span>
                  )}
                  {item.image?.url && (
                    <a href={item.image.url} download className="btn-secondary" style={{ fontSize: 13, textDecoration: 'none' }}>⬇ 下載圖片</a>
                  )}
                </div>
              </div>
            ))}
          </div>
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
