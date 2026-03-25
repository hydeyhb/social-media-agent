import { NavLink, Outlet } from 'react-router-dom'
import './Layout.css'

const navItems = [
  { to: '/', label: '📊 儀表板', end: true },
  { to: '/brand', label: '🎨 品牌人設' },
  { to: '/library', label: '📚 文案庫' },
  { to: '/generate', label: '✨ AI 生成' },
  { to: '/image', label: '🖼 圖片生文' },
  { to: '/thread', label: '🧵 長文分篇' },
  { to: '/analytics', label: '📈 數據分析' },
  { to: '/timing', label: '⏰ 最佳時段' },
  { to: '/optimize', label: '🔧 智慧優化' },
]

export default function Layout() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span>🤖</span>
          <span>Social AI</span>
        </div>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <a href="/api/docs" target="_blank" rel="noreferrer" className="nav-item">
            📖 API Docs
          </a>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
