import { ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function QuickActionCard({ title, description, to, icon: Icon }) {
  return <Link className="quick-action-card" to={to}><span className="quick-action-icon"><Icon size={19}/></span><span className="quick-action-copy"><strong>{title}</strong><small>{description}</small></span><ArrowUpRight className="quick-action-arrow" size={17}/></Link>;
}
