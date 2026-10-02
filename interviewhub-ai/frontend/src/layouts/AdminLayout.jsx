import { BarChart3, BookOpen, Building2, ClipboardList, GraduationCap, LayoutDashboard, LogOut, Users } from 'lucide-react';
import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './admin.css';

const links = [['/admin','Overview',LayoutDashboard],['/admin/users','Users',Users],['/admin/companies','Companies',Building2],['/admin/learning','Learning Content',BookOpen],['/admin/resources','Placement Resources',GraduationCap],['/admin/interviews','Interview Analytics',BarChart3],['/admin/activity-logs','Activity Logs',ClipboardList]];
export default function AdminLayout(){
  const {user,logout}=useAuth();
  return <div className="admin-shell"><aside className="admin-sidebar"><div className="admin-brand">InterviewHub <b>AI</b><small>ADMIN CONSOLE</small></div><nav aria-label="Admin navigation">{links.map(([to,label,Icon])=><NavLink key={to} end={to==='/admin'} to={to}><Icon size={17}/>{label}</NavLink>)}</nav><button className="admin-logout" onClick={logout}><LogOut size={17}/>Log out</button></aside><main className="admin-main"><header className="admin-top"><span>Platform administration</span><span className="admin-profile">{user?.name} <small>Administrator</small></span></header><Outlet/></main></div>
}
