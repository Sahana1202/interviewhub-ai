import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowLeft, LoaderCircle } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import HRAvatar from './HRAvatar';
import QuestionPanel from './QuestionPanel';
import AnswerInput from './AnswerInput';
import TranscriptPanel from './TranscriptPanel';
import InterviewControls from './InterviewControls';
import InterviewTimer from './InterviewTimer';
import { interviewApi } from '../services/api';
import { formatTime } from './InterviewTimer';

export default function InterviewRoom() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [interviewers, setInterviewers] = useState([]);
  const [answer, setAnswer] = useState('');
  const [recording, setRecording] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [confirmEnd, setConfirmEnd] = useState(false);
  const [remaining, setRemaining] = useState(0);
  const [aiStatus, setAiStatus] = useState({ available: false });
  const [aiError, setAiError] = useState('');
  const [requestingQuestion, setRequestingQuestion] = useState(false);
  const [latestAnswer, setLatestAnswer] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const timerAnchor = useRef({ seconds: 0, at: Date.now() });
  const finishing = useRef(false);
  const requestedQuestions = useRef(new Set());

  async function load() {
    setLoading(true); setError('');
    try {
      const [details, profiles, status] = await Promise.all([interviewApi.get(sessionId), interviewApi.interviewers(), interviewApi.aiStatus()]);
      setSession(details); setInterviewers(profiles);
      setAiStatus(status);
      timerAnchor.current = { seconds: details.remaining_seconds, at: Date.now() };
      setRemaining(details.remaining_seconds);
    } catch (requestError) { setError(requestError.message); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, [sessionId]);

  const currentQuestion = useMemo(() => session?.questions.find((question) => question.sequence_number === session.current_question_index), [session]);
  const interviewer = interviewers.find((item) => item.id === session?.interviewer_id);
  const startedLabel = session?.started_at || session?.created_at ? new Date(session.started_at || session.created_at).toLocaleString() : '—';
  const completedLabel = session?.completed_at ? new Date(session.completed_at).toLocaleString() : null;
  const sessionStatus = session?.status;

  async function retryQuestion() {
    if (!session || !currentQuestion) return;
    requestedQuestions.current.add(`${session.id}:${currentQuestion.id}`);
    setRequestingQuestion(true); setAiError('');
    try {
      const question = await interviewApi.aiQuestion(session.id);
      setSession((old) => old ? ({ ...old, questions: old.questions.map((item) => item.id === question.id ? { ...item, ...question } : item) }) : old);
    } catch (requestError) { setAiError(requestError.message); }
    finally { setRequestingQuestion(false); }
  }

  useEffect(() => {
    if (showFeedback || !session?.ai_enabled || !aiStatus.available || !currentQuestion || currentQuestion.answer || currentQuestion.question_source === 'ai_generated') return;
    const key = `${session.id}:${currentQuestion.id}`;
    if (requestedQuestions.current.has(key)) return;
    requestedQuestions.current.add(key);
    setRequestingQuestion(true);
    interviewApi.aiQuestion(session.id).then((question) => {
      setSession((old) => old ? ({ ...old, questions: old.questions.map((item) => item.id === question.id ? { ...item, ...question } : item) }) : old);
      setAiError('');
    }).catch((requestError) => setAiError(requestError.message || 'AI question generation unavailable.')).finally(() => setRequestingQuestion(false));
  }, [session?.id, session?.ai_enabled, aiStatus.available, currentQuestion?.id, currentQuestion?.answer, currentQuestion?.question_source, showFeedback]);

  async function finishWhenTimeExpires() {
    try {
      if (currentQuestion && !currentQuestion.answer && answer.trim() && session) {
        const result = await interviewApi.answer(sessionId, {
          question_id: currentQuestion.id,
          answer_text: answer.trim(),
          transcript: session.response_mode === 'voice' ? answer.trim() : null,
          response_mode: session.response_mode,
        });
        if (result.session.status !== 'completed') await interviewApi.complete(sessionId);
      } else {
        await interviewApi.complete(sessionId);
      }
      navigate(`/interviews/${sessionId}/complete`, { replace: true });
    } catch (requestError) {
      setError(requestError.message);
      finishing.current = false;
    }
  }

  useEffect(() => {
    if (sessionStatus !== 'in_progress') return undefined;
    const tick = () => {
      const left = Math.max(0, timerAnchor.current.seconds - Math.floor((Date.now() - timerAnchor.current.at) / 1000));
      setRemaining(left);
      if (left === 0 && !finishing.current) {
        finishing.current = true;
        finishWhenTimeExpires();
      }
    };
    tick();
    const interval = window.setInterval(tick, 1000);
    return () => window.clearInterval(interval);
  }, [sessionStatus, sessionId, navigate, answer, currentQuestion, session]);

  async function submitAnswer() {
    if (!currentQuestion || !answer.trim() || session.status !== 'in_progress') return;
    setSubmitting(true); setError(''); setAiError('');
    try {
      const result = await interviewApi.answer(sessionId, { question_id: currentQuestion.id, answer_text: answer.trim(), transcript: session.response_mode === 'voice' ? answer.trim() : null, response_mode: session.response_mode });
      setSession(result.session); setAnswer('');
      if (session.ai_enabled) {
        setLatestAnswer({ question: currentQuestion.question_text, category: currentQuestion.category, answer: result.saved_answer, evaluation: null });
        setShowFeedback(true);
      }
      timerAnchor.current = { seconds: result.session.remaining_seconds, at: Date.now() };
      setRemaining(result.session.remaining_seconds);
      if (session.ai_enabled && result.saved_answer?.id) {
        try {
          const evaluation = await interviewApi.evaluate(sessionId, result.saved_answer.id);
          setSession((old) => old ? ({ ...old, questions: old.questions.map((item) => item.answer?.id === result.saved_answer.id ? { ...item, evaluation } : item) }) : old);
          setLatestAnswer((old) => old ? ({ ...old, evaluation }) : old);
        } catch (evaluationError) {
          setAiError(`${evaluationError.message}. Your answer is saved; retry the evaluation when available.`);
        }
      }
      if (result.session.status === 'completed') navigate(`/interviews/${sessionId}/complete`, { replace: true });
    } catch (requestError) { setError(requestError.message); }
    finally { setSubmitting(false); }
  }

  async function retryEvaluation(answerId) {
    setAiError('');
    try {
      const evaluation = await interviewApi.evaluate(sessionId, answerId);
      setSession((old) => old ? ({ ...old, questions: old.questions.map((item) => item.answer?.id === answerId ? { ...item, evaluation } : item) }) : old);
      setLatestAnswer((old) => old?.answer.id === answerId ? ({ ...old, evaluation }) : old);
    } catch (requestError) { setAiError(requestError.message); }
  }

  async function requestFollowup(answerId) {
    setSubmitting(true); setAiError('');
    try {
      await interviewApi.followup(sessionId, answerId);
      const updated = await interviewApi.get(sessionId);
      setSession(updated);
      setShowFeedback(false);
      const active = updated.questions.find((item) => item.sequence_number === updated.current_question_index);
      if (active) requestedQuestions.current.add(`${updated.id}:${active.id}`);
    } catch (requestError) { setAiError(requestError.message); }
    finally { setSubmitting(false); }
  }

  function continueAfterFeedback() { setShowFeedback(false); setAiError(''); }

  async function togglePause() {
    setError('');
    try {
      const updated = await interviewApi.pause(sessionId);
      setSession(updated); timerAnchor.current = { seconds: updated.remaining_seconds, at: Date.now() }; setRemaining(updated.remaining_seconds);
      if (updated.status === 'completed') navigate(`/interviews/${sessionId}/complete`, { replace: true });
    } catch (requestError) { setError(requestError.message); }
  }

  async function finish() {
    setError('');
    try { await interviewApi.complete(sessionId); navigate(`/interviews/${sessionId}/complete`, { replace: true }); }
    catch (requestError) { setError(requestError.message); }
  }

  if (loading) return <div className="interview-loading" role="status"><LoaderCircle className="spin"/> Loading your interview…</div>;
  if (error && !session) return <div className="interview-content"><div className="interview-error" role="alert">{error}<button type="button" onClick={load}>Retry</button></div></div>;
  if (!session) return null;
  const maxQuestions = session.question_limit;
  const questionSetComplete = session.questions.length >= maxQuestions && session.questions.every((question) => question.answer);

  return <div className="interview-room-page"><header className="interview-room-header"><Link to="/interviews" className="room-brand"><span className="brand-icon">IH</span><span>InterviewHub <b>AI</b></span></Link><div className="room-meta"><span>{session.job_role}{session.company_name ? ` · ${session.company_name}` : ' · General Interview'}</span>{session.status==='completed'?<span className="status-pill status-completed">Completed</span>:<InterviewTimer seconds={remaining} paused={session.status==='paused'}/>}</div><Link className="room-exit-link" to="/dashboard"><ArrowLeft size={15}/> Exit room</Link></header>
    {session.status === 'paused' && <div className="paused-banner" role="status">Interview paused. Your timer and saved answers are preserved.</div>}
    {session.status === 'completed' && <div className="paused-banner completed-banner" role="status">Interview complete. This saved session is read only.</div>}
    {error && <div className="room-error" role="alert">{error}</div>}
    {session.ai_enabled && <div className={`ai-mode-banner${aiStatus.available?'':' unavailable'}`} role="status">{aiStatus.available?'AI Interview Mode · provider connected':'AI Interview Mode unavailable · general practice remains usable'}</div>}
    {aiError && <div className="room-error" role="alert">{aiError}</div>}
    <main className="interview-room-content"><section className="session-detail-strip" aria-label="Interview configuration">{session.resume_file_name && <div><span>Resume</span><strong>{session.resume_file_name}</strong></div>}<div><span>Experience</span><strong>{session.experience_level}</strong></div><div><span>Type</span><strong>{session.advanced_interview_type}</strong></div><div><span>Difficulty</span><strong>{session.difficulty_mode==='adaptive'?`Adaptive · ${session.current_difficulty}`:session.difficulty}</strong></div><div><span>Duration</span><strong>{session.duration_minutes} minutes</strong></div><div><span>Response</span><strong>{session.response_mode}</strong></div><div><span>Started</span><strong>{startedLabel}</strong></div>{completedLabel&&<div><span>Completed</span><strong>{completedLabel}</strong></div>}</section><div className="room-main-grid"><HRAvatar interviewer={interviewer} state={session.status==='completed'?'idle':submitting ? 'thinking' : recording ? 'listening' : currentQuestion&&!questionSetComplete ? 'asking' : 'idle'} statusLabel={session.status==='completed'?'Session saved':undefined}/><div className="room-question-column">{showFeedback&&latestAnswer ? <section className="saved-answer-highlight"><strong>Answer saved</strong><p>{latestAnswer.answer.answer_text}</p>{latestAnswer.evaluation?<div className="live-evaluation"><strong>AI-generated practice feedback</strong><p>{latestAnswer.evaluation.overall_feedback}</p>{latestAnswer.evaluation.strengths?.[0]&&<small><b>Strength:</b> {latestAnswer.evaluation.strengths[0]}</small>}{latestAnswer.evaluation.areas_to_improve?.[0]&&<small><b>Improve:</b> {latestAnswer.evaluation.areas_to_improve[0]}</small>}{latestAnswer.evaluation.follow_up_needed&&session.status==='in_progress'&&<button type="button" className="button button-secondary" disabled={submitting} onClick={()=>requestFollowup(latestAnswer.answer.id)}>Ask contextual follow-up</button>}</div>:<div className="live-evaluation"><strong>AI evaluation unavailable</strong><p>Your answer is saved. Continue with general practice, or retry when the provider is available.</p>{aiStatus.available&&<button type="button" className="button button-secondary" disabled={submitting} onClick={()=>retryEvaluation(latestAnswer.answer.id)}>Retry AI evaluation</button>}</div>}<button type="button" className="button button-primary" disabled={submitting} onClick={continueAfterFeedback}>Continue to next question</button></section>:<>{currentQuestion && !questionSetComplete ? <QuestionPanel question={currentQuestion} interviewer={interviewer} questionNumber={currentQuestion.sequence_number} totalQuestions={maxQuestions}/> : <section className="question-panel"><span className="eyebrow">QUESTION SET COMPLETE</span><h2>You’ve reached the end of this practice set.</h2><p>Your saved answers are ready. End the interview whenever you’re ready.</p></section>}
        {session.ai_enabled&&aiStatus.available&&currentQuestion&&!currentQuestion.answer&&currentQuestion.question_source!=='ai_generated'&&<button type="button" className="button button-secondary retry-ai-question" onClick={retryQuestion} disabled={requestingQuestion||submitting}>{requestingQuestion?'Generating question…':'Retry AI question generation'}</button>}
        {currentQuestion && !questionSetComplete && !currentQuestion.answer && <AnswerInput value={answer} onChange={setAnswer} responseMode={session.response_mode} disabled={session.status!=='in_progress'||submitting||requestingQuestion} onRecordingChange={setRecording}/>}
        {currentQuestion?.answer && <div className="saved-answer-highlight"><strong>Answer saved</strong><p>{currentQuestion.answer.answer_text}</p>{currentQuestion.evaluation&&<div className="live-evaluation"><strong>AI-generated practice feedback</strong><p>{currentQuestion.evaluation.overall_feedback}</p></div>}</div>}
        {currentQuestion && <InterviewControls status={session.status} submitting={submitting} answerPresent={Boolean(answer.trim())&&!currentQuestion.answer&&!questionSetComplete} onSubmit={submitAnswer} onTogglePause={togglePause} onEnd={()=>setConfirmEnd(true)}/>}
        {!currentQuestion && <InterviewControls status={session.status} submitting={false} answerPresent={false} onSubmit={()=>{}} onTogglePause={togglePause} onEnd={()=>setConfirmEnd(true)}/>}</>}</div></div>
      <TranscriptPanel questions={session.questions}/>
    </main>
    {confirmEnd && <div className="modal-backdrop" role="presentation"><section className="confirm-modal" role="dialog" aria-modal="true" aria-labelledby="end-interview-title"><h2 id="end-interview-title">Are you sure you want to end this interview?</h2><p>Your saved answers will remain available.</p><div><button className="button button-secondary" onClick={()=>setConfirmEnd(false)}>Continue Interview</button><button className="button button-primary" onClick={finish}>End Interview</button></div></section></div>}
    <footer className="room-safety-note">{session.status==='completed'?'This saved interview is read only.':`${currentQuestion?.question_source==='ai_generated'?'AI-generated practice question.':'Rule-based practice question.'} Remaining time: ${formatTime(remaining)}.`}</footer>
  </div>;
}
