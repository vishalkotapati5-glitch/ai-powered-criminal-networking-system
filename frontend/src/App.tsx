
import { lazy, Suspense, useState } from 'react'
import { Login } from './components/Login'
import { LandingPage } from './pages/LandingPage'
import { Shell, type Page } from './components/Shell'
import { api, setToken } from './services/api'

const Dashboard = lazy(() =>
  import('./pages/Dashboard').then(module => ({ default: module.Dashboard }))
)
const NetworkExplorer = lazy(() =>
  import('./pages/NetworkExplorer').then(module => ({ default: module.NetworkExplorer }))
)
const Investigation = lazy(() =>
  import('./pages/Investigation').then(module => ({ default: module.Investigation }))
)
const Anomalies = lazy(() =>
  import('./pages/Anomalies').then(module => ({ default: module.Anomalies }))
)
const Reports = lazy(() =>
  import('./pages/Reports').then(module => ({ default: module.Reports }))
)
const Settings = lazy(() =>
  import('./pages/Settings').then(module => ({ default: module.Settings }))
)

export default function App() {
  const [authenticated, setAuthenticated] = useState(
    Boolean(localStorage.getItem('access_token'))
  )
  const [showLogin, setShowLogin] = useState(false)
  const [page, setPage] = useState<Page>('overview')

  async function login(email: string, password: string) {
    const result = await api<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })

    setToken(result.access_token)
    setAuthenticated(true)
    setShowLogin(false)
    setPage('overview')
  }

  function logout() {
    setToken(null)
    setAuthenticated(false)
    setShowLogin(false)
    setPage('overview')
  }

  if (!authenticated) {
    if (showLogin) {
      return (
        <>
          <button
            className="landing-back-button"
            onClick={() => setShowLogin(false)}
          >
            ← Back to homepage
          </button>
          <Login onLogin={login} />
        </>
      )
    }

    return <LandingPage onExplore={() => setShowLogin(true)} />
  }

  return (
    <Shell page={page} setPage={setPage} onLogout={logout}>
      <Suspense fallback={<div className="loading">Loading workspace…</div>}>
        {page === 'overview' && <Dashboard />}
        {page === 'network' && <NetworkExplorer />}
        {page === 'investigation' && <Investigation />}
        {page === 'anomalies' && <Anomalies />}
        {page === 'reports' && <Reports />}
        {page === 'settings' && <Settings />}
      </Suspense>
    </Shell>
  )
}
