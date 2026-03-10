import { useState } from 'react'
import client from '../api/client'

export default function ScanHistory() {
  const [historyDomain, setHistoryDomain] = useState('')
  const [history, setHistory] = useState([])
  const [historyError, setHistoryError] = useState('')
  const [loading, setLoading] = useState(false)

  const loadHistory = async (e) => {
    e.preventDefault()
    if (!historyDomain.trim()) return
    setLoading(true)
    setHistoryError('')
    setHistory([])
    try {
      const { data } = await client.get(`/api/history/${encodeURIComponent(historyDomain.trim())}`)
      setHistory(Array.isArray(data) ? data : [])
    } catch {
      setHistoryError('Error loading history')
    }
    setLoading(false)
  }

  return (
    <div className="card">
      <h2 className="section-title">Scan History</h2>
      <form onSubmit={loadHistory}>
        <div className="form-group">
          <label className="label" htmlFor="history-domain">Domain</label>
          <input
            id="history-domain"
            type="text"
            value={historyDomain}
            onChange={(e) => setHistoryDomain(e.target.value)}
            placeholder="example.com"
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Loading…' : 'Load History'}
        </button>
      </form>
      {historyError && <div className="alert error">{historyError}</div>}
      {history.length > 0 && (
        <ul className="history-list">
          {history.map((h) => (
            <li key={h.id} className="history-item">
              <strong>{h.timestamp}</strong>
              {h.changes?.new?.length != null && (
                <span className="history-delta">+{h.changes.new.length} new</span>
              )}
            </li>
          ))}
        </ul>
      )}

      <style>{`
        .section-title { margin: 0 0 1rem; font-size: 1.1rem; font-weight: 600; }
        .form-group { margin-bottom: 1rem; }
        .history-list {
          list-style: none;
          padding: 0;
          margin: 1rem 0 0;
          border-top: 1px solid var(--border);
          padding-top: 1rem;
        }
        .history-item {
          padding: 0.5rem 0;
          border-bottom: 1px solid var(--border);
          font-size: 0.9rem;
        }
        .history-item:last-child { border-bottom: none; }
        .history-delta { color: var(--success); margin-left: 0.5rem; }
      `}</style>
    </div>
  )
}
