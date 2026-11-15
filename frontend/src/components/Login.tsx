import { FormEvent, useState } from 'react'
import { Activity, ArrowRight, ShieldCheck } from 'lucide-react'

type Props = { onLogin: (email: string, password: string) => Promise<void> }

export function Login({ onLogin }: Props) {
  const [email, setEmail] = useState('analyst@fictional.test')
  const [password, setPassword] = useState('demo-pass-01')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try { await onLogin(email, password) }
    catch (issue) { setError(issue instanceof Error ? issue.message : 'Sign-in failed') }
    finally { setBusy(false) }
  }

  return <main className="login-wrap">
    <section className="login-card">
      <div className="brand-mark"><Activity size={21} /></div>
      <div className="eyebrow">SIGNAL ATLAS · SIH26189</div>
      <h1>Intelligence, <span>in context.</span></h1>
      <p className="muted">A synthetic network analysis workspace for authorized analysts.</p>
      <form onSubmit={submit} className="login-form">
        <label>Email<input value={email} onChange={e => setEmail(e.target.value)} type="email" autoComplete="username" required /></label>
        <label>Password<input value={password} onChange={e => setPassword(e.target.value)} type="password" autoComplete="current-password" required /></label>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={busy}>{busy ? 'Signing in…' : 'Enter workspace'} <ArrowRight size={16} /></button>
      </form>
      <div className="login-note"><ShieldCheck size={15} /> Fictional data only · Analytical leads, never proof</div>
    </section>
  </main>
}
