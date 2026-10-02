import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { ArrowRight, LoaderCircle } from 'lucide-react';
import { authApi, profileApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const { user, acceptSession, setUserProfile } = useAuth();
  const navigate = useNavigate();
  if (user) return <Navigate to={user.profile?.onboarding_completed ? '/dashboard' : '/onboarding'} replace />;

  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      acceptSession(await authApi.register({ name, email, password }));
      setUserProfile(await profileApi.get());
      navigate('/onboarding', { replace: true });
    }
    catch (cause) { setError(cause.message); }
    finally { setBusy(false); }
  }

  return <div className="auth-card"><span className="eyebrow">GET STARTED</span><h1>Create your account</h1><p className="muted">Start your personal career preparation workspace.</p><form onSubmit={submit} className="form-stack"><label>Full name<input autoComplete="name" value={name} onChange={(e)=>setName(e.target.value)} required maxLength={100} placeholder="Your name"/></label><label>Email address<input type="email" autoComplete="email" value={email} onChange={(e)=>setEmail(e.target.value)} required maxLength={320} placeholder="you@example.com"/></label><label>Password<input type="password" autoComplete="new-password" value={password} onChange={(e)=>setPassword(e.target.value)} required minLength={8} maxLength={128} placeholder="At least 8 characters"/></label>{error && <p className="form-error" role="alert">{error}</p>}<button className="button button-primary button-wide" disabled={busy}>{busy ? <LoaderCircle className="spin" size={17}/> : <>Create account <ArrowRight size={17}/></>}</button></form><p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p></div>;
}
