import { Clock3 } from 'lucide-react';

export function formatTime(seconds) {
  const safe = Math.max(0, Math.floor(seconds || 0));
  return `${String(Math.floor(safe / 60)).padStart(2, '0')}:${String(safe % 60).padStart(2, '0')}`;
}

export default function InterviewTimer({ seconds, paused = false }) {
  return <div className={`interview-timer${seconds <= 60 ? ' timer-ending' : ''}`} role="timer" aria-label={`Time remaining ${formatTime(seconds)}`}><Clock3 size={17}/><span>{formatTime(seconds)}</span>{paused && <small>Paused</small>}</div>;
}
