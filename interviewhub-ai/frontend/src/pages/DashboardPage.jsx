import { useCallback, useEffect, useState } from 'react';
import { ArrowRight, BookOpenCheck, BriefcaseBusiness, FileText, MessageSquare, RotateCw, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import EmptyState from '../components/EmptyState';
import PageHeader from '../components/PageHeader';
import ProgressCard from '../components/ProgressCard';
import QuickActionCard from '../components/QuickActionCard';
import { dashboardApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

const actions = [
  { title: 'Interview Practice', description: 'Explore guided practice', to: '/interviews', icon: MessageSquare },
  { title: 'Resume Analyzer', description: 'Prepare your resume', to: '/resume', icon: FileText },
  { title: 'Company Preparation', description: 'Plan your research', to: '/companies', icon: BriefcaseBusiness },
  { title: 'Learning Hub', description: 'Browse learning paths', to: '/learning', icon: BookOpenCheck },
];

function greeting() {
  const hour = new Date().getHours();
  return hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setDashboard(await dashboardApi.get()); }
    catch (requestError) { setError(requestError.message || 'Dashboard could not be loaded.'); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="dashboard-content"><div className="dashboard-loading" role="status">Loading your dashboard…</div></div>;
  if (error) return <div className="dashboard-content"><PageHeader eyebrow="YOUR PREPARATION SPACE" title={`Welcome, ${user?.name?.split(/\s+/)[0] || 'there'}`} description="Your preparation overview is temporarily unavailable."/><div className="dashboard-error" role="alert"><p>{error}</p><button className="button button-primary" onClick={load}><RotateCw size={16}/> Try again</button></div></div>;
  const firstName = dashboard.name.split(/\s+/)[0];
  const profile = dashboard.profile;
  return <div className="dashboard-content">
    <PageHeader eyebrow="YOUR PREPARATION SPACE" title={`${greeting()}, ${firstName}`} description="A clear view of your career direction and next steps."/>
    <section className="dashboard-top-grid">
      <article className="profile-overview-card">
        <div className="overview-heading"><div><span className="eyebrow">PROFILE COMPLETION</span><h2>{dashboard.profile_completion}% complete</h2></div><span className="completion-spark"><Sparkles size={18}/></span></div>
        <div className="completion-track" role="progressbar" aria-label="Profile completion" aria-valuenow={dashboard.profile_completion} aria-valuemin={0} aria-valuemax={100}><span style={{width:`${dashboard.profile_completion}%`}}/></div>
        <p className="profile-completion-copy">Based on your saved education and career profile fields.</p>
        <Link className="text-link" to="/profile">{dashboard.profile_completion < 100 ? 'Complete your profile' : 'Review your profile'} <ArrowRight size={15}/></Link>
      </article>
      <article className="goal-card"><span className="eyebrow">YOUR CAREER GOAL</span><h2>{profile.target_role || 'Role not set'}</h2><div className="goal-details"><span>{profile.target_industry || 'Industry not set'}</span><span>{profile.experience_level || 'Experience not set'}</span></div><Link className="text-link" to="/profile">Edit goal <ArrowRight size={15}/></Link></article>
    </section>
    <section className="dashboard-section"><div className="section-heading"><div><span className="eyebrow">GET STARTED</span><h2>Quick actions</h2></div></div><div className="quick-action-grid">{actions.map((action)=><QuickActionCard key={action.to} {...action}/>)}</div></section>
    <section className="dashboard-section"><div className="section-heading"><div><span className="eyebrow">YOUR ACTIVITY</span><h2>Preparation overview</h2></div></div><div className="progress-grid"><ProgressCard label="Technical" value={dashboard.progress.technical}/><ProgressCard label="Aptitude" value={dashboard.progress.aptitude}/><ProgressCard label="English" value={dashboard.progress.english}/><ProgressCard label="Interview" value={dashboard.progress.interview}/></div></section>
    <section className="dashboard-section"><div className="section-heading"><div><span className="eyebrow">SAVED TOPIC ACTIVITY</span><h2>Your Learning Progress</h2></div><Link className="text-link" to="/learning">Learning Hub <ArrowRight size={14}/></Link></div>{dashboard.learning_progress?.length ? <div className="learning-topic-cards">{dashboard.learning_progress.slice(0, 4).map((item)=><Link className="progress-topic-card" to={'/learning/topic/' + item.topic_id} key={item.topic_id}><div><strong>{item.topic}</strong><span>{item.progress_percent}%</span></div><div className="learning-progress-track" role="progressbar" aria-label={item.topic + ' topic progress'} aria-valuenow={item.progress_percent} aria-valuemin="0" aria-valuemax="100"><span style={{width:item.progress_percent+'%'}}/></div><small>{item.practice_accuracy == null ? 'Practice accuracy: no scored answers yet' : 'Practice accuracy: ' + item.practice_accuracy + '%'}</small></Link>)}</div> : <EmptyState title="No learning activity yet" description="Start your first topic to track learning progress." action={<Link className="text-link" to="/learning">Start your first topic <ArrowRight size={14}/></Link>}/>}</section>
    <section className="dashboard-section"><div className="section-heading"><div><span className="eyebrow">YOUR NEXT STEP</span><h2>Recommended Practice</h2></div></div>{dashboard.recommended_learning?.length ? <div className="recommendation-list">{dashboard.recommended_learning.slice(0, 3).map((item)=><Link to={'/learning/topic/' + item.topic_id} key={item.topic_id}><span><strong>{item.topic}</strong><small>{item.reason}</small></span><ArrowRight size={15}/></Link>)}</div> : <EmptyState title="No recommendations yet" description="Start a lesson or practice set to personalize your next suggested topic." action={<Link className="text-link" to="/learning">Browse learning <ArrowRight size={14}/></Link>}/>}</section>
    <section className="dashboard-section"><div className="section-heading"><div><span className="eyebrow">SUGGESTED STARTING POINTS</span><h2>Starter recommendations</h2></div></div>{dashboard.recommended_topics.length ? <><p className="recommendation-note">Based on your saved target role. These are starter topics, not personalized AI recommendations.</p><div className="topic-list">{dashboard.recommended_topics.map((topic)=><span key={topic}>{topic}</span>)}</div></> : <EmptyState title="Add a target role to get started" description="Complete your profile to see starter topics for your chosen role." action={<Link className="text-link" to="/profile">Complete profile <ArrowRight size={15}/></Link>}/>}</section>
    <section className="dashboard-section"><div className="section-heading"><div><span className="eyebrow">RECENT ACTIVITY</span><h2>Recent activity</h2></div></div>{dashboard.recent_activity.length ? <div className="activity-list">{dashboard.recent_activity.map((activity)=><article key={activity.id}><strong>{activity.title}</strong><p>{activity.description}</p><time>{activity.occurred_at}</time></article>)}</div> : <EmptyState title="Nothing here yet" description="Your completed practice and learning activity will appear here."/>}</section>
  </div>;
}
