import { useEffect, useState } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { getOverview, getTrends, getTopPerformers, syncAnalytics } from '../api/analytics'

export default function Analytics() {
  const [overview, setOverview] = useState(null)
  const [trends, setTrends] = useState([])
  const [topPosts, setTopPosts] = useState([])
  const [platform, setPlatform] = useState('')
  const [days, setDays] = useState(30)
  const [syncing, setSyncing] = useState(false)
  const [toast, setToast] = useState(null)

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 2500)
  }

  const load = async () => {
    const [ov, tr, top] = await Promise.all([
      getOverview(platform || undefined).catch(() => ({ data: null })),
      getTrends(days, platform || undefined).catch(() => ({ data: [] })),
      getTopPerformers(10, platform || undefined).catch(() => ({ data: [] })),
    ])
    setOverview(ov.data)
    setTrends(tr.data.map(r => ({ ...r, date: r.date ? r.date.slice(0, 10) : '' })))
    setTopPosts(top.data)
  }

  useEffect(() => { load() }, [platform, days])

  const handleSync = async () => {
    setSyncing(true)
    try {
      const res = await syncAnalytics()
      showToast(`同步完成！已更新 ${res.data.synced} 篇`)
    } catch {
      showToast('同步失敗', 'error')
    }
    setSyncing(false)
    load()
  }

  return (
    <div>
      <h1 className="page-title">📈 數據分析儀表板</h1>

      {/* Controls */}
      <div className="card mb-16">
        <div className="flex gap-12 flex-wrap">
          <select value={platform} onChange={e => setPlatform(e.target.value)} style={{ width: 150 }}>
            <option value="">全部平台</option>
            <option value="facebook">Facebook</option>
            <option value="threads">Threads</option>
          </select>
          <select value={days} onChange={e => setDays(Number(e.target.value))} style={{ width: 120 }}>
            <option value={7}>近 7 天</option>
            <option value={30}>近 30 天</option>
            <option value={90}>近 90 天</option>
          </select>
          <button className="btn-secondary" onClick={handleSync} disabled={syncing}>
            {syncing ? <><span className="spinner" style={{ width: 14, height: 14 }} /> 同步中...</> : '🔄 同步數據'}
          </button>
        </div>
      </div>

      {/* KPI */}
      {overview && (
        <div className="grid-4 mb-16">
          {[
            { v: overview.impressions, l: '總觸及' },
            { v: overview.likes, l: '總按讚' },
            { v: overview.comments, l: '總留言' },
            { v: overview.shares, l: '總分享' },
          ].map(({ v, l }) => (
            <div key={l} className="kpi-card">
              <div className="kpi-value">{(v || 0).toLocaleString()}</div>
              <div className="kpi-label">{l}</div>
            </div>
          ))}
        </div>
      )}

      {/* Charts */}
      <div className="grid-2 mb-16">
        <div className="card">
          <div className="section-title">觸及趨勢</div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)' }} />
              <Line type="monotone" dataKey="impressions" stroke="#6366f1" strokeWidth={2} dot={false} name="觸及" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <div className="section-title">互動分析</div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)' }} />
              <Legend wrapperStyle={{ color: 'var(--text-muted)', fontSize: 12 }} />
              <Line type="monotone" dataKey="likes" stroke="#22c55e" strokeWidth={2} dot={false} name="按讚" />
              <Line type="monotone" dataKey="comments" stroke="#f59e0b" strokeWidth={2} dot={false} name="留言" />
              <Line type="monotone" dataKey="shares" stroke="#3b82f6" strokeWidth={2} dot={false} name="分享" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Performers Table */}
      <div className="card">
        <div className="section-title">🏆 高表現貼文排行</div>
        {topPosts.length === 0 ? (
          <p className="text-muted">尚無數據，請先同步。</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                  <th style={{ textAlign: 'left', padding: '8px 0' }}>貼文內容</th>
                  <th style={{ textAlign: 'center', padding: '8px 12px' }}>平台</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px' }}>觸及</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px' }}>❤️</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px' }}>💬</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px' }}>🔁</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px' }}>互動率</th>
                </tr>
              </thead>
              <tbody>
                {topPosts.map((p, i) => (
                  <tr key={p.post_id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '10px 0', maxWidth: 300 }}>
                      <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i+1}.`} {p.content_preview}
                      </div>
                    </td>
                    <td style={{ textAlign: 'center', padding: '10px 12px' }}>
                      <span className={`tag tag-${p.platform}`}>{p.platform}</span>
                    </td>
                    <td style={{ textAlign: 'right', padding: '10px 12px' }}>{(p.impressions || 0).toLocaleString()}</td>
                    <td style={{ textAlign: 'right', padding: '10px 12px' }}>{p.likes}</td>
                    <td style={{ textAlign: 'right', padding: '10px 12px' }}>{p.comments}</td>
                    <td style={{ textAlign: 'right', padding: '10px 12px' }}>{p.shares}</td>
                    <td style={{ textAlign: 'right', padding: '10px 12px', color: 'var(--success)', fontWeight: 600 }}>
                      {(p.engagement_rate || 0).toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}
    </div>
  )
}
