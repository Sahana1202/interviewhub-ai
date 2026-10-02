import { BookOpenCheck, BriefcaseBusiness, ChartNoAxesCombined, FileText, FolderOpen, GraduationCap, History, House, Languages, Layers3, MessageSquare, Target, X } from 'lucide-react';
import { Link, NavLink } from 'react-router-dom';

const links = [
  { label: 'Dashboard', path: '/dashboard', icon: House },
  { label: 'Interview Practice', path: '/interviews', icon: MessageSquare },
  { label: 'Resume Analyzer', path: '/resume', icon: FileText },
  { label: 'Job Match', path: '/job-match', icon: Target },
  { label: 'Company Preparation', path: '/companies', icon: BriefcaseBusiness },
  { label: 'Learning Hub', path: '/learning', icon: BookOpenCheck },
  { label: 'Aptitude', path: '/learning/aptitude', icon: Layers3 },
  { label: 'English Coach', path: '/learning/english', icon: Languages },
  { label: 'Placement Resources', path: '/resources', icon: FolderOpen },
  { label: 'Learning Roadmap', path: '/roadmap', icon: GraduationCap },
  { label: 'Performance', path: '/performance', icon: ChartNoAxesCombined },
  { label: 'Interview History', path: '/history', icon: History },
];

export default function Sidebar({ open, onClose }) {
  return <>
    {open && <button type="button" className="sidebar-scrim" aria-label="Close navigation" onClick={onClose}/>}
    <aside className={`signed-sidebar${open ? ' sidebar-open' : ''}`} aria-label="Main navigation">
      <div className="sidebar-brand-row"><Link className="brand-lockup" to="/dashboard" onClick={onClose}><span className="brand-icon"><BookOpenCheck size={19}/></span><span>InterviewHub <b>AI</b></span></Link><button className="sidebar-close" type="button" aria-label="Close navigation" onClick={onClose}><X size={18}/></button></div>
      <span className="sidebar-label">WORKSPACE</span>
      <nav className="sidebar-links">{links.map(({label,path,icon:Icon})=><NavLink key={path} end={path==='/dashboard'} className={({isActive})=>`signed-nav-link${isActive?' active':''}`} to={path} onClick={onClose}><Icon size={17}/><span>{label}</span></NavLink>)}</nav>
      <div className="signed-side-note">Learn, practise, and prepare for the roles you want.</div>
    </aside>
  </>;
}
