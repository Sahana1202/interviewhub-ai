import { Link } from 'react-router-dom';
import { ArrowRight, BookOpenCheck, MessageSquare, Sparkles } from 'lucide-react';

export default function LandingPage() {
  return <main className="min-h-screen landing-page">
    <nav className="landing-nav"><a className="brand-lockup" href="/"><span className="brand-icon"><Sparkles size={19}/></span><span>InterviewHub <b>AI</b></span></a><div><Link className="link-button" to="/login">Sign in</Link><Link className="button button-primary" to="/register">Get started <ArrowRight size={16}/></Link></div></nav>
    <section className="hero"><span className="eyebrow"><Sparkles size={15}/> YOUR PERSONAL AI CAREER &amp; INTERVIEW COACH</span><h1>Prepare with purpose.<br/><em>Show up ready.</em></h1><p>Build your skills and practise for the opportunities you want, one step at a time.</p><Link className="button button-primary" to="/register">Create your account <ArrowRight size={17}/></Link></section>
    <section className="feature-row"><article><span><BookOpenCheck size={20}/></span><h2>Learn &amp; improve</h2><p>A focused place for career learning and interview preparation.</p></article><article><span><MessageSquare size={20}/></span><h2>Practise interviews</h2><p>Prepare for conversations with structured, thoughtful practice.</p></article><article><span><Sparkles size={20}/></span><h2>Track your progress</h2><p>Build a foundation for a more personal preparation journey.</p></article></section>
  </main>;
}
