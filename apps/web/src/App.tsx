import { useEffect, useRef, useState, type FormEvent } from 'react';
import { message, session, signIn, signOut, type Session } from './api/client';
import { Preferences } from './components/Preferences';
import { Projects } from './components/Projects';
import { ProjectWorkspace } from './components/ProjectWorkspace';

function projectFromHash() { return /^#project\/([0-9a-f-]{36})$/.exec(location.hash)?.[1]; }
export default function App() {
  const [current, setCurrent] = useState<Session | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [projectId, setProjectId] = useState(projectFromHash);
  const main = useRef<HTMLElement>(null);
  useEffect(() => { let active = true; session().then(value => { if (active) setCurrent(value); }).catch(e => { if (active) setError(message(e)); }); return () => { active = false; }; }, []);
  useEffect(() => {
    const changed = () => { setProjectId(projectFromHash()); window.setTimeout(() => main.current?.focus(), 0); };
    window.addEventListener('hashchange', changed); return () => window.removeEventListener('hashchange', changed);
  }, []);
  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('');
    const data = new FormData(event.currentTarget);
    try { setCurrent(await signIn(String(data.get('username')), String(data.get('password')))); }
    catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  async function logout() {
    setBusy(true); setError('');
    try { await signOut(); setCurrent(await session()); location.hash = ''; }
    catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <><a className="skip-link" href="#main" onClick={event => { event.preventDefault(); main.current?.focus(); }}>Skip to main content</a>
    <header className="topbar"><a className="brand" href="#" aria-label="Tagger home"><span aria-hidden="true" className="brand-mark">t</span>Tagger</a>
      <span className="workspace-label">Private workspace</span>
      {current?.user && <nav aria-label="Account"><Preferences key={current.user.id} userId={current.user.id}/><span>{current.user.username}</span><button className="secondary" onClick={logout} disabled={busy}>Sign out</button></nav>}
    </header>
    <main id="main" ref={main} tabIndex={-1}>
      {error && <p role="alert" className="notice error">{error}</p>}
      {!current && !error && <p role="status">Opening your workspace…</p>}
      {current && !current.user && <section className="login-panel panel"><p className="eyebrow">Welcome to Tagger</p><h1>Sign in to your workspace</h1>
        <p>Your projects and source reports are available only to their project team.</p>
        <form onSubmit={login}><label htmlFor="username">Username</label><input id="username" name="username" autoComplete="username" required/>
          <label htmlFor="password">Password</label><input id="password" name="password" type="password" autoComplete="current-password" required/>
          <button disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button></form>
        <p className="hint">Ask your administrator if you need an account.</p>
      </section>}
      {current?.user && (projectId ? <ProjectWorkspace key={`${current.user.id}:${projectId}`} id={projectId}/> : <Projects key={current.user.id}/>)}
    </main><footer>Tagger · A private home for your reporting projects</footer>
  </>;
}
