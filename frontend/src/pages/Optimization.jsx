import { useEffect, useState } from 'react'
import { listPosts } from '../api/posts'
import { getContentPatterns, optimizePost } from '../api/generation'

export default function Optimization() {
  const [posts, setPosts] = useState([])
  const [selectedPost, setSelectedPost] = useState('')
  const [patterns, setPatterns] = useState(null)
  const [improvement, setImprovement] = useState(null)
  const [loadingPatterns, setLoadingPatterns] = useState(false)
  const [loadingImprove, setLoadingImprove] = useState(false)
  const [platform, setPlatform] = useState('both')

  useEffect(() => {
    listPosts({ status: 'published', limit: 100 })
      .then(r => setPosts(r.data))
      .catch(() => {})
  }, [])

  const handleAnalyzePatterns = async () => {
    setLoadingPatterns(true)
    setPatterns(null)
    try {
      const res = await getContentPatterns(platform)
      setPatterns(res.data)
    } catch (e) {
      console.error(e)
    }
    setLoadingPatterns(false)
  }

  const handleImprovePost = async () => {
    if (!selectedPost) return
    setLoadingImprove(true)
    setImprovement(null)
    try {
      const res = await optimizePost(Number(selectedPost))
      setImprovement(res.data)
    } catch (e) {
      console.error(e)
    }
    setLoadingImprove(false)
  }

  const ListItems = ({ items, color }) => (
    <ul style={{ paddingLeft: 0, listStyle: 'none' }}>
      {(items || []).map((item, i) => (
        <li key={i} style={{ padding: '6px 0', borderBottom: '1px solid var(--border)', fontSize: 14 }}>
          <span style={{ color, marginRight: 8 }}>→</span>{item}
        </li>
      ))}
    </ul>
  )

  return (
    <div>
      <h1 className="page-title">🔧 智慧內容優化</h1>
      <div className="grid-2" style={{ alignItems: 'start' }}>

        {/* Left: Pattern Analysis */}
        <div className="card">
          <div className="section-title">📊 整體內容表現分析</div>
          <p className="text-muted mb-16" style={{ fontSize: 13 }}>
            AI 分析高互動與低互動貼文的差異，找出你的品牌最受歡迎的內容規律。
          </p>

          <div className="form-group">
            <label>分析平台</label>
            <select value={platform} onChange={e => setPlatform(e.target.value)}>
              <option value="both">全部平台</option>
              <option value="facebook">Facebook</option>
              <option value="threads">Threads</option>
            </select>
          </div>

          <button className="btn-primary w-full" onClick={handleAnalyzePatterns} disabled={loadingPatterns}>
            {loadingPatterns ? <><span className="spinner" style={{ width: 14, height: 14 }} /> 分析中...</> : '🤖 分析內容規律'}
          </button>

          {patterns && (
            <div className="mt-16">
              {patterns.patterns?.length > 0 && (
                <div className="mb-16">
                  <div className="text-small" style={{ color: 'var(--success)', fontWeight: 600, marginBottom: 8 }}>✅ 高互動內容特徵</div>
                  <ListItems items={patterns.patterns} color="var(--success)" />
                </div>
              )}
              {patterns.recommendations?.length > 0 && (
                <div className="mb-16">
                  <div className="text-small" style={{ color: 'var(--primary)', fontWeight: 600, marginBottom: 8 }}>💡 優化建議</div>
                  <ListItems items={patterns.recommendations} color="var(--primary)" />
                </div>
              )}
              {patterns.avoid?.length > 0 && (
                <div>
                  <div className="text-small" style={{ color: 'var(--danger)', fontWeight: 600, marginBottom: 8 }}>🚫 應避免</div>
                  <ListItems items={patterns.avoid} color="var(--danger)" />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Post Improvement */}
        <div className="card">
          <div className="section-title">✏️ 單篇貼文改進建議</div>
          <p className="text-muted mb-16" style={{ fontSize: 13 }}>
            選擇一篇表現較低的貼文，AI 根據品牌風格提供改寫建議。
          </p>

          <div className="form-group">
            <label>選擇貼文</label>
            <select value={selectedPost} onChange={e => setSelectedPost(e.target.value)}>
              <option value="">請選擇已發布的貼文...</option>
              {posts.map(p => (
                <option key={p.id} value={p.id}>
                  #{p.id} {p.content?.slice(0, 50)}...
                </option>
              ))}
            </select>
          </div>

          {selectedPost && posts.find(p => p.id === Number(selectedPost)) && (
            <div className="card mb-16" style={{ background: 'var(--surface2)', fontSize: 13, lineHeight: 1.7 }}>
              {posts.find(p => p.id === Number(selectedPost))?.content}
            </div>
          )}

          <button className="btn-primary w-full" onClick={handleImprovePost} disabled={loadingImprove || !selectedPost}>
            {loadingImprove ? <><span className="spinner" style={{ width: 14, height: 14 }} /> 生成建議...</> : '🪄 生成改進建議'}
          </button>

          {improvement && (
            <div className="mt-16">
              <div className="text-small" style={{ color: 'var(--primary)', fontWeight: 600, marginBottom: 8 }}>✨ 改進後版本</div>
              <div className="card" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.2)', whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.8, marginBottom: 12 }}>
                {improvement.rewritten}
              </div>
              {improvement.explanation && (
                <div className="text-small text-muted" style={{ lineHeight: 1.7 }}>
                  💬 {improvement.explanation}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
