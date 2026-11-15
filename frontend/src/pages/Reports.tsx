import { FormEvent, useEffect, useState } from 'react'
import { Download, FileText, Plus } from 'lucide-react'
import { api, downloadReport } from '../services/api'
import type { Report } from '../types'

export function Reports() {
  const [reports, setReports] = useState<Report[]>([])
  const [title, setTitle] = useState('Synthetic network review')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function load() { setReports(await api<Report[]>('/reports')) }
  useEffect(() => { load().catch(issue => setError(String(issue))) }, [])
  async function create(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('')
    try { await api<Report>('/reports/generate', { method: 'POST', body: JSON.stringify({ title, entity_ids: [] }) }); await load() }
    catch (issue) { setError(issue instanceof Error ? issue.message : 'Report generation failed') }
    finally { setBusy(false) }
  }
  return <div className="page-stack">
    <div className="page-heading"><div><div className="eyebrow">ANALYSIS OUTPUTS</div><h1>Investigation reports</h1><p className="muted">Create downloadable summaries of synthetic network analysis.</p></div><div className="dataset-badge"><FileText size={14} /> {reports.length} SAVED REPORTS</div></div>
    <div className="disclaimer"><FileText size={16} /><span>Reports contain fictional data, statistical summaries, and explicit limitations. Review before sharing.</span></div>
    <form className="panel create-report" onSubmit={create}><div><div className="eyebrow">NEW REPORT</div><h2>Generate a summary</h2><p className="muted">Includes network statistics, anomaly findings, and caveats.</p></div><div className="report-create-actions"><input value={title} onChange={e => setTitle(e.target.value)} aria-label="Report title" maxLength={160} required /><button className="primary" disabled={busy}><Plus size={16} />{busy ? 'Generating…' : 'Generate report'}</button></div></form>
    {error && <div className="error-panel">{error}</div>}
    <section className="panel reports-list"><div className="panel-head"><div><div className="eyebrow">ARCHIVE</div><h2>Recent reports</h2></div></div>
      {reports.length ? reports.map(report => <article className="report-row" key={report.reference_id}><div className="report-icon"><FileText size={17} /></div><div className="report-description"><b>{report.title}</b><span>{report.reference_id} · {new Date(report.created_at).toLocaleString()}</span></div><div className="report-stats">{report.network_summary.entity_count} entities · {report.anomaly_findings.length} signals</div><div className="report-downloads"><button title="Download detailed CSV bundle" className="icon-btn" onClick={() => downloadReport(report.reference_id, 'csv').catch(issue => setError(String(issue)))}><Download size={15} /><small>CSV bundle</small></button><button title="Download detailed PDF report" className="icon-btn" onClick={() => downloadReport(report.reference_id, 'pdf').catch(issue => setError(String(issue)))}><Download size={15} /><small>PDF report</small></button></div></article>) : <div className="empty-state roomy">No reports yet. Generate a synthetic analysis report above.</div>}
    </section>
    <div className="footer-note">All reports include the reminder that machine-generated patterns are not proof of wrongdoing.</div>
  </div>
}
