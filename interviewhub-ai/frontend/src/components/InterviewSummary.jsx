export default function InterviewSummary({ company, role, experience, type, difficulty, duration, interviewer, responseMode }) {
  const rows = [
    ['Company', company || 'General Interview'], ['Role', role], ['Experience', experience], ['Type', type],
    ['Difficulty', difficulty], ['Duration', `${duration} minutes`], ['Virtual HR', interviewer?.name || interviewer || '—'], ['Response', responseMode],
  ];
  return <section className="interview-summary"><span className="eyebrow">INTERVIEW SUMMARY</span><h2>Review your setup</h2><dl>{rows.map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl></section>;
}
