import { useEffect, useState } from 'react';
import { ArrowRight, CalendarDays, LoaderCircle, MessageSquareText } from 'lucide-react';
import { Link } from 'react-router-dom';
import { interviewApi } from '../services/api';

function dateLabel(value) {
  return value ? new Date(value).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : '—';
}

export default function InterviewHistory() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  async function load() {
    setLoading(true); setError('');
    try { setSessions(await interviewApi.list()); }
    catch (requestError) { setError(requestError.message); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);
  if (loading) return <div className="interview-loading" role="status"><LoaderCircle className="spin"/> Loading interview history…</div>;
  if (error) return <div className="interview-error" role="alert">{error}<button type="button" onClick={load}>Retry</button></div>;
  if (!sessions.length) return <div className="interview-empty"><span><MessageSquareText size={22}/></span><h2>You haven’t completed an interview yet.</h2><p>Start your first interview to see it here.</p><Link className="button button-primary" to="/interviews/setup">Start an interview <ArrowRight size={16}/></Link></div>;
  return <div className="interview-history-list">{sessions.map((session)=><article className="history-session-card" key={session.id}><div className="history-session-top"><span className={`status-pill status-${session.status}`}>{session.status.replace('_',' ')}</span><span><CalendarDays size={14}/>{dateLabel(session.created_at)}</span></div><h3>{session.job_role}</h3><p>{session.company_name || 'General Interview'} · {session.interview_type} · {session.difficulty}</p><div className="history-session-meta"><span>Virtual HR: {session.interviewer_name}</span><span>{session.duration_minutes} min</span><span>{session.answers_count} answers</span></div><p className="ai-history-status">{session.evaluations_count>0?'AI-generated practice feedback available':session.ai_enabled?'AI evaluation unavailable or not yet generated':'Rule-based practice · No AI evaluation'}</p><div className="history-card-actions"><Link className="text-link" to={`/interviews/${session.id}`}>{session.status==='completed'?'View session':'Continue interview'} <ArrowRight size={15}/></Link>{session.status==='completed'&&session.evaluations_count>0&&<Link className="text-link" to={`/interviews/${session.id}/report`}>Practice report <ArrowRight size={15}/></Link>}</div></article>)}</div>;
}
