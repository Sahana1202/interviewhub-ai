import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, LoaderCircle } from 'lucide-react';
import { companyApi } from '../services/api';

export default function CompanyKnowledgePage() {
  const { companyId } = useParams(); const [question, setQuestion] = useState(null); const [company, setCompany] = useState('Company');
  const [selected, setSelected] = useState(null); const [result, setResult] = useState(null); const [error, setError] = useState(''); const [loading, setLoading] = useState(true);
  async function load() { setLoading(true); setError(''); setResult(null); setSelected(null); try { const [quiz, detail] = await Promise.all([companyApi.quiz(companyId), companyApi.get(companyId)]); setQuestion(quiz); setCompany(detail.company.name); } catch (e) { setError(e.message); } finally { setLoading(false); } }
  useEffect(() => { load(); }, [companyId]);
  async function submit() { if (selected === null) return; try { setResult(await companyApi.answer(companyId, { question_id: question.id, selected_answer: selected })); } catch (e) { setError(e.message); } }
  return <div className="dashboard-content company-page"><Link to={`/company/${companyId}`} className="company-back"><ArrowLeft size={16}/> Back to {company}</Link><section className="company-card knowledge-card"><span className="eyebrow">COMPANY KNOWLEDGE PRACTICE</span><h1>{company}</h1><p>Practice based on stored, source-backed company information. These are not actual interview questions.</p>
    {loading && <p role="status"><LoaderCircle className="spin"/> Loading practice…</p>}
    {error && !loading && <div className="company-message">{error}<p>Practice is available when a verified company fact has been added.</p><button className="button button-secondary" onClick={load}>Retry</button></div>}
    {question && <><h2>{question.question}</h2><div className="quiz-options">{question.options.map((option, index) => <button key={`${question.id}-${index}`} disabled={!!result} className={selected === index ? 'selected' : ''} onClick={() => setSelected(index)}><b>{String.fromCharCode(65 + index)}</b>{option}</button>)}</div>{!result ? <button className="button button-primary" disabled={selected === null} onClick={submit}>Submit answer</button> : <div className="quiz-result"><CheckCircle2/><strong>{result.correct ? 'Correct' : 'Review this fact'}</strong><p>{result.explanation}</p><small>Attempted {result.attempted} · Correct {result.correct_count} · Incorrect {result.incorrect_count}</small><button className="button button-secondary" onClick={load}>Try again</button></div>}</>}
  </section></div>;
}
