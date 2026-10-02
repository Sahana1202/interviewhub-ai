import { useCallback, useEffect, useState } from 'react';
import { ArrowRight, RotateCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import { learningApi, practiceApi } from '../services/api';

export default function LearningHistoryPage() {
  const [categories, setCategories] = useState([]); const [topics, setTopics] = useState([]);
  const [categoryId, setCategoryId] = useState(''); const [topicId, setTopicId] = useState('');
  const [dateFrom, setDateFrom] = useState(''); const [dateTo, setDateTo] = useState('');
  const [attempts, setAttempts] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const params = {};
      if (categoryId) params.category_id = Number(categoryId);
      if (topicId) params.topic_id = Number(topicId);
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const [history, categoryRows, topicData] = await Promise.all([practiceApi.history(params), learningApi.categories(), learningApi.topics(categoryId ? { category_id: Number(categoryId) } : {})]);
      setAttempts(history.attempts); setCategories(categoryRows); setTopics(topicData.topics);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [categoryId, topicId, dateFrom, dateTo]);
  useEffect(() => { load(); }, [load]);
  return <div className="dashboard-content learning-page"><PageHeader eyebrow="LEARNING HISTORY" title="Recent Practice" description="Review your own saved attempts and practice accuracy."/>
    <form className="history-filters" onSubmit={(event) => { event.preventDefault(); load(); }}>
      <label className="learning-field">Category<select value={categoryId} onChange={(event) => { setCategoryId(event.target.value); setTopicId(''); }}><option value="">All categories</option>{categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label className="learning-field">Topic<select value={topicId} onChange={(event) => setTopicId(event.target.value)}><option value="">All topics</option>{topics.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label className="learning-field">From<input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)}/></label>
      <label className="learning-field">To<input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)}/></label>
      <button className="button button-secondary">Apply filters</button>
    </form>
    {loading ? <p role="status">Loading practice history…</p> : error ? <div className="learning-error" role="alert"><p>{error}</p><button className="button button-primary" onClick={load}><RotateCw size={15}/> Retry</button></div> : attempts.length ? <div className="history-attempt-list">{attempts.map((item) => <Link to={'/learning/practice/' + item.id} key={item.id}><div><strong>{item.topic}</strong><small>{item.category} · {item.status === 'completed' ? 'Completed' : 'In progress'} · {new Date(item.started_at).toLocaleString()}</small></div><span>{item.correct_answers}/{item.total_questions}<small>{item.accuracy}% accuracy</small></span><ArrowRight size={16}/></Link>)}</div> : <div className="learning-empty"><strong>No practice attempts yet.</strong><p>Start a topic to see your practice history here.</p><Link className="text-link" to="/learning/practice">Start practice <ArrowRight size={14}/></Link></div>}
  </div>;
}
