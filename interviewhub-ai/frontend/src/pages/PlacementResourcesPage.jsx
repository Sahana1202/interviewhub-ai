import { useCallback, useEffect, useState } from 'react';
import { ArrowRight, ExternalLink, FileText, RotateCw } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import { learningApi } from '../services/api';

const resourceCategories = ['Aptitude', 'Technical', 'HR', 'Interview', 'Coding', 'Resume', 'Communication', 'Company Preparation'];
const providedFolder = 'https://drive.google.com/drive/u/0/folders/1NC5wLHUMUye5_5zHzSgTgXDUdVmh43ZU';
const folderUrl = import.meta.env.VITE_PLACEMENT_RESOURCES_URL || providedFolder;

export default function PlacementResourcesPage() {
  const [category, setCategory] = useState(''); const [search, setSearch] = useState(''); const [appliedSearch, setAppliedSearch] = useState('');
  const [result, setResult] = useState({ resources: [], placement_source: null }); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setResult(await learningApi.resources({ ...(category ? { category } : {}), ...(appliedSearch ? { search: appliedSearch } : {}) })); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [category, appliedSearch]);
  useEffect(() => { load(); }, [load]);
  return <div className="dashboard-content learning-page"><PageHeader eyebrow="PLACEMENT PREPARATION" title="Placement Resources" description="Browse available source-labelled learning resources and the configured placement folder."/>
    <section className="placement-source-card learning-panel"><span className="learning-category-icon"><ExternalLink size={19}/></span><div><h2>Provided placement folder</h2><p>The folder opens in Google Drive. Its contents are not imported or assumed to be accessible, and Google may require sign-in.</p><small>{result.placement_source?.message || 'Placement resource import is not currently configured.'}</small></div><a className="button button-primary" href={folderUrl} target="_blank" rel="noreferrer">Open Drive folder <ExternalLink size={15}/></a></section>
    <div className="resource-category-pills" aria-label="Resource categories">{resourceCategories.map((item) => <button type="button" key={item} className={category === item ? 'selected' : ''} aria-pressed={category === item} onClick={() => setCategory(category === item ? '' : item)}>{item}</button>)}</div>
    <form className="resource-search" onSubmit={(event) => { event.preventDefault(); setAppliedSearch(search); }}><label className="learning-field">Search resources<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by title or description"/></label><button className="button button-secondary">Search</button></form>
    {loading ? <p role="status">Loading resources…</p> : error ? <div className="learning-error" role="alert"><p>{error}</p><button className="button button-primary" onClick={load}><RotateCw size={15}/> Retry</button></div> : result.resources.length ? <div className="resource-card-grid">{result.resources.map((item) => <Link className="learning-resource-card" to={'/resources/' + item.id} key={item.id}><span className="learning-category-icon"><FileText size={18}/></span><div><h2>{item.title}</h2><p>{item.description}</p><small>{item.category} · {item.resource_type} · {item.source}{item.is_verified ? ' · Verified source' : ''}</small></div><ArrowRight size={15}/></Link>)}</div> : <div className="learning-empty"><strong>No resources are currently available.</strong><p>No resource records have been imported. You can still open the configured placement folder directly.</p><a className="text-link" href={folderUrl} target="_blank" rel="noreferrer">Open placement folder <ExternalLink size={14}/></a></div>}
  </div>;
}

export function LearningResourceDetailPage() {
  const { resourceId } = useParams();
  const [resource, setResource] = useState(null); const [error, setError] = useState(''); const [loading, setLoading] = useState(true);
  const load = useCallback(async () => { setLoading(true); setError(''); try { setResource(await learningApi.resource(resourceId)); } catch (e) { setError(e.message); } finally { setLoading(false); } }, [resourceId]);
  useEffect(() => { load(); }, [load]);
  return <div className="dashboard-content learning-page"><Link className="learning-back-link" to="/resources">Placement Resources</Link>{loading ? <p role="status">Loading resource…</p> : error ? <div className="learning-error" role="alert"><p>This resource is currently unavailable. {error}</p><button className="button button-primary" onClick={load}><RotateCw size={15}/> Retry</button></div> : <section className="learning-panel resource-detail"><span className="eyebrow">{resource.category}</span><h1>{resource.title}</h1><p>{resource.description}</p><dl><div><dt>Type</dt><dd>{resource.resource_type}</dd></div><div><dt>Provider</dt><dd>{resource.provider || 'Not specified'}</dd></div><div><dt>Source</dt><dd>{resource.source}</dd></div><div><dt>Duration</dt><dd>{resource.duration_minutes ? resource.duration_minutes + ' minutes' : 'Not specified'}</dd></div><div><dt>Verified</dt><dd>{resource.is_verified ? 'Yes' : 'Not verified'}</dd></div></dl>{resource.url ? <a className="button button-primary" href={resource.url} target="_blank" rel="noreferrer">Open resource <ExternalLink size={15}/></a> : <p>This internal resource is currently unavailable.</p>}</section>}</div>;
}
