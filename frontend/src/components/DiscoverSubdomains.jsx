import { useState, useRef } from 'react'
import client from '../api/client'

export default function DiscoverSubdomains() {
  const [scanDomain, setScanDomain] = useState('')
  const [results, setResults] = useState([])
  const [scanError, setScanError] = useState('')
  const [scanning, setScanning] = useState(false)
  const abortControllerRef = useRef(null)

  const stopScan = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setScanning(false)
    }
  }

  const handleDiscover = async (e) => {
    e.preventDefault()
    if (!scanDomain.trim()) return
    
    setScanning(true)
    setScanError('')
    setResults([])

    // Initialize AbortController
    abortControllerRef.current = new AbortController()

    const baseUrl = client.defaults.baseURL === '/' ? '' : client.defaults.baseURL;
    try {
      const response = await fetch(`${baseUrl}/api/discover/${encodeURIComponent(scanDomain.trim())}`, {
        signal: abortControllerRef.current.signal,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep the last partial line

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine.startsWith('data: ')) {
            try {
              const result = JSON.parse(trimmedLine.substring(6));
              if (result.error) {
                setScanError(result.error);
              } else if (result.keepalive) {
                // ignore SSE keepalive heartbeat
              } else {
                setResults((prev) => {
                  // Ensure no duplicates in the stream
                  if (prev.some(r => r.subdomain === result.subdomain)) return prev;
                  return [...prev, result];
                });
              }
            } catch (parseErr) {
              console.error('Error parsing SSE data:', parseErr, trimmedLine);
            }
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log('Scan aborted by user');
      } else {
        console.error('Discovery stream error:', err);
        setScanError('Error scanning domain');
      }
    } finally {
      setScanning(false)
      abortControllerRef.current = null
    }
  }

  return (
    <div className="card">
      <div className="discover-header">
        <h2 className="section-title">Discover Subdomains</h2>
        <div className="button-group">
          {scanning ? (
            <button
              type="button"
              className="error"
              onClick={stopScan}
            >
              Stop Scan
            </button>
          ) : (
            <button
              type="button"
              className="success"
              onClick={handleDiscover}
              disabled={!scanDomain.trim()}
            >
              Start Scan
            </button>
          )}
        </div>
      </div>
      <form onSubmit={handleDiscover}>
        <div className="form-group">
          <label className="label" htmlFor="scan-domain">Domain to scan</label>
          <input
            id="scan-domain"
            type="text"
            value={scanDomain}
            onChange={(e) => setScanDomain(e.target.value)}
            placeholder="example.com"
          />
        </div>
      </form>
      {scanning && (
        <div className="progress-bar">
          <div className="progress-fill" />
        </div>
      )}
      {scanError && <div className="alert error">{scanError}</div>}
      {results.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Subdomain</th>
                <th>IP</th>
                <th>Status</th>
                <th>Vulnerabilities</th>
              </tr>
            </thead>
            <tbody>
              {results.map((row, i) => (
                <tr key={row.subdomain + i}>
                  <td><code className="cell-mono">{row.subdomain}</code></td>
                  <td><code className="cell-mono">{row.ip || '—'}</code></td>
                  <td>{row.status_code ?? '—'}</td>
                  <td>
                    {row.vulnerabilities?.length
                      ? row.vulnerabilities.map((v, j) => (
                          <span
                            key={j}
                            className={`chip ${v.severity === 'High' ? 'error' : 'warning'}`}
                          >
                            {v.name || v}
                          </span>
                        ))
                      : 'None'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <style>{`
        .section-title { margin: 0; font-size: 1.1rem; font-weight: 600; }
        .discover-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 1rem;
          margin-bottom: 1rem;
        }
        .button-group { display: flex; gap: 0.5rem; }
        .form-group { margin-bottom: 0; }
        .progress-bar {
          height: 4px;
          background: var(--bg-elevated);
          border-radius: 2px;
          overflow: hidden;
          margin: 1rem 0;
        }
        .progress-fill {
          height: 100%;
          width: 40%;
          background: var(--accent);
          animation: progress 1s ease-in-out infinite;
        }
        @keyframes progress {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(350%); }
        }
        .cell-mono {
          font-family: var(--font-mono);
          font-size: 0.85rem;
        }
      `}</style>
    </div>
  )
}
