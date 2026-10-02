import { MessageSquareText } from 'lucide-react';

export default function TranscriptPanel({ questions }) {
  const answered = questions.filter((question) => question.answer);
  return <section className="transcript-panel"><div className="transcript-title"><MessageSquareText size={17}/><strong>Saved answers</strong><span>{answered.length}</span></div>{answered.length ? <ol>{answered.map((question)=><li key={question.id}><strong>{question.question_text}</strong><p>{question.answer.answer_text}</p><time>{new Date(question.answer.submitted_at).toLocaleString()}</time></li>)}</ol> : <p>Your submitted answers will appear here.</p>}</section>;
}
