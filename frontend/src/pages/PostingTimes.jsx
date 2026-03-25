import { useEffect, useState } from 'react'
import { getPostingTimes } from '../api/analytics'
import { getOptimalTimes } from '../api/generation'

const DAY_NAMES = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']

export default function PostingTimes() {
  const [platform, setPlatform] = useState('facebook')
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(false)
  const [aiResult, setAiResult] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)

  const load = async () => {
    setLoading(true)
    const res = await getPostingTimes(platform).catch(() => ({ data: [] }))
    setStats(res.data)
    setLoading(false)
  }
  useEffect(() => { load() }, [platform])

  // Build 7×24 grid
  const grid = {}
  stats.forEach(s => {
    grid[`${s.day_of_week}-${s.hour_of_day}`] = s.avg_engagement_rate
  })
  const maxRate = Math.max(0.001, ...stats.map(s => s.avg_engagement_rate))

  const cellColor = (rate) => {
    if (!rate) return 'rgba(255,255,255,0.02)'
    const intensity = rate / maxRate
    return `rgba(99,102,241,${0.1 + intensity * 0.8})`
  }

  const handleAiAnalysis = async () => {
    setAnalyzing(true)
    try {
      const res = await getOptimalTimes(platform, true)
      setAiResult(res.data)
    } catch (e) {
      console.error(e)
    }
    setAnalyzing(false)
  }

  return (
    <div>
      <h1 className="page-title">⏰ 智慧最佳發文時段</h1>

      <div className="card mb-16">
        <div className="flex gap-12 flex-wrap">
          <select value={platform} onChange={e => setPlatform(e.target.value)} style={{ width: 150 }}>
            <option value="facebook">Facebook</option>
            <option value="threads">Threads</option>
          </select>
          <button className="btn-primary" onClick={handleAiAnalysis} disabled={analyzing}>
            {analyzing ? <><span className="spinner" style={{ width: 14, height: 14 }} /> AI 分析中...</> : '🤖 AI 推薦最佳時段'}
          </button>
          <div className="text-small text-muted flex-center">顏色越深 = 互動率越高</div>
        </div>
      </div>

      {aiResult && (
        <div className="card mb-16" style={{ borderLeft: '3px solid var(--primary)' }}>
          <div className="section-title">🤖 AI 時段建議</div>
          {aiResult.narration && <p style={{ marginBottom: 16, lineHeight: 1.8 }}>{aiResult.narration}</p>}
          {aiResult.windows?.length > 0 && (
            <div className="flex gap-8 flex-wrap">
              {aiResult.windows.map((w, i) => (
                <div key={i} style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 16px', minWidth: 160 }}>
                  <div style={{ fontWeight: 600 }}>{w.day_name} {w.time_label}</div>
                  <div className="text-small text-muted">互動率 {(w.avg_engagement_rate || 0).toFixed(2)}% · {w.sample_count} 筆樣本</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Heatmap */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}><div className="spinner" /></div>
      ) : (
        <div className="card">
          <div className="section-title">互動率熱力圖 (週 × 時)</div>
          {stats.length === 0 ? (
            <p className="text-muted">尚無時段數據。發布並同步數據後，這裡將自動顯示熱力圖。</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'auto repeat(24, 1fr)', gap: 2, minWidth: 700 }}>
                {/* Header row */}
                <div />
                {Array.from({ length: 24 }, (_, h) => (
                  <div key={h} style={{ textAlign: 'center', fontSize: 10, color: 'var(--text-muted)', padding: '2px 0' }}>{h}</div>
                ))}
                {/* Day rows */}
                {DAY_NAMES.map((day, dow) => (
                  <>
                    <div key={`label-${dow}`} style={{ fontSize: 12, color: 'var(--text-muted)', paddingRight: 8, display: 'flex', alignItems: 'center', whiteSpace: 'nowrap' }}>{day}</div>
                    {Array.from({ length: 24 }, (_, h) => {
                      const rate = grid[`${dow}-${h}`] || 0
                      return (
                        <div
                          key={`${dow}-${h}`}
                          title={rate ? `${day} ${h}:00 — 互動率 ${rate.toFixed(2)}%` : '無數據'}
                          style={{ height: 28, borderRadius: 4, background: cellColor(rate), cursor: rate ? 'pointer' : 'default', transition: 'background 0.2s' }}
                        />
                      )
                    })}
                  </>
                ))}
              </div>
              <div className="flex gap-16 mt-16">
                <div className="flex-center gap-8 text-small text-muted">
                  <div style={{ width: 20, height: 12, borderRadius: 3, background: 'rgba(99,102,241,0.1)' }} />低互動
                </div>
                <div className="flex-center gap-8 text-small text-muted">
                  <div style={{ width: 20, height: 12, borderRadius: 3, background: 'rgba(99,102,241,0.9)' }} />高互動
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
