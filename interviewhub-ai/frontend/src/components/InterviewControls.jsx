import { Check, CirclePause, CirclePlay, LogOut } from 'lucide-react';

export default function InterviewControls({ status, submitting, answerPresent, onSubmit, onTogglePause, onEnd }) {
  const paused = status === 'paused';
  const active = status === 'in_progress';
  return <div className="interview-controls">
    <button type="button" className="button button-primary" onClick={onSubmit} disabled={!active || submitting || !answerPresent}><Check size={16}/>{submitting ? 'Saving…' : 'Submit answer'}</button>
    <div><button type="button" className="button button-secondary" onClick={onTogglePause} disabled={!active && !paused}>{paused ? <CirclePlay size={16}/> : <CirclePause size={16}/>} {paused ? 'Resume interview' : 'Pause interview'}</button><button type="button" className="button button-end" onClick={onEnd} disabled={!active && !paused}><LogOut size={16}/> End interview</button></div>
  </div>;
}
