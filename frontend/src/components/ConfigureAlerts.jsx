import { useState } from 'react'
import client from '../api/client'

const initialConfig = {
  slack_webhook: '',
  telegram_bot_token: '',
  telegram_chat_id: ''
}

export default function ConfigureAlerts() {
  const [alertConfig, setAlertConfig] = useState(initialConfig)
  const [message, setMessage] = useState('')
  const [isSuccess, setIsSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  const update = (key, value) => {
    setAlertConfig((c) => ({ ...c, [key]: value }))
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      await client.post('/configure_alerts', alertConfig)
      setMessage('Settings saved!')
      setIsSuccess(true)
    } catch {
      setMessage('Error saving settings')
      setIsSuccess(false)
    }
    setLoading(false)
  }

  return (
    <div className="card">
      <h2 className="section-title">Configure Alerts</h2>
      <form onSubmit={handleSave}>
        <div className="form-group">
          <label className="label" htmlFor="slack-webhook">Slack Webhook URL</label>
          <input
            id="slack-webhook"
            type="url"
            value={alertConfig.slack_webhook}
            onChange={(e) => update('slack_webhook', e.target.value)}
            placeholder="https://hooks.slack.com/..."
          />
        </div>
        <div className="form-group">
          <label className="label" htmlFor="telegram-token">Telegram Bot Token</label>
          <input
            id="telegram-token"
            type="text"
            value={alertConfig.telegram_bot_token}
            onChange={(e) => update('telegram_bot_token', e.target.value)}
            placeholder="Bot token"
          />
        </div>
        <div className="form-group">
          <label className="label" htmlFor="telegram-chat">Telegram Chat ID</label>
          <input
            id="telegram-chat"
            type="text"
            value={alertConfig.telegram_chat_id}
            onChange={(e) => update('telegram_chat_id', e.target.value)}
            placeholder="Chat ID"
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Saving…' : 'Save Settings'}
        </button>
        {message && (
          <div className={`alert ${isSuccess ? 'success' : 'error'}`}>{message}</div>
        )}
      </form>

      <style>{`
        .section-title { margin: 0 0 1rem; font-size: 1.1rem; font-weight: 600; }
        .form-group { margin-bottom: 1rem; }
      `}</style>
    </div>
  )
}
