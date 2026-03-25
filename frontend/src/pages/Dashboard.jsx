import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getOverview, getTopPerformers } from '../api/analytics'
import { listPosts } from '../api/posts'
import { getAuthStatus, getFacebookLoginUrl, getThreadsLoginUrl } from '../api/auth'

export default function Dashboard() {
  const [overview, setOverview] = useState(null)
  const [topPosts, setTopPosts] = useState([])
  const [upcoming, setUpcoming] = useState([])
  const [authStatus, setAuthStatus] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getOverview().catch(() => null),
      getTopPerformers(5).catch(() => []),
      listPosts({ status: 'scheduled', limit: 5 }).catch(() => ({ data: [] })),
      getAuthStatus().catch(() => ({ data: [] })),
    ]).then(([ov, top, sched, auth]) => {
      setOverview(ov?.data || null)
      setTopPosts(top?.data || [])
      setUpcoming(sched?.data || [])
      setAuthStatus(auth?.data || [])
      setLoading(false)
    })
  }, [])

  if (loading) return <div style={{ padding: 40 }}><div className="spinner" /></div>

  return (
    <div>
      <h1 className="page-title">📊 儀表板</h1>

      {/* Auth Status */}
      <div className="card mb-16">
        <div className="section-title">帳號連線狀態</div>
        <div className="flex gap-16 flex-wrap">
          {['facebook', 'threads'].map(platform => {
            const s = authStatus.find(a => a.platform === platform)
            return (
              <div key={platform} className="flex-center gap-8" style={{ background: 'var(--surface2)', padding: '10px 16px', borderRadius: 8, border: '1px solid var(--border)' }}>
                <span>{platform === 'facebook' ? '📘' : '🧵'}</span>
                <div>
                  <div style={{ fontWeight: 600 }}>{platform === 'facebook' ? 'Facebook' : 'Threads'}</div>
                  {s?.is_connected ? (
                    <div className="text-success text-small">✅ 已連線 {s.page_name && `— ${s.page_name}`} {s.days_until_expiry != null ? `(${s.days_until_expiry}天後到期)` : '(永不過期)'}</div>
                  ) : (
                    <a href={platform === 'facebook' ? getFacebookLoginUrl() : getThreadsLoginUrl()} className="text-warning text-small">
                      ⚠️ 未連線，點此授權 →
                    </a>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* KPI Cards */}
      {overview && (
        <div className="grid-4 mb-16">
          <div className="kpi-card">
            <div className="kpi-value">{overview.impressions?.toLocaleString() || 0}</div>
            <div className="kpi-label">總觸及人次</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{overview.likes?.toLocaleString() || 0}</div>
            <div className="kpi-label">總按讚數</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{overview.comments?.toLocaleString() || 0}</div>
            <div className="kpi-label">總留言數</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{(overview.avg_engagement_rate || 0).toFixed(2)}%</div>
            <div className="kpi-label">平均互動率</div>
          </div>
        </div>
      )}

      <div className="grid-2">
        {/* Top Performers */}
        <div className="card">
          <div className="section-title">🏆 近期高表現貼文</div>
          {topPosts.length === 0 ? (
            <p className="text-muted">尚無數據。發布貼文後請至「數據分析」同步數據。</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {topPosts.map((p) => (
                <div key={p.post_id} style={{ background: 'var(--surface2)', borderRadius: 8, padding: 12 }}>
                  <div style={{ marginBottom: 6 }}>{p.content_preview}...</div>
                  <div className="flex gap-8 text-small text-muted">
                    <span>❤️ {p.likes}</span>
                    <span>💬 {p.comments}</span>
                    <span>🔁 {p.shares}</span>
                    <span className="text-success">互動率 {(p.engagement_rate || 0).toFixed(2)}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Upcoming */}
        <div className="card">
          <div className="section-title">📅 即將排程發布</div>
          {upcoming.length === 0 ? (
            <p className="text-muted">目前沒有排程中的貼文。<Link to="/library">前往文案庫</Link>設定排程。</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {upcoming.map((p) => (
                <div key={p.id} style={{ background: 'var(--surface2)', borderRadius: 8, padding: 12 }}>
                  <div className="flex-between mb-8">
                    <span className={`tag tag-${p.platform}`}>{p.platform}</span>
                    <span className="text-small text-muted">
                      {p.scheduled_at ? new Date(p.scheduled_at).toLocaleString('zh-TW') : ''}
                    </span>
                  </div>
                  <div className="text-small">{p.content?.slice(0, 80)}...</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
