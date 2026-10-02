import { useEffect, useState } from 'react';
import { ArrowRight, BookOpenCheck, RotateCw } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import { learningApi } from '../services/api';

export default function LearningCategoryPage({ slugOverride }) {
  const { categoryId } = useParams(); const [category, setCategory] = useState(null);
  const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  async function load() {
    setLoading(true); setError('');
    try {
      let id = categoryId;
      if (slugOverride) id = (await learningApi.categories()).find((item) => item.slug === slugOverride)?.id;
      if (!id) throw new Error('Learning category not found.');
      setCategory(await learningApi.category(id));
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, [categoryId, slugOverride]);
  if (loading) return <div className="dashboard-content"><p role="status">Loading topics…</p></div>;
  return <div className="dashboard-content learning-page">
    <Link className="learning-back-link" to="/learning"><ArrowRight className="back-arrow" size={15}/> Learning Hub</Link>
    {error ? <div className="learning-error" role="alert"><p>{error}</p><button className="button button-primary" onClick={load}><RotateCw size={16}/> Retry</button></div> : <>
      <PageHeader eyebrow="PREPARATION AREA" title={category.name} description={category.description}/>
      {category.topics.length ? <div className="topic-list-grid">{category.topics.map((topic) => <Link className="learning-topic-card" to={'/learning/topic/' + topic.id} key={topic.id}><span className="learning-category-icon"><BookOpenCheck size={18}/></span><div><h2>{topic.name}</h2><p>{topic.description}</p><small>{topic.estimated_minutes} min · {topic.progress.completed ? 'Completed' : topic.progress.progress_percent > 0 ? 'In progress' : topic.difficulty}</small></div><ArrowRight size={16}/></Link>)}</div> : <div className="learning-empty"><strong>No learning topics are available yet.</strong></div>}
    </>}
  </div>;
}
