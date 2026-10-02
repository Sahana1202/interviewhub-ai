import { useEffect, useState } from 'react';
import { ArrowLeft, ArrowRight, LoaderCircle, RotateCcw } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import { interviewApi } from '../services/api';

export default function InterviewCompletePage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [error, setError] = useState('');
  const [reportStatus, setReportStatus] = useState('');
  useEffect(() => {
    interviewApi.get(sessionId).then((value)=>{
      if (value.status !== 'completed') { navigate(`/interviews/${sessionId}`, { replace: true }); return; }
      setSession(value);
      if (value.ai_enabled) interviewApi.aiStatus().then((status)=>{
        if (!status.available) { setReportStatus('Interview completed. AI report could not be generated because the AI provider is unavailable.'); return; }
        interviewApi.finalEvaluation(sessionId).then(()=>setReportStatus('AI-generated practice report is ready.')).catch((requestError)=>setReportStatus(requestError.message));
      });
    }).catch((requestError)=>setError(requestError.message));
  }, [sessionId,navigate]);
  if (error) return <div className="interview-content"><div className="interview-error" role="alert">{error}<Link to="/history">Back to history</Link></div></div>;
  if (!session) return <div className="interview-loading" role="status"><LoaderCircle className="spin"/> Loading completion details…</div>;
  const elapsedSeconds = Math.max(0, session.duration_minutes*60-session.remaining_seconds);
  const elapsedMinutes = Math.floor(elapsedSeconds/60);
  const durationLabel = elapsedSeconds > 0 && elapsedMinutes === 0 ? 'Under 1 minute' : `${elapsedMinutes} ${elapsedMinutes===1?'minute':'minutes'}`;
  return <div className="interview-content completion-page"><div className="completion-celebration">✓</div><PageHeader eyebrow="SESSION SAVED" title="Interview Complete" description="Your interview session has been saved."/>{session.remaining_seconds===0&&<p className="timer-complete-note" role="status">Interview time is complete.</p>}<section className="completion-report"><div><span>Questions answered</span><strong>{session.answers_count}</strong></div><div><span>Duration</span><strong>{durationLabel}</strong></div><div><span>Role</span><strong>{session.job_role}</strong></div><div><span>Virtual HR</span><strong>{session.interviewer_name}</strong></div></section><p className="evaluation-future-note">{reportStatus || (session.ai_enabled?'Preparing your AI-generated practice report…':'No AI report was generated for this rule-based practice interview.')}</p><div className="completion-actions"><Link className="button button-secondary" to="/dashboard"><ArrowLeft size={15}/> Back to Dashboard</Link><Link className="button button-secondary" to="/history">View Interview History <ArrowRight size={15}/></Link>{session.ai_enabled&&<Link className="button button-secondary" to={`/interviews/${sessionId}/report`}>View practice report</Link>}<Link className="button button-primary" to="/interviews/setup"><RotateCcw size={15}/> Start Another Interview</Link></div></div>;
}
