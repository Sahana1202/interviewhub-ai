import { useCallback, useEffect, useRef, useState } from 'react';
import { AlertCircle, Check, FileText, LoaderCircle, LockKeyhole, Trash2, UploadCloud } from 'lucide-react';
import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import { resumeApi } from '../services/api';

const MAX_BYTES = 10 * 1024 * 1024;
const dateLabel = (value) => new Date(value).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });

export default function ResumePage() {
  const inputRef = useRef(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [dragging, setDragging] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [confirmingDelete, setConfirmingDelete] = useState(null);
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setItems(await resumeApi.list()); } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  async function chooseFile(file) {
    if (!file) return;
    setError('');
    if (!file.name.toLowerCase().endsWith('.pdf') || (file.type && file.type !== 'application/pdf')) { setError('Please upload a PDF file.'); return; }
    if (file.size > MAX_BYTES) { setError('This file is larger than the 10 MB limit.'); return; }
    setUploading(true); setProgress(0);
    try {
      const resume = await resumeApi.upload(file, (event) => event.total && setProgress(Math.round(event.loaded * 100 / event.total)));
      window.location.assign(`/resume/${resume.id}`);
    } catch (err) { setError(err.message); }
    finally { setUploading(false); }
  }
  async function remove() {
    const item=confirmingDelete;
    if (!item) return;
    setDeleting(item.id); setError('');
    try { await resumeApi.delete(item.id); setItems((current) => current.filter((entry) => entry.id !== item.id)); setConfirmingDelete(null); }
    catch (err) { setError(err.message); }
    finally { setDeleting(null); }
  }
  const onDrop = (event) => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files?.[0]); };

  return <div className="dashboard-content resume-page">
    <PageHeader eyebrow="RESUME INTELLIGENCE" title="Resume Analyzer" description="Upload your resume to understand your skills, experience, projects, and interview readiness." />
    <section className={`resume-dropzone${dragging ? ' is-dragging' : ''}`} onDragOver={(e) => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={onDrop}>
      <input ref={inputRef} type="file" accept=".pdf,application/pdf" hidden onChange={(e) => { chooseFile(e.target.files?.[0]); e.target.value = ''; }} />
      <div className="resume-upload-icon"><UploadCloud size={26}/></div>
      <h2>Upload your resume</h2><p>Drag and drop a PDF here, or choose a file from your device.</p>
      <button type="button" className="button button-primary" disabled={uploading} onClick={() => inputRef.current?.click()}>{uploading ? <><LoaderCircle className="spin" size={16}/> Uploading…</> : 'Browse files'}</button>
      <span className="resume-file-rules">Supported format: PDF · Maximum size: 10 MB</span>
      {uploading && <div className="resume-upload-progress" role="status"><span style={{ width: `${progress}%` }}/><small>{progress ? `${progress}% uploaded · extracting text…` : 'Preparing upload…'}</small></div>}
    </section>
    <p className="resume-privacy"><LockKeyhole size={15}/> Your resume is stored for your InterviewHub AI account and is used to provide resume analysis and preparation features.</p>
    {error && <div className="resume-alert" role="alert"><AlertCircle size={17}/><span>{error}</span><button type="button" onClick={load}>Retry</button></div>}
    <section className="resume-list-section"><div className="resume-list-heading"><div><span className="eyebrow">YOUR DOCUMENTS</span><h2>Previous Resumes</h2></div>{!loading && <span>{items.length} {items.length === 1 ? 'resume' : 'resumes'}</span>}</div>
      {loading ? <div className="resume-loading" role="status"><LoaderCircle className="spin"/> Loading your resumes…</div> : items.length ? <div className="resume-list">{items.map((item) => <article className="resume-list-card" key={item.id}><span className="resume-file-icon"><FileText size={19}/></span><div className="resume-list-copy"><strong>{item.file_name}</strong><small>Uploaded {dateLabel(item.created_at)} · {(item.file_size / 1024 / 1024).toFixed(2)} MB</small></div><span className={`resume-status status-${item.status}`}>{item.status === 'processed' ? <Check size={13}/> : null}{item.status}</span><Link className="text-link" to={`/resume/${item.id}`}>View</Link><button className="resume-delete" type="button" aria-label={`Delete ${item.file_name}`} disabled={deleting === item.id} onClick={() => setConfirmingDelete(item)}>{deleting === item.id ? <LoaderCircle className="spin" size={16}/> : <Trash2 size={16}/>}</button></article>)}</div> : <div className="resume-empty"><FileText size={22}/><h3>No resumes yet</h3><p>Upload a PDF to see extracted resume details and practice questions.</p></div>}
    </section>
    {confirmingDelete&&<div className="resume-dialog-backdrop"><section className="resume-delete-dialog" role="alertdialog" aria-modal="true" aria-labelledby="resume-delete-title"><h2 id="resume-delete-title">Delete this resume?</h2><p>Delete {confirmingDelete.file_name} and its stored PDF? This action cannot be undone.</p><div><button type="button" onClick={()=>setConfirmingDelete(null)} disabled={deleting===confirmingDelete.id}>Cancel</button><button type="button" className="button button-primary" onClick={remove} disabled={deleting===confirmingDelete.id}>{deleting===confirmingDelete.id?'Deleting…':'Delete resume'}</button></div></section></div>}
  </div>;
}
