import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import Layout from './Layout'
import RegisterDomain from './RegisterDomain'
import ConfigureAlerts from './ConfigureAlerts'
import DiscoverSubdomains from './DiscoverSubdomains'
import ScanHistory from './ScanHistory'
import ExportReport from './ExportReport'

export default function Dashboard() {
  const { user } = useAuth()

  return (
    <Layout username={user?.username} isAdmin={user?.isAdmin}>
      <div className="dashboard-grid">
        <section className="dashboard-section">
          <RegisterDomain />
        </section>
        <section className="dashboard-section">
          <ConfigureAlerts />
        </section>
        <section className="dashboard-section full-width">
          <DiscoverSubdomains />
        </section>
        <section className="dashboard-section">
          <ScanHistory />
        </section>
        <section className="dashboard-section">
          <ExportReport />
        </section>
      </div>

      <style>{`
        .dashboard-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1.5rem;
          padding: 1.5rem;
        }
        .dashboard-section.full-width {
          grid-column: 1 / -1;
        }
        @media (max-width: 900px) {
          .dashboard-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </Layout>
  )
}
