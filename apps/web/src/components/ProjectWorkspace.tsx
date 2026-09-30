import { useEffect, useRef, useState, type FormEvent } from 'react';
import { request, message, type Project, type Document, type Job, type Member, type Audit, type Page } from '../api/client';

const labels: Record<string, string> = {
  queued: 'Waiting for worker', running: 'Checking stored copy', succeeded: 'Stored copy verified', failed: 'Check failed', cancelled: 'Cancelled',
};
export function ProjectWorkspace({ id }: { id: string }) {
  const base = `/projects/${id}/`;
  const [project, setProject] = useState<Project>();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [events, setEvents] = useState<Audit[]>([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [username, setUsername] = useState('');
  const [role, setRole] = useState<Member['role']>('viewer');
  const uploadInput = useRef<HTMLInputElement>(null);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    const controller = new AbortController();
    async function load() {
      try {
        const [p, docs, work, team, audit] = await Promise.all([
          request<Project>(base, { signal: controller.signal }),
          request<Page<Document>>(base + 'documents/', { signal: controller.signal }),
          request<Page<Job>>(base + 'jobs/', { signal: controller.signal }),
          request<Member[]>(base + 'members/', { signal: controller.signal }),
          request<Page<Audit>>(base + 'audit/', { signal: controller.signal }),
        ]);
        if (!controller.signal.aborted) { setProject(p); setDocuments(docs.results); setJobs(work.results); setMembers(team); setEvents(audit.results); }
      } catch (e) { if (!controller.signal.aborted) { setError(message(e)); setProject(undefined); } }
    }
    void load();
    return () => { mounted.current = false; controller.abort(); };
  }, [base]);
  useEffect(() => {
    if (!jobs.some(j => j.state === 'queued' || j.state === 'running')) return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      request<Page<Job>>(base + 'jobs/', { signal: controller.signal }).then(p => { if (!controller.signal.aborted) setJobs(p.results); })
        .catch(e => { if (!controller.signal.aborted) setError(message(e)); });
    }, 2000);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [jobs, base]);
  async function refresh() {
    const [docs, work, team, audit] = await Promise.all([
      request<Page<Document>>(base + 'documents/'), request<Page<Job>>(base + 'jobs/'),
      request<Member[]>(base + 'members/'), request<Page<Audit>>(base + 'audit/'),
    ]);
    if (mounted.current) { setDocuments(docs.results); setJobs(work.results); setMembers(team); setEvents(audit.results); }
  }
  async function action(operation: () => Promise<unknown>, confirmation = '') {
    setBusy(true); setError(''); setNotice('');
    try { await operation(); await refresh(); if (mounted.current) setNotice(confirmation); }
    catch (e) { if (mounted.current) setError(message(e)); }
    finally { if (mounted.current) setBusy(false); }
  }
  function upload(event: FormEvent) {
    event.preventDefault(); const file = uploadInput.current?.files?.[0];
    if (!file) return;
    if (file.size > 50 * 1024 * 1024) { setError('Choose a PDF smaller than 50 MiB.'); return; }
    const body = new FormData(); body.append('file', file);
    void action(async () => { await request(base + 'documents/', { method: 'POST', body }); if (uploadInput.current) uploadInput.current.value = ''; }, 'Source PDF stored.');
  }
  const canEdit = project?.role === 'owner' || project?.role === 'editor';
  return <>
    <a className="back-link" href="#">← All projects</a>
    {error && <p role="alert" className="notice error">{error}</p>}
    <p role="status" className="status-message">{notice}</p>
    {!project && !error && <p>Loading project…</p>}
    {project && <>
      <div className="page-heading"><div><p className="eyebrow">Project workspace</p><h1>{project.name}</h1><p>Source documents, access and activity.</p></div><span className="badge">{project.role}</span></div>
      <div className="workspace-grid"><div>
        <section className="panel" aria-labelledby="documents-title"><h2 id="documents-title">Source documents</h2>
          <p className="hint">Original PDFs stay private. Conversion and tagging will be available in a later milestone.</p>
          {canEdit && <form className="upload-form" onSubmit={upload}>
            <label htmlFor="pdf-file">Choose a PDF <span className="hint">(up to 50 MiB)</span></label>
            <input id="pdf-file" type="file" accept="application/pdf,.pdf" ref={uploadInput} required/>
            <button disabled={busy}>{busy ? 'Working…' : 'Store PDF'}</button>
          </form>}
          {documents.length === 0 && <p className="empty">No source documents yet.</p>}
          <ul className="document-list">{documents.map(doc => <li key={doc.id}>
            <div><strong>{doc.name}</strong><p className="hint">{(doc.size_bytes / 1024).toFixed(1)} KiB · {new Date(doc.created_at).toLocaleDateString('en-GB')}</p></div>
            <div className="actions"><a href={`/api/v1${base}documents/${doc.id}/download/`}>Download original</a>
              {canEdit && <button className="secondary" disabled={busy} onClick={() => void action(() => request(base + `documents/${doc.id}/verify/`, {
                method: 'POST', body: JSON.stringify({ operation_id: crypto.randomUUID() }),
              }), 'Verification queued.')}>Verify stored copy</button>}
            </div>
          </li>)}</ul>
        </section>
        <section className="panel" aria-labelledby="jobs-title"><h2 id="jobs-title">Document checks</h2>
          <p className="hint">These checks confirm the stored bytes match the upload. They do not validate accounts or filing eligibility.</p>
          {jobs.length === 0 && <p>No checks requested yet.</p>}
          <ul className="job-list">{jobs.map(job => <li key={job.id}>
            <div><strong>{documents.find(d => d.id === job.document_id)?.name ?? 'Source document'}</strong><p className={`job-state ${job.state}`}>{labels[job.state]}</p>
              {job.state === 'running' && <progress aria-label="Document verification progress" value={job.progress} max={100}/>}
              {job.state === 'failed' && <p className="hint">The check could not confirm this stored copy. Contact your administrator before using it.</p>}
            </div>
            {canEdit && (job.state === 'queued' || job.state === 'running') && <button className="secondary" disabled={busy || job.cancel_requested} onClick={() => void action(() => request(base + `jobs/${job.id}/cancel/`, { method: 'POST' }))}>{job.cancel_requested ? 'Cancellation requested' : 'Cancel check'}</button>}
          </li>)}</ul>
        </section>
      </div><aside>
        <section className="panel" aria-labelledby="team-title"><h2 id="team-title">Project team</h2>
          <p className="hint">The owner manages access. Editors can add documents; other roles can view this workspace.</p>
          <ul className="team-list">{members.map(member => <li key={member.user_id}><span><strong>{member.username}</strong><span className="hint"> · {member.role}</span></span>
            {project.role === 'owner' && <button className="text-button" disabled={busy} aria-label={`Remove ${member.username}`} onClick={() => void action(() => request(base + `members/${member.user_id}/`, { method: 'DELETE' }))}>Remove</button>}
          </li>)}</ul>
          {project.role === 'owner' && <form onSubmit={e => { e.preventDefault(); void action(async () => { await request(base + 'members/', { method: 'POST', body: JSON.stringify({ username, role }) }); setUsername(''); }, 'Project access updated.'); }}>
            <label htmlFor="member-name">Account username</label><input id="member-name" value={username} onChange={e => setUsername(e.target.value)} required maxLength={150}/>
            <label htmlFor="member-role">Project role</label><select id="member-role" value={role} onChange={e => setRole(e.target.value as Member['role'])}>
              <option value="viewer">Viewer</option><option value="editor">Editor</option><option value="reviewer">Reviewer</option><option value="filer">Filer</option>
            </select><button disabled={busy || !username.trim()}>Save access</button>
          </form>}
        </section>
        <section className="panel" aria-labelledby="activity-title"><h2 id="activity-title">Recent activity</h2>
          <ol className="activity-list">{events.slice(0, 12).map(event => <li key={event.id}><strong>{event.operation.replaceAll('.', ' ').replaceAll('_', ' ')}</strong>
            <p className="hint">{event.actor ?? 'System'} · {new Date(event.created_at).toLocaleString('en-GB')}</p></li>)}</ol>
        </section>
      </aside></div>
    </>}
  </>;
}
