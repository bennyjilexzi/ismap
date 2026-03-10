import { useState } from 'react'
import client from '../api/client'

export default function ExportReport() {
  const [exportDomain, setExportDomain] = useState('')
  const [exportError, setExportError] = useState('')
  const [exporting, setExporting] = useState(false)

  const handleExport = async (e) => {
    e.preventDefault()
    if (!exportDomain.trim()) return
    setExporting(true)
    setExportError('')
    try {
      const { data } = await client.get(`/api/export/${encodeURIComponent(exportDomain.trim())}`)
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${exportDomain.trim()}_report.json`
      a.click()
      URL.revokeObjectURL(url)
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
        <button type="submit" className="warning" disabled={exporting}>
          {exporting ? 'Exporting…' : 'Download JSON'}
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
