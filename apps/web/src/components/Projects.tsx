import { useEffect, useState, type FormEvent } from 'react';
import { request, nextPage, message, type Page, type Project } from '../api/client';

export function Projects() {
  const [page, setPage] = useState<Page<Project>>();
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    request<Page<Project>>('/projects/', { signal: controller.signal }).then(setPage)
      .catch(e => { if (!controller.signal.aborted) setError(message(e)); });
    return () => controller.abort();
  }, []);
  async function create(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const project = await request<Project>('/projects/', { method: 'POST', body: JSON.stringify({ name }) });
      window.location.hash = `project/${project.id}`;
    } catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  async function more() {
    if (!page?.next) return;
    setBusy(true);
    try { const result = await nextPage<Project>(page.next); setPage({ ...result, results: [...page.results, ...result.results] }); }
    catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <>
    <div className="page-heading"><div><p className="eyebrow">Your workspace</p><h1>Private projects</h1>
      <p>Keep source reports and your team’s work together.</p></div><span className="count">{page?.count ?? '…'} projects</span></div>
    {error && <p role="alert" className="notice error">{error}</p>}
    <section className="panel create-project" aria-labelledby="create-title"><h2 id="create-title">Start a project</h2>
      <form onSubmit={create}><label htmlFor="project-name">Project name</label><div className="input-action">
        <input id="project-name" value={name} onChange={e => setName(e.target.value)} maxLength={200} required placeholder="Company and reporting year"/>
        <button disabled={busy || !name.trim()}>{busy ? 'Creating…' : 'Create project'}</button>
      </div><p className="hint">Only you can access a new project until you add team members.</p></form>
    </section>
    <section aria-labelledby="projects-title"><h2 id="projects-title">Your projects</h2>
      {!page && !error && <p role="status">Loading projects…</p>}
      {page?.count === 0 && <div className="empty">Your first project starts here. Add a name above to get started.</div>}
      <div className="project-grid">{page?.results.map(project => <a className="project-card" key={project.id} href={`#project/${project.id}`}>
        <span className="project-symbol" aria-hidden="true">▤</span><h3>{project.name}</h3><span className="badge">{project.role}</span>
        <p>Created {new Date(project.created_at).toLocaleDateString('en-GB')}</p><span className="open-label">Open project →</span>
      </a>)}</div>
      {page?.next && <button className="secondary" onClick={more} disabled={busy}>Load more projects</button>}
    </section>
  </>;
}
