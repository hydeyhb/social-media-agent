import { useState, useRef } from 'react'
import { uploadAsset } from '../api/assets'
import { createPost, publishNow } from '../api/posts'

export default function ImageCaption() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [platform, setPlatform] = useState('both')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [caption, setCaption] = useState('')
  const [assetId, setAssetId] = useState(null)
  const [toast, setToast] = useState(null)
  const [publishing, setPublishing] = useState(false)
  const inputRef = useRef()

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 2500)
  }

  const handleFile = (f) => {
    if (!f || !f.type.startsWith('image/')) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
    setCaption('')
  }

  const handleDrop = (e) => {
    e.preventDefault()
    handleFile(e.dataTransfer.files[0])
  }

  const handleAnalyze = async () => {
    if (!file) return
    setLoading(true)
    try {
      const res = await uploadAsset(file, platform)
      const data = res.data
      setResult(data)
      setCaption(data.generated_caption || '')
      setAssetId(data.id)
      showToast('圖片分析完成！')
    } catch (e) {
      showToast(e?.response?.data?.detail || '分析失敗', 'error')
    }
    setLoading(false)
  }

  const handlePublishNow = async () => {
    if (!caption.trim()) return
    setPublishing(true)
    try {
      const post = await createPost({ content: caption, platform, media_asset_id: assetId })
      await publishNow(post.data.id)
      showToast('圖文已發布！')
    } catch (e) {
      showToast(e?.response?.data?.detail || '發布失敗', 'error')
    }
    setPublishing(false)
  }

  const handleSaveToLibrary = async () => {
    try {
      await createPost({ content: caption, platform, media_asset_id: assetId })
      showToast('已存入文案庫')
    } catch {
      showToast('儲存失敗', 'error')
    }
  }

  return (
    <div>
      <h1 className="page-title">🖼 圖片看圖生文</h1>
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
              padding: 40,
              textAlign: 'center',
              cursor: 'pointer',
              background: 'var(--surface2)',
              transition: 'border-color 0.15s',
            }}
          >
            {preview ? (
              <img src={preview} alt="preview" style={{ maxWidth: '100%', maxHeight: 300, borderRadius: 8 }} />
            ) : (
              <div>
                <div style={{ fontSize: 40, marginBottom: 12 }}>📁</div>
                <div style={{ color: 'var(--text-muted)' }}>拖曳圖片或點此上傳</div>
                <div className="text-small text-muted mt-8">支援 JPG、PNG、WEBP</div>
              </div>
            )}
            <input ref={inputRef} type="file" accept="image/*" style={{ display: 'none' }}
              onChange={e => handleFile(e.target.files[0])} />
          </div>

          {file && (
            <div className="mt-16">
              <div className="text-small text-muted mb-8">{file.name} ({(file.size / 1024).toFixed(1)} KB)</div>
              <button className="btn-primary w-full" onClick={handleAnalyze} disabled={loading}>
                {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> AI 分析中...</> : '🤖 AI 看圖生文'}
              </button>
            </div>
          )}
        </div>

        {/* Right: Result */}
        <div className="card">
          {!result ? (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px 0' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>✨</div>
              <div>上傳圖片後，AI 將自動分析圖片內容</div>
              <div>並根據品牌風格生成專屬文案</div>
            </div>
          ) : (
            <div>
              <div className="section-title">📝 AI 圖片分析</div>
              <div className="card mb-16" style={{ background: 'var(--surface2)' }}>
                <div className="text-small text-muted mb-4">圖片描述</div>
                <div>{result.vision_analysis || result.description}</div>
              </div>

              <div className="form-group">
                <label>生成文案（可編輯）</label>
                <textarea value={caption} onChange={e => setCaption(e.target.value)} rows={6} />
              </div>

              <div className="flex gap-8">
                <button className="btn-success" onClick={handlePublishNow} disabled={publishing || !caption}>
                  {publishing ? '發布中...' : '▶ 立即發布'}
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
