import { useCallback, useEffect, useState } from 'react';
import { ArrowRight, BookOpenCheck, BriefcaseBusiness, Calculator, Code2, Languages, RotateCw, Users } from 'lucide-react';
import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import { learningApi } from '../services/api';

const icons = { technical: Code2, hr: Users, aptitude: Calculator, 'professional-english': Languages, 'placement-resources': BriefcaseBusiness };

export default function LearningHubPage() {
  const [data, setData] = useState({ categories: [], progress: [], recommendations: null });
  const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [categories, progress, recommendations] = await Promise.all([learningApi.categories(), learningApi.progress(), learningApi.recommendations()]);
      setData({ categories, progress, recommendations });
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  if (loading) return <div className="dashboard-content"><p role="status">Loading learning topics…</p></div>;
  if (error) return <div className="dashboard-content"><PageHeader eyebrow="LEARNING HUB" title="Learn. Practice. Improve." description="Your learning center for placement preparation."/><div className="learning-error" role="alert"><p>{error}</p><button className="button button-primary" onClick={load}><RotateCw size={16}/> Retry</button></div></div>;
  const continueTopics = data.progress.filter((item) => !item.completed).slice(0, 4);
  const recommendations = data.recommendations?.recommended_topics || [];
  const companyPrep = data.recommendations?.company_preparation;
  const firstPractice = recommendations[0];
  return <div className="dashboard-content learning-page">
    <PageHeader eyebrow="LEARNING HUB" title="Learn. Practice. Improve." description="Build interview readiness with concise lessons and scored practice."/>
    <section className="learning-category-grid" aria-label="Preparation areas">{data.categories.map((category) => {
      const Icon = icons[category.slug] || BookOpenCheck;
      const target = category.slug === 'placement-resources' ? '/resources' : category.slug === 'professional-english' ? '/learning/english' : '/learning/category/' + category.id;
      return <Link className="learning-category-card" to={target} key={category.id}><span className="learning-category-icon"><Icon size={20}/></span><h2>{category.name}</h2><p>{category.description}</p><div><span>{category.topic_count} topics</span>{category.topic_count > 0 && <span>{category.progress_percent}% topic progress</span>}</div><ArrowRight size={16}/></Link>;
    })}</section>
    <section className="dashboard-section"><div className="section-heading"><div><span className="eyebrow">PICK UP WHERE YOU LEFT OFF</span><h2>Continue Learning</h2></div><Link className="text-link" to="/learning/history">Practice history <ArrowRight size={14}/></Link></div>
      {continueTopics.length ? <div className="learning-topic-cards">{continueTopics.map((item) => <ProgressTopic key={item.topic_id} item={item}/>)}</div> : <div className="learning-empty"><strong>No learning activity yet.</strong><p>Start your first topic to create a saved progress record.</p><Link className="text-link" to={data.categories[0] ? '/learning/category/' + data.categories[0].id : '/learning'}>Browse topics <ArrowRight size={14}/></Link></div>}
    </section>
    <section className="dashboard-section learning-highlight"><div><span className="eyebrow">TODAY'S PRACTICE</span><h2>Practice a few questions</h2><p>Choose a topic and get instant feedback with explanations.</p></div><Link className="button button-primary" to={firstPractice ? '/learning/practice?topic_id=' + firstPractice.topic_id : '/learning/practice'}>Start Practice <ArrowRight size={16}/></Link></section>
    <section className="dashboard-section"><div className="section-heading"><div><span className="eyebrow">BASED ON YOUR ACTIVITY</span><h2>Recommended For You</h2></div></div>
      {recommendations.length ? <div className="recommendation-list">{recommendations.slice(0, 5).map((item) => <Link to={'/learning/topic/' + item.topic_id} key={item.topic_id}><span><strong>{item.topic}</strong><small>{item.reason}</small></span><ArrowRight size={16}/></Link>)}</div> : <div className="learning-empty"><strong>No recommendations yet.</strong><p>Learning recommendations will appear as you start topics and practice.</p></div>}
    </section>
    <section className="dashboard-section company-learning-card"><div><span className="eyebrow">COMPANY PREPARATION</span><h2>{companyPrep?.company_name ? 'Prepare for ' + companyPrep.company_name : 'Company preparation topics'}</h2><p>{companyPrep?.message || 'No company-specific learning content is currently available.'}</p>{companyPrep?.topics?.length > 0 && <div className="learning-pills">{companyPrep.topics.map((topic, i) => <span key={topic.topic + i}>{topic.topic} · {topic.verification_status.replaceAll('_', ' ')}</span>)}</div>}</div><Link className="button button-secondary" to="/company">Company Intelligence <ArrowRight size={15}/></Link></section>
  </div>;
}

function ProgressTopic({ item }) {
  return <Link className="progress-topic-card" to={'/learning/topic/' + item.topic_id}><div><strong>{item.topic}</strong><span>{item.progress_percent}%</span></div><div className="learning-progress-track" role="progressbar" aria-label={item.topic + ' topic progress'} aria-valuenow={item.progress_percent} aria-valuemin="0" aria-valuemax="100"><span style={{ width: item.progress_percent + '%' }}/></div><small>{item.practice_accuracy == null ? 'Practice accuracy: no scored answers yet' : 'Practice accuracy: ' + item.practice_accuracy + '%'}</small></Link>;
}
