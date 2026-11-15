import { Activity, AlertTriangle, FileText, GitFork, LayoutDashboard, LogOut, Search, Settings2, UserRound } from 'lucide-react'

export type Page = 'overview' | 'network' | 'investigation' | 'anomalies' | 'reports' | 'settings'

const links: Array<{ id: Page; label: string; icon: typeof LayoutDashboard }> = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'network', label: 'Network explorer', icon: GitFork },
  { id: 'investigation', label: 'Entity investigation', icon: UserRound },
  { id: 'anomalies', label: 'Pattern signals', icon: AlertTriangle },
  { id: 'reports', label: 'Reports', icon: FileText },
]

export function Shell({ page, setPage, onLogout, children }: { page: Page; setPage: (page: Page) => void; onLogout: () => void; children: React.ReactNode }) {
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark small"><Activity size={17} /></div><div><b>Signal Atlas</b><small>NETWORK INTELLIGENCE</small></div></div>
      <div className="workspace-label">WORKSPACE <span className="live-dot" /> SYNTHETIC DATA</div>
      <nav>{links.map(({ id, label, icon: Icon }) => <button key={id} onClick={() => setPage(id)} className={`nav-link ${page === id ? 'active' : ''}`}><Icon size={17} />{label}</button>)}</nav>
      <div className="sidebar-bottom">
        <button onClick={() => setPage('settings')} className={`nav-link ${page === 'settings' ? 'active' : ''}`}><Settings2 size={17} />Workspace notes</button>
        <div className="analyst"><div className="avatar">A</div><div><b>Demo analyst</b><small>Authorized session</small></div><button title="Sign out" className="icon-btn logout" onClick={onLogout}><LogOut size={16} /></button></div>
      </div>
    </aside>
    <main className="main-area">
      <header className="topbar"><div className="breadcrumb"><span>Workspace</span><span className="slash">/</span><strong>{links.find(link => link.id === page)?.label || 'Notes'}</strong></div><div className="top-meta"><span className="secure"><span className="live-dot" /> Local workspace</span><button className="icon-btn search-icon" title="Search"><Search size={17} /></button></div></header>
      <div className="page-content">{children}</div>
    </main>
  </div>
}
