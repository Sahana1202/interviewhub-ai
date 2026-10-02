import { useEffect, useRef, useState } from 'react';
import { Mic, MicOff } from 'lucide-react';

function recognitionConstructor() {
  if (typeof window === 'undefined') return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

export default function VoiceRecorder({ onTranscript, onRecordingChange, disabled }) {
  const [recording, setRecording] = useState(false);
  const [message, setMessage] = useState('');
  const recognition = useRef(null);
  const Constructor = recognitionConstructor();

  useEffect(() => () => {
    const activeRecognition = recognition.current;
    if (!activeRecognition) return;
    activeRecognition.onend = null;
    activeRecognition.onerror = null;
    activeRecognition.onresult = null;
    try { activeRecognition.stop(); } catch { /* Browser may already have stopped recognition. */ }
  }, []);

  function start() {
    setMessage('');
    if (!Constructor) { setMessage("Voice input isn't supported in this browser. You can continue using text input."); return; }
    try {
      const instance = new Constructor();
      instance.lang = navigator.language || 'en-US';
      instance.interimResults = true;
      instance.continuous = true;
      instance.onresult = (event) => {
        const text = Array.from(event.results).map((result) => result[0]?.transcript || '').join(' ').trim();
        onTranscript(text);
      };
      instance.onerror = (event) => {
        const errors = {
          'not-allowed': 'Microphone permission was denied. You can continue using text input.',
          'service-not-allowed': 'Speech recognition is not allowed here. You can continue using text input.',
          'audio-capture': 'No microphone was found. You can continue using text input.',
          network: 'Speech recognition had a network error. You can continue using text input.',
          'no-speech': 'No speech was detected. Try again or type your answer.',
        };
        setMessage(errors[event.error] || 'Speech recognition stopped unexpectedly. You can continue using text input.');
        setRecording(false);
        onRecordingChange?.(false);
      };
      instance.onend = () => { setRecording(false); onRecordingChange?.(false); };
      instance.start();
      recognition.current = instance;
      setRecording(true);
      onRecordingChange?.(true);
    } catch (error) {
      setMessage(error?.name === 'NotAllowedError' ? 'Microphone permission was denied. You can continue using text input.' : 'The microphone could not be started. You can continue using text input.');
      setRecording(false);
      onRecordingChange?.(false);
    }
  }

  function stop() {
    try { recognition.current?.stop(); } catch { /* Already stopped. */ }
    setRecording(false);
    onRecordingChange?.(false);
  }

  useEffect(() => { if (disabled && recording) stop(); }, [disabled, recording]);

  return <div className="voice-recorder"><button type="button" className={`button ${recording ? 'button-recording' : 'button-secondary'}`} onClick={recording ? stop : start} disabled={disabled} aria-pressed={recording}>{recording ? <MicOff size={16}/> : <Mic size={16}/>} {recording ? 'Stop recording' : 'Record answer'}</button>{message && <p className="voice-note" role="status">{message}</p>}</div>;
}
