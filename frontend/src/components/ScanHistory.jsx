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

  const downloadReport = async (scanId) => {
    try {
      const { data } = await client.get(`/api/report/${scanId}`)
      
      let text = `ISMAP Scan Report\n`
      text += `=================\n`
      text += `Domain: ${data.domain}\n`
      text += `Timestamp: ${data.timestamp}\n\n`
      
      const { added = [], removed = [], modified = [] } = data.changes || {}
      text += `Summary of Changes\n`
      text += `------------------\n`
      text += `Added: ${added.length}\n`
      added.forEach(sub => text += `  + ${sub}\n`)
      text += `Removed: ${removed.length}\n`
      removed.forEach(sub => text += `  - ${sub}\n`)
      text += `Modified: ${modified.length}\n`
      modified.forEach(m => text += `  ~ ${m.subdomain} (IP: ${m.old_ip} -> ${m.new_ip}, Status: ${m.old_status} -> ${m.new_status})\n`)
      
      text += `\nDiscovered Subdomains (${data.subdomains.length} total)\n`
      text += `---------------------------------\n`
      data.subdomains.forEach((sub, i) => {
        text += `${i + 1}. ${sub.subdomain}\n`
        text += `   IP: ${sub.ip || 'N/A'}\n`
        text += `   Status: ${sub.status_code || 'N/A'}\n`
        text += `   Title: ${sub.title || 'N/A'}\n`
        if (sub.vulnerabilities && sub.vulnerabilities.length > 0) {
          text += `   Vulnerabilities:\n`
          sub.vulnerabilities.forEach(v => {
             text += `     - [${v.severity}] ${v.name || v}\n`
          })
        } else {
          text += `   Vulnerabilities: None\n`
        }
        text += `\n`
      })
      
      const blob = new Blob([text], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `scan_report_${data.domain}_${scanId}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error(err)
      alert("Failed to download report.")
    }
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
              <div className="history-info">
                <strong>{new Date(h.timestamp).toLocaleString()}</strong>
                {h.changes?.added?.length != null && (
                  <span className="history-delta"> (+{h.changes.added.length} added)</span>
                )}
              </div>
              <button 
                className="btn-small outline" 
                onClick={() => downloadReport(h.id)}
                title="Download text report"
              >
                Download Report
              </button>
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
          padding: 0.75rem 0;
          border-bottom: 1px solid var(--border);
          font-size: 0.9rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .history-item:last-child { border-bottom: none; }
        .history-info strong { display: block; font-size: 0.95rem; }
        .history-delta { color: var(--success); font-size: 0.85rem; }
        .btn-small {
          padding: 0.4rem 0.8rem;
          font-size: 0.85rem;
          background: var(--bg-elevated);
          color: var(--text-base);
          border: 1px solid var(--border);
        }
        .btn-small:hover {
          background: var(--accent);
          color: #fff;
          border-color: var(--accent);
        }
      `}</style>
    </div>
  )
}
