import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { authApi } from '../services/api';

const AuthContext = createContext(null);
const TOKEN_KEY = 'interviewhub_access_token';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) { setLoading(false); return; }
    authApi.me().then(setUser).catch(() => {
      localStorage.removeItem(TOKEN_KEY);
      setUser(null);
    }).finally(() => setLoading(false));
  }, []);

  const acceptSession = useCallback((session) => {
    if (!session?.access_token || !session?.user) throw new Error('The server returned an invalid authentication response.');
    localStorage.setItem(TOKEN_KEY, session.access_token);
    setUser(session.user);
  }, []);

  const setUserProfile = useCallback((profile) => {
    setUser((current) => current ? { ...current, profile } : current);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  useEffect(() => {
    window.addEventListener('interviewhub:unauthorized', logout);
    return () => window.removeEventListener('interviewhub:unauthorized', logout);
  }, [logout]);

  const value = useMemo(() => ({ user, loading, acceptSession, setUserProfile, logout }), [user, loading, acceptSession, setUserProfile, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider');
  return context;
}
