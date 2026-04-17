import { useState, useRef } from 'react'
import { uploadAssets } from '../api/assets'
import { createPost, publishNow } from '../api/posts'

const MAX_IMAGES = 6

export default function ImageCaption() {
  const [files, setFiles] = useState([])
  const [previews, setPreviews] = useState([])
  const [platform, setPlatform] = useState('both')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [caption, setCaption] = useState('')
  const [primaryAssetId, setPrimaryAssetId] = useState(null)
  const [toast, setToast] = useState(null)
  const [publishing, setPublishing] = useState(false)
  const inputRef = useRef()

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 2500)
  }

  const addFiles = (incoming) => {
    const imgs = Array.from(incoming || []).filter(f => f.type.startsWith('image/'))
    if (!imgs.length) return
    const combined = [...files, ...imgs].slice(0, MAX_IMAGES)
    if (files.length + imgs.length > MAX_IMAGES) {
      showToast(`最多只能上傳 ${MAX_IMAGES} 張`, 'error')
    }
    setFiles(combined)
    setPreviews(combined.map(f => URL.createObjectURL(f)))
    setResult(null)
    setCaption('')
    setPrimaryAssetId(null)
  }

  const removeAt = (idx) => {
    const next = files.filter((_, i) => i !== idx)
    setFiles(next)
    setPreviews(next.map(f => URL.createObjectURL(f)))
  }

  const handleDrop = (e) => {
    e.preventDefault()
    addFiles(e.dataTransfer.files)
  }

  const handleAnalyze = async () => {
    if (!files.length) return
    setLoading(true)
    try {
      const res = await uploadAssets(files, platform)
      const data = res.data
      setResult(data)
      setCaption(data.caption || '')
      setPrimaryAssetId(data.primary_asset_id)
      showToast(`已綜合 ${files.length} 張圖生成文案！`)
    } catch (e) {
      showToast(e?.response?.data?.detail || '分析失敗', 'error')
    }
    setLoading(false)
  }

  const handlePublishNow = async () => {
    if (!caption.trim() || !primaryAssetId) return
    setPublishing(true)
    try {
      const post = await createPost({ content: caption, platform, media_asset_id: primaryAssetId })
      await publishNow(post.data.id)
      showToast('圖文已發布！（單張主圖）')
    } catch (e) {
      showToast(e?.response?.data?.detail || '發布失敗', 'error')
    }
    setPublishing(false)
  }

  const handleSaveToLibrary = async () => {
    try {
      await createPost({ content: caption, platform, media_asset_id: primaryAssetId })
      showToast('已存入文案庫')
    } catch {
      showToast('儲存失敗', 'error')
    }
  }

  return (
    <div>
      <h1 className="page-title">🖼 圖片看圖生文（最多 {MAX_IMAGES} 張）</h1>
      <div className="grid-2" style={{ alignItems: 'start' }}>

        {/* Left: Upload */}
        <div className="card">
          <div className="form-group">
            <label>目標平台</label>
            <select value={platform} onChange={e => setPlatform(e.target.value)}>
              <option value="both">兩個平台</option>
              <option value="facebook">Facebook</option>
              <option value="threads">Threads</option>
            </select>
          </div>

          <div
            onDrop={handleDrop}
            onDragOver={e => e.preventDefault()}
            onClick={() => inputRef.current?.click()}
            style={{
              border: '2px dashed var(--border)',
              borderRadius: 10,
              padding: previews.length ? 16 : 40,
              textAlign: 'center',
              cursor: 'pointer',
              background: 'var(--surface2)',
              transition: 'border-color 0.15s',
            }}
          >
            {previews.length ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))', gap: 8 }}>
                {previews.map((src, i) => (
                  <div key={i} style={{ position: 'relative' }}>
                    <img src={src} alt={`preview-${i}`} style={{ width: '100%', height: 100, objectFit: 'cover', borderRadius: 6 }} />
                    <button
                      onClick={(e) => { e.stopPropagation(); removeAt(i) }}
                      style={{ position: 'absolute', top: 2, right: 2, background: 'rgba(0,0,0,0.7)', color: 'white', border: 'none', borderRadius: '50%', width: 22, height: 22, padding: 0, cursor: 'pointer', fontSize: 14, lineHeight: 1 }}
                    >×</button>
                    {i === 0 && (
                      <span style={{ position: 'absolute', bottom: 2, left: 2, background: 'var(--primary)', color: 'white', fontSize: 10, padding: '1px 6px', borderRadius: 4 }}>主圖</span>
                    )}
                  </div>
                ))}
                {files.length < MAX_IMAGES && (
                  <div style={{ height: 100, border: '1px dashed var(--border)', borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 24 }}>+</div>
                )}
              </div>
            ) : (
              <div>
                <div style={{ fontSize: 40, marginBottom: 12 }}>📁</div>
                <div style={{ color: 'var(--text-muted)' }}>拖曳或點此上傳圖片（可多選）</div>
                <div className="text-small text-muted mt-8">支援 JPG、PNG、WEBP，最多 {MAX_IMAGES} 張</div>
              </div>
            )}
            <input ref={inputRef} type="file" accept="image/*" multiple style={{ display: 'none' }}
              onChange={e => addFiles(e.target.files)} />
          </div>

          {files.length > 0 && (
            <div className="mt-16">
              <div className="text-small text-muted mb-8">
                已選 {files.length} 張（總計 {(files.reduce((s, f) => s + f.size, 0) / 1024).toFixed(1)} KB）
              </div>
              <button className="btn-primary w-full" onClick={handleAnalyze} disabled={loading}>
                {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> AI 綜合分析中...</> : `🤖 AI 看圖生文（${files.length} 張綜合）`}
              </button>
            </div>
          )}
        </div>

        {/* Right: Result */}
        <div className="card">
          {!result ? (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px 0' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>✨</div>
              <div>上傳圖片後（可多張），AI 將綜合分析所有圖片</div>
              <div>並產出**一則統整**的品牌風格貼文</div>
            </div>
          ) : (
            <div>
              <div className="section-title">📝 AI 綜合分析</div>
              <div className="card mb-16" style={{ background: 'var(--surface2)' }}>
                <div className="text-small text-muted mb-4">圖組描述（{files.length} 張）</div>
                <div>{result.description}</div>
              </div>

              <div className="form-group">
                <label>統整文案（可編輯）</label>
                <textarea value={caption} onChange={e => setCaption(e.target.value)} rows={6} />
              </div>

              <div className="text-small text-muted mb-8">
                ※ 發布時僅帶第 1 張作為主圖（FB / Threads 多圖發布尚未支援）
              </div>

              <div className="flex gap-8">
                <button className="btn-success" onClick={handlePublishNow} disabled={publishing || !caption}>
                  {publishing ? '發布中...' : '▶ 立即發布（主圖）'}
                </button>
                <button className="btn-secondary" onClick={handleSaveToLibrary}>💾 存入文案庫</button>
              </div>
            </div>
          )}
        </div>
      </div>

      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}
    </div>
  )
}
