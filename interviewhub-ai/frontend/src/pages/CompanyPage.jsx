import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowRight, Bookmark, Building2, ExternalLink, Search, ShieldCheck } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import { companyApi } from '../services/api';

const resourcesUrl = import.meta.env.VITE_PLACEMENT_RESOURCES_URL || 'https://drive.google.com/drive/u/0/folders/1NC5wLHUMUye5_5zHzSgTgXDUdVmh43ZU';
const missing = 'This information could not be verified from available sources.';

export default function CompanyPage() {
  const { companyId } = useParams(); const navigate = useNavigate();
  const [query, setQuery] = useState(''); const [companies, setCompanies] = useState([]); const [data, setData] = useState(null);
  const [bookmarks, setBookmarks] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [notice, setNotice] = useState('');
  async function loadSearch(term = query) { setLoading(true); setError(''); try { const result = await companyApi.list(term); setCompanies(result.companies); setNotice(result.research_status || ''); } catch (e) { setError(e.message); } finally { setLoading(false); } }
  async function loadDetail(id = companyId) { if (!id) { setData(null); return; } setLoading(true); setError(''); try { setData(await companyApi.get(id)); } catch (e) { setData(null); setError(e.message); } finally { setLoading(false); } }
  async function loadBookmarks() { try { setBookmarks(await companyApi.bookmarks()); } catch { setBookmarks([]); } }
  useEffect(() => { loadSearch(''); loadBookmarks(); }, []);
  useEffect(() => { loadDetail(); }, [companyId]);
  async function toggleBookmark(company) { try { const saved = bookmarks.some((x) => x.id === company.id); if (saved) await companyApi.unbookmark(company.id); else await companyApi.bookmark(company.id); await loadBookmarks(); } catch (e) { setError(e.message); } }
  const selected = data?.company;
  return <div className="dashboard-content company-page">
    <PageHeader eyebrow="COMPANY INTELLIGENCE" title="Prepare with better context" description="Explore source-backed company information and practice from verified facts."/>
    <form className="company-search" onSubmit={(e) => { e.preventDefault(); loadSearch(); }}><Search size={18}/><input aria-label="Search company" placeholder="Search company..." value={query} onChange={(e) => setQuery(e.target.value)}/><button className="button button-primary">Search</button></form>
    {error && <div className="company-message error" role="alert">{error}<button onClick={() => companyId ? loadDetail() : loadSearch()}>Retry</button></div>}
    {loading && <p role="status" className="company-muted">Loading company information…</p>}
    {!companyId && !loading && <>
      <p className="company-muted">{notice || 'Company research is temporarily unavailable.'} Search previously saved companies or use your placement materials.</p>
      {companies.length ? <section className="company-card"><h2>Available company records</h2><div className="company-list">{companies.map((c) => <div key={c.id} className="company-row"><Building2/><Link to={`/company/${c.id}`}><strong>{c.name}</strong><small>{c.industry || missing}</small></Link><button aria-label="Bookmark company" onClick={() => toggleBookmark(c)}><Bookmark size={17}/></button></div>)}</div></section> : <section className="company-empty"><Building2/><h2>{query ? 'No company information was found for this search.' : 'Search for a company to begin your preparation.'}</h2><p>No company records are currently available. Facts will appear here only after source-backed information is added.</p></section>}
      {bookmarks.length > 0 && <section className="company-card"><h2>My saved companies</h2><div className="company-list">{bookmarks.map((c) => <div className="company-row" key={c.id}><Bookmark/><Link to={`/company/${c.id}`}><strong>{c.name}</strong><small>{c.industry || missing}</small></Link></div>)}</div></section>}
      <a className="placement-link" href={resourcesUrl} target="_blank" rel="noreferrer"><ExternalLink size={16}/> Open placement preparation materials</a>
    </>}
    {selected && <>
      <section className="company-hero company-card"><span className="company-icon"><Building2/></span><div><span className="eyebrow">COMPANY PROFILE</span><h2>{selected.name}</h2><p>{selected.industry || missing}{selected.headquarters ? ` · ${selected.headquarters}` : ''}</p></div><button className="button button-secondary" onClick={() => toggleBookmark(selected)}><Bookmark size={16}/>{bookmarks.some((x) => x.id === selected.id) ? 'Saved' : 'Save company'}</button></section>
      <div className="company-grid"><section className="company-card"><h2>Overview</h2><dl className="company-facts"><div><dt>Industry</dt><dd>{selected.industry || missing}</dd></div><div><dt>Founded</dt><dd>{selected.founded_year || missing}</dd></div><div><dt>Headquarters</dt><dd>{selected.headquarters || missing}</dd></div><div><dt>Website</dt><dd>{selected.website ? <a href={selected.website} target="_blank" rel="noreferrer">Official website <ExternalLink size={13}/></a> : missing}</dd></div></dl><p>{selected.description || missing}</p></section>
      <section className="company-card"><h2>Technologies</h2>{data.technologies.length ? data.technologies.map((item) => <p key={item.id}><strong>{item.technology}</strong> · {item.category} <Status value={item.source?.verification_status}/></p>) : <p>{missing}</p>}</section>
      <section className="company-card"><h2>Roles &amp; skills</h2>{data.roles.length ? data.roles.map((item) => <article key={item.id}><strong>{item.role_title}</strong><p>{item.location || 'Location unavailable'} · {item.status}</p><p>{(item.skills || []).join(', ') || missing}</p><Status value={item.source?.verification_status}/></article>) : <p>Current vacancy status could not be verified.</p>}</section>
      <section className="company-card"><h2>Public interview insights</h2>{data.interview_insights.length ? data.interview_insights.map((item) => <article key={item.id}><p>{item.process_summary}</p><Status value={item.verification_status}/></article>) : <p>{missing}</p>}<h3>Preparation prompts</h3><ul><li>Research the company’s main products or services.</li><li>Explain why you are interested in this company.</li><li>Connect your skills to a publicly documented role.</li></ul></section></div>
      <section className="company-card"><h2><ShieldCheck size={19}/> Sources</h2>{data.sources.length ? data.sources.map((s) => <article className="source-row" key={s.id}><div><a href={s.url} target="_blank" rel="noreferrer">{s.title} <ExternalLink size={13}/></a><p>{s.publisher || 'Publisher unavailable'} · {s.source_type.replaceAll('_', ' ')}</p><small>Published: {s.published_at ? new Date(s.published_at).toLocaleDateString() : 'Date unavailable'} · Retrieved: {s.retrieved_at ? new Date(s.retrieved_at).toLocaleDateString() : 'Date unavailable'}</small></div><Status value={s.verification_status}/></article>) : <p>{missing}</p>}</section>
      <section className="company-cta"><div><span className="eyebrow">COMPANY KNOWLEDGE PRACTICE</span><h2>Learn from verified company facts</h2><p>Practice prompts are generated only when verified source information is available. These are not actual interview questions.</p></div><Link className="button button-primary" to={`/company/${selected.id}/knowledge`}>Start practice <ArrowRight size={16}/></Link><button className="button button-secondary" onClick={() => navigate('/interviews/setup', { state: { companyId: selected.id } })}>Prepare with Virtual HR</button></section>
    </>}
  </div>;
}

function Status({ value }) { const label = value === 'verified' ? 'Verified' : value === 'publicly_reported' ? 'Publicly reported' : value === 'needs_verification' ? 'Needs verification' : 'Unavailable'; return <span className={`verification-pill ${value || 'unavailable'}`}>{label}</span>; }
