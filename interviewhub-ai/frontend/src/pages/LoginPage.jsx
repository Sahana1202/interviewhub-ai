import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { ArrowRight, LoaderCircle, LockKeyhole } from 'lucide-react';
import { authApi, profileApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const { user, acceptSession, setUserProfile } = useAuth();
  const navigate = useNavigate();
  if (user) return <Navigate to={user.role === 'admin' ? '/admin' : user.profile?.onboarding_completed ? '/dashboard' : '/onboarding'} replace />;

  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const session = await authApi.login({ email, password });
      acceptSession(session);
      if (session.user.role === 'admin') { navigate('/admin', { replace: true }); return; }
      const profile = await profileApi.get();
      setUserProfile(profile);
      navigate(profile.onboarding_completed ? '/dashboard' : '/onboarding', { replace: true });
    }
    catch (cause) { setError(cause.message); }
    finally { setBusy(false); }
  }

  return <div className="auth-card"><span className="eyebrow">WELCOME BACK</span><h1>Sign in to your account</h1><p className="muted">Continue building your interview readiness.</p><form onSubmit={submit} className="form-stack"><label>Email address<input type="email" autoComplete="email" value={email} onChange={(e)=>setEmail(e.target.value)} required maxLength={320} placeholder="you@example.com"/></label><label>Password<input type="password" autoComplete="current-password" value={password} onChange={(e)=>setPassword(e.target.value)} required maxLength={128} placeholder="Your password"/></label>{error && <p className="form-error" role="alert">{error}</p>}<button className="button button-primary button-wide" disabled={busy}>{busy ? <LoaderCircle className="spin" size={17}/> : <>Sign in <ArrowRight size={17}/></>}</button></form><p className="auth-switch">New to InterviewHub AI? <Link to="/register">Create an account</Link></p><p className="secure-note"><LockKeyhole size={14}/> Your account details are protected.</p></div>;
}
