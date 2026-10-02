import { Check, UserRound } from 'lucide-react';
import { virtualHrAvatars } from '../config/virtualHrAvatars';

export default function InterviewerCard({ interviewer, selected, onSelect }) {
  return <button type="button" className={`interviewer-card${selected ? ' selected' : ''}`} aria-pressed={selected} onClick={onSelect}>
    <span className="interviewer-avatar">{virtualHrAvatars[interviewer.id] ? <img src={virtualHrAvatars[interviewer.id]} alt={`${interviewer.name} virtual interviewer portrait`}/> : <UserRound size={23} />}{selected && <i><Check size={12}/></i>}</span>
    <span className="interviewer-card-copy"><strong>{interviewer.name}</strong><small>{interviewer.role}</small><small>{interviewer.description}</small><span className="interviewer-styles">{interviewer.style.join(' · ')}</span></span>
  </button>;
}
