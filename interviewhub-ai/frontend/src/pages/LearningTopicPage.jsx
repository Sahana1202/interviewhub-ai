import { useCallback, useEffect, useState } from 'react';
import { ArrowRight, CheckCircle2, Circle, RotateCw } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import { learningApi } from '../services/api';

export default function LearningTopicPage() {
  const { topicId } = useParams(); const [topic, setTopic] = useState(null);
  const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [saving, setSaving] = useState(false);
  const load = useCallback(async () => { setLoading(true); setError(''); try { setTopic(await learningApi.topic(topicId)); } catch (e) { setError(e.message); } finally { setLoading(false); } }, [topicId]);
  useEffect(() => { load(); }, [load]);
  async function markComplete() { setSaving(true); setError(''); try { await learningApi.completeTopic(topicId); await load(); } catch (e) { setError(e.message); } finally { setSaving(false); } }
  if (loading) return <div className="dashboard-content"><p role="status">Loading topic…</p></div>;
  if (error && !topic) return <div className="dashboard-content"><div className="learning-error" role="alert"><p>{error}</p><button className="button button-primary" onClick={load}><RotateCw size={16}/> Retry</button></div></div>;
  const content = topic.content || {};
  return <div className="dashboard-content learning-page">
    <Link className="learning-back-link" to={'/learning/category/' + topic.category_id}><ArrowRight className="back-arrow" size={15}/> {topic.category_name}</Link>
    <PageHeader eyebrow={topic.category_name.toUpperCase()} title={topic.name} description={topic.description}/>
    {error && <div className="learning-error" role="alert">{error}<button onClick={load}>Retry</button></div>}
    <div className="topic-detail-layout"><main className="topic-content-column">
      <section className="learning-panel"><h2>Overview</h2><p>{content.definition}</p><p>{content.why_it_matters}</p><p>{content.simple_explanation}</p></section>
      <section className="learning-panel"><h2>Example</h2><p>{content.example}</p></section>
      {content.why_interviewers_ask && <section className="learning-panel"><h2>HR preparation</h2><h3>Why interviewers ask</h3><p>{content.why_interviewers_ask}</p><h3>What to include</h3><Bullets items={content.what_to_include}/><h3>Suggested structure</h3><Bullets items={content.suggested_structure}/><h3>Common mistakes</h3><Bullets items={content.common_mistakes}/><p className="learning-note">Use this as a flexible guide. There is no single correct answer for every company.</p></section>}
      <section className="learning-panel"><h2>Key interview points</h2><Bullets items={content.key_interview_points}/></section>
      <section className="learning-panel"><h2>Quick revision</h2><Bullets items={content.quick_revision}/></section>
      <section className="learning-panel"><h2>Practice prompts</h2><Bullets items={content.practice_prompts}/><p className="learning-note">These are InterviewHub practice prompts, not questions attributed to an employer.</p></section>
      <section className="learning-panel"><h2>Resources</h2>{topic.resources?.length ? topic.resources.map((resource) => <Resource key={resource.id} resource={resource}/>) : <p>No external resources are attached. This internal lesson is available without external links.</p>}</section>
    </main><aside className="topic-sidebar">
      <section className="learning-panel topic-progress-panel"><h2>Your progress</h2><div className="learning-progress-track" role="progressbar" aria-label="Topic progress" aria-valuenow={topic.progress.progress_percent} aria-valuemin="0" aria-valuemax="100"><span style={{ width: topic.progress.progress_percent + '%' }}/></div><strong>{topic.progress.progress_percent}% Topic Progress</strong><p>{topic.progress.questions_attempted} questions attempted · {topic.progress.questions_correct} correct</p><p>{topic.progress.practice_accuracy == null ? 'Practice Accuracy: no scored answers yet' : 'Practice Accuracy: ' + topic.progress.practice_accuracy + '%'}</p>{topic.progress.completed ? <p className="learning-completed"><CheckCircle2 size={16}/> Topic completed</p> : <button className="button button-secondary button-wide" onClick={markComplete} disabled={saving}><Circle size={16}/>{saving ? 'Saving…' : 'Mark topic complete'}</button>}</section>
      <section className="learning-panel"><h2>Practice</h2><p>{topic.practice_options?.length ? topic.practice_options.reduce((sum, item) => sum + item.question_count, 0) + ' scored questions available.' : 'No scored questions are available for this topic yet.'}</p>{topic.practice_options?.length > 0 && <Link className="button button-primary button-wide" to={'/learning/practice?topic_id=' + topic.id}>Practice Questions <ArrowRight size={15}/></Link>}</section>
    </aside></div>
  </div>;
}

function Bullets({ items = [] }) { return items.length ? <ul className="learning-bullets">{items.map((item, i) => <li key={i}>{item}</li>)}</ul> : null; }
function Resource({ resource }) { return <article className="learning-resource-row"><div><strong>{resource.title}</strong><p>{resource.description}</p><small>{resource.source} · {resource.resource_type}{resource.provider ? ' · ' + resource.provider : ''}</small></div>{resource.url && <a href={resource.url} target="_blank" rel="noreferrer">Open resource</a>}</article>; }
