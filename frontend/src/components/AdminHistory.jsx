import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import client from '../api/client'

export default function AdminHistory() {
  const { user } = useAuth()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    if (user?.isAdmin) {
      fetchGlobalHistory()
    }
  }, [user])

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
    const baseUrl = client.defaults.baseURL === '/' ? '' : client.defaults.baseURL;
    const url = `${baseUrl}/api/report/${scanId}?format=txt&token=${token}`
    window.open(url, '_blank')
  }

  if (!user?.isAdmin) return null

  return (
    <div className="card admin-card">
      <div className="admin-header" onClick={() => setIsOpen(!isOpen)} style={{ cursor: 'pointer' }}>
        <h2 className="section-title">
          {isOpen ? '▼' : '▶'} Global Scan History (Admin)
        </h2>
        <div className="admin-actions">
          <button 
            className="btn-small refresh-btn" 
            onClick={(e) => { e.stopPropagation(); fetchGlobalHistory(); }}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>
      
      {isOpen && (
        <div className="admin-content animate-fade-in">
          {error && <div className="alert error">{error}</div>}
          
          {history.length === 0 ? (
            <p className="text-muted">No scans found in the system. Start a scan to see it here.</p>
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
                        <span className="delta-tag add">+{h.changes.added?.length || 0}</span>
                        <span className="delta-tag rem">-{h.changes.removed?.length || 0}</span>
                        <span className="delta-tag mod">~{h.changes.modified?.length || 0}</span>
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
        </div>
      )}

      <style>{`
        .admin-card { border-left: 4px solid var(--primary); }
        .admin-header { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; }
        .admin-actions { display: flex; gap: 0.5rem; }
        .section-title { margin: 0; font-size: 1.1rem; user-select: none; }
        .admin-content { margin-top: 1.5rem; border-top: 1px solid var(--border); padding-top: 1rem; }
        .table-wrap { overflow-x: auto; }
        .admin-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        .admin-table th { text-align: left; padding: 0.75rem; border-bottom: 2px solid var(--border); color: var(--text-muted); }
        .admin-table td { padding: 0.75rem; border-bottom: 1px solid var(--border); }
        .delta-tag { display: inline-block; padding: 0.1rem 0.3rem; border-radius: 4px; margin-right: 0.3rem; font-weight: 600; font-size: 0.75rem; }
        .delta-tag.add { background: rgba(0, 255, 0, 0.1); color: #00c800; }
        .delta-tag.rem { background: rgba(255, 0, 0, 0.1); color: #ff3c3c; }
        .delta-tag.mod { background: rgba(0, 0, 255, 0.1); color: #3c3cff; }
        .animate-fade-in { animation: fadeIn 0.3s ease-in; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  )
}
