import { ArrowRight, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function ComingSoon({ title, description }) {
  return <section className="coming-soon-card"><span className="coming-icon"><Sparkles size={20}/></span><span className="coming-badge">COMING SOON</span><h2>{title}</h2><p>{description}</p><Link className="text-link" to="/dashboard">Back to dashboard <ArrowRight size={15}/></Link></section>;
}
