import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children, profileStatus }) {
  const { user, loading } = useAuth();
  if (loading) return <main className="page-center"><p>Loading your workspace…</p></main>;
  if (!user) return <Navigate to="/login" replace />;
  const complete = Boolean(user.profile?.onboarding_completed);
  if (profileStatus === 'complete' && !complete) return <Navigate to="/onboarding" replace />;
  if (profileStatus === 'incomplete' && complete) return <Navigate to="/dashboard" replace />;
  return children;
}
