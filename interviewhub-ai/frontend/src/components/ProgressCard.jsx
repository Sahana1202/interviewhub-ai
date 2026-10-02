export default function ProgressCard({ label, value }) {
  const started = value !== null && value !== undefined;
  return <article className="progress-card"><div><strong>{label}</strong><span>{started ? `${value}%` : 'Not started'}</span></div>{started ? <div className="completion-track" role="progressbar" aria-label={`${label} progress`} aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}><span style={{width:`${value}%`}}/></div> : <p>Progress will appear after you begin.</p>}</article>;
}
