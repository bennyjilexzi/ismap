import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Layout({ children, username, isAdmin }) {
  const { logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="layout">
      <header className="layout-header">
        <h1 className="layout-title">ISMAP</h1>
        <span className="layout-subtitle">Subdomain &amp; Vulnerability Scanner</span>
        <div className="layout-actions">
          <span className="layout-user">
            {username}
            {isAdmin && <span className="layout-badge">Admin</span>}
          </span>
          <div className="layout-menu-wrap">
            <button
              type="button"
              className="layout-menu-btn"
              onClick={() => setMenuOpen((o) => !o)}
              aria-expanded={menuOpen}
              aria-haspopup="true"
            >
              Account ▾
            </button>
            {menuOpen && (
              <>
                <div
                  className="layout-menu-backdrop"
                  onClick={() => setMenuOpen(false)}
                  aria-hidden="true"
                />
                <div className="layout-menu card">
                  <div className="layout-menu-item static">
                    Logged in as <strong>{username}</strong>
                  </div>
                  <button
                    type="button"
                    className="layout-menu-item button"
                    onClick={() => { logout(); setMenuOpen(false); }}
                  >
                    Logout
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="layout-main">
        {children}
      </main>

      <style>{`
        .layout {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }
        .layout-header {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 1rem;
          padding: 1rem 1.5rem;
          background: var(--bg-elevated);
          border-bottom: 1px solid var(--border);
        }
        .layout-title {
          margin: 0;
          font-size: 1.35rem;
          font-weight: 700;
          letter-spacing: -0.02em;
        }
        .layout-subtitle {
          color: var(--text-muted);
          font-size: 0.9rem;
        }
        .layout-actions {
          margin-left: auto;
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        .layout-user {
          color: var(--text-muted);
          font-size: 0.9rem;
        }
        .layout-badge {
          margin-left: 0.5rem;
          padding: 0.15rem 0.5rem;
          font-size: 0.7rem;
          font-weight: 600;
          background: var(--accent);
          color: #fff;
          border-radius: 6px;
        }
        .layout-menu-wrap {
          position: relative;
        }
        .layout-menu-btn {
          background: var(--bg-card);
          color: var(--text);
          border: 1px solid var(--border);
        }
        .layout-menu-backdrop {
          position: fixed;
          inset: 0;
          z-index: 10;
        }
        .layout-menu {
          position: absolute;
          right: 0;
          top: calc(100% + 0.5rem);
          min-width: 200px;
          z-index: 20;
          padding: 0.5rem;
        }
        .layout-menu-item {
          display: block;
          width: 100%;
          padding: 0.6rem 0.75rem;
          border: none;
          border-radius: 6px;
          background: none;
          color: var(--text);
          text-align: left;
          cursor: pointer;
          font-size: 0.9rem;
        }
        .layout-menu-item.static {
          cursor: default;
          color: var(--text-muted);
        }
        .layout-menu-item.button:hover {
          background: var(--bg-elevated);
        }
        .layout-main {
          flex: 1;
        }
      `}</style>
    </div>
  )
}
