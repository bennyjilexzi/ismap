import { useState } from 'react'
import client from '../api/client'

export default function RegisterDomain() {
  const [newDomain, setNewDomain] = useState('')
  const [scanInterval, setScanInterval] = useState(6)
  const [message, setMessage] = useState('')
  const [isSuccess, setIsSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleRegister = async (e) => {
    e.preventDefault()
    if (!newDomain.trim()) return
    setLoading(true)
    setMessage('')
    try {
      await client.post(`/api/register/${encodeURIComponent(newDomain.trim())}`, { interval: scanInterval });
      setMessage('Domain registered!')
      setIsSuccess(true)
    } catch (err) {

      if (err.response && err.response.data && err.response.data.message) {
        setMessage(err.response.data.message)
      } else {
        setMessage('Error registering domain')
      }
      setIsSuccess(false)
    }
    setLoading(false)
  }

  return (
    <div className="card">
      <h2 className="section-title">Register Domain</h2>
      <form onSubmit={handleRegister}>
        <div className="form-group">
          <label className="label" htmlFor="register-domain">Domain (e.g. example.com)</label>
          <input
            id="register-domain"
            type="text"
            value={newDomain}
            onChange={(e) => setNewDomain(e.target.value)}
            placeholder="example.com"
          />
        </div>
        <div className="form-group">
          <label className="label" htmlFor="scan-interval">Scan every (hours)</label>
          <select
            id="scan-interval"
            value={scanInterval}
            onChange={(e) => setScanInterval(Number(e.target.value))}
          >
            {[1, 6, 12, 24, 48].map((h) => (
              <option key={h} value={h}>{h} hour{h !== 1 ? 's' : ''}</option>
            ))}
          </select>
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Registering…' : 'Register'}
        </button>
        {message && (
          <div className={`alert ${isSuccess ? 'success' : 'error'}`}>{message}</div>
        )}
      </form>

      <style>{`
        .section-title {
          margin: 0 0 1rem;
          font-size: 1.1rem;
          font-weight: 600;
        }
        .form-group {
          margin-bottom: 1rem;
        }
      `}</style>
    </div>
  )
}
