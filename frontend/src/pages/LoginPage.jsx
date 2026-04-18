import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'
import api from '../api/client'
import './LoginPage.css'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('username', username)
      params.append('password', password)
      const { data } = await api.post('/admin/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      login(data.access_token)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || '登入失敗，請重試')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-logo">
          <span>🤖</span>
          <span>Social AI</span>
        </div>
        <p className="login-subtitle">管理員登入</p>
        {error && <div className="login-error">{error}</div>}
        <input
          type="text"
          placeholder="帳號"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoFocus
          required
        />
        <input
          type="password"
          placeholder="密碼"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? '登入中...' : '登入'}
        </button>
      </form>
    </div>
  )
}
