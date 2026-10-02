import { Headphones, MessageCircle, Pause, Sparkles } from 'lucide-react';
import { virtualHrAvatars } from '../config/virtualHrAvatars';

const stateContent = {
  idle: ['Ready when you are', Sparkles],
  asking: ['Asking a question', MessageCircle],
  listening: ['Listening to your response', Headphones],
  thinking: ['Saving your answer', Pause],
};

export default function HRAvatar({ interviewer, state = 'idle', statusLabel }) {
  const [defaultLabel, Icon] = stateContent[state] || stateContent.idle;
  const label = statusLabel || defaultLabel;
  return <section className={`hr-avatar-card avatar-${state}`} aria-label={`${interviewer?.name || 'Virtual HR'} interviewer`}>
    <div className="hr-avatar-circle" aria-hidden="true">{interviewer && virtualHrAvatars[interviewer.id] ? <span className="hr-avatar-photo"><img src={virtualHrAvatars[interviewer.id]} alt=""/></span> : <span className="hr-avatar-initial">{interviewer?.name?.slice(0, 1)?.toUpperCase() || 'H'}</span>}<Icon className="hr-avatar-state-icon" size={18}/></div>
    <span className="virtual-label">AI VIRTUAL INTERVIEWER</span>
    <h2>{interviewer?.name || 'Virtual HR'}</h2>
    <p>{interviewer?.role || 'Virtual HR Interviewer'}</p>
    <div className="avatar-status"><i/>{label}</div>
  </section>;
}
