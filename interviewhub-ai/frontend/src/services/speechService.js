export function speechAvailable() {
  return typeof window !== 'undefined' && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
}

export function stopSpeech() {
  if (speechAvailable()) window.speechSynthesis.cancel();
}

export function speakQuestion(text, preferredVoiceName) {
  if (!speechAvailable()) return false;
  stopSpeech();
  const utterance = new SpeechSynthesisUtterance(text);
  const voice = window.speechSynthesis.getVoices().find((item) => item.name.toLowerCase().includes((preferredVoiceName || '').toLowerCase()))
    || window.speechSynthesis.getVoices().find((item) => item.lang.toLowerCase().startsWith((navigator.language || 'en').slice(0, 2).toLowerCase()));
  if (voice) utterance.voice = voice;
  utterance.rate = 0.96;
  window.speechSynthesis.speak(utterance);
  return true;
}
