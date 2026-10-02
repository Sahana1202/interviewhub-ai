import { Volume2, VolumeX } from 'lucide-react';
import { speechAvailable, speakQuestion, stopSpeech } from '../services/speechService';

export default function QuestionPanel({ question, interviewer, questionNumber, totalQuestions }) {
  function replay() {
    if (!speechAvailable()) return;
    speakQuestion(question.question_text, interviewer?.voice_name);
  }
  return <section className="question-panel"><div className="question-panel-top"><div><span className="eyebrow">QUESTION {questionNumber}{totalQuestions ? ` OF ${totalQuestions}` : ''}</span><span className="question-category">{question.category} · {question.difficulty}</span><span className="question-source-label">{question.question_source==='ai_generated'?'AI-generated practice question':'Rule-based practice question'}</span></div><div className="speech-controls">{speechAvailable() ? <><button type="button" className="icon-button" onClick={replay} aria-label="Replay question"><Volume2 size={17}/></button><button type="button" className="icon-button" onClick={stopSpeech} aria-label="Mute or stop speech"><VolumeX size={17}/></button></> : <small>Speech playback isn't supported in this browser.</small>}</div></div><h2>{question.question_text}</h2><p>Take a moment to think through your response before you submit.</p></section>;
}
