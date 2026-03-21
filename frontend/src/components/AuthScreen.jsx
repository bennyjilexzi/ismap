import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import client from '../api/client'

export default function AuthScreen({ initialTab = 'login' }) {
  const { login } = useAuth()
  const [tab, setTab] = useState(initialTab === 'signup' ? 'signup' : 'login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [isSuccess, setIsSuccess] = useState(false)

  const handleLogin = async (e) => {
  e.preventDefault()
  setMessage('')
  try {
    const { data } = await client.post('/api/login', { email, password })
    // Store token in localStorage explicitly
    if (data.token) localStorage.setItem('token', data.token)
    if (data.is_admin !== undefined) localStorage.setItem('isAdmin', data.is_admin)
    if (data.username) localStorage.setItem('username', data.username)
    login(data)   // your context login
  } catch {
    setMessage('Invalid credentials')
    setIsSuccess(false)
  }
}

  const handleSignup = async (e) => {
    e.preventDefault()
    setMessage('')
    try {
      await client.post('/api/register', { username, email, password })
      setMessage('Account created! Please login.')
      setIsSuccess(true)
      setTab('login')
    } catch {
      setMessage('Username or email already exists')
      setIsSuccess(false)
    }
  }

  const handleSubmit = tab === 'login' ? handleLogin : handleSignup

  useEffect(() => {
    setTab(initialTab === 'signup' ? 'signup' : 'login')
  }, [initialTab])

  return (
    <div className="auth-screen">
      <div className="auth-card card">
        <h1 className="auth-title">Sign in to ISMAP</h1>
        <p className="auth-subtitle">
          Access your dashboards, scheduled scans, and alerts.
        </p>

        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${tab === 'login' ? 'active' : ''}`}
            onClick={() => { setTab('login'); setMessage('') }}
          >
            Login
          </button>
          <button
            type="button"
            className={`auth-tab ${tab === 'signup' ? 'active' : ''}`}
            onClick={() => { setTab('signup'); setMessage('') }}
          >
            Sign Up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {tab === 'signup' && (
            <div className="auth-field">
              <label className="label" htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                required={tab === 'signup'}
              />
            </div>
          )}
          <div className="auth-field">
            <label className="label" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
          </div>
          <div className="auth-field">
            <label className="label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          <button type="submit" className="auth-submit">
            {tab === 'login' ? 'Login' : 'Sign Up'}
          </button>
          {message && (
            <div className={`alert ${isSuccess ? 'success' : 'error'}`}>
              {message}
            </div>
          )}
        </form>
      </div>

      <style>{`
        .auth-screen {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem 1.5rem;
          background: radial-gradient(circle at top, #020617 0, #020617 45%, #000000 100%);
        }
        .auth-card {
          width: 100%;
          max-width: 420px;
          position: relative;
          overflow: hidden;
        }
        .auth-card::before {
          content: '';
          position: absolute;
          inset: -1px;
          background: radial-gradient(circle at top, rgba(74, 222, 128, 0.35), transparent 55%);
          opacity: 0.8;
          mix-blend-mode: screen;
          pointer-events: none;
        }
        .auth-card > * {
          position: relative;
          z-index: 1;
        }
        .auth-title {
          margin: 0 0 0.35rem;
          font-size: 1.6rem;
          font-weight: 700;
          letter-spacing: -0.02em;
        }
        .auth-subtitle {
          margin: 0 0 1.4rem;
          color: var(--text-muted);
          font-size: 0.9rem;
        }
        .auth-tabs {
          display: flex;
          gap: 0.25rem;
          margin-bottom: 1.4rem;
          background: rgba(15, 23, 42, 0.95);
          padding: 0.25rem;
          border-radius: 999px;
        }
        .auth-tab {
          flex: 1;
          background: transparent;
          color: var(--text-muted);
          border-radius: 999px;
        }
        .auth-tab:hover {
          color: var(--text);
        }
        .auth-tab.active {
          background: #020617;
          color: var(--text);
          box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.4);
        }
        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        .auth-field {
          display: flex;
          flex-direction: column;
          gap: 0.35rem;
        }
        .auth-submit {
          margin-top: 0.5rem;
          padding: 0.75rem;
          font-size: 1rem;
          background: linear-gradient(90deg, #22c55e, #4ade80);
          color: #020617;
          font-weight: 600;
        }
      `}</style>
    </div>
  )
}
