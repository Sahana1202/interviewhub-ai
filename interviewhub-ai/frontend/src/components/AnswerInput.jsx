import VoiceRecorder from './VoiceRecorder';

export default function AnswerInput({ value, onChange, responseMode, disabled, onRecordingChange }) {
  return <div className="answer-input"><label htmlFor="interview-answer">Your answer</label><textarea id="interview-answer" value={value} onChange={(event)=>onChange(event.target.value)} maxLength={12000} placeholder="Take a moment to structure your thoughts, then type or dictate your answer…" disabled={disabled}/><div className="answer-input-footer"><span>{value.length}/12,000 characters</span>{responseMode === 'voice' && <VoiceRecorder disabled={disabled} onTranscript={onChange} onRecordingChange={onRecordingChange}/>}</div><small className="text-mode-note">Your answer is saved to this interview session. No AI evaluation is performed yet.</small></div>;
}
