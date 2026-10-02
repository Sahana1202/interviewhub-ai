import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlignJustify, ChevronDown, LogOut, Settings, UserRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function TopNavbar({ sidebarOpen, onOpenNavigation }) {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();
  function signOut() {
    logout();
    navigate('/login', { replace: true });
  }
  return <header className="signed-topbar">
    <button className="mobile-menu-toggle" type="button" aria-label="Open navigation" aria-expanded={sidebarOpen} onClick={onOpenNavigation}><AlignJustify size={19}/></button>
    <span>Personal workspace</span>
    <details className="user-menu" open={menuOpen} onToggle={(event)=>setMenuOpen(event.currentTarget.open)}>
      <summary aria-label="Open user menu"><span className="user-avatar">{user?.name?.slice(0,1)?.toUpperCase()}</span><span>{user?.name}</span><ChevronDown size={15}/></summary>
      <div className="user-menu-panel"><div className="user-menu-name">{user?.name}</div><Link aria-label="Profile" to="/profile" onClick={()=>setMenuOpen(false)}><UserRound size={15}/><span>Profile</span></Link><Link aria-label="Settings" to="/settings" onClick={()=>setMenuOpen(false)}><Settings size={15}/><span>Settings</span></Link><button onClick={signOut}><LogOut size={15}/><span>Logout</span></button></div>
    </details>
  </header>;
}
