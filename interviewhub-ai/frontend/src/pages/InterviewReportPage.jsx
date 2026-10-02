import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowRight, LoaderCircle, RotateCcw } from 'lucide-react';
import PageHeader from '../components/PageHeader';
import { interviewApi } from '../services/api';

export default function InterviewReportPage() {
  const { sessionId } = useParams();
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true); setError('');
    try { setReport(await interviewApi.report(sessionId)); }
    catch (requestError) { setError(requestError.message); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, [sessionId]);

  async function generate() {
    setLoading(true); setError('');
    try { setReport(await interviewApi.finalEvaluation(sessionId)); }
    catch (requestError) { setError(requestError.message); }
    finally { setLoading(false); }
  }

  return <div className="interview-content report-page"><PageHeader eyebrow="AI-GENERATED PRACTICE FEEDBACK" title="Interview Practice Report" description="Evidence-based feedback from your saved answers. This is not a hiring prediction or recruiter score."/>
    {loading&&<div className="interview-loading" role="status"><LoaderCircle className="spin"/> Loading your report…</div>}
    {!loading&&error&&<div className="report-empty"><p role="status">{error}</p><p>Reports are generated from saved answers that received AI evaluation. Rule-based interviews have no AI report.</p><div className="completion-actions"><button className="button button-primary" onClick={generate}><RotateCcw size={15}/> Retry AI report</button><Link className="button button-secondary" to={`/interviews/${sessionId}/complete`}>Back to interview summary</Link></div></div>}
    {!loading&&report&&<div className="report-content"><section className="report-card"><h2>Overview</h2><p>{report.summary}</p><small>AI-generated practice feedback · {report.provider} · {report.model}</small></section><div className="report-columns"><section className="report-card"><h2>What went well</h2><ul>{report.strengths.map((item,index)=><li key={index}>{item}</li>)}</ul></section><section className="report-card"><h2>Areas to improve</h2><ul>{report.improvement_areas.map((item,index)=><li key={index}>{item}</li>)}</ul></section></div><div className="report-columns"><section className="report-card"><h2>Technical feedback</h2><p>{report.technical_feedback}</p></section><section className="report-card"><h2>Communication feedback</h2><p>{report.communication_feedback}</p></section></div><section className="report-card"><h2>Topics discussed</h2>{report.topic_breakdown.length?<ul>{report.topic_breakdown.map((item,index)=><li key={index}><b>{item.topic || item.summary || 'Interview topic'}</b>{item.evidence&&<span> — {item.evidence}</span>}</li>)}</ul>:<p>No topic breakdown was returned.</p>}</section><section className="report-card"><h2>Recommended next steps</h2>{report.recommended_topics.length?<ul>{report.recommended_topics.map((item,index)=><li key={index}>{item.href?<Link to={item.href}>{item.topic} <ArrowRight size={13}/></Link>:<span>{item.topic} — Review this area before your next interview.</span>}<small>{item.reason}</small></li>)}</ul>:<p>No additional topics were recommended.</p>}</section><section className="report-card"><h2>Question-by-question feedback</h2>{report.question_feedback?.length?<div className="question-feedback-list">{report.question_feedback.map((item,index)=><article key={index}><span className="question-category">{item.category}</span><h3>{item.question}</h3><p><b>Your answer</b> — {item.answer}</p><p><b>Practice feedback</b> — {item.feedback}</p>{item.strengths?.[0]&&<small><b>Strength:</b> {item.strengths[0]}</small>}{item.areas_to_improve?.[0]&&<small><b>Improve:</b> {item.areas_to_improve[0]}</small>}</article>)}</div>:<p>No answer-specific evaluation is available.</p>}</section><Link className="button button-secondary" to="/history">View interview history</Link></div>}
  </div>;
}
