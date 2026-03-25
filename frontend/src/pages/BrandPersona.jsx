import { useEffect, useState } from 'react'
import { getAllBrands, createBrand, updateBrand, activateBrand, deleteBrand } from '../api/brand'

const TONE_OPTIONS = ['professional', 'playful', 'authoritative', 'warm', 'inspirational', 'casual', 'luxurious']
const EMOJI_OPTIONS = [
  { value: 'none', label: '完全不用 Emoji' },
  { value: 'moderate', label: '適量使用 (1-3個)' },
  { value: 'heavy', label: '大量使用 Emoji' },
]
const LENGTH_OPTIONS = [
  { value: 'short', label: '短文 (50-100字)' },
  { value: 'medium', label: '中文 (100-200字)' },
  { value: 'long', label: '長文 (200-400字)' },
]

function TagInput({ tags, onChange, placeholder }) {
  const [input, setInput] = useState('')
  const add = () => {
    const v = input.trim()
    if (v && !tags.includes(v)) onChange([...tags, v])
    setInput('')
  }
  return (
    <div>
      <div className="flex gap-8 flex-wrap mb-8">
        {tags.map((t) => (
          <span key={t} style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 20, padding: '2px 10px', fontSize: 13, display: 'flex', alignItems: 'center', gap: 4 }}>
            {t}
            <button onClick={() => onChange(tags.filter(x => x !== t))} style={{ background: 'none', padding: 0, color: 'var(--text-muted)', fontSize: 16, lineHeight: 1 }}>×</button>
          </span>
        ))}
      </div>
      <div className="flex gap-8">
        <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && add()} placeholder={placeholder} />
        <button className="btn-secondary" onClick={add} style={{ whiteSpace: 'nowrap' }}>+ 新增</button>
      </div>
    </div>
  )
}

const defaultForm = {
  name: '',
  tone: 'professional',
  style_notes: '',
  target_audience: '',
  keywords: [],
  avoid_phrases: [],
  emoji_usage: 'moderate',
  post_length_preference: 'medium',
}

export default function BrandPersona() {
  const [personas, setPersonas] = useState([])
  const [selected, setSelected] = useState(null)
  const [form, setForm] = useState(defaultForm)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState(null)

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 2500)
  }

  const load = async () => {
    const res = await getAllBrands().catch(() => ({ data: [] }))
    setPersonas(res.data)
  }
  useEffect(() => { load() }, [])

  const handleSelect = (p) => {
    setSelected(p)
    setForm({ ...p })
  }

  const handleNew = () => {
    setSelected(null)
    setForm(defaultForm)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      if (selected) {
        await updateBrand(selected.id, form)
        showToast('品牌人設已更新')
      } else {
        await createBrand(form)
        showToast('品牌人設已新增')
      }
      await load()
    } catch {
      showToast('儲存失敗', 'error')
    }
    setSaving(false)
  }

  const handleActivate = async (id) => {
    await activateBrand(id)
    showToast('已設為使用中人設')
    await load()
  }

  const handleDelete = async (id) => {
    if (!confirm('確定刪除此人設？')) return
    await deleteBrand(id)
    if (selected?.id === id) { setSelected(null); setForm(defaultForm) }
    await load()
  }

  return (
    <div>
      <h1 className="page-title">🎨 品牌人設設定</h1>
      <div className="grid-2" style={{ alignItems: 'start' }}>

        {/* Left: Persona list */}
        <div>
          <div className="card mb-16">
            <div className="flex-between mb-16">
              <div className="section-title" style={{ margin: 0 }}>已儲存人設</div>
              <button className="btn-primary" onClick={handleNew}>+ 新建人設</button>
            </div>
            {personas.length === 0 ? (
              <p className="text-muted">尚未建立任何品牌人設。請點擊「新建人設」開始。</p>
            ) : (
              personas.map((p) => (
                <div key={p.id}
                  onClick={() => handleSelect(p)}
                  style={{ padding: '12px', borderRadius: 8, cursor: 'pointer', background: selected?.id === p.id ? 'rgba(99,102,241,0.1)' : 'var(--surface2)', border: `1px solid ${selected?.id === p.id ? 'var(--primary)' : 'var(--border)'}`, marginBottom: 8 }}>
                  <div className="flex-between">
                    <div>
                      <strong>{p.name}</strong>
                      {p.is_active && <span className="tag tag-published ml-8" style={{ marginLeft: 8 }}>使用中</span>}
                    </div>
                    <div className="flex gap-8">
                      {!p.is_active && (
                        <button className="btn-success" style={{ padding: '4px 10px', fontSize: 12 }}
                          onClick={e => { e.stopPropagation(); handleActivate(p.id) }}>啟用</button>
                      )}
                      <button className="btn-danger" style={{ padding: '4px 10px', fontSize: 12 }}
                        onClick={e => { e.stopPropagation(); handleDelete(p.id) }}>刪除</button>
                    </div>
                  </div>
                  <div className="text-small text-muted mt-8">{p.tone} · {p.target_audience || '未設定受眾'}</div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: Form */}
        <div className="card">
          <div className="section-title">{selected ? `編輯：${selected.name}` : '新建品牌人設'}</div>

          <div className="form-group">
            <label>品牌名稱 *</label>
            <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="例：Acme 品牌" />
          </div>

          <div className="form-group">
            <label>口吻風格</label>
            <select value={form.tone} onChange={e => setForm({ ...form, tone: e.target.value })}>
              {TONE_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label>目標受眾</label>
            <input value={form.target_audience} onChange={e => setForm({ ...form, target_audience: e.target.value })} placeholder="例：25-35歲的都市女性，注重生活品質" />
          </div>

          <div className="form-group">
            <label>品牌風格說明</label>
            <textarea value={form.style_notes} onChange={e => setForm({ ...form, style_notes: e.target.value })} placeholder="描述品牌的個性、價值觀、溝通方式..." rows={3} />
          </div>

          <div className="form-group">
            <label>常用關鍵字（按 Enter 新增）</label>
            <TagInput tags={form.keywords} onChange={v => setForm({ ...form, keywords: v })} placeholder="輸入關鍵字..." />
          </div>

          <div className="form-group">
            <label>禁用詞（按 Enter 新增）</label>
            <TagInput tags={form.avoid_phrases} onChange={v => setForm({ ...form, avoid_phrases: v })} placeholder="輸入禁用詞..." />
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label>Emoji 使用</label>
              <select value={form.emoji_usage} onChange={e => setForm({ ...form, emoji_usage: e.target.value })}>
                {EMOJI_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>貼文長度偏好</label>
              <select value={form.post_length_preference} onChange={e => setForm({ ...form, post_length_preference: e.target.value })}>
                {LENGTH_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
          </div>

          <button className="btn-primary w-full" onClick={handleSave} disabled={saving || !form.name}>
            {saving ? <span className="spinner" /> : (selected ? '💾 儲存更新' : '✅ 建立人設')}
          </button>
        </div>
      </div>

      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}
    </div>
  )
}
