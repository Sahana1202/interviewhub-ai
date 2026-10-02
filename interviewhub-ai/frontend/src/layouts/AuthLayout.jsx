import { Link, Outlet } from 'react-router-dom';
import { Sparkles } from 'lucide-react';

export default function AuthLayout() {
  return <main className="min-h-screen auth-page">
    <header className="auth-brand"><Link to="/" className="brand-lockup"><span className="brand-icon"><Sparkles size={19}/></span><span>InterviewHub <b>AI</b></span></Link></header>
    <section className="auth-panel"><Outlet /></section>
    <footer className="auth-footer">Your Personal AI Career &amp; Interview Coach</footer>
  </main>;
}
