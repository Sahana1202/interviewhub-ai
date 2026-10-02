import { useEffect, useState } from 'react';
import { ArrowRight, Clock3, LoaderCircle, MessageSquare, ShieldCheck, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import InterviewHistory from '../components/InterviewHistory';
import { interviewApi } from '../services/api';

export default function InterviewsPage() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { interviewApi.list().then(setSessions).catch(()=>setSessions([])).finally(()=>setLoading(false)); }, []);
  const active = sessions.filter((session)=>session.status==='in_progress'||session.status==='paused');
  return <div className="interview-content"><PageHeader eyebrow="VIRTUAL HR PRACTICE" title="Interview Practice" description="Build confidence with structured, self-paced interview practice." action={<Link className="button button-primary" to="/interviews/setup">Start New Interview <ArrowRight size={16}/></Link>}/>
    <section className="interview-intro-card"><span className="interview-intro-icon"><Sparkles size={22}/></span><div><span className="virtual-label">AI VIRTUAL INTERVIEWERS</span><h2>Practice at your pace, with a clear next step.</h2><p>Choose a practice format, meet a Virtual HR interviewer, and save your answers as you go. This foundation uses a general starter question bank.</p></div></section>
    <div className="interview-feature-notes"><article><MessageSquare size={18}/><strong>Structured practice</strong><span>HR, technical, and combined question sets.</span></article><article><Clock3 size={18}/><strong>Your pace</strong><span>Choose a 10, 15, 20, or 30 minute session.</span></article><article><ShieldCheck size={18}/><strong>Saved sessions</strong><span>Your questions and answers stay in your account.</span></article></div>
    {active.length > 0 && <section className="active-session-section"><div className="section-heading"><div><span className="eyebrow">PICK UP WHERE YOU LEFT OFF</span><h2>Active sessions</h2></div></div>{active.map((session)=><Link className="active-session-row" key={session.id} to={`/interviews/${session.id}`}><span><strong>{session.job_role}</strong><small>{session.company_name||'General Interview'} · {session.status==='paused'?'Paused':'In progress'}</small></span><span>{session.interviewer_name}<ArrowRight size={16}/></span></Link>)}</section>}
    <section className="interview-history-preview"><div className="section-heading"><div><span className="eyebrow">YOUR SESSIONS</span><h2>Interview History</h2></div><Link className="text-link" to="/history">View history <ArrowRight size={15}/></Link></div>{loading ? <div className="interview-loading"><LoaderCircle className="spin"/> Loading sessions…</div> : <InterviewHistory/>}</section>
  </div>;
}
