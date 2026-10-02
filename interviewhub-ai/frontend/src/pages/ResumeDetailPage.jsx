import { useEffect, useState } from 'react';
import { ArrowLeft, FileText, LoaderCircle, Sparkles } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import { resumeApi } from '../services/api';

function Section({ title, children }) { return <section className="resume-result-card"><h2>{title}</h2>{children || <p className="resume-muted">Not detected in the extracted text.</p>}</section>; }

export default function ResumeDetailPage() {
  const { resumeId } = useParams(); const navigate = useNavigate();
  const [resume, setResume] = useState(null); const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [analyzing, setAnalyzing] = useState(false);
  async function load() { setLoading(true); setError(''); try { setResume(await resumeApi.get(resumeId)); } catch (err) { setError(err.message); } finally { setLoading(false); } }
  useEffect(() => { load(); }, [resumeId]);
  async function analyze() { setAnalyzing(true); setError(''); try { setResume(await resumeApi.analyze(resumeId)); } catch (err) { setError(err.message); } finally { setAnalyzing(false); } }
  if (loading) return <div className="dashboard-content resume-page"><div className="resume-loading"><LoaderCircle className="spin"/> Loading extracted resume…</div></div>;
  if (error && !resume) return <div className="dashboard-content resume-page"><div className="resume-alert" role="alert">{error}<button onClick={load}>Retry</button></div><Link to="/resume" className="text-link"><ArrowLeft size={15}/> Back to Resume Analyzer</Link></div>;
  const data = resume || {};
  const checks = data.completeness?.checks || {};
  return <div className="dashboard-content resume-page resume-detail-page">
    <Link to="/resume" className="resume-back"><ArrowLeft size={15}/> Resume Analyzer</Link>
    <PageHeader eyebrow="EXTRACTED FROM YOUR RESUME" title={data.file_name} description={`Uploaded ${new Date(data.created_at).toLocaleString()} · ${data.status}`} />
    {error && <div className="resume-alert" role="alert">{error}<button onClick={load}>Retry</button></div>}
    {data.status === 'failed' && <div className="resume-scan-notice" role="status">{data.processing_message || "We couldn't extract text from this PDF. It may be scanned or image-based."}</div>}
    {!!data.completeness?.total_checks && <section className="resume-result-card completeness-card"><div className="resume-section-heading"><div><span className="eyebrow">DETERMINISTIC STRUCTURE CHECK</span><h2>Resume Completeness</h2><p>Section detection only; this is not an ATS score or an assessment of resume quality.</p></div><strong>{data.completeness.present_count}/{data.completeness.total_checks}</strong></div><div className="completeness-grid">{Object.entries(checks).map(([key, present]) => <div key={key}><span className={present ? 'check-present' : 'check-missing'}>{present ? '✓' : '—'}</span><span>{key[0].toUpperCase() + key.slice(1)}</span><small>{present ? 'Detected' : 'Not detected'}</small></div>)}</div></section>}
    {data.status === 'processed' && <><div className="resume-result-grid">
      <Section title="Contact"><dl className="resume-contact-list">{Object.entries(data.contact || {}).filter(([,value]) => value).map(([key,value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl></Section>
      <Section title="Education">{data.education?.length > 0 && <ul className="resume-entry-list">{data.education.map((entry,i) => <li key={i}><strong>{entry.degree || entry.institution}</strong><span>{entry.institution}</span><small>{[entry.graduation_year,entry.grade].filter(Boolean).join(' · ')}</small></li>)}</ul>}</Section>
      <Section title="Skills">{data.skills?.length > 0 && <div className="resume-skill-chips">{data.skills.map((skill) => <span key={skill}>{skill}</span>)}</div>}<small className="resume-muted">Skills were detected in the resume’s skills section. They have not been added to your profile.</small></Section>
      <Section title="Projects">{data.projects?.length > 0 && <ul className="resume-entry-list">{data.projects.map((entry,i) => <li key={i}><strong>{entry.name}</strong><span>{entry.description}</span>{entry.technologies?.length > 0 && <small>{entry.technologies.join(' · ')}</small>}</li>)}</ul>}</Section>
      <Section title="Experience">{data.experience?.length > 0 && <ul className="resume-entry-list">{data.experience.map((entry,i) => <li key={i}><strong>{entry.role}</strong>{entry.organization && <span>{entry.organization}</span>}{entry.dates && <small>{entry.dates}</small>}<span>{entry.description}</span></li>)}</ul>}</Section>
      <Section title="Certifications">{data.certifications?.length > 0 && <ul className="resume-simple-list">{data.certifications.map((entry,i) => <li key={i}>{entry}</li>)}</ul>}</Section>
      <Section title="Achievements">{data.achievements?.length > 0 && <ul className="resume-simple-list">{data.achievements.map((entry,i) => <li key={i}>{entry}</li>)}</ul>}</Section>
    </div>
    <section className="resume-result-card"><div className="resume-section-heading"><div><span className="eyebrow">DETERMINISTIC GUIDANCE</span><h2>Suggestions</h2></div><button className="button button-secondary" disabled={analyzing} onClick={analyze}>{analyzing ? <LoaderCircle className="spin" size={15}/> : <Sparkles size={15}/>} Re-analyze</button></div>{data.suggestions?.length ? <ul className="resume-suggestions">{data.suggestions.map((text,i)=><li key={i}>{text}</li>)}</ul> : <p className="resume-muted">No structural suggestions detected.</p>}</section>
    {data.practice_questions?.length > 0 && <section className="resume-result-card"><span className="eyebrow">PRACTICE QUESTIONS BASED ON YOUR RESUME</span><h2>Prepare to discuss your experience</h2><ol className="resume-question-list">{data.practice_questions.map((question,i)=><li key={i}>{question}</li>)}</ol></section>}
    </>}
    <div className="resume-result-actions"><Link to="/interviews/setup" state={{resumeId: data.id}} className="button button-primary">Practice with Virtual HR</Link><button className="button button-secondary" onClick={() => navigate('/resume')}>Back to resumes</button></div>
  </div>;
}
