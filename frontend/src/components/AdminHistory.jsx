import { useState, useEffect } from 'react'
import client from '../api/client'

export default function AdminHistory() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchGlobalHistory()
  }, [])

  const fetchGlobalHistory = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await client.get('/api/admin/history')
      setHistory(data)
    } catch (err) {
      setError('Failed to load global history. Are you an admin?')
    }
    setLoading(false)
  }

  const downloadReport = (scanId) => {
    // Navigate to the backend download URL directly for TXT
    const token = localStorage.getItem('token')
    const url = `${client.defaults.baseURL}/api/report/${scanId}?format=txt&token=${token}`
    window.open(url, '_blank')
  }

  if (loading) return <div className="card">Loading global history...</div>
  if (error) return <div className="card alert error">{error}</div>

  return (
    <div className="card">
      <div className="admin-header">
        <h2 className="section-title">Global Scan History (Admin)</h2>
        <button className="btn-small" onClick={fetchGlobalHistory}>Refresh</button>
      </div>
      
      {history.length === 0 ? (
        <p className="text-muted">No scans found in the system.</p>
      ) : (
        <div className="table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Domain</th>
                <th>Time</th>
                <th>Changes</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {history.map(h => (
                <tr key={h.id}>
                  <td><strong>{h.domain}</strong></td>
                  <td>{new Date(h.timestamp).toLocaleString()}</td>
                  <td>
                    <span className="delta-tag add">+{h.changes.added.length}</span>
                    <span className="delta-tag rem">-{h.changes.removed.length}</span>
                    <span className="delta-tag mod">~{h.changes.modified.length}</span>
                  </td>
                  <td>
                    <button className="btn-small outline" onClick={() => downloadReport(h.id)}>TXT</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <style>{`
        .admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
        .section-title { margin: 0; font-size: 1.1rem; }
        .table-wrap { overflow-x: auto; }
        .admin-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        .admin-table th { text-align: left; padding: 0.75rem; border-bottom: 2px solid var(--border); color: var(--text-muted); }
        .admin-table td { padding: 0.75rem; border-bottom: 1px solid var(--border); }
        .delta-tag { display: inline-block; padding: 0.1rem 0.3rem; border-radius: 4px; margin-right: 0.3rem; font-weight: 600; font-size: 0.75rem; }
        .delta-tag.add { background: rgba(0, 255, 0, 0.1); color: #00c800; }
        .delta-tag.rem { background: rgba(255, 0, 0, 0.1); color: #ff3c3c; }
        .delta-tag.mod { background: rgba(0, 0, 255, 0.1); color: #3c3cff; }
      `}</style>
    </div>
  )
}
