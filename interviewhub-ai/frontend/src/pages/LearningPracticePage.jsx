import { useCallback, useEffect, useState } from 'react';
import { ArrowRight, CheckCircle2, LoaderCircle, RotateCw } from 'lucide-react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import { learningApi, practiceApi } from '../services/api';

export default function LearningPracticePage() {
  const { attemptId } = useParams(); const navigate = useNavigate(); const [searchParams] = useSearchParams();
  const [categories, setCategories] = useState([]); const [topics, setTopics] = useState([]);
  const [difficultyOptions, setDifficultyOptions] = useState([]);
  const [categoryId, setCategoryId] = useState(''); const [topicId, setTopicId] = useState(searchParams.get('topic_id') || '');
  const [difficulty, setDifficulty] = useState(''); const [questionCount, setQuestionCount] = useState('10');
  const [attempt, setAttempt] = useState(null); const [selected, setSelected] = useState(null); const [feedback, setFeedback] = useState(null); const [pending, setPending] = useState(null);
  const [loading, setLoading] = useState(true); const [submitting, setSubmitting] = useState(false); const [error, setError] = useState('');
  const loadSetup = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [categoryRows, topicData] = await Promise.all([learningApi.categories(), learningApi.topics()]);
      setCategories(categoryRows); setTopics(topicData.topics);
      const fromQuery = searchParams.get('topic_id') || '';
      if (fromQuery && topicData.topics.some((topic) => String(topic.id) === fromQuery)) {
        const selectedTopic = topicData.topics.find((topic) => String(topic.id) === fromQuery);
        setTopicId(fromQuery); setCategoryId(String(selectedTopic.category_id));
      } else {
        setCategoryId(String(categoryRows[0]?.id || ''));
      }
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [searchParams]);
  const loadAttempt = useCallback(async () => {
    if (!attemptId) return;
    setLoading(true); setError('');
    try { setAttempt(await practiceApi.get(attemptId)); setFeedback(null); setPending(null); setSelected(null); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [attemptId]);
  useEffect(() => { if (attemptId) loadAttempt(); else loadSetup(); }, [attemptId, loadAttempt, loadSetup]);
  useEffect(() => {
    let active = true;
    if (!topicId) { setDifficultyOptions([]); setDifficulty(''); return () => { active = false; }; }
    learningApi.topic(topicId).then((item) => {
      if (!active) return;
      const levels = item.practice_options || [];
      setDifficultyOptions(levels);
      setDifficulty((current) => current && levels.some((option) => option.difficulty === current) ? current : '');
    }).catch(() => active && setDifficultyOptions([]));
    return () => { active = false; };
  }, [topicId]);
  const visibleTopics = topics.filter((topic) => !categoryId || String(topic.category_id) === categoryId);
  async function start(event) {
    event.preventDefault(); setError(''); setSubmitting(true);
    try {
      const result = await practiceApi.start({ topic_id: topicId ? Number(topicId) : null, category_id: categoryId ? Number(categoryId) : null, difficulty: difficulty || null, question_count: Number(questionCount) });
      navigate('/learning/practice/' + result.id);
    } catch (e) { setError(e.message); }
    finally { setSubmitting(false); }
  }
  async function submitAnswer() {
    if (!attempt?.current_question || selected === null) return;
    setSubmitting(true); setError('');
    try {
      const result = await practiceApi.answer(attempt.id, { question_id: attempt.current_question.id, selected_answer: selected });
      setFeedback(result);
      if (result.completed && result.attempt) setAttempt(result.attempt);
      else setPending(result.next_question || null);
    } catch (e) { setError(e.message); }
    finally { setSubmitting(false); }
  }
  async function nextQuestion() {
    if (pending) { setAttempt((current) => ({ ...current, answered_count: feedback.answered_count, current_question: pending })); setSelected(null); setFeedback(null); setPending(null); }
    else await loadAttempt();
  }
  async function finishEarly() {
    setSubmitting(true); setError('');
    try { setAttempt(await practiceApi.complete(attempt.id)); setFeedback(null); }
    catch (e) { setError(e.message); }
    finally { setSubmitting(false); }
  }
  if (loading) return <div className="dashboard-content"><p role="status"><LoaderCircle className="spin"/> Loading practice…</p></div>;
  if (error && !attemptId) return <div className="dashboard-content"><PageHeader eyebrow="PRACTICE" title="Set up a practice session" description="Choose a topic, difficulty, and question count."/><ErrorPanel error={error} retry={loadSetup}/></div>;
  if (attemptId && error && !attempt) return <div className="dashboard-content"><Link className="learning-back-link" to="/learning/history">Back to history</Link><ErrorPanel error={error} retry={loadAttempt}/></div>;
  if (!attemptId) return <div className="dashboard-content learning-page">
    <PageHeader eyebrow="PRACTICE SETUP" title="Choose a practice session" description="Answers are scored by the backend and explanations appear after submission."/>
    {error && <div className="learning-error" role="alert">{error}<button onClick={loadSetup}>Retry</button></div>}
    <form className="learning-panel practice-setup-form" onSubmit={start}>
      <label className="learning-field">Preparation area<select value={categoryId} onChange={(event) => { setCategoryId(event.target.value); setTopicId(''); }}><option value="">Any available area</option>{categories.filter((item) => item.slug !== 'placement-resources').map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
      <label className="learning-field">Topic<select value={topicId} onChange={(event) => setTopicId(event.target.value)}><option value="">Choose a topic</option>{visibleTopics.map((topic) => <option key={topic.id} value={topic.id}>{topic.name}</option>)}</select><small>Scored practice is available only for topics with saved multiple-choice questions.</small></label>
      <label className="learning-field">Difficulty<select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}><option value="">Any available</option>{difficultyOptions.map((item) => <option key={item.difficulty} value={item.difficulty}>{item.difficulty} ({item.question_count})</option>)}</select></label>
      <label className="learning-field">Question count<select value={questionCount} onChange={(event) => setQuestionCount(event.target.value)}>{[5, 10, 15, 20].map((n) => <option key={n} value={n}>{n} questions (up to available)</option>)}</select></label>
      <button className="button button-primary" disabled={submitting || !topicId}>{submitting ? 'Starting…' : 'Start Practice'} <ArrowRight size={16}/></button>
    </form>
    <p className="learning-note">Practice questions are labeled by source. Internal questions are written by InterviewHub and are not attributed to employers.</p>
  </div>;
  if (!attempt) return null;
  if (attempt.status === 'completed') return <PracticeResult attempt={attempt} onAgain={() => navigate('/learning/practice?topic_id=' + attempt.topic_id)}/>;
  const question = attempt.current_question;
  return <div className="dashboard-content learning-page">
    <Link className="learning-back-link" to="/learning/history">Practice history</Link>
    <PageHeader eyebrow={attempt.category.toUpperCase()} title={attempt.topic} description="Practice questions · InterviewHub-owned internal material"/>
    {error && <div className="learning-error" role="alert">{error}<button onClick={loadAttempt}>Retry</button></div>}
    {question ? <section className="practice-room learning-panel">
      <div className="practice-progress-line"><span>Question {attempt.answered_count + 1} / {attempt.total_questions}</span><span>{attempt.answered_count} answered</span></div>
      <div className="learning-progress-track" role="progressbar" aria-label="Practice session progress" aria-valuenow={attempt.answered_count} aria-valuemin="0" aria-valuemax={attempt.total_questions}><span style={{ width: (attempt.answered_count / attempt.total_questions * 100) + '%' }}/></div>
      <span className="practice-source-label">{question.source.replaceAll('_', ' ')} question</span><h2>{question.question}</h2>
      <div className="practice-options" role="radiogroup" aria-label="Answer options">{question.options.map((option, index) => <button key={index} type="button" role="radio" aria-checked={selected === index} className={selected === index ? 'selected' : ''} disabled={!!feedback} onClick={() => setSelected(index)}><span>{String.fromCharCode(65 + index)}</span>{option}</button>)}</div>
      {feedback && <div className={'practice-feedback ' + (feedback.correct ? 'correct' : 'incorrect')} role="status"><strong>{feedback.correct ? 'Correct' : 'Not quite'}</strong><p>{feedback.explanation}</p>{feedback.correct_option && !feedback.correct && <small>Correct option: {feedback.correct_option}</small>}</div>}
      {!feedback ? <div className="practice-actions"><button className="button button-primary" onClick={submitAnswer} disabled={selected === null || submitting}>{submitting ? 'Submitting…' : 'Submit answer'} <ArrowRight size={16}/></button><button className="button button-secondary" onClick={finishEarly} disabled={submitting}>Finish practice</button></div> : <button className="button button-primary" onClick={nextQuestion}>{attempt.status === 'completed' ? 'View results' : 'Next question'} <ArrowRight size={16}/></button>}
    </section> : <ErrorPanel error="This practice session has no pending question." retry={loadAttempt}/>}
  </div>;
}

function PracticeResult({ attempt, onAgain }) {
  return <div className="dashboard-content learning-page"><section className="practice-result learning-panel"><span className="learning-category-icon"><CheckCircle2/></span><span className="eyebrow">PRACTICE COMPLETE</span><h1>{attempt.topic}</h1><p>Score: <strong>{attempt.correct_answers} / {attempt.total_questions}</strong></p><p>Accuracy: <strong>{attempt.accuracy}%</strong></p><p>Correct: {attempt.correct_answers} · Incorrect: {attempt.incorrect_answers}</p><p className="learning-note">Practice accuracy summarizes these submitted answers; it is not a measure of overall knowledge.</p><div className="practice-actions"><button className="button button-primary" onClick={onAgain}>Practice Again</button><Link className="button button-secondary" to="/learning/history">Practice History</Link><Link className="button button-secondary" to={'/learning/topic/' + attempt.topic_id}>Review Topic</Link></div></section>
    {attempt.review?.length > 0 && <section className="learning-panel review-panel"><h2>Review Answers</h2>{attempt.review.map((item, index) => <article key={item.id}><span>Question {index + 1}</span><h3>{item.question}</h3><p className={item.answered ? (item.correct ? 'correct-text' : 'incorrect-text') : ''}>{item.answered ? (item.correct ? 'Correct' : 'Incorrect') : 'Not answered'}{item.correct_option ? ' · Correct option: ' + item.correct_option : ''}</p>{item.explanation && <p>{item.explanation}</p>}</article>)}</section>}</div>;
}

function ErrorPanel({ error, retry }) { return <div className="learning-error" role="alert"><p>{error}</p>{retry && <button className="button button-primary" onClick={retry}><RotateCw size={15}/> Retry</button>}</div>; }
