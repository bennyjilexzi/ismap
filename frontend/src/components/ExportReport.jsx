import { useState } from 'react'
import client from '../api/client'

export default function ExportReport() {
  const [exportDomain, setExportDomain] = useState('')
  const [exportError, setExportError] = useState('')
  const [exporting, setExporting] = useState(false)

  const [format, setFormat] = useState('json')

  const handleExport = async (e) => {
    e.preventDefault()
    if (!exportDomain.trim()) return
    setExporting(true)
    setExportError('')
    try {
      if (format === 'txt') {
        const token = localStorage.getItem('token')
        // For TXT we use the report endpoint which we know is fully formatted
        // We'll need to find the latest scan ID for this domain if we want it to be automatic
        // But for now, let's just use the export endpoint for JSON as before
        // AND add a way to get the latest scan ID
        const { data: latestScan } = await client.get(`/api/history/${encodeURIComponent(exportDomain.trim())}`)
        if (latestScan && latestScan.length > 0) {
          const scanId = latestScan[0].id
          const baseUrl = client.defaults.baseURL === '/' ? '' : client.defaults.baseURL;
          const url = `${baseUrl}/api/report/${scanId}?format=txt&token=${token}`
          window.open(url, '_blank')
        } else {
          setExportError('No scan history found for this domain.')
        }
      } else {
        const { data } = await client.get(`/api/export/${encodeURIComponent(exportDomain.trim())}`)
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${exportDomain.trim()}_report.json`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch {
      setExportError('Error exporting report')
    }
    setExporting(false)
  }

  return (
    <div className="card">
      <h2 className="section-title">Export Report</h2>
      <form onSubmit={handleExport}>
        <div className="form-group">
          <label className="label" htmlFor="export-domain">Domain</label>
          <input
            id="export-domain"
            type="text"
            value={exportDomain}
            onChange={(e) => setExportDomain(e.target.value)}
            placeholder="example.com"
          />
        </div>
        <div className="form-group">
          <label className="label">Format</label>
          <select value={format} onChange={(e) => setFormat(e.target.value)}>
            <option value="json">JSON</option>
            <option value="txt">Text (TXT)</option>
          </select>
        </div>
        <button type="submit" className="warning" disabled={exporting}>
          {exporting ? 'Exporting…' : `Download ${format.toUpperCase()}`}
        </button>
      </form>
      {exportError && <div className="alert error">{exportError}</div>}

      <style>{`
        .section-title { margin: 0 0 1rem; font-size: 1.1rem; font-weight: 600; }
        .form-group { margin-bottom: 1rem; }
      `}</style>
    </div>
  )
}
